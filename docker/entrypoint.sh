#!/usr/bin/env bash
set -e

# Attendre que la DB réponde (utilise Python pour éviter d’installer netcat)
echo "⏳ Attente de la base de données..."
python - <<'PYCODE'
import os, time, sys
import psycopg2
from urllib.parse import urlparse

url = os.environ.get("DATABASE_URL")
if not url:
    print("DATABASE_URL non défini", file=sys.stderr)
    sys.exit(1)

for i in range(30):
    try:
        with psycopg2.connect(url, connect_timeout=3) as conn:
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
if [[ -n "$DJANGO_SUPERUSER_PHONE" && -n "$DJANGO_SUPERUSER_PASSWORD" ]]; then
  echo "👤 Création du superuser..."
  # Créer le superuser avec le modèle User personnalisé (phone-based)
  python - <<'PYCODE'
import os
import django
from django.core.management import execute_from_command_line

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'waterbill.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
phone = os.environ.get('DJANGO_SUPERUSER_PHONE')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
first_name = os.environ.get('DJANGO_SUPERUSER_FIRST_NAME', 'Admin')
last_name = os.environ.get('DJANGO_SUPERUSER_LAST_NAME', 'User')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
address = os.environ.get('DJANGO_SUPERUSER_ADDRESS', '123 Main St')

if not User.objects.filter(phone=phone).exists():
    User.objects.create_superuser(
        phone=phone,
        password=password,
        first_name=first_name,
        last_name=last_name,
        email=email,
        address=address
    )
    print(f"✅ Superutilisateur créé avec le numéro {phone}")
else:
    print(f"⚠️ Superutilisateur avec le numéro {phone} existe déjà")
PYCODE
fi

# Lancement serveur (Gunicorn en prod, runserver en dev)
if [[ "$DJANGO_RUNSERVER" == "1" ]]; then
  echo "🚀 Lancement devserver (mode développement)..."
  exec python manage.py runserver 0.0.0.0:8000
else
  echo "🚀 Lancement gunicorn (mode production)..."
  exec gunicorn waterbill.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
fi
