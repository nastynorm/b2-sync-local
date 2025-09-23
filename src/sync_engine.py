"""
Sync Engine module for bidirectional synchronization between local and B2 storage
"""

import os
import time
import hashlib
import logging
import threading
from pathlib import Path
from typing import Dict, Set, List, Optional, Tuple
from datetime import datetime, timezone
from enum import Enum

from .b2_client import B2Client
from .file_monitor import FileMonitor, FileChangeEvent
from .config_manager import ConfigManager

logger = logging.getLogger(__name__)

class SyncAction(Enum):
    """Types of sync actions"""
    UPLOAD = "upload"
    DOWNLOAD = "download"
    DELETE_LOCAL = "delete_local"
    DELETE_REMOTE = "delete_remote"
    CONFLICT = "conflict"
    SKIP = "skip"

class SyncStatus(Enum):
    """Sync status states"""
    IDLE = "idle"
    SYNCING = "syncing"
    ERROR = "error"
    PAUSED = "paused"

class FileInfo:
    """Information about a file for sync comparison"""
    
    def __init__(self, path: str, size: int = 0, modified_time: float = 0, 
                 hash_value: str = "", exists: bool = True):
        self.path = path
        self.size = size
        self.modified_time = modified_time
        self.hash_value = hash_value
        self.exists = exists
    
    def __eq__(self, other):
        if not isinstance(other, FileInfo):
            return False
        return (self.size == other.size and 
                abs(self.modified_time - other.modified_time) < 2.0 and
                self.hash_value == other.hash_value)
    
    def __str__(self):
        return f"FileInfo({self.path}, {self.size}B, {datetime.fromtimestamp(self.modified_time)})"

