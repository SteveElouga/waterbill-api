"""
Gestionnaire d'utilisateurs personnalisé pour WaterBill API.

Ce module implémente la logique de création et gestion des utilisateurs
avec authentification par numéro de téléphone.
"""

from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
from typing import Optional


class UserManager(BaseUserManager):
    """
    Gestionnaire personnalisé pour le modèle User.

    Gère la création des utilisateurs avec numéro de téléphone
    comme identifiant unique.
    """

    def _validate_phone(self, phone: str) -> None:
        """
        Valide le format du numéro de téléphone.

        Args:
            phone: Numéro de téléphone à valider

        Raises:
            ValidationError: Si le numéro n'est pas valide
        """
        if not phone:
            raise ValidationError("Le numéro de téléphone est obligatoire.")

        # Nettoyer le numéro (supprimer espaces, tirets, etc.)
        cleaned_phone = "".join(filter(str.isdigit, phone))

        if len(cleaned_phone) < 8:
            raise ValidationError(
                "Le numéro de téléphone doit contenir au moins 8 chiffres."
            )

        if len(cleaned_phone) > 15:
            raise ValidationError(
                "Le numéro de téléphone ne peut pas dépasser 15 chiffres."
            )

    def create_user(
        self,
        phone: str,
        first_name: str,
        last_name: str,
        password: Optional[str] = None,
        **extra_fields,
    ):
        """
        Crée et sauvegarde un utilisateur normal.

        Args:
            phone: Numéro de téléphone unique
            first_name: Prénom de l'utilisateur
            last_name: Nom de famille
            password: Mot de passe (optionnel)
            **extra_fields: Champs supplémentaires (email, address, etc.)

        Returns:
            User: Instance de l'utilisateur créé

        Raises:
            ValidationError: Si les données ne sont pas valides
        """
        # Validation des champs obligatoires
        self._validate_phone(phone)

        if not first_name:
            raise ValidationError("Le prénom est obligatoire.")

        if not last_name:
            raise ValidationError("Le nom de famille est obligatoire.")

        # Nettoyer le numéro de téléphone (garder seulement les chiffres)
        cleaned_phone = "".join(filter(str.isdigit, phone))

        # Formater au format international
        international_phone = "+" + cleaned_phone

        # Vérifier l'unicité avec le format international
        if self.filter(phone=international_phone).exists():
            raise ValidationError(
                f"Un utilisateur avec le numéro {international_phone} existe déjà."
            )

        # Créer l'utilisateur
        user = self.model(
            phone=international_phone,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            **extra_fields,
        )

        # Définir le mot de passe si fourni
        if password:
            user.set_password(password)

        # Sauvegarder
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        phone: str,
        first_name: str,
        last_name: str,
        password: Optional[str] = None,
        **extra_fields,
    ):
        """
        Crée et sauvegarde un superutilisateur.

        Args:
            phone: Numéro de téléphone unique
            first_name: Prénom de l'utilisateur
            last_name: Nom de famille
            password: Mot de passe
            **extra_fields: Champs supplémentaires

        Returns:
            User: Instance du superutilisateur créé
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValidationError("Le superutilisateur doit avoir is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValidationError("Le superutilisateur doit avoir is_superuser=True.")

        return self.create_user(
            phone=phone,
            first_name=first_name,
            last_name=last_name,
            password=password,
            **extra_fields,
        )

    def get_by_phone(self, phone: str):
        """
        Récupère un utilisateur par son numéro de téléphone.

        Args:
            phone: Numéro de téléphone à rechercher

        Returns:
            User: Instance de l'utilisateur ou None

        Raises:
            User.DoesNotExist: Si l'utilisateur n'existe pas
        """
        # Nettoyer le numéro (garder seulement les chiffres)
        cleaned_phone = "".join(filter(str.isdigit, phone))

        # Formater au format international
        international_phone = "+" + cleaned_phone

        return self.get(phone=international_phone)
