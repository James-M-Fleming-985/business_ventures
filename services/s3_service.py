"""
S3 Service for Causal Affect Platform
Handles file uploads, data backups, and storage management
"""

import boto3
import logging
import os
from typing import Optional, BinaryIO
from datetime import datetime
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class S3Service:
    """Service for managing S3 storage operations"""
    
    def __init__(self):
        """Initialize S3 client with credentials from environment variables"""
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        
        # Check if S3 is configured
        self.enabled = all([
            self.aws_access_key_id,
            self.aws_secret_access_key,
            self.bucket_name
        ])
        
        if self.enabled:
            self.client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region
            )
            logger.info(f"✅ S3 service initialized - Bucket: {self.bucket_name}, Region: {self.aws_region}")
        else:
            self.client = None
            logger.warning("⚠️  S3 service disabled - Missing required environment variables")
            logger.warning("   Required: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME")
    
    def upload_file(
        self,
        file_obj: BinaryIO,
        object_key: str,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Optional[str]:
        """
        Upload a file to S3
        
        Args:
            file_obj: File-like object to upload
            object_key: S3 object key (path/filename)
            content_type: MIME type of the file
            metadata: Additional metadata to attach
        
        Returns:
            S3 URL if successful, None otherwise
        """
        if not self.enabled:
            logger.warning("S3 upload skipped - service not enabled")
            return None
        
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            if metadata:
                extra_args['Metadata'] = metadata
            
            self.client.upload_fileobj(
                file_obj,
                self.bucket_name,
                object_key,
                ExtraArgs=extra_args
            )
            
            url = f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{object_key}"
            logger.info(f"✅ File uploaded to S3: {object_key}")
            return url
            
        except ClientError as e:
            logger.error(f"❌ S3 upload failed: {e}")
            return None
    
    def download_file(self, object_key: str, local_path: str) -> bool:
        """
        Download a file from S3
        
        Args:
            object_key: S3 object key to download
            local_path: Local file path to save to
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.warning("S3 download skipped - service not enabled")
            return False
        
        try:
            self.client.download_file(
                self.bucket_name,
                object_key,
                local_path
            )
            logger.info(f"✅ File downloaded from S3: {object_key}")
            return True
            
        except ClientError as e:
            logger.error(f"❌ S3 download failed: {e}")
            return False
    
    def delete_file(self, object_key: str) -> bool:
        """
        Delete a file from S3
        
        Args:
            object_key: S3 object key to delete
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.warning("S3 delete skipped - service not enabled")
            return False
        
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            logger.info(f"✅ File deleted from S3: {object_key}")
            return True
            
        except ClientError as e:
            logger.error(f"❌ S3 delete failed: {e}")
            return False
    
    def list_files(self, prefix: str = "") -> list:
        """
        List files in S3 bucket with given prefix
        
        Args:
            prefix: Prefix to filter objects (folder path)
        
        Returns:
            List of object keys
        """
        if not self.enabled:
            logger.warning("S3 list skipped - service not enabled")
            return []
        
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                return []
            
            return [obj['Key'] for obj in response['Contents']]
            
        except ClientError as e:
            logger.error(f"❌ S3 list failed: {e}")
            return []
    
    def backup_database_export(self, file_path: str) -> Optional[str]:
        """
        Backup a database export file to S3
        
        Args:
            file_path: Local path to database export file
        
        Returns:
            S3 URL if successful, None otherwise
        """
        if not self.enabled:
            logger.warning("Database backup skipped - S3 not enabled")
            return None
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        object_key = f"backups/database_{timestamp}.sql"
        
        try:
            with open(file_path, 'rb') as f:
                return self.upload_file(
                    f,
                    object_key,
                    content_type="application/sql",
                    metadata={
                        "backup_timestamp": timestamp,
                        "backup_type": "database_export"
                    }
                )
        except Exception as e:
            logger.error(f"❌ Database backup failed: {e}")
            return None


# Global S3 service instance
s3_service = S3Service()
