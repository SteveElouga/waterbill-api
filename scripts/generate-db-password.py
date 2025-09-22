#!/usr/bin/env python3
"""
Script utilitaire pour générer un mot de passe PostgreSQL sécurisé.
Usage: python scripts/generate-db-password.py
"""

import secrets
import string


def generate_secure_password(length: int = 16) -> str:
    """Génère un mot de passe sécurisé pour PostgreSQL."""
    # Caractères autorisés pour PostgreSQL (évite les caractères spéciaux problématiques)
    chars = string.ascii_letters + string.digits + "!@#$%^&*"

    # Assure qu'il y a au moins une majuscule, une minuscule et un chiffre
    password = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
    ]

    # Complète avec des caractères aléatoires
    for _ in range(length - 3):
        password.append(secrets.choice(chars))

    # Mélange le mot de passe
    secrets.SystemRandom().shuffle(password)

    return "".join(password)


if __name__ == "__main__":
    password = generate_secure_password()
    print(f"POSTGRES_PASSWORD={password}")
    print("\n⚠️  IMPORTANT:")
    print("- Copiez ce mot de passe dans votre fichier .env")
    print("- Ne commitez JAMAIS ce mot de passe dans Git")
    print("- Utilisez un mot de passe différent pour chaque environnement")
    print("- Le mot de passe doit être défini dans POSTGRES_PASSWORD")
