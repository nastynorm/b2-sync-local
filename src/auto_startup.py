"""
Auto-startup functionality for B2 Sync Local
Handles adding/removing the application from Windows startup
"""

import os
import sys
import winreg
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class AutoStartup:
    """Manages auto-startup functionality for Windows"""
    
    def __init__(self):
        self.app_name = "B2SyncLocal"
        self.registry_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        
    def is_enabled(self) -> bool:
        """Check if auto-startup is currently enabled"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key, 0, winreg.KEY_READ) as key:
                try:
                    winreg.QueryValueEx(key, self.app_name)
                    return True
                except FileNotFoundError:
                    return False
        except Exception as e:
            logger.error(f"Error checking auto-startup status: {e}")
            return False
    
    def enable(self) -> bool:
        """Enable auto-startup by adding registry entry"""
        try:
            # Get the path to the current Python executable and script
            python_exe = sys.executable
            script_path = Path(__file__).parent.parent / "main.py"
            
            # Create the command to run
            command = f'"{python_exe}" "{script_path}" --minimized'
            
            # Add to registry
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, command)
            
            logger.info("Auto-startup enabled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error enabling auto-startup: {e}")
            return False
    
    def disable(self) -> bool:
        """Disable auto-startup by removing registry entry"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key, 0, winreg.KEY_WRITE) as key:
                try:
                    winreg.DeleteValue(key, self.app_name)
                    logger.info("Auto-startup disabled successfully")
                    return True
                except FileNotFoundError:
                    logger.info("Auto-startup was not enabled")
                    return True
                    
        except Exception as e:
            logger.error(f"Error disabling auto-startup: {e}")
            return False
    
    def toggle(self) -> bool:
        """Toggle auto-startup on/off"""
        if self.is_enabled():
            return self.disable()
        else:
            return self.enable()
    
    def get_startup_command(self) -> str:
        """Get the current startup command from registry"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key, 0, winreg.KEY_READ) as key:
                try:
                    value, _ = winreg.QueryValueEx(key, self.app_name)
                    return value
                except FileNotFoundError:
                    return ""
        except Exception as e:
            logger.error(f"Error getting startup command: {e}")
            return ""


class StartupManager:
    """Cross-platform startup manager (currently Windows only)"""
    
    def __init__(self):
        self.platform = sys.platform
        
        if self.platform == "win32":
            self.startup_handler = AutoStartup()
        else:
            self.startup_handler = None
            logger.warning(f"Auto-startup not supported on platform: {self.platform}")
    
    def is_supported(self) -> bool:
        """Check if auto-startup is supported on current platform"""
        return self.startup_handler is not None
    
    def is_enabled(self) -> bool:
        """Check if auto-startup is enabled"""
        if not self.is_supported():
            return False
        return self.startup_handler.is_enabled()
    
    def enable(self) -> bool:
        """Enable auto-startup"""
        if not self.is_supported():
            logger.warning("Auto-startup not supported on this platform")
            return False
        return self.startup_handler.enable()
    
    def disable(self) -> bool:
        """Disable auto-startup"""
        if not self.is_supported():
            logger.warning("Auto-startup not supported on this platform")
            return False
        return self.startup_handler.disable()
    
    def toggle(self) -> bool:
        """Toggle auto-startup"""
        if not self.is_supported():
            logger.warning("Auto-startup not supported on this platform")
            return False
        return self.startup_handler.toggle()


# For testing
if __name__ == "__main__":
    startup_manager = StartupManager()
    
    print(f"Platform: {sys.platform}")
    print(f"Auto-startup supported: {startup_manager.is_supported()}")
    
    if startup_manager.is_supported():
        print(f"Auto-startup enabled: {startup_manager.is_enabled()}")
        
        if startup_manager.startup_handler:
            command = startup_manager.startup_handler.get_startup_command()
            if command:
                print(f"Startup command: {command}")