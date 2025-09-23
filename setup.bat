@echo off
REM Script d'installation batch pour projet Django REST Framework - Facturation d'eau
REM Compatible Windows 11 avec Python 3.12
REM ⚠️ Sous Git Bash/WSL, utiliser setup.sh au lieu de ce script

echo 🚀 Démarrage de l'installation du projet Django REST Framework...
echo 📋 Configuration: Windows 11, Python 3.12, pip

REM Vérifier la version de Python
echo 🔍 Vérification de la version Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python non trouvé! Veuillez installer Python 3.12
    pause
    exit /b 1
)
python --version

REM Vérifier si pip est installé
echo 🔍 Vérification de pip...
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip non trouvé!
    pause
    exit /b 1
)
pip --version

REM Étape 1: Créer l'environnement virtuel
echo 📦 Création de l'environnement virtuel 'venv'...
if exist "venv" (
    echo ⚠️  L'environnement virtuel existe déjà. Suppression...
    rmdir /s /q venv
)

python -m venv venv

REM Étape 2: Activer l'environnement virtuel
echo 🔄 Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

REM Vérifier que l'environnement virtuel est activé
echo ✅ Environnement virtuel activé

REM Étape 3: Mise à jour de pip
echo ⬆️  Mise à jour de pip...
python -m pip install --upgrade pip

REM Étape 4: Installation des dépendances Python
echo 📚 Installation des dépendances...

REM Vérifier que les fichiers requirements existent
if not exist "requirements.txt" (
    echo ❌ Erreur: requirements.txt non trouvé!
    pause
    exit /b 1
)

if not exist "requirements-dev.txt" (
    echo ❌ Erreur: requirements-dev.txt non trouvé!
    pause
    exit /b 1
)

echo   - Installation des dépendances de production...
pip install -r requirements.txt

echo   - Installation des dépendances de développement...
pip install -r requirements-dev.txt

REM Étape 5: Vérification finale
echo 🔍 Vérification finale des installations principales...
python -c "import django; print('  - Django:', django.get_version())" 2>nul || echo   - Django: ❌ Erreur
python -c "import rest_framework; print('  - DRF:', rest_framework.VERSION)" 2>nul || echo   - DRF: ❌ Erreur
python -c "import psycopg2; print('  - PostgreSQL (psycopg2): ✅ Installé')" 2>nul || echo   - PostgreSQL (psycopg2): ❌ Erreur

echo.
echo 🎉 Installation terminée!
echo.
echo 📝 Prochaines étapes:
echo   1. Activez l'environnement virtuel:
echo      venv\Scripts\activate.bat
echo.
echo   2. Créez votre projet Django:
echo      django-admin startproject waterbill .
echo.
echo   3. Configurez votre base de données PostgreSQL dans settings.py
echo.
echo   4. Lancez les migrations:
echo      python manage.py migrate
echo.
echo   5. Créez un superutilisateur:
echo      python manage.py createsuperuser
echo.
echo 🔧 Pour désactiver l'environnement virtuel: deactivate

pause
