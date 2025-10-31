#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Copy Tibber Graph component to local Home Assistant instance and
    restart.

.DESCRIPTION
    Copies all files from custom_components\tibber_graph to the destination,
    preserving the directory structure and excluding __pycache__ folders.

    If no destination is provided, reads from local_deploy.json in the same directory.

    After copying the files, restarts Home Assistant using an API call.

.PARAMETER Destination
    None. Required information is read from local_deploy.json.

.PARAMETER y
    Skip restart confirmation prompt and automatically restart Home Assistant.

.EXAMPLE
    .\local_deploy.ps1

.EXAMPLE
    .\local_deploy.ps1 -y
#>

param(
    [switch]$y
)

$ErrorActionPreference = "Stop"

# If no destination provided, try to read from config file
if (-not $Destination) {
    $configPath = Join-Path $PSScriptRoot "local_deploy.json"
    if (Test-Path $configPath) {
        try {
            $config = Get-Content $configPath -Raw | ConvertFrom-Json
            $Destination = $config.destination
            $HomeAssistantUrl = $config.host
            $AccessToken = $config.token
            Write-Host "Loaded configuration from local_deploy.json" -ForegroundColor Gray
        }
        catch {
            Write-Error "Failed to read local_deploy.json: $_"
            exit 1
        }
    }
    else {
        Write-Error "No destination provided and local_deploy.json not found. Create local_deploy.json with: { `"destination`": `"your-path-here`", `"host`": `"http://your-ha-url:8123`", `"token`": `"your-long-lived-token`" }"
        exit 1
    }
}

# Get the source directory
$Source = Join-Path $PSScriptRoot "..\custom_components\tibber_graph" -Resolve

# Verify source exists
if (-not (Test-Path $Source)) {
    Write-Error "Source directory not found: $Source"
    exit 1
}

Write-Host "Deploying Tibber Graph integration..." -ForegroundColor Cyan
Write-Host "Source:      $Source" -ForegroundColor Gray
Write-Host "Destination: $Destination" -ForegroundColor Gray
Write-Host ""

# Create destination if it doesn't exist
if (-not (Test-Path $Destination)) {
    Write-Host "Creating destination directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
}

# Copy files, excluding __pycache__
Write-Host "Copying files..." -ForegroundColor Cyan
$copied = 0
$skipped = 0

Get-ChildItem -Path $Source -Recurse -File | ForEach-Object {
    # Skip __pycache__ directories
    if ($_.FullName -match '\\__pycache__\\') {
        $skipped++
        return
    }

    # Calculate relative path and destination path
    $relativePath = $_.FullName.Substring($Source.Length + 1)
    $destPath = Join-Path $Destination $relativePath
    $destDir = Split-Path $destPath -Parent

    # Create destination directory if needed
    if (-not (Test-Path $destDir)) {
        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
    }

    # Copy file
    Copy-Item -Path $_.FullName -Destination $destPath -Force
    Write-Host "  ✓ $relativePath" -ForegroundColor Green
    $copied++
}

Write-Host ""
Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host "Files copied: $copied" -ForegroundColor Gray
Write-Host "Files skipped: $skipped" -ForegroundColor Gray
Write-Host ""

# Restart Home Assistant if URL and token are provided
if ($HomeAssistantUrl -and $AccessToken) {
    # Skip confirmation if -y switch is provided
    if ($y) {
        $confirmation = 'y'
        Write-Host "Restarting Home Assistant (auto-confirmed with -y)..." -ForegroundColor Yellow
        Write-Host "  Host: $HomeAssistantUrl" -ForegroundColor Gray
    }
    else {
        Write-Host "Restart Home Assistant?" -ForegroundColor Yellow
        Write-Host "  Host: $HomeAssistantUrl" -ForegroundColor Gray
        $confirmation = Read-Host "Proceed with restart? (y/N)"
    }

    if ($confirmation -eq 'y' -or $confirmation -eq 'Y') {
        Write-Host ""
        Write-Host "Restarting Home Assistant..." -ForegroundColor Cyan

        try {
            $restartUrl = "$HomeAssistantUrl/api/services/homeassistant/restart"
            $headers = @{
                "Authorization" = "Bearer $AccessToken"
                "Content-Type" = "application/json"
            }

            $response = Invoke-RestMethod -Uri $restartUrl -Method Post -Headers $headers -Body "{}" -TimeoutSec 10

            Write-Host "✓ Restart request sent successfully!" -ForegroundColor Green
            Write-Host "Home Assistant is restarting..." -ForegroundColor Gray
        }
        catch {
            Write-Host "✗ Failed to restart Home Assistant" -ForegroundColor Red
            Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red

            if ($_.Exception.Response) {
                $statusCode = [int]$_.Exception.Response.StatusCode
                Write-Host "Status Code: $statusCode" -ForegroundColor Red
            }
        }
    }
    else {
        Write-Host "Restart cancelled." -ForegroundColor Gray
        Write-Host "Remember to manually restart Home Assistant to load the changes." -ForegroundColor Yellow
    }
}
else {
    Write-Host "Remember to restart Home Assistant to load the changes." -ForegroundColor Yellow
    Write-Host "Tip: Add 'host' and 'token' to local_deploy.json for automatic restart." -ForegroundColor Gray
}
