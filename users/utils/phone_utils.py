"""
Utilitaires pour la gestion des numéros de téléphone.

Ce module contient les fonctions de normalisation et validation
des numéros de téléphone pour l'application WaterBill.
"""

import re
from typing import Optional


def normalize_phone(phone: str) -> Optional[str]:
    """
    Nettoie et normalise un numéro de téléphone en format international.

    Cette fonction :
    - Supprime tous les caractères non-numériques (espaces, tirets, parenthèses, etc.)
    - Ajoute un préfixe '+' si absent
    - Retourne le numéro au format international (+XXXXXXXXX)

    Args:
        phone: Numéro de téléphone à normaliser

    Returns:
        str: Numéro normalisé au format international (+XXXXXXXXX)
        None: Si le numéro est vide ou invalide

    Examples:
        >>> normalize_phone("675799743")
        "+675799743"
        >>> normalize_phone("675 799 750")
        "+675799750"
        >>> normalize_phone("(675) 799-752")
        "+675799752"
        >>> normalize_phone("+675799749")
        "+675799749"
    """
    if not phone:
        return None

    # Supprimer tous les caractères non numériques sauf +
    digits = re.sub(r"[^\d+]", "", phone)

    # Ajouter le + si manquant
    if not digits.startswith("+"):
        digits = f"+{digits}"

    return digits


def validate_phone_length(
    phone: str, min_length: int = 9, max_length: int = 15
) -> bool:
    """
    Valide la longueur d'un numéro de téléphone après normalisation.

    Args:
        phone: Numéro de téléphone à valider
        min_length: Longueur minimale (par défaut 9)
        max_length: Longueur maximale (par défaut 15)

    Returns:
        bool: True si la longueur est valide, False sinon
    """
    if not phone:
        return False

    # Extraire seulement les chiffres pour la validation de longueur
    digits_only = "".join(filter(str.isdigit, phone))
    return min_length <= len(digits_only) <= max_length


def clean_phone_for_display(phone: str) -> str:
    """
    Nettoie un numéro de téléphone pour l'affichage.

    Args:
        phone: Numéro de téléphone à nettoyer

    Returns:
        str: Numéro nettoyé pour l'affichage
    """
    if not phone:
        return ""

    # Supprimer tous les caractères non numériques sauf +
    return re.sub(r"[^\d+]", "", phone)
