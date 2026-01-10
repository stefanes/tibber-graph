#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Copy Tibber Graph component to local Home Assistant instance and
    restart.

.DESCRIPTION
    Copies all files from custom_components\tibber_graph to the destination,
    preserving the directory structure and excluding __pycache__ folders.

    After copying the files, restarts Home Assistant using an API call.

.PARAMETER i
    Instance to deploy to. Required information is read from local_deploy.<i>.json.

.PARAMETER y
    Skip restart confirmation prompt and automatically restart Home Assistant.

.PARAMETER z
    Deploy from tibber_graph.zip instead of the source directory.
    The zip file should be located in local/local_deploy/tibber_graph.zip.

.EXAMPLE
    .\local_deploy.ps1

.EXAMPLE
    .\local_deploy.ps1 -y

.EXAMPLE
    .\local_deploy.ps1 -z -y

.EXAMPLE
    .\local_deploy.ps1 -i live
#>

param(
    [string]$i,
    [switch]$y,
    [switch]$z
)

$ErrorActionPreference = "Stop"

$instance = if ($i) { ".$i" } else { "" }
$configPath = Join-Path $PSScriptRoot "local_deploy$instance.json"
if (Test-Path $configPath) {
    try {
        $config = Get-Content $configPath -Raw | ConvertFrom-Json
        $destination = $config.destination
        $destination = Join-Path $config.destination "custom_components\tibber_graph" -Resolve
        $HomeAssistantUrl = $config.host
        $AccessToken = $config.token
        Write-Host "Loaded configuration from local_deploy$instance.json" -ForegroundColor Gray
    } catch {
        Write-Error "Failed to read local_deploy.json: $_"
        exit 1
    }
} else {
    Write-Error "local_deploy$instance.json not found. Create local_deploy$instance.json with: { `"destination`": `"your-path-here`", `"host`": `"http://your-ha-url:8123`", `"token`": `"your-long-lived-token`" }"
    exit 1
}

# Get the source directory
if ($z) {
    # Deploy from zip file
    $zipPath = Join-Path $PSScriptRoot "tibber_graph.zip" -Resolve

    if (-not (Test-Path $zipPath)) {
        Write-Error "Zip file not found: $zipPath"
        exit 1
    }

    # Create temporary directory for extraction
    $tempDir = Join-Path $env:TEMP "tibber_graph_deploy_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

    Write-Host "Extracting tibber_graph.zip to temporary location..." -ForegroundColor Cyan
    Write-Host "  Zip: $zipPath" -ForegroundColor Gray
    Write-Host "  Temp: $tempDir" -ForegroundColor Gray

    try {
        Expand-Archive -Path $zipPath -DestinationPath $tempDir -Force

        # The zip structure should be: version_folder/manifest.json, __init__.py, etc.
        # Find the directory containing manifest.json
        $manifestPath = Get-ChildItem -Path $tempDir -Filter "manifest.json" -Recurse -File | Select-Object -First 1
        if ($manifestPath) {
            $Source = $manifestPath.Directory.FullName
            Write-Host "✓ Extraction complete" -ForegroundColor Green
        } else {
            Write-Error "Could not find manifest.json in extracted zip"
            Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
            exit 1
        }
        Write-Host ""
    } catch {
        Write-Error "Failed to extract zip file: $_"
        Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
        exit 1
    }
} else {
    # Deploy from source directory
    $Source = Join-Path $PSScriptRoot "..\..\custom_components\tibber_graph" -Resolve
}

# Verify source exists
if (-not (Test-Path $Source)) {
    Write-Error "Source directory not found: $Source"
    exit 1
}

Write-Host "Deploying Tibber Graph integration..." -ForegroundColor Cyan
Write-Host "Source:      $Source" -ForegroundColor Gray
Write-Host "Destination: $destination" -ForegroundColor Gray
Write-Host ""

