#!/usr/bin/env bash
# Script pour lancer WaterBill API en mode PRODUCTION avec Docker Compose
# Usage: ./scripts/prod.sh [command]

set -e

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction d'aide
show_help() {
    echo -e "${BLUE}WaterBill API - Script de production Docker${NC}"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  up          Lancer les services en mode production (défaut)"
    echo "  down        Arrêter les services"
    echo "  restart     Redémarrer les services"
    echo "  logs        Afficher les logs en temps réel"
    echo "  build       Reconstruire les images"
    echo "  shell       Accéder au conteneur web"
    echo "  db          Accéder à PostgreSQL"
    echo "  migrate     Exécuter les migrations Django"
    echo "  status      Vérifier le statut des services"
    echo "  backup      Sauvegarder la base de données"
    echo "  restore     Restaurer la base de données"
    echo "  restore-env Restaurer le fichier .env original (DEBUG=True)"
    echo "  update      Mise à jour complète (build + restart)"
    echo "  help        Afficher cette aide"
    echo ""
    echo "Exemples:"
    echo "  $0 up       # Lancer en mode production"
    echo "  $0 status   # Vérifier le statut"
    echo "  $0 backup   # Sauvegarder la DB"
    echo ""
    echo -e "${RED}⚠️  ATTENTION: Mode PRODUCTION - Soyez prudent !${NC}"
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

    if [ ! -f ".env" ]; then
        echo -e "${RED}❌ Erreur: Fichier .env obligatoire en production${NC}"
        echo -e "${YELLOW}   Configurez vos variables d'environnement de production${NC}"
        exit 1
    fi

    # Forcer DEBUG=False en mode production
    if grep -q "DEBUG=True" .env 2>/dev/null; then
        echo -e "${YELLOW}⚠️  DEBUG=True détecté, passage automatique à DEBUG=False pour la production${NC}"
        # Créer une sauvegarde du fichier .env
        cp .env .env.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
        # Remplacer DEBUG=True par DEBUG=False
        sed -i 's/DEBUG=True/DEBUG=False/g' .env
        echo -e "${GREEN}✅ DEBUG=False appliqué automatiquement${NC}"
    fi
}

# Vérifier le statut des services
check_status() {
    echo -e "${BLUE}📊 Statut des services:${NC}"
    docker-compose -f docker-compose.yml ps
    echo ""
    echo -e "${BLUE}📈 Utilisation des ressources:${NC}"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" $(docker-compose -f docker-compose.yml ps -q) 2>/dev/null || echo "Aucun conteneur en cours d'exécution"
}

