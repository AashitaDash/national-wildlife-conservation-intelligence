# ==============================================================================
# Wildlife Conservation Intelligence Platform - Clean Zip Packager
# ==============================================================================
# This script bundles the project into a clean, lightweight zip file for sharing
# with teammates or evaluators. It preserves the database, backend, and frontend
# source code while excluding heavy temporary folders (node_modules, __pycache__).
# ==============================================================================

$ProjectDir = $PSScriptRoot
$ZipFile = Join-Path (Split-Path $ProjectDir -Parent) "Wildlife_Conservation_Shareable.zip"

Write-Host "Creating clean shareable package..." -ForegroundColor Cyan

# Remove old zip if present
if (Test-Path $ZipFile) {
    Remove-Item $ZipFile -Force
}

# Collect files excluding heavy/temporary folders
$ExcludePatterns = @(
    "\\node_modules\\",
    "\\\.pytest_cache\\",
    "\\__pycache__\\",
    "\\frontend\\dist\\",
    "\\\.vite\\"
)

$FilesToZip = Get-ChildItem -Path $ProjectDir -Recurse -File | Where-Object {
    $filePath = $_.FullName
    $exclude = $false
    foreach ($pattern in $ExcludePatterns) {
        if ($filePath -match $pattern) {
            $exclude = $true
            break
        }
    }
    -not $exclude
}

Write-Host "Zipping $(($FilesToZip).Count) files into: $ZipFile" -ForegroundColor Yellow

# Create zip archive
$TempDir = Join-Path $env:TEMP "wildlife_pkg_temp"
if (Test-Path $TempDir) { Remove-Item $TempDir -Recurse -Force }
New-Item -ItemType Directory -Path $TempDir | Out-Null

foreach ($file in $FilesToZip) {
    $relative = $file.FullName.Substring($ProjectDir.Length).TrimStart("\/")
    $targetPath = Join-Path $TempDir $relative
    $targetFolder = Split-Path $targetPath -Parent
    if (-not (Test-Path $targetFolder)) {
        New-Item -ItemType Directory -Path $targetFolder -Force | Out-Null
    }
    Copy-Item $file.FullName -Destination $targetPath -Force
}

Compress-Archive -Path "$TempDir\*" -DestinationPath $ZipFile -Force
Remove-Item $TempDir -Recurse -Force

$ZipSizeMB = [math]::Round((Get-Item $ZipFile).Length / 1MB, 2)
Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "  PACKAGE READY TO SHARE!" -ForegroundColor Green
Write-Host "  Location: $ZipFile" -ForegroundColor Cyan
Write-Host "  Size    : $ZipSizeMB MB" -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "Your teammate simply needs to:" -ForegroundColor Yellow
Write-Host "  1. Unzip the file" -ForegroundColor White
Write-Host "  2. In 'frontend', run: npm install" -ForegroundColor White
Write-Host "  3. Double-click 'run_platform.bat'" -ForegroundColor White

