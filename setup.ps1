# Script d'installation PowerShell pour projet Django REST Framework - Facturation d'eau
# Compatible Windows 11 avec Python 3.12
# ⚠️ Sous Git Bash/WSL, utiliser setup.sh au lieu de ce script

param(
    [switch]$Force
)

# Configuration des couleurs et messages
$ErrorActionPreference = "Stop"

Write-Host "🚀 Démarrage de l'installation du projet Django REST Framework..." -ForegroundColor Green
Write-Host "📋 Configuration: Windows 11, Python 3.12, pip" -ForegroundColor Cyan

# Vérifier la version de Python
Write-Host "🔍 Vérification de la version Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python non trouvé! Veuillez installer Python 3.12" -ForegroundColor Red
    exit 1
}

# Vérifier si pip est installé
Write-Host "🔍 Vérification de pip..." -ForegroundColor Yellow
try {
    $pipVersion = pip --version 2>&1
    Write-Host "✅ $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ pip non trouvé!" -ForegroundColor Red
    exit 1
}

# Étape 1: Créer l'environnement virtuel
Write-Host "📦 Création de l'environnement virtuel 'venv'..." -ForegroundColor Yellow
if (Test-Path "venv") {
    if ($Force) {
        Write-Host "⚠️  Suppression de l'environnement virtuel existant..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force "venv"
    } else {
        Write-Host "⚠️  L'environnement virtuel existe déjà. Utilisez -Force pour le recréer." -ForegroundColor Yellow
        $response = Read-Host "Continuer avec l'environnement existant? (y/N)"
        if ($response -ne "y" -and $response -ne "Y") {
            exit 0
        }
    }
}

python -m venv venv

# Étape 2: Activer l'environnement virtuel
Write-Host "🔄 Activation de l'environnement virtuel..." -ForegroundColor Yellow
$activateScript = ".\venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "✅ Environnement virtuel activé" -ForegroundColor Green
} else {
    Write-Host "❌ Impossible d'activer l'environnement virtuel" -ForegroundColor Red
    exit 1
}

# Étape 3: Mise à jour de pip
Write-Host "⬆️  Mise à jour de pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Étape 4: Installation des dépendances Python
Write-Host "📚 Installation des dépendances..." -ForegroundColor Yellow

# Vérifier que les fichiers requirements existent
if (-not (Test-Path "requirements.txt")) {
    Write-Host "❌ Erreur: requirements.txt non trouvé!" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "requirements-dev.txt")) {
    Write-Host "❌ Erreur: requirements-dev.txt non trouvé!" -ForegroundColor Red
    exit 1
}

# Installer les dépendances de production
Write-Host "  - Installation des dépendances de production..." -ForegroundColor White
pip install -r requirements.txt

# Installer les dépendances de développement
Write-Host "  - Installation des dépendances de développement..." -ForegroundColor White
pip install -r requirements-dev.txt

# Étape 5: Vérification finale
Write-Host "🔍 Vérification finale des installations principales..." -ForegroundColor Yellow
try {
    $djangoVersion = python -c "import django; print(django.get_version())" 2>&1
    Write-Host "  - Django: $djangoVersion" -ForegroundColor Green
} catch {
    Write-Host "  - Django: ❌ Erreur" -ForegroundColor Red
}

try {
    $drfVersion = python -c "import rest_framework; print(rest_framework.VERSION)" 2>&1
    Write-Host "  - DRF: $drfVersion" -ForegroundColor Green
} catch {
    Write-Host "  - DRF: ❌ Erreur" -ForegroundColor Red
}

try {
    python -c "import psycopg2; print('✅ Installé')" 2>&1 | Out-Null
    Write-Host "  - PostgreSQL (psycopg2): ✅ Installé" -ForegroundColor Green
} catch {
    Write-Host "  - PostgreSQL (psycopg2): ❌ Erreur" -ForegroundColor Red
}

Write-Host ""
Write-Host "🎉 Installation terminée!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Prochaines étapes:" -ForegroundColor Cyan
Write-Host "  1. Activez l'environnement virtuel:" -ForegroundColor White
Write-Host "     .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""
Write-Host "  2. Créez votre projet Django:" -ForegroundColor White
Write-Host "     django-admin startproject waterbill ." -ForegroundColor White
Write-Host ""
Write-Host "  3. Configurez votre base de données PostgreSQL dans settings.py" -ForegroundColor White
Write-Host ""
Write-Host "  4. Lancez les migrations:" -ForegroundColor White
Write-Host "     python manage.py migrate" -ForegroundColor White
Write-Host ""
Write-Host "  5. Créez un superutilisateur:" -ForegroundColor White
Write-Host "     python manage.py createsuperuser" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Pour désactiver l'environnement virtuel: deactivate" -ForegroundColor Cyan
