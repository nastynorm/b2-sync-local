# B2 Sync Local

A Backblaze B2 cloud storage synchronization application that works like OneDrive, providing seamless file synchronization between your local computer and B2 cloud storage with a convenient system tray interface.

## Features

- **Bidirectional Sync**: Automatically sync files between local folders and Backblaze B2 buckets
- **System Tray Integration**: Lives in your system tray for easy access and monitoring
- **Real-time Monitoring**: Watches for file changes and syncs automatically
- **Conflict Resolution**: Handles file conflicts intelligently
- **Pause/Resume**: Control sync operations as needed
- **Statistics Tracking**: Monitor upload/download progress and statistics
- **Auto-startup**: Optional automatic startup with Windows
- **Secure**: Uses Backblaze B2 SDK with proper authentication

## Requirements

- Python 3.8 or later
- Windows 10/11 (primary support)
- Backblaze B2 account with API credentials

## Installation

### Quick Install (Windows)

1. Download or clone this repository
2. Run `install.bat` as administrator
3. Follow the installation prompts
4. Configure your B2 credentials in the settings

### Manual Install

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/b2-sync-local.git
   cd b2-sync-local
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python main.py
   ```

## Configuration

### First Time Setup

1. Right-click the system tray icon and select "Settings"
2. In the B2 Configuration tab:
   - Enter your B2 Application Key ID
   - Enter your B2 Application Key
   - Enter your B2 Bucket Name
   - Test the connection
3. In the Sync Settings tab:
   - Choose your local sync folder
   - Set sync interval (default: 30 seconds)
   - Configure conflict resolution preferences
4. Click "Apply" to save settings

### B2 Credentials

You'll need to create B2 application keys:

1. Log into your Backblaze B2 account
2. Go to "App Keys" in the B2 Cloud Storage section
3. Create a new application key with appropriate permissions
4. Note down the Key ID and Application Key

## Usage

### System Tray Menu

- **Sync Now**: Manually trigger a sync operation
- **Pause Sync**: Temporarily pause automatic syncing
- **Open Sync Folder**: Open the local sync folder in File Explorer
- **Settings**: Open the configuration dialog
- **View Statistics**: See sync statistics and recent activity
- **Exit**: Close the application

### File Operations

- **Upload**: Add files to your local sync folder to upload them to B2
- **Download**: Files added to B2 will automatically download to your local folder
- **Delete**: Deleting files locally will remove them from B2 (and vice versa)
- **Modify**: File changes are detected and synced automatically

## Conflict Resolution

When conflicts occur (same file modified in both locations):

- **Local Priority** (default): Local file takes precedence
- **Remote Priority**: B2 file takes precedence
- **Timestamp**: Newer file takes precedence
- **Manual**: Prompt user for decision

## Logging

Logs are stored in:
- Windows: `%LOCALAPPDATA%\B2SyncLocal\logs\`

Log levels can be configured in the settings.

## Troubleshooting

### Common Issues

1. **Connection Failed**: Check your B2 credentials and internet connection
2. **Sync Not Working**: Verify folder permissions and B2 bucket access
3. **High CPU Usage**: Adjust sync interval or exclude large files
4. **Missing Files**: Check conflict resolution settings and logs

### Log Files

Check the application logs for detailed error information:
```
%LOCALAPPDATA%\B2SyncLocal\logs\b2_sync.log
```

## Uninstallation

Run `uninstall.bat` to remove the application, or manually:

1. Stop the application
2. Remove desktop and startup shortcuts
3. Delete the application folder
4. Optionally remove configuration files from `%APPDATA%\B2SyncLocal\`

## Security

- B2 credentials are stored securely in the Windows credential store
- All communications use HTTPS
- File integrity is verified using checksums
- No sensitive data is logged

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Check the logs for error details
- Review the troubleshooting section
- Create an issue on GitHub

## Acknowledgments

- Built with the Backblaze B2 SDK
- Uses PyQt5 for the GUI components
- File monitoring powered by Watchdog
- System tray integration via pystray