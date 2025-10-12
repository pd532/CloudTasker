import boto3, os, datetime
backup_file = f"backup_{datetime.date.today()}.sql"
os.system(f"mysqldump -h your-rds-endpoint -u admin -pyourpassword cloudtasker > {backup_file}")

s3 = boto3.client('s3')
s3.upload_file(backup_file, "cloudtasker-backups", backup_file)
print("Backup uploaded to S3 successfully.")
