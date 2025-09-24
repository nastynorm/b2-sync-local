"""
B2 Client module for handling Backblaze B2 API operations
"""

import os
import hashlib
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from b2sdk.v2 import InMemoryAccountInfo, B2Api, FileVersion
from b2sdk.v2.exception import B2Error, BucketIdNotFound, FileNotPresent

logger = logging.getLogger(__name__)

class B2Client:
    """Client for interacting with Backblaze B2 cloud storage"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.account_info = InMemoryAccountInfo()
        self.api = B2Api(self.account_info)
        self.bucket = None
        self._authenticated = False
        
    def authenticate(self) -> bool:
        """Authenticate with B2 using stored credentials"""
        try:
            app_key_id = self.config.get_b2_key_id()
            app_key = self.config.get_b2_app_key()
            bucket_name = self.config.get_b2_bucket_name()
            
            if not all([app_key_id, app_key, bucket_name]):
                logger.error("Missing B2 credentials in configuration")
                return False
                
            # Authorize the application
            self.api.authorize_account("production", app_key_id, app_key)
            
            # Get the bucket
            self.bucket = self.api.get_bucket_by_name(bucket_name)
            self._authenticated = True
            
            logger.info(f"Successfully authenticated with B2 bucket: {bucket_name}")
            return True
            
        except B2Error as e:
            logger.error(f"B2 authentication failed: {e}")
            self._authenticated = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            self._authenticated = False
            return False
    
    def is_authenticated(self) -> bool:
        """Check if client is authenticated"""
        return self._authenticated
    
    def upload_file(self, local_path: Path, remote_path: str) -> bool:
        """Upload a file to B2"""
        if not self.is_authenticated():
            logger.error("Not authenticated with B2")
            return False
            
        try:
            # Calculate file hash
            file_hash = self._calculate_file_hash(local_path)
            
            # Upload the file
            file_info = {
                'src_last_modified_millis': str(int(local_path.stat().st_mtime * 1000)),
                'local_path': str(local_path)
            }
            
            # Use the correct B2 SDK v2 API
            file_data = local_path.read_bytes()
            uploaded_file = self.bucket.upload_bytes(
                file_data,
                remote_path,
                content_type=self._get_content_type(local_path),
                file_info=file_info
            )
            
            logger.info(f"Successfully uploaded: {local_path} -> {remote_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload {local_path}: {e}")
            return False
    
    def download_file(self, remote_path: str, local_path: Path) -> bool:
        """Download a file from B2"""
        if not self.is_authenticated():
            logger.error("Not authenticated with B2")
            return False
            
        try:
            # Ensure local directory exists
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download the file using the correct B2 SDK v2 API
            with open(local_path, 'wb') as local_file:
                download_dest = self.bucket.download_file_by_name(remote_path, local_file)
            
            # Set modification time if available
            try:
                file_info = download_dest.response.file_info
                if 'src_last_modified_millis' in file_info:
                    mod_time = int(file_info['src_last_modified_millis']) / 1000
                    os.utime(local_path, (mod_time, mod_time))
            except (AttributeError, KeyError, ValueError) as e:
                logger.debug(f"Could not set modification time for {local_path}: {e}")
            
            logger.info(f"Successfully downloaded: {remote_path} -> {local_path}")
            return True
            
        except FileNotPresent:
            logger.warning(f"File not found in B2: {remote_path}")
            return False
        except Exception as e:
            logger.error(f"Failed to download {remote_path}: {e}")
            return False
    
    def delete_file(self, remote_path: str) -> bool:
        """Delete a file from B2"""
        if not self.is_authenticated():
            logger.error("Not authenticated with B2")
            return False
            
        try:
            # Find the file version
            file_versions = list(self.bucket.ls(remote_path, recursive=False))
            
            for file_version, _ in file_versions:
                if file_version.file_name == remote_path:
                    self.bucket.delete_file_version(file_version.id_, file_version.file_name)
                    logger.info(f"Successfully deleted: {remote_path}")
                    return True
            
            logger.warning(f"File not found for deletion: {remote_path}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete {remote_path}: {e}")
            return False
    
    def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """List files in B2 bucket with optional prefix"""
        if not self.is_authenticated():
            logger.error("Not authenticated with B2")
            return []
            
        try:
            files = []
            for file_version, _ in self.bucket.ls(prefix, recursive=True):
                files.append({
                    'name': file_version.file_name,
                    'size': file_version.size,
                    'upload_timestamp': file_version.upload_timestamp,
                    'file_info': file_version.file_info,
                    'id': file_version.id_
                })
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []
    
    def get_file_info(self, remote_path: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific file in B2"""
        if not self.is_authenticated():
            return None
            
        try:
            for file_version, _ in self.bucket.ls(remote_path, recursive=False):
                if file_version.file_name == remote_path:
                    return {
                        'name': file_version.file_name,
                        'size': file_version.size,
                        'upload_timestamp': file_version.upload_timestamp,
                        'file_info': file_version.file_info,
                        'id': file_version.id_
                    }
            return None
            
        except Exception as e:
            logger.error(f"Failed to get file info for {remote_path}: {e}")
            return None
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA1 hash of a file"""
        sha1_hash = hashlib.sha1()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha1_hash.update(chunk)
        return sha1_hash.hexdigest()
    
    def _get_content_type(self, file_path: Path) -> str:
        """Get content type based on file extension"""
        extension = file_path.suffix.lower()
        content_types = {
            '.txt': 'text/plain',
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.mp4': 'video/mp4',
            '.mp3': 'audio/mpeg',
            '.zip': 'application/zip',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        return content_types.get(extension, 'application/octet-stream')