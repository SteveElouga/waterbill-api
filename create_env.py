#!/usr/bin/env python3
"""
Script pour créer le fichier .env basé sur env.example
"""

import os
import shutil


def create_env_file():
    """Crée le fichier .env à partir de env.example"""

    # Vérifier si .env existe déjà
    if os.path.exists('.env'):
        print("⚠️  Le fichier .env existe déjà.")
        response = input("Voulez-vous le remplacer? (y/N): ")
        if response.lower() != 'y':
            print("❌ Annulé.")
            return

    # Copier env.example vers .env
    try:
        shutil.copy('env.example', '.env')
        print("✅ Fichier .env créé avec succès!")
        print("📝 N'oubliez pas de personnaliser les valeurs dans .env")
        print("🔒 Le fichier .env est dans .gitignore pour des raisons de sécurité")

        # Afficher les variables importantes à personnaliser
        print("\n🎯 Variables importantes à personnaliser:")
        print("  - SECRET_KEY: Générez une clé secrète unique")
        print("  - POSTGRES_PASSWORD: Mot de passe de la base de données")
        print("  - DJANGO_SUPERUSER_PASSWORD: Mot de passe de l'admin")
        print("  - PGADMIN_PASSWORD: Mot de passe de pgAdmin")
        print("  - TWILIO_*: Variables pour les SMS (optionnel)")

    except FileNotFoundError:
        print("❌ Erreur: Le fichier env.example n'existe pas.")
    except Exception as e:
        print(f"❌ Erreur lors de la création du fichier .env: {e}")


if __name__ == "__main__":
    create_env_file()
