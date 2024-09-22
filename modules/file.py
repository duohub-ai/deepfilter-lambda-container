import os
import logging
import uuid
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone

logger = logging.getLogger()
dynamodb = boto3.client('dynamodb')
stage = os.getenv('STAGE', 'dev')

def create_file_entry(filename):
    """Create a new file entry in DB."""
    try:
        logger.info(f"Created file entry for {filename}")
        return 'file_id'
    except ClientError as e:
        logger.error(f"Error creating file entry: {e}")
        raise

def fetch_file(file_id):
    """Fetch file metadata from DB."""
    try:
        logger.info(f"Fetching file metadata for {file_id}")
        return  None
    except ClientError as e:
        logger.error(f"Failed to fetch file from DynamoDB: {e}")
        return None

