# PowerShell-Script zum Erstellen einer Desktop-Verknuepfung mit Logo
$ErrorActionPreference = "Stop"

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$startScript = Join-Path $scriptPath "start_phoenyra.bat"
$stopScript = Join-Path $scriptPath "stop_phoenyra.bat"
$desktopPath = [Environment]::GetFolderPath("Desktop")
$logoPngPath = Join-Path $scriptPath "logo\Phoenyra_Logos\Phoenyra_kl.png"
$logoIcoPath = Join-Path $scriptPath "logo\Phoenyra_Logos\Phoenyra_kl.ico"

# Pruefen ob Start-Script existiert
if (-not (Test-Path $startScript)) {
    Write-Host "Fehler: start_phoenyra.bat nicht gefunden!" -ForegroundColor Red
    exit 1
}

# Logo-Pfad bestimmen
$iconPath = $null

if (Test-Path $logoIcoPath) {
    # ICO-Datei vorhanden
    $iconPath = $logoIcoPath
    Write-Host "Verwende vorhandene ICO-Datei: $iconPath" -ForegroundColor Cyan
} elseif (Test-Path $logoPngPath) {
    # PNG zu ICO konvertieren
    Write-Host "Konvertiere PNG zu ICO..." -ForegroundColor Cyan
    try {
        Add-Type -AssemblyName System.Drawing
        $png = New-Object System.Drawing.Bitmap($logoPngPath)
        $ico = [System.Drawing.Icon]::FromHandle($png.GetHicon())
        
        # ICO speichern
        $icoStream = New-Object System.IO.FileStream($logoIcoPath, [System.IO.FileMode]::Create)
        $ico.Save($icoStream)
        $icoStream.Close()
        $ico.Dispose()
        $png.Dispose()
        
        $iconPath = $logoIcoPath
        Write-Host "ICO-Datei erstellt: $iconPath" -ForegroundColor Green
    } catch {
        # Fallback: PNG direkt verwenden (funktioniert in Windows 10/11)
        Write-Host "Konvertierung fehlgeschlagen, verwende PNG direkt..." -ForegroundColor Yellow
        $iconPath = $logoPngPath
    }
} else {
    Write-Host "Warnung: Logo nicht gefunden: $logoPngPath" -ForegroundColor Yellow
    Write-Host "Verwende Standard-Icon..." -ForegroundColor Yellow
    $iconPath = "C:\Windows\System32\shell32.dll,13"
}

$shell = New-Object -ComObject WScript.Shell

# Start-Verknuepfung
Write-Host "Erstelle Desktop-Verknuepfung mit Logo..." -ForegroundColor Cyan
$shortcutPath = Join-Path $desktopPath "Phoenyra BESS Trade System.lnk"
if (Test-Path $shortcutPath) {
    Remove-Item $shortcutPath -Force
}
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $startScript
$shortcut.WorkingDirectory = $scriptPath
$shortcut.Description = "Phoenyra BESS Trade System - Startet alle Docker-Services"
$shortcut.IconLocation = $iconPath
$shortcut.Save()

Write-Host "Desktop-Verknuepfung erstellt!" -ForegroundColor Green
Write-Host "Pfad: $shortcutPath" -ForegroundColor Yellow

# Stop-Verknuepfung (mit gleichem Logo)
Write-Host "Erstelle Stop-Verknuepfung mit Logo..." -ForegroundColor Cyan
$stopShortcutPath = Join-Path $desktopPath "Phoenyra BESS - Stoppen.lnk"
if (Test-Path $stopShortcutPath) {
    Remove-Item $stopShortcutPath -Force
}
$stopShortcut = $shell.CreateShortcut($stopShortcutPath)
$stopShortcut.TargetPath = $stopScript
$stopShortcut.WorkingDirectory = $scriptPath
$stopShortcut.Description = "Phoenyra BESS Trade System - Stoppt alle Docker-Services"
$stopShortcut.IconLocation = $iconPath
$stopShortcut.Save()

Write-Host "Stop-Verknuepfung erstellt!" -ForegroundColor Green
Write-Host "Pfad: $stopShortcutPath" -ForegroundColor Yellow

Write-Host ""
Write-Host "Fertig! Die Verknuepfungen sind auf dem Desktop verfuegbar." -ForegroundColor Green
Write-Host "Logo verwendet: $iconPath" -ForegroundColor Cyan
