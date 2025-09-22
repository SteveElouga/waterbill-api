#!/usr/bin/env python3
"""
Script utilitaire pour générer une clé secrète Django sécurisée.
Usage: python scripts/generate-secret-key.py
"""

import secrets
import string


def generate_secret_key() -> str:
    """Génère une clé secrète Django sécurisée."""
    # Utilise Django's get_random_secret_key si disponible
    try:
        from django.core.management.utils import get_random_secret_key

        return get_random_secret_key()
    except ImportError:
        # Fallback si Django n'est pas installé
        chars = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"
        return "".join(secrets.choice(chars) for _ in range(50))


if __name__ == "__main__":
    secret_key = generate_secret_key()
    print(f"SECRET_KEY={secret_key}")
    print("\n⚠️  IMPORTANT:")
    print("- Copiez cette clé dans votre fichier .env")
    print("- Ne commitez JAMAIS cette clé dans Git")
    print("- Utilisez une clé différente pour chaque environnement")
