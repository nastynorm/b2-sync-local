"""
File Monitor module for detecting local file system changes
"""

import os
import time
import logging
import threading
from pathlib import Path
from typing import Callable, Set, Dict, Any
from datetime import datetime

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)

class FileChangeEvent:
    """Represents a file system change event"""
    
    def __init__(self, event_type: str, file_path: Path, is_directory: bool = False):
        self.event_type = event_type  # 'created', 'modified', 'deleted', 'moved'
        self.file_path = file_path
        self.is_directory = is_directory
        self.timestamp = datetime.now()
    
    def __str__(self):
        return f"{self.event_type}: {self.file_path} ({'dir' if self.is_directory else 'file'})"

class FileMonitorHandler(FileSystemEventHandler):
    """Handler for file system events"""
    
    def __init__(self, callback: Callable[[FileChangeEvent], None], sync_hidden: bool = False):
        super().__init__()
        self.callback = callback
        self.sync_hidden = sync_hidden
        self._debounce_events = {}
        self._debounce_timer = None
        self._lock = threading.Lock()
    
    def _should_ignore(self, path: str) -> bool:
        """Check if file should be ignored"""
        path_obj = Path(path)
        
        # Ignore hidden files if not configured to sync them
        if not self.sync_hidden and path_obj.name.startswith('.'):
            return True
        
        # Ignore temporary files
        temp_extensions = {'.tmp', '.temp', '.swp', '.~'}
        if path_obj.suffix.lower() in temp_extensions:
            return True
        
        # Ignore system files
        system_files = {'Thumbs.db', 'desktop.ini', '.DS_Store'}
        if path_obj.name in system_files:
            return True
        
        # Ignore lock files
        if path_obj.name.startswith('~$') or path_obj.name.endswith('.lock'):
            return True
        
        return False
    
    def _debounce_event(self, event: FileChangeEvent):
        """Debounce rapid file events (like during file saves)"""
        with self._lock:
            key = (str(event.file_path), event.event_type)
            self._debounce_events[key] = event
            
            # Cancel existing timer
            if self._debounce_timer:
                self._debounce_timer.cancel()
            
            # Start new timer
            self._debounce_timer = threading.Timer(1.0, self._process_debounced_events)
            self._debounce_timer.start()
    
    def _process_debounced_events(self):
        """Process debounced events"""
        with self._lock:
            events_to_process = list(self._debounce_events.values())
            self._debounce_events.clear()
        
        for event in events_to_process:
            try:
                self.callback(event)
            except Exception as e:
                logger.error(f"Error processing file event {event}: {e}")
    
    def on_created(self, event: FileSystemEvent):
        if self._should_ignore(event.src_path):
            return
        
        file_event = FileChangeEvent(
            'created',
            Path(event.src_path),
            event.is_directory
        )
        self._debounce_event(file_event)
    
    def on_modified(self, event: FileSystemEvent):
        if self._should_ignore(event.src_path) or event.is_directory:
            return
        
        file_event = FileChangeEvent(
            'modified',
            Path(event.src_path),
            event.is_directory
        )
        self._debounce_event(file_event)
    
    def on_deleted(self, event: FileSystemEvent):
        if self._should_ignore(event.src_path):
            return
        
        file_event = FileChangeEvent(
            'deleted',
            Path(event.src_path),
            event.is_directory
        )
        self._debounce_event(file_event)
    
    def on_moved(self, event: FileSystemEvent):
        if hasattr(event, 'dest_path'):
            # Handle as delete + create
            if not self._should_ignore(event.src_path):
                delete_event = FileChangeEvent(
                    'deleted',
                    Path(event.src_path),
                    event.is_directory
                )
                self._debounce_event(delete_event)
            
            if not self._should_ignore(event.dest_path):
                create_event = FileChangeEvent(
                    'created',
                    Path(event.dest_path),
                    event.is_directory
                )
                self._debounce_event(create_event)

class FileMonitor:
    """Monitors local file system for changes"""
    
    def __init__(self, watch_folder: Path):
        self.watch_folder = Path(watch_folder)
        self.observer = Observer()
        self.is_monitoring = False
        self.event_handlers = []
        self._sync_hidden = False
        
        # Ensure watch folder exists
        self.watch_folder.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"File monitor initialized for: {self.watch_folder}")
    
    def add_event_handler(self, callback: Callable[[FileChangeEvent], None]):
        """Add a callback for file change events"""
        self.event_handlers.append(callback)
    
    def set_sync_hidden_files(self, sync_hidden: bool):
        """Set whether to sync hidden files"""
        self._sync_hidden = sync_hidden
    
    def start_monitoring(self):
        """Start monitoring the watch folder"""
        if self.is_monitoring:
            logger.warning("File monitoring is already active")
            return
        
        try:
            # Create handler that calls all registered callbacks
            def combined_callback(event: FileChangeEvent):
                for handler in self.event_handlers:
                    try:
                        handler(event)
                    except Exception as e:
                        logger.error(f"Error in event handler: {e}")
            
            handler = FileMonitorHandler(combined_callback, self._sync_hidden)
            
            self.observer.schedule(
                handler,
                str(self.watch_folder),
                recursive=True
            )
            
            self.observer.start()
            self.is_monitoring = True
            
            logger.info(f"Started monitoring: {self.watch_folder}")
            
        except Exception as e:
            logger.error(f"Failed to start file monitoring: {e}")
            raise
    
    def stop_monitoring(self):
        """Stop monitoring the watch folder"""
        if not self.is_monitoring:
            return
        
        try:
            self.observer.stop()
            self.observer.join(timeout=5.0)
            self.is_monitoring = False
            
            logger.info("Stopped file monitoring")
            
        except Exception as e:
            logger.error(f"Error stopping file monitor: {e}")
    
    def get_all_files(self) -> Set[Path]:
        """Get all files in the watch folder"""
        files = set()
        
        try:
            for root, dirs, filenames in os.walk(self.watch_folder):
                # Filter directories if not syncing hidden
                if not self._sync_hidden:
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for filename in filenames:
                    file_path = Path(root) / filename
                    
                    # Skip hidden files if not configured to sync them
                    if not self._sync_hidden and filename.startswith('.'):
                        continue
                    
                    # Skip temporary and system files
                    if self._should_ignore_file(file_path):
                        continue
                    
                    files.add(file_path)
        
        except Exception as e:
            logger.error(f"Error scanning files: {e}")
        
        return files
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored (same logic as handler)"""
        # Ignore temporary files
        temp_extensions = {'.tmp', '.temp', '.swp', '.~'}
        if file_path.suffix.lower() in temp_extensions:
            return True
        
        # Ignore system files
        system_files = {'Thumbs.db', 'desktop.ini', '.DS_Store'}
        if file_path.name in system_files:
            return True
        
        # Ignore lock files
        if file_path.name.startswith('~$') or file_path.name.endswith('.lock'):
            return True
        
        return False
    
    def get_relative_path(self, file_path: Path) -> str:
        """Get relative path from watch folder"""
        try:
            return str(file_path.relative_to(self.watch_folder)).replace('\\', '/')
        except ValueError:
            # File is not under watch folder
            return str(file_path).replace('\\', '/')
    
    def get_absolute_path(self, relative_path: str) -> Path:
        """Get absolute path from relative path"""
        return self.watch_folder / relative_path.replace('/', os.sep)
    
    def __enter__(self):
        self.start_monitoring()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_monitoring()