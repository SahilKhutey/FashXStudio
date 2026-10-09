# Database backup script for Phase 4
param (
    [string]$User = "fashion",
    [string]$Db = "fashion"
)

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$backupDir = Join-Path $PSScriptRoot "..\..\backups"
if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir | Out-Null
}

$dumpFile = Join-Path $backupDir "fashx-$timestamp.dump"
Write-Host "Creating database backup to $dumpFile..."

docker compose exec postgres pg_dump -Fc -U $User $Db > $dumpFile

if ($LASTEXITCODE -eq 0) {
    Write-Host "Backup completed successfully: $dumpFile"
} else {
    Write-Warning "Backup encountered an error. Ensure postgres service is running."
}
