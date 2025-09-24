"""
Configuration Manager for B2 Sync Local application
"""

import os
import configparser
import logging
from pathlib import Path
from typing import Optional
import appdirs

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages application configuration and settings"""
    
    def __init__(self):
        self.app_name = "B2SyncLocal"
        self.app_author = "B2Sync"
        
        # Get config directory
        self.config_dir = Path(appdirs.user_config_dir(self.app_name, self.app_author))
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.config_dir / "config.ini"
        self.config = configparser.ConfigParser()
        
        # Load existing config or create default
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file or create default"""
        if self.config_file.exists():
            try:
                self.config.read(self.config_file)
                logger.info(f"Loaded configuration from {self.config_file}")
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
                self._create_default_config()
        else:
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default configuration"""
        self.config['B2'] = {
            'key_id': '',
            'app_key': '',
            'bucket_name': ''
        }
        
        self.config['Sync'] = {
            'local_folder': str(Path.home() / "B2Sync"),
            'sync_interval': '30',
            'auto_sync': 'true',
            'sync_hidden_files': 'false',
            'sync_direction': 'bidirectional'
        }
        
        self.config['App'] = {
            'start_with_windows': 'true',
            'minimize_to_tray': 'true',
            'show_notifications': 'true',
            'log_level': 'INFO'
        }
        
        self._save_config()
        logger.info("Created default configuration")
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                self.config.write(f)
            logger.debug("Configuration saved")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def is_configured(self) -> bool:
        """Check if B2 credentials are configured"""
        return bool(
            self.get_b2_key_id() and 
            self.get_b2_app_key() and 
            self.get_b2_bucket_name()
        )
    
    # B2 Configuration
    def get_b2_key_id(self) -> str:
        return self.config.get('B2', 'key_id', fallback='')
    
    def set_b2_key_id(self, key_id: str):
        self.config.set('B2', 'key_id', key_id)
        self._save_config()
    
    def get_b2_app_key(self) -> str:
        return self.config.get('B2', 'app_key', fallback='')
    
    def set_b2_app_key(self, app_key: str):
        self.config.set('B2', 'app_key', app_key)
        self._save_config()
    
    def get_b2_bucket_name(self) -> str:
        return self.config.get('B2', 'bucket_name', fallback='')
    
    def set_b2_bucket_name(self, bucket_name: str):
        self.config.set('B2', 'bucket_name', bucket_name)
        self._save_config()
    
    # Sync Configuration
    def get_local_folder(self) -> Path:
        folder_str = self.config.get('Sync', 'local_folder', fallback=str(Path.home() / "B2Sync"))
        return Path(folder_str)
    
    def set_local_folder(self, folder_path: Path):
        self.config.set('Sync', 'local_folder', str(folder_path))
        self._save_config()
    
    def get_sync_interval(self) -> int:
        return self.config.getint('Sync', 'sync_interval', fallback=30)
    
    def set_sync_interval(self, interval: int):
        self.config.set('Sync', 'sync_interval', str(interval))
        self._save_config()
    
    def get_auto_sync(self) -> bool:
        return self.config.getboolean('Sync', 'auto_sync', fallback=True)
    
    def set_auto_sync(self, enabled: bool):
        self.config.set('Sync', 'auto_sync', str(enabled))
        self._save_config()
    
    def get_sync_hidden_files(self) -> bool:
        return self.config.getboolean('Sync', 'sync_hidden_files', fallback=False)
    
    def set_sync_hidden_files(self, enabled: bool):
        self.config.set('Sync', 'sync_hidden_files', str(enabled))
        self._save_config()
    
    def get_sync_direction(self) -> str:
        return self.config.get('Sync', 'sync_direction', fallback='bidirectional')
    
    def set_sync_direction(self, direction: str):
        """Set sync direction: 'bidirectional', 'upload_only', 'download_only'"""
        valid_directions = ['bidirectional', 'upload_only', 'download_only']
        if direction not in valid_directions:
            raise ValueError(f"Invalid sync direction. Must be one of: {valid_directions}")
        self.config.set('Sync', 'sync_direction', direction)
        self._save_config()
    
    # App Configuration
    def get_start_with_windows(self) -> bool:
        return self.config.getboolean('App', 'start_with_windows', fallback=True)
    
    def set_start_with_windows(self, enabled: bool):
        self.config.set('App', 'start_with_windows', str(enabled))
        self._save_config()
    
    def get_minimize_to_tray(self) -> bool:
        return self.config.getboolean('App', 'minimize_to_tray', fallback=True)
    
    def set_minimize_to_tray(self, enabled: bool):
        self.config.set('App', 'minimize_to_tray', str(enabled))
        self._save_config()
    
    def get_show_notifications(self) -> bool:
        return self.config.getboolean('App', 'show_notifications', fallback=True)
    
    def set_show_notifications(self, enabled: bool):
        self.config.set('App', 'show_notifications', str(enabled))
        self._save_config()
    
    def get_log_level(self) -> str:
        return self.config.get('App', 'log_level', fallback='INFO')
    
    def set_log_level(self, level: str):
        self.config.set('App', 'log_level', level)
        self._save_config()
    
    def get_config_dir(self) -> Path:
        """Get the configuration directory"""
        return self.config_dir
    
    def export_config(self) -> dict:
        """Export configuration as dictionary"""
        config_dict = {}
        for section in self.config.sections():
            config_dict[section] = dict(self.config[section])
        return config_dict
    
    def import_config(self, config_dict: dict):
        """Import configuration from dictionary"""
        for section, options in config_dict.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
            for option, value in options.items():
                self.config.set(section, option, str(value))
        self._save_config()