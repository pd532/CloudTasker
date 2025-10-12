from flask import Flask, render_template, request, redirect, session, flash
import pymysql, boto3, datetime
from config import db_config, s3_config

app = Flask(__name__)
app.secret_key = "cloudtasker-secret-key"

# Connect to AWS RDS
def get_connection():
    return pymysql.connect(
        host=db_config["host"],
        user=db_config["user"],
        password=db_config["password"],
        database=db_config["database"]
    )

@app.route('/')
def home():
    if 'user' not in session:
        return redirect('/login')
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE user=%s", (session['user'],))
    data = cur.fetchall()
    conn.close()
    return render_template('tasks.html', tasks=data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        password = request.form['password']
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (user, password))
        data = cur.fetchone()
        conn.close()
        if data:
            session['user'] = user
            return redirect('/')
        flash("Invalid credentials!")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = request.form['username']
        password = request.form['password']
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (user, password))
        conn.commit()
        conn.close()
        flash("Registered successfully! Login now.")
        return redirect('/login')
    return render_template('register.html')

@app.route('/add', methods=['POST'])
def add():
    task = request.form['task']
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (task, user, date) VALUES (%s, %s, %s)",
                (task, session['user'], datetime.date.today()))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/delete/<int:id>')
def delete(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
