#!/usr/bin/env python3
"""
B2 Sync Local - Main Entry Point
A Backblaze B2 cloud storage sync application similar to OneDrive
"""

import sys
import os
import argparse
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.b2_client import B2Client
from src.file_monitor import FileMonitor
from src.sync_engine import SyncEngine
from src.system_tray import SystemTrayApp
from src.config_manager import ConfigManager
from src.logger import setup_logger


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="B2 Sync Local - Backblaze B2 sync application")
    parser.add_argument("--minimized", action="store_true", 
                       help="Start the application minimized to system tray")
    parser.add_argument("--debug", action="store_true",
                       help="Enable debug logging")
    parser.add_argument("--config-dir", type=str,
                       help="Custom configuration directory")
    return parser.parse_args()


def main():
    """Main entry point for the B2 Sync Local application"""
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Setup logging
    log_level = "DEBUG" if args.debug else "INFO"
    logger = setup_logger(level=log_level)
    logger.info("Starting B2 Sync Local application")
    
    if args.minimized:
        logger.info("Starting in minimized mode")
    
    try:
        # Initialize configuration manager
        config_manager = ConfigManager()
        
        # Initialize B2 client
        b2_client = B2Client(config_manager)
        
        # Initialize file monitor
        local_folder = config_manager.get_local_folder()
        if not local_folder:
            # Set a default local folder if none is configured
            local_folder = Path.home() / "B2Sync"
            config_manager.set_local_folder(local_folder)
        file_monitor = FileMonitor(local_folder)
        
        # Initialize sync engine
        sync_engine = SyncEngine(b2_client, file_monitor, config_manager)
        
        # Initialize and start system tray application
        tray_app = SystemTrayApp(sync_engine, config_manager)
        tray_app.run()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()