class SyncEngine:
    """Main synchronization engine"""
    
    def __init__(self, b2_client: B2Client, file_monitor: FileMonitor, config: ConfigManager):
        self.b2_client = b2_client
        self.file_monitor = file_monitor
        self.config = config
        
        self.status = SyncStatus.IDLE
        self.last_sync_time = None
        self.sync_thread = None
        self.auto_sync_thread = None
        self.stop_event = threading.Event()
        
        # Sync statistics
        self.stats = {
            'files_uploaded': 0,
            'files_downloaded': 0,
            'files_deleted': 0,
            'bytes_uploaded': 0,
            'bytes_downloaded': 0,
            'conflicts': 0,
            'errors': 0
        }
        
        # Event callbacks
        self.sync_callbacks = []
        self.status_callbacks = []
        
        # Setup file monitor callback
        self.file_monitor.add_event_handler(self._on_file_change)
        self.file_monitor.set_sync_hidden_files(config.get_sync_hidden_files())
        
        logger.info("Sync engine initialized")
    
    def add_sync_callback(self, callback):
        """Add callback for sync events"""
        self.sync_callbacks.append(callback)
    
    def add_status_callback(self, callback):
        """Add callback for status changes"""
        self.status_callbacks.append(callback)
    
    def _notify_sync_event(self, action: SyncAction, file_path: str, success: bool = True, error: str = None):
        """Notify sync event callbacks"""
        for callback in self.sync_callbacks:
            try:
                callback(action, file_path, success, error)
            except Exception as e:
                logger.error(f"Error in sync callback: {e}")
    
    def _notify_status_change(self, status: SyncStatus):
        """Notify status change callbacks"""
        self.status = status
        for callback in self.status_callbacks:
            try:
                callback(status)
            except Exception as e:
                logger.error(f"Error in status callback: {e}")
    
    def start(self):
        """Start the sync engine"""
        if not self.b2_client.is_authenticated():
            if not self.b2_client.authenticate():
                logger.error("Cannot start sync engine - B2 authentication failed")
                self._notify_status_change(SyncStatus.ERROR)
                return False
        
        # Start file monitoring
        self.file_monitor.start_monitoring()
        
        # Start auto-sync if enabled
        if self.config.get_auto_sync():
            self._start_auto_sync()
        
        # Perform initial sync
        self.sync_now()
        
        logger.info("Sync engine started")
        return True
    
    def stop(self):
        """Stop the sync engine"""
        self.stop_event.set()
        
        # Stop auto-sync
        if self.auto_sync_thread and self.auto_sync_thread.is_alive():
            self.auto_sync_thread.join(timeout=5.0)
        
        # Stop current sync
        if self.sync_thread and self.sync_thread.is_alive():
            self.sync_thread.join(timeout=10.0)
        
        # Stop file monitoring
        self.file_monitor.stop_monitoring()
        
        self._notify_status_change(SyncStatus.IDLE)
        logger.info("Sync engine stopped")
    
    def sync_now(self):
        """Trigger immediate sync"""
        if self.status == SyncStatus.SYNCING:
            logger.warning("Sync already in progress")
            return
        
        if self.sync_thread and self.sync_thread.is_alive():
            return
        
        self.sync_thread = threading.Thread(target=self._perform_sync, daemon=True)
        self.sync_thread.start()
    
    def pause_sync(self):
        """Pause automatic synchronization"""
        self._notify_status_change(SyncStatus.PAUSED)
        logger.info("Sync paused")
    
    def resume_sync(self):
        """Resume automatic synchronization"""
        if self.status == SyncStatus.PAUSED:
            self._notify_status_change(SyncStatus.IDLE)
            if self.config.get_auto_sync():
                self._start_auto_sync()
            logger.info("Sync resumed")
    
    def _start_auto_sync(self):
        """Start automatic sync thread"""
        if self.auto_sync_thread and self.auto_sync_thread.is_alive():
            return
        
        self.auto_sync_thread = threading.Thread(target=self._auto_sync_loop, daemon=True)
        self.auto_sync_thread.start()
    
    def _auto_sync_loop(self):
        """Auto-sync loop"""
        interval = self.config.get_sync_interval()
        
        while not self.stop_event.is_set():
            if self.status not in [SyncStatus.PAUSED, SyncStatus.SYNCING]:
                self.sync_now()
            
            # Wait for interval or stop event
            self.stop_event.wait(interval)
    
    def _on_file_change(self, event: FileChangeEvent):
        """Handle file change events from monitor"""
        if self.status == SyncStatus.PAUSED:
            return
        
        logger.debug(f"File change detected: {event}")
        
        # Trigger sync after a short delay to batch changes
        if not hasattr(self, '_change_timer') or not self._change_timer.is_alive():
            self._change_timer = threading.Timer(5.0, self.sync_now)
            self._change_timer.start()
    
    def _perform_sync(self):
        """Perform synchronization"""
        try:
            self._notify_status_change(SyncStatus.SYNCING)
            logger.info("Starting synchronization")
            
            # Get local and remote file lists
            local_files = self._get_local_files()
            remote_files = self._get_remote_files()
            
            # Determine sync actions
            actions = self._determine_sync_actions(local_files, remote_files)
            
            # Execute sync actions
            self._execute_sync_actions(actions)
            
            self.last_sync_time = datetime.now()
            self._notify_status_change(SyncStatus.IDLE)
            
            logger.info(f"Synchronization completed. Processed {len(actions)} actions")
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            self._notify_status_change(SyncStatus.ERROR)
            self.stats['errors'] += 1
    
    def _get_local_files(self) -> Dict[str, FileInfo]:
        """Get information about all local files"""
        local_files = {}
        
        try:
            for file_path in self.file_monitor.get_all_files():
                relative_path = self.file_monitor.get_relative_path(file_path)
                
                if file_path.exists() and file_path.is_file():
                    stat = file_path.stat()
                    file_info = FileInfo(
                        path=relative_path,
                        size=stat.st_size,
                        modified_time=stat.st_mtime,
                        hash_value=self._calculate_file_hash(file_path),
                        exists=True
                    )
                    local_files[relative_path] = file_info
        
        except Exception as e:
            logger.error(f"Error getting local files: {e}")
        
        return local_files
    
    def _get_remote_files(self) -> Dict[str, FileInfo]:
        """Get information about all remote files"""
        remote_files = {}
        
        try:
            b2_files = self.b2_client.list_files()
            
            for file_data in b2_files:
                file_info = FileInfo(
                    path=file_data['name'],
                    size=file_data['size'],
                    modified_time=file_data['upload_timestamp'] / 1000,  # Convert to seconds
                    hash_value="",  # B2 doesn't provide SHA1 in list
                    exists=True
                )
                
                # Try to get modification time from file info
                if 'src_last_modified_millis' in file_data.get('file_info', {}):
                    file_info.modified_time = int(file_data['file_info']['src_last_modified_millis']) / 1000
                
                remote_files[file_data['name']] = file_info
        
        except Exception as e:
            logger.error(f"Error getting remote files: {e}")
        
        return remote_files
    
    def _determine_sync_actions(self, local_files: Dict[str, FileInfo], 
                              remote_files: Dict[str, FileInfo]) -> List[Tuple[SyncAction, str, FileInfo]]:
        """Determine what sync actions need to be performed"""
        actions = []
        
        all_files = set(local_files.keys()) | set(remote_files.keys())
        
        for file_path in all_files:
            local_file = local_files.get(file_path)
            remote_file = remote_files.get(file_path)
            
            if local_file and remote_file:
                # File exists in both locations
                if local_file == remote_file:
                    # Files are identical, skip
                    actions.append((SyncAction.SKIP, file_path, local_file))
                elif local_file.modified_time > remote_file.modified_time:
                    # Local file is newer, upload
                    actions.append((SyncAction.UPLOAD, file_path, local_file))
                elif remote_file.modified_time > local_file.modified_time:
                    # Remote file is newer, download
                    actions.append((SyncAction.DOWNLOAD, file_path, remote_file))
                else:
                    # Same modification time but different content - conflict
                    actions.append((SyncAction.CONFLICT, file_path, local_file))
            
            elif local_file and not remote_file:
                # File only exists locally, upload
                actions.append((SyncAction.UPLOAD, file_path, local_file))
            
            elif remote_file and not local_file:
                # File only exists remotely, download
                actions.append((SyncAction.DOWNLOAD, file_path, remote_file))
        
        return actions
    
    def _execute_sync_actions(self, actions: List[Tuple[SyncAction, str, FileInfo]]):
        """Execute the determined sync actions"""
        for action, file_path, file_info in actions:
            if self.stop_event.is_set():
                break
            
            try:
                if action == SyncAction.UPLOAD:
                    self._upload_file(file_path, file_info)
                elif action == SyncAction.DOWNLOAD:
                    self._download_file(file_path, file_info)
                elif action == SyncAction.DELETE_LOCAL:
                    self._delete_local_file(file_path)
                elif action == SyncAction.DELETE_REMOTE:
                    self._delete_remote_file(file_path)
                elif action == SyncAction.CONFLICT:
                    self._handle_conflict(file_path, file_info)
                # SKIP actions don't need processing
                
            except Exception as e:
                logger.error(f"Error executing {action.value} for {file_path}: {e}")
                self._notify_sync_event(action, file_path, False, str(e))
                self.stats['errors'] += 1
    
    def _upload_file(self, file_path: str, file_info: FileInfo):
        """Upload a file to B2"""
        local_path = self.file_monitor.get_absolute_path(file_path)
        
        if self.b2_client.upload_file(local_path, file_path):
            self.stats['files_uploaded'] += 1
            self.stats['bytes_uploaded'] += file_info.size
            self._notify_sync_event(SyncAction.UPLOAD, file_path, True)
            logger.debug(f"Uploaded: {file_path}")
        else:
            self._notify_sync_event(SyncAction.UPLOAD, file_path, False)
    
    def _download_file(self, file_path: str, file_info: FileInfo):
        """Download a file from B2"""
        local_path = self.file_monitor.get_absolute_path(file_path)
        
        if self.b2_client.download_file(file_path, local_path):
            self.stats['files_downloaded'] += 1
            self.stats['bytes_downloaded'] += file_info.size
            self._notify_sync_event(SyncAction.DOWNLOAD, file_path, True)
            logger.debug(f"Downloaded: {file_path}")
        else:
            self._notify_sync_event(SyncAction.DOWNLOAD, file_path, False)
    
    def _delete_local_file(self, file_path: str):
        """Delete a local file"""
        local_path = self.file_monitor.get_absolute_path(file_path)
        
        try:
            if local_path.exists():
                local_path.unlink()
                self.stats['files_deleted'] += 1
                self._notify_sync_event(SyncAction.DELETE_LOCAL, file_path, True)
                logger.debug(f"Deleted local: {file_path}")
        except Exception as e:
            self._notify_sync_event(SyncAction.DELETE_LOCAL, file_path, False, str(e))
    
    def _delete_remote_file(self, file_path: str):
        """Delete a remote file"""
        if self.b2_client.delete_file(file_path):
            self.stats['files_deleted'] += 1
            self._notify_sync_event(SyncAction.DELETE_REMOTE, file_path, True)
            logger.debug(f"Deleted remote: {file_path}")
        else:
            self._notify_sync_event(SyncAction.DELETE_REMOTE, file_path, False)
    
    def _handle_conflict(self, file_path: str, file_info: FileInfo):
        """Handle sync conflicts"""
        # For now, prefer local file (upload)
        # TODO: Implement user-configurable conflict resolution
        logger.warning(f"Conflict detected for {file_path}, preferring local version")
        self.stats['conflicts'] += 1
        self._upload_file(file_path, file_info)
        self._notify_sync_event(SyncAction.CONFLICT, file_path, True)
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA1 hash of a file"""
        try:
            sha1_hash = hashlib.sha1()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha1_hash.update(chunk)
            return sha1_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""
    
    def get_status(self) -> SyncStatus:
        """Get current sync status"""
        return self.status
    
    def get_stats(self) -> Dict:
        """Get sync statistics"""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset sync statistics"""
        self.stats = {
            'files_uploaded': 0,
            'files_downloaded': 0,
            'files_deleted': 0,
            'bytes_uploaded': 0,
            'bytes_downloaded': 0,
            'conflicts': 0,
            'errors': 0
        }