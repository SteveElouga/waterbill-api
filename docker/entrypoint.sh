#!/usr/bin/env bash
set -e

# Attendre que la DB réponde (utilise Python pour éviter d’installer netcat)
echo "⏳ Attente de la base de données..."
python - <<'PYCODE'
import os, time, sys
import psycopg
from urllib.parse import urlparse

url = os.environ.get("DATABASE_URL")
if not url:
    print("DATABASE_URL non défini", file=sys.stderr)
    sys.exit(1)

for i in range(30):
    try:
        with psycopg.connect(url, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                print("✅ Base de données prête.")
                sys.exit(0)
    except Exception as e:
        print(f"DB non prête ({e}), retry {i+1}/30...")
        time.sleep(2)

print("❌ Échec de connexion à la DB après 30 essais.", file=sys.stderr)
sys.exit(1)
PYCODE

# Création du dossier logs
echo "📁 Création du dossier logs..."
mkdir -p /app/logs

# Migrations
echo "⚙️  Django migrate..."
python manage.py migrate --noinput

# Collect static (si whitenoise)
echo "📦 Collectstatic..."
python manage.py collectstatic --noinput 2>/dev/null || echo "⚠️  Collectstatic ignoré (pas de fichiers statiques)"

# Création auto du superuser si variables présentes (optionnel)
if [[ -n "$DJANGO_SUPERUSER_USERNAME" && -n "$DJANGO_SUPERUSER_EMAIL" && -n "$DJANGO_SUPERUSER_PASSWORD" ]]; then
  echo "👤 Création du superuser..."
  # Utiliser le numéro de téléphone comme identifiant pour notre modèle User personnalisé
  python manage.py createsuperuser \
    --username "$DJANGO_SUPERUSER_USERNAME" \
    --email "$DJANGO_SUPERUSER_EMAIL" \
    --phone "$DJANGO_SUPERUSER_USERNAME" \
    --noinput || true
fi

# Lancement serveur (Gunicorn en prod, runserver en dev)
if [[ "$DJANGO_RUNSERVER" == "1" ]]; then
  echo "🚀 Lancement devserver (mode développement)..."
  exec python manage.py runserver 0.0.0.0:8000
else
  echo "🚀 Lancement gunicorn (mode production)..."
  exec gunicorn waterbill.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
fi
