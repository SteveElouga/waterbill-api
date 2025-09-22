#!/bin/bash

# Script d'installation pour projet Django REST Framework - Facturation d'eau
# Compatible Windows 11 (Git Bash / WSL) et Linux
# ⚠️ Sous PowerShell, utiliser .ps1 au lieu de ce script

set -e  # Arrêter en cas d'erreur

echo "🚀 Démarrage de l'installation du projet Django REST Framework..."
echo "📋 Configuration: Windows 11, Python 3.12, pip"

# Vérifier la version de Python
echo "🔍 Vérification de la version Python..."
python --version

# Vérifier si pip est installé
echo "🔍 Vérification de pip..."
pip --version

# Étape 1: Créer l'environnement virtuel
echo "📦 Création de l'environnement virtuel 'venv'..."
if [ -d "venv" ]; then
    echo "⚠️  L'environnement virtuel existe déjà. Suppression..."
    rm -rf venv
fi

python -m venv venv

# Étape 2: Activer l'environnement virtuel
echo "🔄 Activation de l'environnement virtuel..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    # Windows (Git Bash, WSL, etc.)
    source venv/Scripts/activate
else
    # Linux/Mac
    source venv/bin/activate
fi

# Vérifier que l'environnement virtuel est activé
echo "✅ Environnement virtuel activé: $(which python)"

# Étape 3: Mise à jour de pip
echo "⬆️  Mise à jour de pip..."
python -m pip install --upgrade pip

# Étape 4: Installation des dépendances Python
echo "📚 Installation des dépendances..."

# Vérifier que les fichiers requirements existent
if [ ! -f "requirements.txt" ]; then
    echo "❌ Erreur: requirements.txt non trouvé!"
    exit 1
fi

if [ ! -f "requirements-dev.txt" ]; then
    echo "❌ Erreur: requirements-dev.txt non trouvé!"
    exit 1
fi

# Installer les dépendances de production
echo "  - Installation des dépendances de production..."
pip install -r requirements.txt

# Installer les dépendances de développement
echo "  - Installation des dépendances de développement..."
pip install -r requirements-dev.txt

# Étape 5: Vérification finale
echo "🔍 Vérification finale des installations principales..."
echo "  - Django: $(python -c 'import django; print(django.get_version())')"
echo "  - DRF: $(python -c 'import rest_framework; print(rest_framework.VERSION)')"
echo "  - PostgreSQL (psycopg): $(python -c 'import psycopg; print(\"✅ Installé\")')"
echo "  - Outils de développement:"
echo "    - Black: $(python -c 'import black; print(black.__version__)' 2>/dev/null || echo '❌ Non installé')"
echo "    - Ruff: $(python -c 'import ruff; print(ruff.__version__)' 2>/dev/null || echo '❌ Non installé')"
echo "    - MyPy: $(python -c 'import mypy; print(mypy.__version__)' 2>/dev/null || echo '❌ Non installé')"
echo "    - Pytest: $(python -c 'import pytest; print(pytest.__version__)' 2>/dev/null || echo '❌ Non installé')"

echo ""
echo "🎉 Installation terminée!"
echo ""
echo "📝 Prochaines étapes:"
echo "  1. Activez l'environnement virtuel:"
echo "     - Git Bash/WSL: source venv/Scripts/activate"
echo "     - Linux/Mac: source venv/bin/activate"
echo ""
echo "  2. Créez votre projet Django:"
echo "     django-admin startproject waterbill ."
echo ""
echo "  3. Configurez votre base de données PostgreSQL dans settings.py"
echo ""
echo "  4. Lancez les migrations:"
echo "     python manage.py migrate"
echo ""
echo "  5. Créez un superutilisateur:"
echo "     python manage.py createsuperuser"
echo ""
echo "🔧 Pour désactiver l'environnement virtuel: deactivate"
