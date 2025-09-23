"""
Settings Dialog for B2 Sync Local application
"""

import os
import sys
from pathlib import Path

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget,
    QLineEdit, QSpinBox, QCheckBox, QPushButton, QFileDialog,
    QLabel, QGroupBox, QComboBox, QTextEdit, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from .auto_startup import StartupManager

from .config_manager import ConfigManager
from .sync_engine import SyncEngine
from .logger import get_logger

logger = get_logger(__name__)

class SettingsDialog(QDialog):
    """Settings dialog for configuring B2 Sync"""
    
    def __init__(self, config: ConfigManager, sync_engine: SyncEngine, parent=None):
        super().__init__(parent)
        self.config = config
        self.sync_engine = sync_engine
        self.startup_manager = StartupManager()
        
        self.setWindowTitle("B2 Sync Settings")
        self.setModal(True)
        self.resize(500, 400)
        
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self._create_b2_tab()
        self._create_sync_tab()
        self._create_app_tab()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.test_connection_btn = QPushButton("Test B2 Connection")
        self.test_connection_btn.clicked.connect(self._test_b2_connection)
        button_layout.addWidget(self.test_connection_btn)
        
        button_layout.addStretch()
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self._save_and_close)
        button_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self._apply_settings)
        button_layout.addWidget(self.apply_btn)
        
        layout.addLayout(button_layout)
    
    def _create_b2_tab(self):
        """Create B2 configuration tab"""
        tab = QDialog()
        layout = QVBoxLayout(tab)
        
        # B2 Credentials Group
        credentials_group = QGroupBox("Backblaze B2 Credentials")
        credentials_layout = QFormLayout(credentials_group)
        
        self.key_id_edit = QLineEdit()
        self.key_id_edit.setPlaceholderText("Enter your B2 Key ID")
        credentials_layout.addRow("Key ID:", self.key_id_edit)
        
        self.app_key_edit = QLineEdit()
        self.app_key_edit.setEchoMode(QLineEdit.Password)
        self.app_key_edit.setPlaceholderText("Enter your B2 Application Key")
        credentials_layout.addRow("Application Key:", self.app_key_edit)
        
        self.bucket_name_edit = QLineEdit()
        self.bucket_name_edit.setPlaceholderText("Enter your B2 bucket name")
        credentials_layout.addRow("Bucket Name:", self.bucket_name_edit)
        
        layout.addWidget(credentials_group)
        
        # Help text
        help_text = QLabel("""
<b>How to get B2 credentials:</b><br>
1. Log in to your Backblaze account<br>
2. Go to "App Keys" section<br>
3. Create a new application key<br>
4. Copy the Key ID and Application Key<br>
5. Create or select a bucket for sync
        """)
        help_text.setWordWrap(True)
        help_text.setStyleSheet("QLabel { color: #666; }")
        layout.addWidget(help_text)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "B2 Configuration")
    
    def _create_sync_tab(self):
        """Create sync configuration tab"""
        tab = QDialog()
        layout = QVBoxLayout(tab)
        
        # Local Folder Group
        folder_group = QGroupBox("Local Sync Folder")
        folder_layout = QHBoxLayout(folder_group)
        
        self.local_folder_edit = QLineEdit()
        folder_layout.addWidget(self.local_folder_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_folder)
        folder_layout.addWidget(browse_btn)
        
        layout.addWidget(folder_group)
        
        # Sync Options Group
        sync_group = QGroupBox("Sync Options")
        sync_layout = QFormLayout(sync_group)
        
        self.auto_sync_check = QCheckBox("Enable automatic sync")
        sync_layout.addRow(self.auto_sync_check)
        
        self.sync_interval_spin = QSpinBox()
        self.sync_interval_spin.setRange(10, 3600)
        self.sync_interval_spin.setSuffix(" seconds")
        sync_layout.addRow("Sync Interval:", self.sync_interval_spin)
        
        self.sync_hidden_check = QCheckBox("Sync hidden files and folders")
        sync_layout.addRow(self.sync_hidden_check)
        
        layout.addWidget(sync_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Sync Settings")
    
    def _create_app_tab(self):
        """Create application settings tab"""
        tab = QDialog()
        layout = QVBoxLayout(tab)
        
        # Startup Group
        startup_group = QGroupBox("Startup Options")
        startup_layout = QFormLayout(startup_group)
        
        self.start_with_windows_check = QCheckBox("Start with Windows")
        self.start_with_windows_check.stateChanged.connect(self.on_auto_start_changed)
        startup_layout.addRow(self.start_with_windows_check)
        
        self.minimize_to_tray_check = QCheckBox("Minimize to system tray")
        startup_layout.addRow(self.minimize_to_tray_check)
        
        layout.addWidget(startup_group)
        
        # Notifications Group
        notifications_group = QGroupBox("Notifications")
        notifications_layout = QFormLayout(notifications_group)
        
        self.show_notifications_check = QCheckBox("Show sync notifications")
        notifications_layout.addRow(self.show_notifications_check)
        
        layout.addWidget(notifications_group)
        
        # Logging Group
        logging_group = QGroupBox("Logging")
        logging_layout = QFormLayout(logging_group)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        logging_layout.addRow("Log Level:", self.log_level_combo)
        
        layout.addWidget(logging_group)
        
        # Actions Group
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        open_logs_btn = QPushButton("Open Log Folder")
        open_logs_btn.clicked.connect(self._open_log_folder)
        actions_layout.addWidget(open_logs_btn)
        
        reset_stats_btn = QPushButton("Reset Statistics")
        reset_stats_btn.clicked.connect(self._reset_statistics)
        actions_layout.addWidget(reset_stats_btn)
        
        layout.addWidget(actions_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Application")
    
    def _load_settings(self):
        """Load current settings into the dialog"""
        # B2 settings
        self.key_id_edit.setText(self.config.get_b2_key_id())
        self.app_key_edit.setText(self.config.get_b2_app_key())
        self.bucket_name_edit.setText(self.config.get_b2_bucket_name())
        
        # Sync settings
        self.local_folder_edit.setText(str(self.config.get_local_folder()))
        self.auto_sync_check.setChecked(self.config.get_auto_sync())
        self.sync_interval_spin.setValue(self.config.get_sync_interval())
        self.sync_hidden_check.setChecked(self.config.get_sync_hidden_files())
        
        # App settings
        self.start_with_windows_check.setChecked(self.startup_manager.is_enabled())
        self.minimize_to_tray_check.setChecked(self.config.get_minimize_to_tray())
        self.show_notifications_check.setChecked(self.config.get_show_notifications())
        
        log_level = self.config.get_log_level()
        index = self.log_level_combo.findText(log_level)
        if index >= 0:
            self.log_level_combo.setCurrentIndex(index)
    
    def _browse_folder(self):
        """Browse for local sync folder"""
        current_folder = self.local_folder_edit.text()
        if not current_folder:
            current_folder = str(Path.home())
        
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Sync Folder",
            current_folder
        )
        
        if folder:
            self.local_folder_edit.setText(folder)
    
    def _test_b2_connection(self):
        """Test B2 connection with current credentials"""
        # Temporarily save credentials
        old_key_id = self.config.get_b2_key_id()
        old_app_key = self.config.get_b2_app_key()
        old_bucket = self.config.get_b2_bucket_name()
        
        try:
            # Set new credentials
            self.config.set_b2_key_id(self.key_id_edit.text().strip())
            self.config.set_b2_app_key(self.app_key_edit.text().strip())
            self.config.set_b2_bucket_name(self.bucket_name_edit.text().strip())
            
            # Test authentication
            if self.sync_engine.b2_client.authenticate():
                QMessageBox.information(
                    self,
                    "Connection Test",
                    "Successfully connected to Backblaze B2!"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Connection Test",
                    "Failed to connect to Backblaze B2. Please check your credentials."
                )
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Connection Test",
                f"Error testing connection: {str(e)}"
            )
        
        finally:
            # Restore old credentials
            self.config.set_b2_key_id(old_key_id)
            self.config.set_b2_app_key(old_app_key)
            self.config.set_b2_bucket_name(old_bucket)
    
    def _open_log_folder(self):
        """Open the log folder"""
        log_dir = self.config.get_config_dir().parent / "Logs"
        
        try:
            if sys.platform == "win32":
                os.startfile(str(log_dir))
            elif sys.platform == "darwin":
                os.system(f"open '{log_dir}'")
            else:
                os.system(f"xdg-open '{log_dir}'")
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to open log folder: {str(e)}"
            )
    
    def _reset_statistics(self):
        """Reset sync statistics"""
        reply = QMessageBox.question(
            self,
            "Reset Statistics",
            "Are you sure you want to reset all sync statistics?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.sync_engine.reset_stats()
            QMessageBox.information(
                self,
                "Statistics Reset",
                "Sync statistics have been reset."
            )
    
    def _apply_settings(self):
        """Apply settings without closing dialog"""
        try:
            # Validate settings
            if not self._validate_settings():
                return
            
            # Save B2 settings
            self.config.set_b2_key_id(self.key_id_edit.text().strip())
            self.config.set_b2_app_key(self.app_key_edit.text().strip())
            self.config.set_b2_bucket_name(self.bucket_name_edit.text().strip())
            
            # Save sync settings
            self.config.set_local_folder(Path(self.local_folder_edit.text().strip()))
            self.config.set_auto_sync(self.auto_sync_check.isChecked())
            self.config.set_sync_interval(self.sync_interval_spin.value())
            self.config.set_sync_hidden_files(self.sync_hidden_check.isChecked())
            
            # Save app settings
            self.config.set_start_with_windows(self.start_with_windows_check.isChecked())
            self.config.set_minimize_to_tray(self.minimize_to_tray_check.isChecked())
            self.config.set_show_notifications(self.show_notifications_check.isChecked())
            self.config.set_log_level(self.log_level_combo.currentText())
            
            # Update file monitor settings
            self.sync_engine.file_monitor.set_sync_hidden_files(
                self.config.get_sync_hidden_files()
            )
            
            QMessageBox.information(
                self,
                "Settings Applied",
                "Settings have been applied successfully."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to apply settings: {str(e)}"
            )
    
    def _validate_settings(self) -> bool:
        """Validate settings before saving"""
        # Check B2 credentials
        if not all([
            self.key_id_edit.text().strip(),
            self.app_key_edit.text().strip(),
            self.bucket_name_edit.text().strip()
        ]):
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please fill in all B2 credentials."
            )
            self.tab_widget.setCurrentIndex(0)
            return False
        
        # Check local folder
        local_folder = self.local_folder_edit.text().strip()
        if not local_folder:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please select a local sync folder."
            )
            self.tab_widget.setCurrentIndex(1)
            return False
        
        # Try to create folder if it doesn't exist
        try:
            Path(local_folder).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Validation Error",
                f"Cannot create or access local folder: {str(e)}"
            )
            self.tab_widget.setCurrentIndex(1)
            return False
        
        return True
    
    def _save_and_close(self):
        """Save settings and close dialog"""
        if self._apply_settings():
            self.accept()

    def on_auto_start_changed(self, state):
        """Handle auto-start checkbox change"""
        try:
            if state == Qt.Checked:
                success = self.startup_manager.enable()
                if not success:
                    QMessageBox.warning(self, "Auto-start Error", 
                                      "Failed to enable auto-start. Please check permissions.")
                    self.auto_start_cb.setChecked(False)
            else:
                success = self.startup_manager.disable()
                if not success:
                    QMessageBox.warning(self, "Auto-start Error", 
                                      "Failed to disable auto-start. Please check permissions.")
                    self.auto_start_cb.setChecked(True)
        except Exception as e:
            QMessageBox.critical(self, "Auto-start Error", f"Error managing auto-start: {e}")