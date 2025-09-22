#!/usr/bin/env bash
set -e

# Variables de couleur
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧹 WaterBill API - Nettoyage${NC}"

case "$1" in
    logs)
        echo -e "${GREEN}📋 Nettoyage des logs...${NC}"
        rm -rf logs/ 2>/dev/null || true
        echo -e "${GREEN}✅ Logs supprimés.${NC}"
        ;;
    cache)
        echo -e "${GREEN}🗑️  Nettoyage du cache Python...${NC}"
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find . -name "*.pyc" -delete 2>/dev/null || true
        find . -name "*.pyo" -delete 2>/dev/null || true
        echo -e "${GREEN}✅ Cache Python supprimé.${NC}"
        ;;
    docker)
        echo -e "${GREEN}🐳 Nettoyage Docker...${NC}"
        # Arrêter les conteneurs
        docker-compose -f docker-compose.yml down 2>/dev/null || true
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml down 2>/dev/null || true

        # Supprimer les images
        docker-compose -f docker-compose.yml down --rmi all 2>/dev/null || true
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml down --rmi all 2>/dev/null || true

        # Nettoyer les volumes
        docker-compose -f docker-compose.yml down -v 2>/dev/null || true
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml down -v 2>/dev/null || true

        echo -e "${GREEN}✅ Docker nettoyé.${NC}"
        ;;
    test)
        echo -e "${GREEN}🧪 Nettoyage des fichiers de test...${NC}"
        rm -rf htmlcov/ .coverage .pytest_cache/ 2>/dev/null || true
        rm -f bandit-report.json safety-report.json 2>/dev/null || true
        echo -e "${GREEN}✅ Fichiers de test supprimés.${NC}"
        ;;
    all)
        echo -e "${GREEN}🚀 Nettoyage complet...${NC}"
        echo -e "${YELLOW}1/4 - Logs...${NC}"
        rm -rf logs/ 2>/dev/null || true

        echo -e "${YELLOW}2/4 - Cache Python...${NC}"
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find . -name "*.pyc" -delete 2>/dev/null || true
        find . -name "*.pyo" -delete 2>/dev/null || true

        echo -e "${YELLOW}3/4 - Fichiers de test...${NC}"
        rm -rf htmlcov/ .coverage .pytest_cache/ 2>/dev/null || true
        rm -f bandit-report.json safety-report.json 2>/dev/null || true

        echo -e "${YELLOW}4/4 - Docker (attention, cela supprime tout)...${NC}"
        read -p "Voulez-vous vraiment supprimer les conteneurs et images Docker ? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose -f docker-compose.yml down --rmi all -v 2>/dev/null || true
            docker-compose -f docker-compose.yml -f docker-compose.dev.yml down --rmi all -v 2>/dev/null || true
            echo -e "${GREEN}✅ Docker nettoyé.${NC}"
        else
            echo -e "${YELLOW}Docker non nettoyé.${NC}"
        fi

        echo -e "${GREEN}✅ Nettoyage complet terminé.${NC}"
        ;;
    prebuild)
        echo -e "${GREEN}🔨 Nettoyage avant build...${NC}"
        # Nettoyage minimal pour les builds
        rm -rf logs/ 2>/dev/null || true
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find . -name "*.pyc" -delete 2>/dev/null || true
        echo -e "${GREEN}✅ Nettoyage pré-build terminé.${NC}"
        ;;
    *)
        echo -e "${YELLOW}Usage: ./scripts/clean.sh [logs|cache|docker|test|all|prebuild]${NC}"
        echo -e "${BLUE}Commandes disponibles:${NC}"
        echo -e "  ${GREEN}logs${NC}      - Supprime le dossier logs/"
        echo -e "  ${GREEN}cache${NC}     - Supprime le cache Python (__pycache__, *.pyc)"
        echo -e "  ${GREEN}docker${NC}    - Nettoyage complet Docker (conteneurs, images, volumes)"
        echo -e "  ${GREEN}test${NC}      - Supprime les fichiers de test (htmlcov, .coverage, etc.)"
        echo -e "  ${GREEN}all${NC}       - Nettoyage complet (logs + cache + test + docker optionnel)"
        echo -e "  ${GREEN}prebuild${NC}  - Nettoyage minimal avant build (logs + cache)"
        exit 1
        ;;
esac
