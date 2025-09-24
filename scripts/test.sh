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

echo -e "${BLUE}🧪 WaterBill API - Tests${NC}"

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

# Vérifier les permissions de l'entrypoint
if [ ! -x "docker/entrypoint.sh" ]; then
    echo -e "${YELLOW}⚠️  Le script docker/entrypoint.sh n'est pas exécutable. Ajout des permissions...${NC}"
    chmod +x docker/entrypoint.sh
fi

# Vérifier les fins de ligne (CRLF sur Windows)
if grep -q $'\r' "docker/entrypoint.sh"; then
    echo -e "${YELLOW}⚠️  Fins de ligne CRLF détectées dans docker/entrypoint.sh. Conversion en LF...${NC}"
    if command -v dos2unix &> /dev/null; then
        dos2unix docker/entrypoint.sh
    elif command -v sed &> /dev/null; then
        sed -i 's/\r$//' docker/entrypoint.sh
    else
        echo -e "${RED}❌ Ni dos2unix ni sed trouvés. Veuillez convertir manuellement docker/entrypoint.sh en fins de ligne LF.${NC}"
        exit 1
    fi
fi

case "$1" in
    unit)
        echo -e "${GREEN}🧪 Lancement des tests unitaires...${NC}"
        # Tous les tests unitaires (y compris throttling maintenant corrigé)
        docker-compose $COMPOSE_FILES exec web bash -c "DJANGO_TEST_MODE=1 pytest --tb=short -v"
        ;;
    integration)
        echo -e "${GREEN}🔗 Lancement des tests d'intégration...${NC}"
        docker-compose $COMPOSE_FILES exec web bash -c "DJANGO_TEST_MODE=1 pytest --tb=short -v -m integration"
        ;;
    coverage)
        echo -e "${GREEN}📊 Génération du rapport de couverture...${NC}"
        docker-compose $COMPOSE_FILES exec web bash -c "DJANGO_TEST_MODE=1 pytest --cov=. --cov-report=html --cov-report=term"
        echo -e "${GREEN}✅ Rapport de couverture généré dans htmlcov/${NC}"
        ;;
    watch)
        echo -e "${GREEN}👀 Mode watch - Tests automatiques sur modification...${NC}"
        docker-compose $COMPOSE_FILES exec web bash -c "DJANGO_TEST_MODE=1 pytest-watch -- --tb=short"
        ;;
    specific)
        if [ -z "$2" ]; then
            echo -e "${RED}❌ Erreur: Veuillez spécifier le fichier ou le pattern de test.${NC}"
            echo -e "${YELLOW}Usage: ./scripts/test.sh specific <fichier_ou_pattern>${NC}"
            exit 1
        fi
        echo -e "${GREEN}🎯 Lancement des tests spécifiques: $2${NC}"
        # Tous les tests spécifiques avec mode test activé
        docker-compose $COMPOSE_FILES exec web bash -c "DJANGO_TEST_MODE=1 pytest --tb=short -v $2"
        ;;
    all)
        echo -e "${GREEN}🚀 Lancement de tous les tests...${NC}"
        docker-compose $COMPOSE_FILES exec web bash -c "DJANGO_TEST_MODE=1 pytest --tb=short -v --cov=. --cov-report=html --cov-report=term"
        echo -e "${GREEN}✅ Tous les tests terminés. Rapport de couverture dans htmlcov/${NC}"
        ;;
    clean)
        echo -e "${YELLOW}🧹 Nettoyage des fichiers de test...${NC}"
        docker-compose $COMPOSE_FILES exec web find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        docker-compose $COMPOSE_FILES exec web find . -name "*.pyc" -delete 2>/dev/null || true
        docker-compose $COMPOSE_FILES exec web rm -rf htmlcov/ .coverage .pytest_cache/ 2>/dev/null || true
        echo -e "${GREEN}✅ Nettoyage terminé.${NC}"
        ;;
    *)
        echo -e "${YELLOW}Usage: ./scripts/test.sh [unit|integration|coverage|watch|specific|all|clean]${NC}"
        echo -e "${BLUE}Commandes disponibles:${NC}"
        echo -e "  ${GREEN}unit${NC}        - Tests unitaires seulement"
        echo -e "  ${GREEN}integration${NC} - Tests d'intégration"
        echo -e "  ${GREEN}coverage${NC}    - Rapport de couverture de code"
        echo -e "  ${GREEN}watch${NC}       - Mode watch (tests automatiques)"
        echo -e "  ${GREEN}specific${NC}    - Tests spécifiques (ex: ./scripts/test.sh specific core/tests.py)"
        echo -e "  ${GREEN}all${NC}         - Tous les tests avec couverture"
        echo -e "  ${GREEN}clean${NC}       - Nettoyage des fichiers de test"
        exit 1
        ;;
esac
