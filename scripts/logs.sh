#!/usr/bin/env bash
set -e

# Variables de couleur
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fichiers Docker Compose
COMPOSE_FILES="-f docker-compose.yml -f docker-compose.dev.yml"

echo -e "${BLUE}📋 WaterBill API - Gestion des Logs${NC}"

# Fonction pour vérifier si un fichier existe
check_file() {
    if [ ! -f "$1" ]; then
        echo -e "${RED}❌ Erreur: Le fichier '$1' est manquant.${NC}"
        exit 1
    fi
}

# Vérifier les fichiers essentiels
check_file "docker-compose.yml"
check_file "docker-compose.dev.yml"
check_file "Dockerfile.dev"
check_file "docker/entrypoint.sh"
check_file ".env"

case "$1" in
    show)
        echo -e "${GREEN}📋 Affichage des logs Django...${NC}"
        if [ -f "logs/django.log" ]; then
            tail -n 50 logs/django.log
        else
            echo -e "${YELLOW}⚠️  Le fichier logs/django.log n'existe pas encore.${NC}"
        fi
        ;;
    follow)
        echo -e "${GREEN}👀 Suivi en temps réel des logs Django (Ctrl+C pour quitter)...${NC}"
        if [ -f "logs/django.log" ]; then
            tail -f logs/django.log
        else
            echo -e "${YELLOW}⚠️  Le fichier logs/django.log n'existe pas encore.${NC}"
            echo -e "${BLUE}💡 Lancez d'abord l'application avec: ./scripts/dev.sh up${NC}"
        fi
        ;;
    errors)
        echo -e "${GREEN}🚨 Affichage des erreurs dans les logs...${NC}"
        if [ -f "logs/django.log" ]; then
            grep -i "error\|exception\|traceback" logs/django.log | tail -n 20
        else
            echo -e "${YELLOW}⚠️  Le fichier logs/django.log n'existe pas encore.${NC}"
        fi
        ;;
    clear)
        echo -e "${YELLOW}🧹 Nettoyage des logs...${NC}"
        if [ -f "logs/django.log" ]; then
            > logs/django.log
            echo -e "${GREEN}✅ Logs effacés.${NC}"
        else
            echo -e "${YELLOW}⚠️  Le fichier logs/django.log n'existe pas.${NC}"
        fi
        ;;
    docker)
        echo -e "${GREEN}🐳 Affichage des logs Docker...${NC}"
        docker-compose $COMPOSE_FILES logs -f web
        ;;
    size)
        echo -e "${GREEN}📊 Taille des fichiers de logs...${NC}"
        if [ -d "logs" ]; then
            ls -lh logs/
        else
            echo -e "${YELLOW}⚠️  Le dossier logs/ n'existe pas.${NC}"
        fi
        ;;
    *)
        echo -e "${YELLOW}Usage: ./scripts/logs.sh [show|follow|errors|clear|docker|size]${NC}"
        echo -e "${BLUE}Commandes disponibles:${NC}"
        echo -e "  ${GREEN}show${NC}    - Affiche les 50 dernières lignes des logs Django"
        echo -e "  ${GREEN}follow${NC}  - Suit les logs Django en temps réel"
        echo -e "  ${GREEN}errors${NC}  - Affiche uniquement les erreurs"
        echo -e "  ${GREEN}clear${NC}   - Efface le fichier de logs"
        echo -e "  ${GREEN}docker${NC}  - Affiche les logs du conteneur Docker"
        echo -e "  ${GREEN}size${NC}    - Affiche la taille des fichiers de logs"
        exit 1
        ;;
esac
