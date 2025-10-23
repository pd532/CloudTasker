from flask import Flask, render_template, request, redirect, session, flash, jsonify, send_file
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
import pymysql
import boto3
import datetime
import os
from functools import wraps
from werkzeug.utils import secure_filename
import uuid
from config import db_config, s3_config, app_config

app = Flask(__name__)
app.secret_key = app_config['secret_key']
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['WTF_CSRF_ENABLED'] = True

bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)

# S3 Client
s3_client = boto3.client(
    's3',
    region_name=s3_config['region'],
    aws_access_key_id=s3_config.get('access_key'),
    aws_secret_access_key=s3_config.get('secret_key')
)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Database connection
def get_connection():
    return pymysql.connect(
        host=db_config["host"],
        user=db_config["user"],
        password=db_config["password"],
        database=db_config["database"],
        cursorclass=pymysql.cursors.DictCursor
    )


# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect('/login')
        return f(*args, **kwargs)

    return decorated_function


# Initialize database tables
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tasks table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            task TEXT NOT NULL,
            description TEXT,
            priority ENUM('low', 'medium', 'high') DEFAULT 'medium',
            status ENUM('pending', 'in_progress', 'completed') DEFAULT 'pending',
            category VARCHAR(50),
            due_date DATE,
            attachment_url VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Shared tasks table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS shared_tasks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            task_id INT NOT NULL,
            shared_by INT NOT NULL,
            shared_with INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
            FOREIGN KEY (shared_by) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (shared_with) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


