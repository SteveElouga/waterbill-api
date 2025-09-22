#!/usr/bin/env bash
set -e

# Variables de couleur
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 WaterBill API - Qualité du Code${NC}"

# Fonction pour vérifier si une commande existe
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}❌ Erreur: '$1' n'est pas installé. Veuillez l'installer avec: pip install $2${NC}"
        exit 1
    fi
}

# Vérifier les outils de qualité essentiels
check_command "black" "black"
check_command "ruff" "ruff"
check_command "bandit" "bandit"

# Vérifier les outils optionnels
if ! command -v safety &> /dev/null && ! command -v pip-audit &> /dev/null; then
    echo -e "${YELLOW}⚠️  Aucun outil de vérification des dépendances disponible.${NC}"
    echo -e "${YELLOW}   Installation recommandée: pip install safety ou pip install pip-audit${NC}"
fi


case "$1" in
    format)
        echo -e "${GREEN}🎨 Formatage du code avec Black...${NC}"
        black . --line-length=88
        echo -e "${GREEN}✅ Formatage terminé.${NC}"
        ;;
    lint)
        echo -e "${GREEN}🔍 Analyse du code avec Ruff...${NC}"
        ruff check . --fix
        echo -e "${GREEN}✅ Analyse terminée.${NC}"
        ;;
    security)
        echo -e "${GREEN}🔒 Analyse de sécurité avec Bandit...${NC}"
        # Configuration optimisée via .bandit
        bandit -r . \
            -f json \
            -o bandit-report.json \
            --configfile .bandit
        echo -e "${GREEN}✅ Rapport de sécurité généré dans bandit-report.json${NC}"
        ;;
    security-quick)
        echo -e "${GREEN}⚡ Analyse de sécurité rapide avec Bandit...${NC}"
        # Version rapide sans génération de rapport JSON
        bandit -r . \
            --configfile .bandit
        echo -e "${GREEN}✅ Analyse de sécurité rapide terminée${NC}"
        ;;
    deps)
        echo -e "${GREEN}📦 Vérification des dépendances avec Safety...${NC}"
        if safety check --json --output safety-report.json 2>/dev/null; then
            echo -e "${GREEN}✅ Rapport de sécurité des dépendances généré dans safety-report.json${NC}"
        else
            echo -e "${YELLOW}⚠️  Safety a rencontré une erreur. Tentative avec pip-audit...${NC}"
            if command -v pip-audit &> /dev/null; then
                pip-audit --format=json --output=safety-report.json
                echo -e "${GREEN}✅ Rapport de sécurité des dépendances généré avec pip-audit${NC}"
            else
                echo -e "${RED}❌ Safety et pip-audit non disponibles. Installation recommandée: pip install pip-audit${NC}"
            fi
        fi
        ;;
    precommit)
        echo -e "${GREEN}🪝 Exécution des hooks pre-commit...${NC}"
        pre-commit run --all-files
        echo -e "${GREEN}✅ Hooks pre-commit exécutés.${NC}"
        ;;
    install-hooks)
        echo -e "${GREEN}🪝 Installation des hooks pre-commit...${NC}"
        pre-commit install
        echo -e "${GREEN}✅ Hooks pre-commit installés.${NC}"
        ;;
    all)
        echo -e "${GREEN}🚀 Exécution de tous les contrôles de qualité...${NC}"
        echo -e "${YELLOW}1/4 - Formatage...${NC}"
        black . --line-length=88 --check
        echo -e "${YELLOW}2/4 - Linting...${NC}"
        ruff check .
        echo -e "${YELLOW}3/4 - Sécurité (Bandit)...${NC}"
        bandit -r . \
            -f json \
            -o bandit-report.json \
            --configfile .bandit
        echo -e "${YELLOW}4/4 - Dépendances (Safety)...${NC}"
        if safety check --json --output safety-report.json 2>/dev/null; then
            echo -e "${GREEN}✅ Tous les contrôles de qualité terminés.${NC}"
            echo -e "${BLUE}📊 Rapports générés:${NC}"
            echo -e "  - bandit-report.json (sécurité)"
            echo -e "  - safety-report.json (dépendances)"
        else
            echo -e "${YELLOW}⚠️  Safety a rencontré une erreur. Tentative avec pip-audit...${NC}"
            if command -v pip-audit &> /dev/null; then
                pip-audit --format=json --output=safety-report.json
                echo -e "${GREEN}✅ Tous les contrôles de qualité terminés.${NC}"
                echo -e "${BLUE}📊 Rapports générés:${NC}"
                echo -e "  - bandit-report.json (sécurité)"
                echo -e "  - safety-report.json (dépendances - pip-audit)"
            else
                echo -e "${GREEN}✅ Contrôles de qualité terminés (safety ignoré).${NC}"
                echo -e "${BLUE}📊 Rapports générés:${NC}"
                echo -e "  - bandit-report.json (sécurité)"
                echo -e "${YELLOW}⚠️  Safety non disponible - installation recommandée: pip install pip-audit${NC}"
            fi
        fi
        ;;
    fix)
        echo -e "${GREEN}🔧 Correction automatique du code...${NC}"
        echo -e "${YELLOW}1/2 - Formatage automatique...${NC}"
        black . --line-length=88
        echo -e "${YELLOW}2/2 - Corrections automatiques...${NC}"
        ruff check . --fix
        echo -e "${GREEN}✅ Corrections automatiques terminées.${NC}"
        ;;
    clean)
        echo -e "${GREEN}🧹 Nettoyage des fichiers de qualité...${NC}"
        rm -f bandit-report.json safety-report.json .mypy_cache/ 2>/dev/null || true
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find . -name "*.pyc" -delete 2>/dev/null || true
        echo -e "${GREEN}✅ Nettoyage terminé.${NC}"
        ;;
    *)
        echo -e "${YELLOW}Usage: ./scripts/quality.sh [format|lint|security|security-quick|deps|precommit|install-hooks|all|fix|clean]${NC}"
        echo -e "${BLUE}Commandes disponibles:${NC}"
        echo -e "  ${GREEN}format${NC}       - Formatage du code avec Black"
        echo -e "  ${GREEN}lint${NC}         - Analyse du code avec Ruff"
        echo -e "  ${GREEN}security${NC}     - Analyse de sécurité avec Bandit (complet)"
        echo -e "  ${GREEN}security-quick${NC} - Analyse de sécurité rapide avec Bandit"
        echo -e "  ${GREEN}deps${NC}         - Vérification des dépendances avec Safety"
        echo -e "  ${GREEN}precommit${NC}    - Exécution des hooks pre-commit"
        echo -e "  ${GREEN}install-hooks${NC} - Installation des hooks pre-commit"
        echo -e "  ${GREEN}all${NC}          - Tous les contrôles de qualité"
        echo -e "  ${GREEN}fix${NC}          - Corrections automatiques (format + lint)"
        echo -e "  ${GREEN}clean${NC}        - Nettoyage des fichiers de qualité"
        exit 1
        ;;
esac
