import boto3
from django.conf import settings

def upload_file_to_s3(local_path, s3_key):
    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )
    bucket = settings.AWS_STORAGE_BUCKET_NAME
    s3.upload_file(local_path, bucket, s3_key)
    url = f"https://{bucket}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_key}"
    return url