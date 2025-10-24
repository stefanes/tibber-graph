#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Copy Tibber Graph component to local Home Assistant instance.

.DESCRIPTION
    Copies all files from custom_components\tibber_graph to the destination,
    preserving the directory structure and excluding __pycache__ folders.

    If no destination is provided, reads from local_copy.json in the same directory.

.PARAMETER Destination
    The destination path where files should be copied.
    If not provided, reads from local_copy.json

.EXAMPLE
    .\local_copy.ps1

.EXAMPLE
    .\local_copy.ps1 -Destination "C:\some\other\path"
#>

param(
    [string]$Destination
)

$ErrorActionPreference = "Stop"

# If no destination provided, try to read from config file
if (-not $Destination) {
    $configPath = Join-Path $PSScriptRoot "local_copy.json"
    if (Test-Path $configPath) {
        try {
            $config = Get-Content $configPath -Raw | ConvertFrom-Json
            $Destination = $config.destination
            Write-Host "Loaded destination from local_copy.json" -ForegroundColor Gray
        }
        catch {
            Write-Error "Failed to read local_copy.json: $_"
            exit 1
        }
    }
    else {
        Write-Error "No destination provided and local_copy.json not found. Create local_copy.json with: { `"destination`": `"your-path-here`" }"
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
Write-Host "Remember to restart Home Assistant to load the changes." -ForegroundColor Yellow
