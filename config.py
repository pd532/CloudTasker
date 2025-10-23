# db_config = {
#     "host": "cloudtasker-db.cvmqkque0l0k.eu-north-1.rds.amazonaws.com",
#     "user": "admin",
#     "password": "admin123pass",
#     "database": "cloudtasker-db"
# }
#
# s3_config = {
#     "bucket_name": "cloudtasker-backups",
#     "region": "eu-north-1c"
# }

import os
from dotenv import load_dotenv

load_dotenv()

# Application Configuration
app_config = {
    "secret_key": os.getenv("SECRET_KEY", "cloudtasker-secret-key-change-in-production"),
    "debug": os.getenv("DEBUG", "False") == "True"
}

# Database Configuration
db_config = {
    "host": os.getenv("DB_HOST", "your-rds-endpoint.rds.amazonaws.com"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASSWORD", "yourpassword"),
    "database": os.getenv("DB_NAME", "cloudtasker"),
    "port": int(os.getenv("DB_PORT", "3306"))
}

# AWS S3 Configuration
s3_config = {
    "bucket_name": os.getenv("S3_BUCKET_NAME", "cloudtasker-backups"),
    "region": os.getenv("AWS_REGION", "ap-south-1"),
    "access_key": os.getenv("AWS_ACCESS_KEY_ID", None),
    "secret_key": os.getenv("AWS_SECRET_ACCESS_KEY", None)
}

# Email Configuration (for future notifications)
email_config = {
    "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", "587")),
    "sender_email": os.getenv("SENDER_EMAIL", ""),
    "sender_password": os.getenv("SENDER_PASSWORD", "")
}
