import boto3
import os
import datetime
import subprocess
import sys
from dotenv import load_dotenv

load_dotenv()

# Configuration
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
S3_BUCKET = os.getenv('S3_BUCKET_NAME')
AWS_REGION = os.getenv('AWS_REGION')


def backup_database():
    """Create database backup"""
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"backup_{timestamp}.sql"

    try:
        print(f"Starting backup at {datetime.datetime.now()}")

        # Create backup using mysqldump
        cmd = [
            'mysqldump',
            f'-h{DB_HOST}',
            f'-u{DB_USER}',
            f'-p{DB_PASSWORD}',
            DB_NAME
        ]

        with open(backup_file, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            print(f"Error creating backup: {result.stderr}")
            return None

        print(f"Backup created successfully: {backup_file}")
        return backup_file

    except Exception as e:
        print(f"Error during backup: {str(e)}")
        return None


def upload_to_s3(filename):
    """Upload backup to S3"""
    try:
        print(f"Uploading {filename} to S3...")

        s3_client = boto3.client('s3', region_name=AWS_REGION)
        s3_client.upload_file(
            filename,
            S3_BUCKET,
            f"backups/{filename}",
            ExtraArgs={'StorageClass': 'STANDARD_IA'}
        )

        print(f"Backup uploaded to S3: s3://{S3_BUCKET}/backups/{filename}")
        return True

    except Exception as e:
        print(f"Error uploading to S3: {str(e)}")
        return False


def cleanup_old_backups(days=7):
    """Delete local backups older than specified days"""
    try:
        current_time = datetime.datetime.now()
        for filename in os.listdir('.'):
            if filename.startswith('backup_') and filename.endswith('.sql'):
                file_path = os.path.join('.', filename)
                file_time = datetime.datetime.fromtimestamp(os.path.getctime(file_path))

                if (current_time - file_time).days > days:
                    os.remove(file_path)
                    print(f"Deleted old backup: {filename}")

    except Exception as e:
        print(f"Error during cleanup: {str(e)}")


def main():
    print("=" * 50)
    print("CloudTasker Database Backup")
    print("=" * 50)

    # Create backup
    backup_file = backup_database()

    if backup_file:
        # Upload to S3
        if upload_to_s3(backup_file):
            print("Backup process completed successfully!")

            # Cleanup old backups
            print("\nCleaning up old backups...")
            cleanup_old_backups(days=7)
        else:
            print("Failed to upload backup to S3")
            sys.exit(1)
    else:
        print("Failed to create backup")
        sys.exit(1)

    print("=" * 50)


if __name__ == "__main__":
    main()