# Create destination if it doesn't exist
if (-not (Test-Path $destination)) {
    Write-Host "Creating destination directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $destination -Force | Out-Null
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
    $destPath = Join-Path $destination $relativePath
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

# Copy tibber_graph.yaml into the Home Assistant `packages` folder
$localYamlSource = Join-Path $PSScriptRoot "..\..\tibber_graph.yaml" -Resolve
$packagesRoot = Split-Path (Split-Path $destination -Parent) -Parent
$packagesDir = Join-Path $packagesRoot "packages"

if (Test-Path $localYamlSource) {
    if (-not (Test-Path $packagesDir)) {
        New-Item -ItemType Directory -Path $packagesDir -Force | Out-Null
    }

    $destYaml = Join-Path $packagesDir "tibber_graph_repo.yaml"
    try {
        Copy-Item -Path $localYamlSource -Destination $destYaml -Force
        Write-Host "  ✓ " -ForegroundColor Green -NoNewline; Write-Host "\packages\tibber_graph_repo.yaml" -BackgroundColor Green
        $copied++
    } catch {
        Write-Warning "Failed to copy tibber_graph.yaml to packages: $_"
    }
} else {
    Write-Warning "Local tibber_graph.yaml not found at: $localYamlSource. Skipping copying to packages."
}

Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host "Files copied: $copied" -ForegroundColor Gray
Write-Host "Files skipped: $skipped" -ForegroundColor Gray

# Update manifest.json version at destination to 'lHHmm'
$destManifestPath = Join-Path $destination "manifest.json"
if (-Not $z.IsPresent -And (Test-Path $destManifestPath)) {
    try {
        $manifest = Get-Content $destManifestPath -Raw | ConvertFrom-Json
        $originalVersion = $manifest.version
        # Extract major.minor from original version and append HHMM
        if ($originalVersion -match '^(\d+\.\d+)') {
            $timestamp = Get-Date -Format "HHmm"
            $newVersion = "$originalVersion+$timestamp"
            $manifest.version = $newVersion
            $manifest | ConvertTo-Json -Depth 10 | Set-Content $destManifestPath
            Write-Host ""
            Write-Host "Updated destination manifest version: $originalVersion → $newVersion" -ForegroundColor Yellow
        }
    } catch {
        Write-Warning "Failed to update destination manifest version: $_"
    }
}

Write-Host ""

# Restart Home Assistant if URL and token are provided
if ($HomeAssistantUrl -and $AccessToken) {
    # Skip confirmation if -y switch is provided
    if ($y) {
        $confirmation = 'y'
        Write-Host "Restarting Home Assistant (auto-confirmed with -y)..." -ForegroundColor Yellow
        Write-Host "  Host: $HomeAssistantUrl" -ForegroundColor Gray
    } else {
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
                "Content-Type"  = "application/json"
            }

            Invoke-RestMethod -Uri $restartUrl -Method Post -Headers $headers -Body "{}" -TimeoutSec 10 | Out-Null

            Write-Host "✓ Restart request sent successfully!" -ForegroundColor Green
            Write-Host "Home Assistant is restarting..." -ForegroundColor Gray
        } catch {
            Write-Host "✗ Failed to restart Home Assistant" -ForegroundColor Red
            Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red

            if ($_.Exception.Response) {
                $statusCode = [int]$_.Exception.Response.StatusCode
                Write-Host "Status Code: $statusCode" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "Restart cancelled." -ForegroundColor Gray
        Write-Host "Remember to manually restart Home Assistant to load the changes." -ForegroundColor Yellow
    }
} else {
    Write-Host "Remember to restart Home Assistant to load the changes." -ForegroundColor Yellow
    Write-Host "Tip: Add 'host' and 'token' to local_deploy.json for automatic restart." -ForegroundColor Gray
}

# Clean up temporary directory if created
if ($z -and $tempDir -and (Test-Path $tempDir)) {
    Write-Host ""
    Write-Host "Cleaning up temporary files..." -ForegroundColor Gray
    Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
}