@app.route('/')
@login_required
def home():
    conn = get_connection()
    cur = conn.cursor()

    # Get filter parameters
    status_filter = request.args.get('status', 'all')
    priority_filter = request.args.get('priority', 'all')
    search_query = request.args.get('search', '')

    # Build query
    query = """
        SELECT t.*, 
               (SELECT username FROM users WHERE id = t.user_id) as owner
        FROM tasks t
        WHERE (t.user_id = %s 
               OR t.id IN (SELECT task_id FROM shared_tasks WHERE shared_with = %s))
    """
    params = [session['user_id'], session['user_id']]

    if status_filter != 'all':
        query += " AND t.status = %s"
        params.append(status_filter)

    if priority_filter != 'all':
        query += " AND t.priority = %s"
        params.append(priority_filter)

    if search_query:
        query += " AND (t.task LIKE %s OR t.description LIKE %s)"
        params.extend([f'%{search_query}%', f'%{search_query}%'])

    query += " ORDER BY t.created_at DESC"

    cur.execute(query, params)
    tasks = cur.fetchall()

    # Get task statistics
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress
        FROM tasks 
        WHERE user_id = %s
    """, (session['user_id'],))
    stats = cur.fetchone()

    conn.close()
    return render_template('tasks.html', tasks=tasks, stats=stats, username=session.get('username'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect('/')

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Please provide both username and password.', 'danger')
            return render_template('login.html')

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        conn.close()

        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f'Welcome back, {username}!', 'success')
            return redirect('/')
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect('/')

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        # Hash password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                (username, email, hashed_password)
            )
            conn.commit()
            conn.close()
            flash('Registration successful! Please login.', 'success')
            return redirect('/login')
        except pymysql.IntegrityError:
            flash('Username or email already exists.', 'danger')

    return render_template('register.html')


@app.route('/add', methods=['POST'])
@login_required
def add():
    task = request.form.get('task', '').strip()
    description = request.form.get('description', '').strip()
    priority = request.form.get('priority', 'medium')
    category = request.form.get('category', '').strip()
    due_date = request.form.get('due_date', None)

    if not task:
        flash('Task title is required.', 'danger')
        return redirect('/')

    attachment_url = None
    if 'attachment' in request.files:
        file = request.files['attachment']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"

            try:
                s3_client.upload_fileobj(
                    file,
                    s3_config['bucket_name'],
                    unique_filename,
                    ExtraArgs={'ACL': 'private'}
                )
                attachment_url = unique_filename
            except Exception as e:
                flash(f'Error uploading file: {str(e)}', 'warning')

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO tasks (user_id, task, description, priority, category, due_date, attachment_url) 
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (session['user_id'], task, description, priority, category, due_date or None, attachment_url)
    )
    conn.commit()
    conn.close()

    flash('Task added successfully!', 'success')
    return redirect('/')


@app.route('/update/<int:id>', methods=['POST'])
@login_required
def update(id):
    conn = get_connection()
    cur = conn.cursor()

    # Check ownership
    cur.execute("SELECT * FROM tasks WHERE id = %s AND user_id = %s", (id, session['user_id']))
    task = cur.fetchone()

    if not task:
        flash('Task not found or unauthorized.', 'danger')
        conn.close()
        return redirect('/')

    task_title = request.form.get('task', '').strip()
    description = request.form.get('description', '').strip()
    priority = request.form.get('priority', 'medium')
    status = request.form.get('status', 'pending')
    category = request.form.get('category', '').strip()
    due_date = request.form.get('due_date', None)

    cur.execute(
        """UPDATE tasks 
           SET task = %s, description = %s, priority = %s, status = %s, 
               category = %s, due_date = %s
           WHERE id = %s""",
        (task_title, description, priority, status, category, due_date or None, id)
    )
    conn.commit()
    conn.close()

    flash('Task updated successfully!', 'success')
    return redirect('/')


@app.route('/delete/<int:id>')
@login_required
def delete(id):
    conn = get_connection()
    cur = conn.cursor()

    # Get task to delete attachment if exists
    cur.execute("SELECT * FROM tasks WHERE id = %s AND user_id = %s", (id, session['user_id']))
    task = cur.fetchone()

    if task:
        # Delete attachment from S3
        if task.get('attachment_url'):
            try:
                s3_client.delete_object(Bucket=s3_config['bucket_name'], Key=task['attachment_url'])
            except:
                pass

        cur.execute("DELETE FROM tasks WHERE id = %s", (id,))
        conn.commit()
        flash('Task deleted successfully!', 'success')
    else:
        flash('Task not found or unauthorized.', 'danger')

    conn.close()
    return redirect('/')


@app.route('/share/<int:task_id>', methods=['POST'])
@login_required
def share_task(task_id):
    share_username = request.form.get('share_username', '').strip()

    if not share_username:
        flash('Please provide a username to share with.', 'danger')
        return redirect('/')

    conn = get_connection()
    cur = conn.cursor()

    # Check if task exists and belongs to user
    cur.execute("SELECT * FROM tasks WHERE id = %s AND user_id = %s", (task_id, session['user_id']))
    task = cur.fetchone()

    if not task:
        flash('Task not found or unauthorized.', 'danger')
        conn.close()
        return redirect('/')

    # Get user to share with
    cur.execute("SELECT id FROM users WHERE username = %s", (share_username,))
    share_user = cur.fetchone()

    if not share_user:
        flash('User not found.', 'danger')
        conn.close()
        return redirect('/')

    if share_user['id'] == session['user_id']:
        flash('Cannot share task with yourself.', 'warning')
        conn.close()
        return redirect('/')

    # Check if already shared
    cur.execute(
        "SELECT * FROM shared_tasks WHERE task_id = %s AND shared_with = %s",
        (task_id, share_user['id'])
    )

    if cur.fetchone():
        flash('Task already shared with this user.', 'warning')
    else:
        cur.execute(
            "INSERT INTO shared_tasks (task_id, shared_by, shared_with) VALUES (%s, %s, %s)",
            (task_id, session['user_id'], share_user['id'])
        )
        conn.commit()
        flash(f'Task shared with {share_username} successfully!', 'success')

    conn.close()
    return redirect('/')


@app.route('/download/<int:task_id>')
@login_required
def download_attachment(task_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT attachment_url FROM tasks 
           WHERE id = %s AND (user_id = %s OR id IN 
           (SELECT task_id FROM shared_tasks WHERE shared_with = %s))""",
        (task_id, session['user_id'], session['user_id'])
    )
    task = cur.fetchone()
    conn.close()

    if not task or not task.get('attachment_url'):
        flash('Attachment not found.', 'danger')
        return redirect('/')

    try:
        file_obj = s3_client.get_object(Bucket=s3_config['bucket_name'], Key=task['attachment_url'])
        return send_file(
            file_obj['Body'],
            as_attachment=True,
            download_name=task['attachment_url'].split('_', 1)[1] if '_' in task['attachment_url'] else task[
                'attachment_url']
        )
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'danger')
        return redirect('/')


@app.route('/api/tasks', methods=['GET'])
@login_required
def api_tasks():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE user_id = %s", (session['user_id'],))
    tasks = cur.fetchall()
    conn.close()

    # Convert datetime objects to strings
    for task in tasks:
        if task.get('created_at'):
            task['created_at'] = task['created_at'].isoformat()
        if task.get('updated_at'):
            task['updated_at'] = task['updated_at'].isoformat()
        if task.get('due_date'):
            task['due_date'] = task['due_date'].isoformat()

    return jsonify(tasks)


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect('/login')


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)