# Fonction principale
main() {
    local command=${1:-up}

    echo -e "${RED}🏭 WaterBill API - Mode PRODUCTION${NC}"
    echo ""

    check_docker_compose
    check_files

    case $command in
        up)
            echo -e "${GREEN}🚀 Lancement des services en mode production...${NC}"
            echo -e "${YELLOW}⚠️  Vérification de la configuration de production...${NC}"

            # Vérifications de sécurité supplémentaires
            if ! grep -q "SECRET_KEY=" .env || grep -q "your-secret-key" .env; then
                echo -e "${RED}❌ ERREUR: SECRET_KEY non configuré ou par défaut !${NC}"
                exit 1
            fi

            docker-compose -f docker-compose.yml up -d
            echo -e "${GREEN}✅ Services de production lancés !${NC}"
            echo -e "${BLUE}📊 Accès:${NC}"
            echo -e "  - API: http://localhost:8000"
            echo -e "  - Documentation: http://localhost:8000/api/docs/"
            echo ""
            echo -e "${YELLOW}💡 Commandes utiles:${NC}"
            echo -e "  $0 status  # Vérifier le statut"
            echo -e "  $0 logs    # Voir les logs"
            echo -e "  $0 backup  # Sauvegarder la DB"
            ;;
        down)
            echo -e "${RED}🛑 Arrêt des services de production...${NC}"
            read -p "Êtes-vous sûr de vouloir arrêter les services de production ? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                docker-compose -f docker-compose.yml down
                echo -e "${GREEN}✅ Services arrêtés${NC}"

                # Proposer de restaurer le fichier .env original
                if ls .env.backup.* >/dev/null 2>&1; then
                    echo ""
                    read -p "Restaurer le fichier .env original (avec DEBUG=True) ? (y/N): " -n 1 -r
                    echo
                    if [[ $REPLY =~ ^[Yy]$ ]]; then
                        latest_backup=$(ls -t .env.backup.* | head -n1)
                        cp "$latest_backup" .env
                        rm .env.backup.*
                        echo -e "${GREEN}✅ Fichier .env restauré (DEBUG=True)${NC}"
                    fi
                fi
            else
                echo -e "${YELLOW}❌ Arrêt annulé${NC}"
            fi
            ;;
        restart)
            echo -e "${YELLOW}🔄 Redémarrage des services de production...${NC}"
            docker-compose -f docker-compose.yml restart
            echo -e "${GREEN}✅ Services redémarrés${NC}"
            ;;
        logs)
            echo -e "${BLUE}📋 Logs de production en temps réel (Ctrl+C pour quitter)${NC}"
            docker-compose -f docker-compose.yml logs -f
            ;;
        build)
            echo -e "${BLUE}🔨 Reconstruction des images de production...${NC}"
            # Nettoyage des logs avant build pour éviter de les copier
            echo -e "${YELLOW}🧹 Nettoyage des logs avant build...${NC}"
            rm -rf logs/ 2>/dev/null || true
            # Build optimisé avec cache Docker BuildKit
            DOCKER_BUILDKIT=1 docker-compose -f docker-compose.yml build --parallel
            echo -e "${GREEN}✅ Images reconstruites${NC}"
            ;;
        shell)
            echo -e "${BLUE}🐚 Accès au conteneur web de production...${NC}"
            docker-compose -f docker-compose.yml exec web bash
            ;;
        db)
            echo -e "${BLUE}🗄️  Accès à PostgreSQL de production...${NC}"
            docker-compose -f docker-compose.yml exec db psql -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-waterbill}
            ;;
        migrate)
            echo -e "${BLUE}🔄 Exécution des migrations Django en production...${NC}"
            docker-compose -f docker-compose.yml exec web python manage.py migrate
            echo -e "${GREEN}✅ Migrations terminées${NC}"
            ;;
        status)
            check_status
            ;;
        backup)
            echo -e "${BLUE}💾 Sauvegarde de la base de données...${NC}"
            local backup_file="backup_$(date +%Y%m%d_%H%M%S).sql"
            docker-compose -f docker-compose.yml exec db pg_dump -U ${POSTGRES_USER:-postgres} ${POSTGRES_DB:-waterbill} > "$backup_file"
            echo -e "${GREEN}✅ Sauvegarde créée: $backup_file${NC}"
            ;;
        restore)
            echo -e "${RED}⚠️  Restauration de la base de données...${NC}"
            read -p "Fichier de sauvegarde à restaurer: " backup_file
            if [ ! -f "$backup_file" ]; then
                echo -e "${RED}❌ Fichier non trouvé: $backup_file${NC}"
                exit 1
            fi
            read -p "Êtes-vous sûr de vouloir restaurer la base de données ? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                docker-compose -f docker-compose.yml exec -T db psql -U ${POSTGRES_USER:-postgres} ${POSTGRES_DB:-waterbill} < "$backup_file"
                echo -e "${GREEN}✅ Base de données restaurée${NC}"
            else
                echo -e "${YELLOW}❌ Restauration annulée${NC}"
            fi
            ;;
        update)
            echo -e "${BLUE}🔄 Mise à jour complète de production...${NC}"
            echo -e "${YELLOW}1. Arrêt des services...${NC}"
            docker-compose -f docker-compose.yml down
            echo -e "${YELLOW}2. Nettoyage des logs avant build...${NC}"
            rm -rf logs/ 2>/dev/null || true
            echo -e "${YELLOW}3. Reconstruction des images...${NC}"
            docker-compose -f docker-compose.yml build --no-cache
            echo -e "${YELLOW}4. Redémarrage des services...${NC}"
            docker-compose -f docker-compose.yml up -d
            echo -e "${YELLOW}5. Exécution des migrations...${NC}"
            docker-compose -f docker-compose.yml exec web python manage.py migrate
            echo -e "${GREEN}✅ Mise à jour terminée${NC}"
            ;;
        restore-env)
            echo -e "${BLUE}🔄 Restauration du fichier .env original...${NC}"
            if ls .env.backup.* >/dev/null 2>&1; then
                latest_backup=$(ls -t .env.backup.* | head -n1)
                echo -e "${YELLOW}📁 Fichier de sauvegarde trouvé: $latest_backup${NC}"
                cp "$latest_backup" .env
                rm .env.backup.*
                echo -e "${GREEN}✅ Fichier .env restauré (DEBUG=True)${NC}"
                echo -e "${BLUE}💡 Vous pouvez maintenant lancer le mode développement${NC}"
            else
                echo -e "${RED}❌ Aucune sauvegarde de .env trouvée${NC}"
                echo -e "${YELLOW}   Les sauvegardes sont créées automatiquement lors du lancement en production${NC}"
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
