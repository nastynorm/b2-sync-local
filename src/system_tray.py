"""
System Tray Application for B2 Sync Local
"""

import sys
import os
import threading
import webbrowser
from pathlib import Path
from typing import Optional

import pystray
from pystray import MenuItem, Menu
from PIL import Image, ImageDraw
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox
from PyQt5.QtCore import QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QPixmap

from .sync_engine import SyncEngine, SyncStatus, SyncAction
from .config_manager import ConfigManager
from .settings_dialog import SettingsDialog
from .logger import get_logger

logger = get_logger(__name__)

class SyncNotifier(QObject):
    """Qt object for handling sync notifications"""
    status_changed = pyqtSignal(str)
    sync_event = pyqtSignal(str, str, bool, str)

class SystemTrayApp:
    """System tray application for B2 Sync"""
    
    def __init__(self, sync_engine: SyncEngine, config: ConfigManager):
        self.sync_engine = sync_engine
        self.config = config
        self.app = None
        self.tray_icon = None
        self.notifier = SyncNotifier()
        
        # Setup Qt application
        self._setup_qt_app()
        
        # Setup sync engine callbacks
        self.sync_engine.add_status_callback(self._on_status_change)
        self.sync_engine.add_sync_callback(self._on_sync_event)
        
        # Create tray icon
        self._create_tray_icon()
        
        logger.info("System tray application initialized")
    
    def _setup_qt_app(self):
        """Setup Qt application"""
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
            self.app.setQuitOnLastWindowClosed(False)
        else:
            self.app = QApplication.instance()
    
    def _create_tray_icon(self):
        """Create system tray icon and menu"""
        # Create icon
        icon = self._create_icon()
        
        # Create tray icon
        self.tray_icon = QSystemTrayIcon(icon, self.app)
        self.tray_icon.setToolTip("B2 Sync Local")
        
        # Create context menu
        menu = QMenu()
        
        # Status item
        self.status_action = QAction("Status: Initializing...", self.app)
        self.status_action.setEnabled(False)
        menu.addAction(self.status_action)
        
        menu.addSeparator()
        
        # Sync actions
        sync_now_action = QAction("Sync Now", self.app)
        sync_now_action.triggered.connect(self._sync_now)
        menu.addAction(sync_now_action)
        
        self.pause_resume_action = QAction("Pause Sync", self.app)
        self.pause_resume_action.triggered.connect(self._toggle_pause_resume)
        menu.addAction(self.pause_resume_action)
        
        menu.addSeparator()
        
        # Folder actions
        open_folder_action = QAction("Open Sync Folder", self.app)
        open_folder_action.triggered.connect(self._open_sync_folder)
        menu.addAction(open_folder_action)
        
        menu.addSeparator()
        
        # Settings and info
        settings_action = QAction("Settings...", self.app)
        settings_action.triggered.connect(self._show_settings)
        menu.addAction(settings_action)
        
        stats_action = QAction("View Statistics", self.app)
        stats_action.triggered.connect(self._show_statistics)
        menu.addAction(stats_action)
        
        menu.addSeparator()
        
        # Exit
        exit_action = QAction("Exit", self.app)
        exit_action.triggered.connect(self._exit_application)
        menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(menu)
        
        # Connect double-click to open folder
        self.tray_icon.activated.connect(self._on_tray_activated)
        
        # Show tray icon
        self.tray_icon.show()
    
    def _create_icon(self, status: str = "idle") -> QIcon:
        """Create tray icon based on status"""
        from PyQt5.QtGui import QPainter, QBrush, QPen, QColor
        from PyQt5.QtCore import Qt
        
        # Create a simple icon using Qt directly
        size = 64
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Choose color based on status
        colors = {
            'idle': (100, 149, 237),      # Cornflower blue
            'syncing': (50, 205, 50),     # Lime green
            'error': (220, 20, 60),       # Crimson
            'paused': (255, 165, 0)       # Orange
        }
        
        color = colors.get(status, colors['idle'])
        brush = QBrush(Qt.SolidPattern)
        qcolor = QColor(*color)
        brush.setColor(qcolor)
        
        painter.setBrush(brush)
        painter.setPen(QPen(Qt.NoPen))
        
        # Draw cloud-like shape
        painter.drawEllipse(10, 20, 25, 20)
        painter.drawEllipse(25, 15, 25, 20)
        painter.drawEllipse(35, 20, 20, 20)
        painter.drawRect(15, 30, 35, 15)
        
        painter.end()
        return QIcon(pixmap)
    
    def _on_tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            self._open_sync_folder()
    
    def _sync_now(self):
        """Trigger immediate sync"""
        self.sync_engine.sync_now()
        if self.config.get_show_notifications():
            self.tray_icon.showMessage(
                "B2 Sync",
                "Synchronization started",
                QSystemTrayIcon.Information,
                3000
            )
    
    def _toggle_pause_resume(self):
        """Toggle pause/resume sync"""
        if self.sync_engine.get_status() == SyncStatus.PAUSED:
            self.sync_engine.resume_sync()
            self.pause_resume_action.setText("Pause Sync")
        else:
            self.sync_engine.pause_sync()
            self.pause_resume_action.setText("Resume Sync")
    
    def _open_sync_folder(self):
        """Open sync folder in file explorer"""
        folder_path = self.config.get_local_folder()
        folder_path.mkdir(parents=True, exist_ok=True)
        
        try:
            if sys.platform == "win32":
                os.startfile(str(folder_path))
            elif sys.platform == "darwin":
                os.system(f"open '{folder_path}'")
            else:
                os.system(f"xdg-open '{folder_path}'")
        except Exception as e:
            logger.error(f"Failed to open sync folder: {e}")
            self._show_error("Failed to open sync folder", str(e))
    
    def _show_settings(self):
        """Show settings dialog"""
        try:
            dialog = SettingsDialog(self.config, self.sync_engine)
            dialog.exec_()
        except Exception as e:
            logger.error(f"Failed to show settings: {e}")
            self._show_error("Failed to open settings", str(e))
    
    def _show_statistics(self):
        """Show sync statistics"""
        stats = self.sync_engine.get_stats()
        last_sync = self.sync_engine.last_sync_time
        
        message = f"""Sync Statistics:
        
Files Uploaded: {stats['files_uploaded']}
Files Downloaded: {stats['files_downloaded']}
Files Deleted: {stats['files_deleted']}
Bytes Uploaded: {self._format_bytes(stats['bytes_uploaded'])}
Bytes Downloaded: {self._format_bytes(stats['bytes_downloaded'])}
Conflicts: {stats['conflicts']}
Errors: {stats['errors']}

Last Sync: {last_sync.strftime('%Y-%m-%d %H:%M:%S') if last_sync else 'Never'}
Status: {self.sync_engine.get_status().value.title()}"""
        
        msg_box = QMessageBox()
        msg_box.setWindowTitle("B2 Sync Statistics")
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.exec_()
    
    def _format_bytes(self, bytes_count: int) -> str:
        """Format bytes in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} PB"
    
    def _exit_application(self):
        """Exit the application"""
        reply = QMessageBox.question(
            None,
            "Exit B2 Sync",
            "Are you sure you want to exit B2 Sync?\nSynchronization will stop.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            logger.info("Exiting application")
            self.sync_engine.stop()
            self.tray_icon.hide()
            self.app.quit()
    
    def _show_error(self, title: str, message: str):
        """Show error message"""
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.exec_()
    
    def _on_status_change(self, status: SyncStatus):
        """Handle sync status changes"""
        status_text = {
            SyncStatus.IDLE: "Idle",
            SyncStatus.SYNCING: "Syncing...",
            SyncStatus.ERROR: "Error",
            SyncStatus.PAUSED: "Paused"
        }
        
        self.status_action.setText(f"Status: {status_text.get(status, 'Unknown')}")
        
        # Update icon
        icon = self._create_icon(status.value)
        self.tray_icon.setIcon(icon)
        
        # Update pause/resume action
        if status == SyncStatus.PAUSED:
            self.pause_resume_action.setText("Resume Sync")
        else:
            self.pause_resume_action.setText("Pause Sync")
        
        # Show notification for errors
        if status == SyncStatus.ERROR and self.config.get_show_notifications():
            self.tray_icon.showMessage(
                "B2 Sync Error",
                "Synchronization encountered an error. Check logs for details.",
                QSystemTrayIcon.Critical,
                5000
            )
    
    def _on_sync_event(self, action: SyncAction, file_path: str, success: bool, error: str = None):
        """Handle sync events"""
        if not self.config.get_show_notifications():
            return
        
        if not success and error:
            self.tray_icon.showMessage(
                "B2 Sync Error",
                f"Failed to {action.value} {file_path}: {error}",
                QSystemTrayIcon.Warning,
                3000
            )
    
    def run(self):
        """Run the system tray application"""
        logger.info("Starting system tray application...")
        
        # Check if system tray is available
        logger.info("Checking if system tray is available...")
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.error("System tray is not available on this system")
            QMessageBox.critical(
                None,
                "System Tray",
                "System tray is not available on this system."
            )
            sys.exit(1)
        
        logger.info("System tray is available")
        
        # Try to start sync engine
        logger.info("Attempting to start sync engine...")
        sync_started = self.sync_engine.start()
        logger.info(f"Sync engine start result: {sync_started}")
        
        if sync_started:
            # Show initial notification if sync started successfully
            logger.info("Sync engine started successfully")
            if self.config.get_show_notifications():
                logger.info("Showing success notification")
                self.tray_icon.showMessage(
                    "B2 Sync Started",
                    f"Monitoring: {self.config.get_local_folder()}",
                    QSystemTrayIcon.Information,
                    3000
                )
        else:
            # Show notification that configuration is needed
            logger.info("Sync engine failed to start - showing configuration notification")
            self.tray_icon.showMessage(
                "B2 Sync - Configuration Required",
                "Please configure your B2 credentials through Settings.",
                QSystemTrayIcon.Warning,
                5000
            )
            logger.warning("Sync engine failed to start - B2 credentials may be missing")
        
        # Run Qt event loop regardless of sync engine status
        logger.info("Starting Qt event loop...")
        try:
            logger.info("Entering app.exec_()...")
            sys.exit(self.app.exec_())
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            if sync_started:
                self.sync_engine.stop()
            self.app.quit()