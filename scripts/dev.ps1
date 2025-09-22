#!/usr/bin/env pwsh
# Script PowerShell pour le développement
# Évite les problèmes de fork avec Git Bash sur Windows

param(
    [string]$Command = "help"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$EnvFile = Join-Path $ProjectRoot ".env"

function Show-Help {
    Write-Host "=== Script de Développement - PowerShell ===" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\scripts\dev.ps1 [COMMAND]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Commandes disponibles:" -ForegroundColor Green
    Write-Host "  up          - Lancer les services de développement" -ForegroundColor White
    Write-Host "  down        - Arrêter les services de développement" -ForegroundColor White
    Write-Host "  status      - Vérifier le statut des services" -ForegroundColor White
    Write-Host "  logs        - Afficher les logs" -ForegroundColor White
    Write-Host "  shell       - Accéder au conteneur web" -ForegroundColor White
    Write-Host "  test        - Lancer les tests" -ForegroundColor White
    Write-Host "  migrate     - Appliquer les migrations" -ForegroundColor White
    Write-Host ""
    Write-Host "Exemples:" -ForegroundColor Yellow
    Write-Host "  .\scripts\dev.ps1 up" -ForegroundColor Gray
    Write-Host "  .\scripts\dev.ps1 logs" -ForegroundColor Gray
    Write-Host ""
}

function Backup-EnvFile {
    if (Test-Path $EnvFile) {
        $Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $BackupFile = "$EnvFile.backup.dev.$Timestamp"
        Copy-Item $EnvFile $BackupFile
        Write-Host "✅ Fichier .env sauvegardé : $BackupFile" -ForegroundColor Green
        return $BackupFile
    }
    return $null
}

function Force-DebugTrue {
    if (Test-Path $EnvFile) {
        $Content = Get-Content $EnvFile -Raw
        if ($Content -match "DEBUG=False") {
            Write-Host "⚠️  DEBUG=False détecté, passage automatique à DEBUG=True pour le développement" -ForegroundColor Yellow
            $Content = $Content -replace "DEBUG=False", "DEBUG=True"
            Set-Content $EnvFile $Content
            Write-Host "✅ DEBUG=True appliqué automatiquement" -ForegroundColor Green
            return $true
        }
    }
    return $false
}

function Start-Development {
    Write-Host "🐳 Lancement des services de développement..." -ForegroundColor Cyan
    
    # Sauvegarder .env si DEBUG=False
    Force-DebugTrue | Out-Null
    
    # Lancer en mode développement
    Set-Location $ProjectRoot
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
    
    Write-Host "✅ Services de développement lancés !" -ForegroundColor Green
    Write-Host "🌐 API disponible sur : http://localhost:8000" -ForegroundColor Blue
    Write-Host "📚 Documentation : http://localhost:8000/api/docs/" -ForegroundColor Blue
    Write-Host "📱 Codes SMS visibles dans les logs" -ForegroundColor Magenta
}

function Stop-Development {
    Write-Host "🛑 Arrêt des services de développement..." -ForegroundColor Yellow
    
    $Confirm = Read-Host "Êtes-vous sûr de vouloir arrêter les services de développement ? (y/N)"
    if ($Confirm -eq "y" -or $Confirm -eq "Y") {
        Set-Location $ProjectRoot
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
        Write-Host "✅ Services arrêtés" -ForegroundColor Green
    } else {
        Write-Host "❌ Opération annulée" -ForegroundColor Red
    }
}

function Show-Status {
    Write-Host "📊 Statut des services de développement..." -ForegroundColor Cyan
    Set-Location $ProjectRoot
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml ps
}

function Show-Logs {
    Write-Host "📋 Logs des services de développement..." -ForegroundColor Cyan
    Set-Location $ProjectRoot
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f
}

function Enter-Shell {
    Write-Host "🐚 Accès au conteneur web..." -ForegroundColor Cyan
    Set-Location $ProjectRoot
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec web bash
}

function Run-Tests {
    Write-Host "🧪 Lancement des tests..." -ForegroundColor Cyan
    Set-Location $ProjectRoot
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py test
}

function Run-Migrations {
    Write-Host "🔄 Application des migrations..." -ForegroundColor Cyan
    Set-Location $ProjectRoot
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py migrate
}

# Exécution des commandes
switch ($Command.ToLower()) {
    "up" { Start-Development }
    "down" { Stop-Development }
    "status" { Show-Status }
    "logs" { Show-Logs }
    "shell" { Enter-Shell }
    "test" { Run-Tests }
    "migrate" { Run-Migrations }
    "help" { Show-Help }
    default {
        Write-Host "❌ Commande inconnue : $Command" -ForegroundColor Red
        Show-Help
    }
}
