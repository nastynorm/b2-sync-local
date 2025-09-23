param(
    [string]$ShortcutPath,
    [string]$TargetPath,
    [string]$WorkingDirectory,
    [int]$WindowStyle = 1
)

$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TargetPath
$Shortcut.WorkingDirectory = $WorkingDirectory
if ($WindowStyle -ne 1) {
    $Shortcut.WindowStyle = $WindowStyle
}
$Shortcut.Save()

Write-Host "Shortcut created: $ShortcutPath"