# CloudTasker - Quick Start Guide

Get CloudTasker running in **15 minutes**!

## ⚡ Quick Setup

### 1. Prerequisites
```bash
# Check Python version (need 3.12+)
python --version

# Install pip
python -m ensurepip --upgrade
```

### 2. Clone & Install
```bash
# Clone repository
git clone https://github.com/yourusername/CloudTasker.git
cd CloudTasker

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your details
nano .env  # or use any text editor
```

**Minimum .env configuration:**
```env
SECRET_KEY=your-secret-key-here
DEBUG=True

DB_HOST=your-rds-endpoint.amazonaws.com
DB_USER=admin
DB_PASSWORD=your-password
DB_NAME=cloudtasker

S3_BUCKET_NAME=your-bucket-name
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

### 4. Set Up AWS (if using cloud)

#### Quick RDS Setup:
```
1. Go to AWS Console → RDS
2. Create Database → MySQL
3. Choose Free Tier template
4. Set master password
5. Make publicly accessible (for dev)
6. Create database
7. Copy endpoint to .env
```

#### Quick S3 Setup:
```
1. Go to AWS Console → S3
2. Create bucket
3. Name it (e.g., cloudtasker-backups-yourname)
4. Keep default settings
5. Create bucket
6. Go to IAM → Create user for S3 access
7. Copy access keys to .env
```

### 5. Run Application
```bash
# Start the application
python app.py

# Access in browser
open http://localhost:5000
```

### 6. Create First User
```
1. Click "Register"
2. Enter: username, email, password
3. Login
4. Start adding tasks!
```

## 🐳 Docker Quick Start (Alternative)

### Using Docker Compose:
```bash
# Create .env file first
cp .env.example .env
# Edit .env with your AWS credentials

# Start everything
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Access app
open http://localhost:5000
```

## 📝 Essential Commands

### Application Management
```bash
# Start app
python app.py

# Stop app
Ctrl + C

# Run in background (production)
gunicorn --bind 0.0.0.0:5000 --daemon app:app

# Stop background process
pkill gunicorn
```

### Database Commands
```bash
# Initialize database
python -c "from app import init_db; init_db()"

# Test connection
python -c "from app import get_connection; conn = get_connection(); print('Success!')"

# Backup database
cd backup
python backup_script.py
```

### Docker Commands
```bash
# Start containers
docker-compose up -d

# Stop containers
docker-compose down

# Rebuild containers
docker-compose up -d --build

# View logs
docker-compose logs -f web

# SSH into container
docker-compose exec web bash
```

## 🎯 First Tasks

### Test Core Features:
1. ✅ Register a new user
2. ✅ Login
3. ✅ Add a task with:
   - Title
   - Description
   - Priority (High)
   - Due date
   - Category
4. ✅ Upload an attachment
5. ✅ Edit the task
6. ✅ Mark as "In Progress"
7. ✅ Share with another user (create second user)
8. ✅ Filter by status
9. ✅ Search tasks
10. ✅ Download attachment
11. ✅ Delete task

## 🔧 Common Issues & Solutions

### Issue: "Can't connect to database"
```bash
# Check if RDS is accessible
mysql -h your-rds-endpoint -u admin -p

# Check security group allows your IP
# Verify DB_HOST in .env is correct
```

### Issue: "Module not found"
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Issue: "S3 upload failed"
```bash
# Test AWS credentials
python -c "import boto3; s3 = boto3.client('s3'); print(s3.list_buckets())"

# Check IAM permissions
# Verify bucket name and region in .env
```

### Issue: "Port 5000 already in use"
```bash
# Find process
lsof -i :5000

# Kill process
kill -9 <PID>

# Or use different port
python app.py --port 5001
```

### Issue: "CSRF token missing"
```bash
# Clear browser cookies
# Restart application
# Check if csrf_token() is in forms
```

## 📚 Next Steps

### After Getting It Running:

1. **Secure Your App:**
   - Change SECRET_KEY to random value
   - Use strong passwords
   - Set DEBUG=False for production

2. **Customize:**
   - Modify colors in base.html
   - Add your logo
   - Change app name

3. **Deploy:**
   - Follow SETUP_GUIDE.md for production deployment
   - Set up domain name
   - Enable HTTPS

4. **Extend Features:**
   - Add email notifications
   - Implement task reminders
   - Create mobile app
   - Add team features

## 📖 Documentation

- **README.md** - Project overview
- **SETUP_GUIDE.md** - Detailed setup instructions
- **IMPLEMENTATION_GUIDE.md** - Code explanation & architecture
- **QUICKSTART.md** - This file

## 🆘 Getting Help

### Before Asking for Help:

1. Check error messages carefully
2. Review the logs: `tail -f app.log`
3. Verify all environment variables
4. Test database and S3 connections separately
5. Check AWS Console for service status

### Where to Get Help:

- GitHub Issues
- Stack Overflow (tag: flask, aws)
- AWS Support
- Python Discord communities

## 🎉 Success Checklist

- [ ] Application starts without errors
- [ ] Can access http://localhost:5000
- [ ] Registration works
- [ ] Login works
- [ ] Can create tasks
- [ ] Can upload files
- [ ] Can edit/delete tasks
- [ ] Statistics show correctly
- [ ] Search and filters work
- [ ] Task sharing works

**If all checked, you're ready to go! 🚀**

## 💡 Pro Tips

1. **Development Workflow:**
   ```bash
   # Open 3 terminals:
   # Terminal 1: Run app
   python app.py
   
   # Terminal 2: Watch logs
   tail -f app.log
   
   # Terminal 3: Database queries
   mysql -h your-rds-endpoint -u admin -p
   ```

2. **Backup Before Changes:**
   ```bash
   cd backup
   python backup_script.py
   ```

3. **Test in Incognito:**
   - Use incognito mode to test auth
   - Avoids cache issues
   - Clean session testing

4. **Use Environment Variables:**
   ```bash
   # Don't hardcode secrets
   # Always use .env file
   # Add .env to .gitignore
   ```

5. **Monitor Resources:**
   ```bash
   # Check disk space
   df -h
   
   # Check memory
   free -m
   
   # Check processes
   ps aux | grep python
   ```

## 🔄 Update Application

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart application
pkill gunicorn
gunicorn --bind 0.0.0.0:5000 --daemon app:app
```

## 🎊 You're All Set!

CloudTasker is now running. Start managing your tasks efficiently!

**Happy Task Management! 🎯**