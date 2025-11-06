# Quick launcher for Tibber Graph UI Test

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Tibber Graph UI Test Launcher" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Get the directory where this script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Check if app.py exists in the script directory
$AppPath = Join-Path $ScriptDir "app.py"
if (-not (Test-Path $AppPath)) {
    Write-Host "Error: app.py not found at $AppPath" -ForegroundColor Red
    exit 1
}

# Check if requirements are installed
$RequirementsPath = Join-Path $ScriptDir "requirements.txt"
Write-Host "Checking dependencies..." -ForegroundColor Yellow
try {
    python -c "import flask; import dateutil" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Dependencies not found"
    }
    Write-Host "✓ Dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -r $RequirementsPath
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Starting server..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Navigate to: " -NoNewline
Write-Host "http://localhost:5000" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""

# Start the Flask app from the script directory
python $AppPath
