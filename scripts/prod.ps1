#!/usr/bin/env pwsh
# Script PowerShell pour la production
# Évite les problèmes de fork avec Git Bash sur Windows

param(
    [string]$Command = "help"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$EnvFile = Join-Path $ProjectRoot ".env"

function Show-Help {
    Write-Host "=== Script de Production - PowerShell ===" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\scripts\prod.ps1 [COMMAND]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Commandes disponibles:" -ForegroundColor Green
    Write-Host "  up          - Lancer les services de production" -ForegroundColor White
    Write-Host "  down        - Arrêter les services de production" -ForegroundColor White
    Write-Host "  status      - Vérifier le statut des services" -ForegroundColor White
    Write-Host "  logs        - Afficher les logs" -ForegroundColor White
    Write-Host "  build       - Construire les images" -ForegroundColor White
    Write-Host "  backup      - Sauvegarder la base de données" -ForegroundColor White
    Write-Host "  restore-env - Restaurer le fichier .env original" -ForegroundColor White
    Write-Host ""
    Write-Host "Exemples:" -ForegroundColor Yellow
    Write-Host "  .\scripts\prod.ps1 up" -ForegroundColor Gray
    Write-Host "  .\scripts\prod.ps1 status" -ForegroundColor Gray
    Write-Host ""
}

function Backup-EnvFile {
    if (Test-Path $EnvFile) {
        $Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $BackupFile = "$EnvFile.backup.$Timestamp"
        Copy-Item $EnvFile $BackupFile
        Write-Host "✅ Fichier .env sauvegardé : $BackupFile" -ForegroundColor Green
        return $BackupFile
    }
    return $null
}

function Force-DebugFalse {
    if (Test-Path $EnvFile) {
        $Content = Get-Content $EnvFile -Raw
        if ($Content -match "DEBUG=True") {
            Write-Host "⚠️  DEBUG=True détecté, passage automatique à DEBUG=False pour la production" -ForegroundColor Yellow
            $Content = $Content -replace "DEBUG=True", "DEBUG=False"
            Set-Content $EnvFile $Content
            Write-Host "✅ DEBUG=False appliqué automatiquement" -ForegroundColor Green
            return $true
        }
    }
    return $false
}

function Start-Production {
    Write-Host "🏭 Lancement des services de production..." -ForegroundColor Cyan
    
    # Sauvegarder .env si DEBUG=True
    Force-DebugFalse | Out-Null
    
    # Construire et lancer
    Set-Location $ProjectRoot
    docker-compose -f docker-compose.yml build --no-cache
    docker-compose -f docker-compose.yml up -d
    
    Write-Host "✅ Services de production lancés !" -ForegroundColor Green
    Write-Host "🌐 API disponible sur : http://localhost:8000" -ForegroundColor Blue
    Write-Host "📚 Documentation : http://localhost:8000/api/docs/" -ForegroundColor Blue
}

function Stop-Production {
    Write-Host "🛑 Arrêt des services de production..." -ForegroundColor Yellow
    
    $Confirm = Read-Host "Êtes-vous sûr de vouloir arrêter les services de production ? (y/N)"
    if ($Confirm -eq "y" -or $Confirm -eq "Y") {
        Set-Location $ProjectRoot
        docker-compose -f docker-compose.yml down
        Write-Host "✅ Services arrêtés" -ForegroundColor Green
        
        $Restore = Read-Host "Restaurer le fichier .env original (avec DEBUG=True) ? (y/N)"
        if ($Restore -eq "y" -or $Restore -eq "Y") {
            Restore-EnvFile
        }
    } else {
        Write-Host "❌ Opération annulée" -ForegroundColor Red
    }
}

function Show-Status {
    Write-Host "📊 Statut des services de production..." -ForegroundColor Cyan
    Set-Location $ProjectRoot
    docker-compose -f docker-compose.yml ps
}

function Show-Logs {
    Write-Host "📋 Logs des services de production..." -ForegroundColor Cyan
    Set-Location $ProjectRoot
    docker-compose -f docker-compose.yml logs -f
}

function Build-Images {
    Write-Host "🔨 Construction des images de production..." -ForegroundColor Cyan
    Set-Location $ProjectRoot
    docker-compose -f docker-compose.yml build --no-cache
    Write-Host "✅ Images construites !" -ForegroundColor Green
}

function Backup-Database {
    Write-Host "💾 Sauvegarde de la base de données..." -ForegroundColor Cyan
    Set-Location $ProjectRoot
    
    $Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $BackupFile = "backup_prod_$Timestamp.sql"
    
    docker-compose -f docker-compose.yml exec -T db pg_dump -U postgres waterbill > $BackupFile
    
    if (Test-Path $BackupFile) {
        Write-Host "✅ Base de données sauvegardée : $BackupFile" -ForegroundColor Green
    } else {
        Write-Host "❌ Erreur lors de la sauvegarde" -ForegroundColor Red
    }
}

function Restore-EnvFile {
    Write-Host "🔄 Restauration du fichier .env original..." -ForegroundColor Cyan
    
    $BackupFiles = Get-ChildItem -Path $ProjectRoot -Name ".env.backup.*" | Sort-Object LastWriteTime -Descending
    
    if ($BackupFiles.Count -gt 0) {
        $LatestBackup = $BackupFiles[0]
        $BackupPath = Join-Path $ProjectRoot $LatestBackup
        
        Copy-Item $BackupPath $EnvFile -Force
        Write-Host "✅ Fichier .env restauré depuis : $LatestBackup" -ForegroundColor Green
        Write-Host "💡 Vous pouvez maintenant lancer le mode développement" -ForegroundColor Blue
    } else {
        Write-Host "❌ Aucun fichier de sauvegarde trouvé" -ForegroundColor Red
        Write-Host "💡 Créez manuellement un fichier .env avec DEBUG=True" -ForegroundColor Yellow
    }
}

# Exécution des commandes
switch ($Command.ToLower()) {
    "up" { Start-Production }
    "down" { Stop-Production }
    "status" { Show-Status }
    "logs" { Show-Logs }
    "build" { Build-Images }
    "backup" { Backup-Database }
    "restore-env" { Restore-EnvFile }
    "help" { Show-Help }
    default {
        Write-Host "❌ Commande inconnue : $Command" -ForegroundColor Red
        Show-Help
    }
}
