import os
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
s3 = boto3.client('s3')
stage = os.getenv('STAGE', 'dev')

def fetch_file_from_s3(file_key, region):
    """Fetch file content from S3."""
    bucket_name = f"bucketname-raw-{stage}-{region}"
    try:
        response = s3.get_object(Bucket=bucket_name, Key=file_key)
        return response['Body'].read(), response['ContentType']
    except ClientError as e:
        logger.error(f"Failed to fetch file from S3: {e}")
        return None

def upload_file_to_s3(file_path, s3_key, region, corrected_filename=None):
    """Upload a file to the S3 bucket."""
    bucket_name = f"bucketname-content-{stage}-{region}"
    try:
        # Use the corrected filename for the S3 key if provided
        if corrected_filename:
            s3_key = s3_key.replace(os.path.basename(s3_key), corrected_filename)

        with open(file_path, 'rb') as f:
            s3.upload_fileobj(f, bucket_name, s3_key)
        logger.info(f"File {file_path} uploaded to {bucket_name}/{s3_key}")
        return True
    except ClientError as e:
        logger.error(f"Failed to upload file to S3: {e}")
        return False
