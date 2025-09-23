#!/usr/bin/env bash
# Script pour lancer WaterBill API en mode DÉVELOPPEMENT avec Docker Compose
# Usage: ./scripts/dev.sh [command]

set -e

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction d'aide
show_help() {
    echo -e "${BLUE}WaterBill API - Script de développement Docker${NC}"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  up          Lancer les services en mode développement (défaut)"
    echo "  down        Arrêter les services"
    echo "  restart     Redémarrer les services"
    echo "  logs        Afficher les logs en temps réel"
    echo "  build       Reconstruire les images"
    echo "  shell       Accéder au conteneur web"
    echo "  db          Accéder à PostgreSQL"
    echo "  migrate     Exécuter les migrations Django"
    echo "  test        Lancer les tests"
    echo "  clean       Nettoyer les conteneurs et volumes"
    echo "  help        Afficher cette aide"
    echo ""
    echo "Exemples:"
    echo "  $0 up       # Lancer en mode développement"
    echo "  $0 logs     # Voir les logs"
    echo "  $0 shell    # Accéder au conteneur"
}

# Vérifier que Docker Compose est disponible
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ Erreur: Docker Compose n'est pas installé ou accessible${NC}"
        exit 1
    fi
}

# Vérifier que les fichiers nécessaires existent
check_files() {
    if [ ! -f "docker-compose.yml" ]; then
        echo -e "${RED}❌ Erreur: docker-compose.yml non trouvé${NC}"
        exit 1
    fi

    if [ ! -f "docker-compose.dev.yml" ]; then
        echo -e "${RED}❌ Erreur: docker-compose.dev.yml non trouvé${NC}"
        exit 1
    fi

    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}⚠️  Attention: Fichier .env non trouvé${NC}"
        echo -e "${YELLOW}   Copiez env.example vers .env et configurez vos variables${NC}"
        echo -e "${YELLOW}   cp env.example .env${NC}"
        exit 1
    fi

    # S'assurer que DEBUG=True en mode développement
    if grep -q "DEBUG=False" .env 2>/dev/null; then
        echo -e "${YELLOW}⚠️  DEBUG=False détecté, passage automatique à DEBUG=True pour le développement${NC}"
        # Créer une sauvegarde du fichier .env
        cp .env .env.backup.dev.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
        # Remplacer DEBUG=False par DEBUG=True
        sed -i 's/DEBUG=False/DEBUG=True/g' .env
        echo -e "${GREEN}✅ DEBUG=True appliqué automatiquement${NC}"
    fi
}

# Fonction principale
main() {
    local command=${1:-up}

    echo -e "${BLUE}🐳 WaterBill API - Mode DÉVELOPPEMENT${NC}"
    echo ""

    check_docker_compose
    check_files

    case $command in
        up)
            echo -e "${GREEN}🚀 Lancement des services en mode développement...${NC}"
            docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
            echo -e "${GREEN}✅ Services lancés !${NC}"
            echo -e "${BLUE}📊 Accès:${NC}"
            echo -e "  - API: http://localhost:8000"
            echo -e "  - Documentation: http://localhost:8000/api/docs/"
            echo -e "  - pgAdmin: http://localhost:5050"
            echo ""
            echo -e "${YELLOW}💡 Commandes utiles:${NC}"
            echo -e "  $0 logs    # Voir les logs"
            echo -e "  $0 shell   # Accéder au conteneur"
            echo -e "  $0 test    # Lancer les tests"
            ;;
        down)
            echo -e "${YELLOW}🛑 Arrêt des services...${NC}"
            docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
            echo -e "${GREEN}✅ Services arrêtés${NC}"
            ;;
        restart)
            echo -e "${YELLOW}🔄 Redémarrage des services...${NC}"
            docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart
            echo -e "${GREEN}✅ Services redémarrés${NC}"
            ;;
        logs)
            echo -e "${BLUE}📋 Logs en temps réel (Ctrl+C pour quitter)${NC}"
            docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f
            ;;
        build)
            echo -e "${BLUE}🔨 Reconstruction des images...${NC}"
            # Nettoyage des logs avant build pour éviter de les copier
            echo -e "${YELLOW}🧹 Nettoyage des logs avant build...${NC}"
            rm -rf logs/ 2>/dev/null || true
            # Build optimisé avec cache Docker BuildKit
            DOCKER_BUILDKIT=1 docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --parallel
            echo -e "${GREEN}✅ Images reconstruites${NC}"
            ;;
        shell)
            echo -e "${BLUE}🐚 Accès au conteneur web...${NC}"
            docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec web bash
            ;;
        db)
            echo -e "${BLUE}🗄️  Accès à PostgreSQL...${NC}"
            docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec db psql -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-waterbill}
            ;;
        migrate)
            echo -e "${BLUE}🔄 Exécution des migrations Django...${NC}"
            docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py migrate
            echo -e "${GREEN}✅ Migrations terminées${NC}"
            ;;
        test)
            echo -e "${BLUE}🧪 Lancement des tests...${NC}"
            docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec web python -m pytest
            ;;
        clean)
            echo -e "${RED}🧹 Nettoyage des conteneurs et volumes...${NC}"
            read -p "Êtes-vous sûr de vouloir supprimer tous les conteneurs et volumes ? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                docker-compose -f docker-compose.yml -f docker-compose.dev.yml down -v --remove-orphans
                docker system prune -f
                echo -e "${GREEN}✅ Nettoyage terminé${NC}"
            else
                echo -e "${YELLOW}❌ Nettoyage annulé${NC}"
            fi
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}❌ Commande inconnue: $command${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Exécuter la fonction principale avec tous les arguments
main "$@"
