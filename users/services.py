"""
Services d'authentification pour WaterBill API.

Ce module implémente la logique métier pour l'inscription,
connexion, activation et gestion des utilisateurs.
"""

import logging
from typing import Dict, Any, Optional, Tuple
from django.utils import timezone
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, ActivationToken
from .serializers import UserSerializer
from .gateways.sms import get_sms_gateway

logger = logging.getLogger(__name__)


class AuthService:
    """
    Service d'authentification centralisé.

    Implémente la logique métier pour l'inscription et connexion
    des utilisateurs avec gestion des erreurs et validation.
    """

    @staticmethod
    def register_user(user_data: Dict[str, Any]) -> User:
        """
        Enregistre un nouvel utilisateur inactif et génère un token d'activation.

        OPÉRATION ATOMIQUE : Si l'envoi SMS échoue, l'utilisateur n'est pas créé.

        Args:
            user_data: Dictionnaire contenant les données utilisateur

        Returns:
            User: Utilisateur créé (inactif)

        Raises:
            ValueError: Si les données ne sont pas valides
            ValidationError: Si la création échoue
        """
        try:
            # Supprimer password_confirm des données avant création
            user_data_clean = user_data.copy()
            user_data_clean.pop("password_confirm", None)

            # OPÉRATION ATOMIQUE : Transaction qui annule tout si une étape échoue
            with transaction.atomic():
                # 1. Créer l'utilisateur (inactif par défaut)
                user = User.objects.create_user(**user_data_clean)

                # 2. Créer le token d'activation et envoyer le SMS
                # Si cette étape échoue, la transaction entière est annulée
                ActivationService.create_and_send_activation_code(user)

                # 3. Si tout s'est bien passé, valider la transaction
                logger.info(
                    f"Utilisateur créé et code d'activation envoyé: {user.phone}"
                )
                return user

        except Exception as e:
            # En cas d'erreur, la transaction est automatiquement annulée
            logger.error(f"Erreur lors de l'inscription atomique: {str(e)}")
            raise ValueError(f"Erreur lors de l'inscription: {str(e)}")

    @staticmethod
    def authenticate_user(phone: str, password: str) -> Optional[User]:
        """
        Authentifie un utilisateur par téléphone et mot de passe.

        Args:
            phone: Numéro de téléphone de l'utilisateur
            password: Mot de passe de l'utilisateur

        Returns:
            Optional[User]: Utilisateur authentifié ou None
        """
        # Nettoyer et formater le numéro de téléphone au format international
        cleaned_phone = "".join(filter(str.isdigit, phone))
        international_phone = "+" + cleaned_phone

        try:
            # Récupérer l'utilisateur par téléphone (format international)
            user = User.objects.get(phone=international_phone)

            # Vérifier le mot de passe
            if user.check_password(password) and user.is_active:
                # Mettre à jour la dernière connexion
                user.last_login = timezone.now()
                user.save(update_fields=["last_login"])
                return user

        except User.DoesNotExist:
            pass

        return None

    @staticmethod
    def login_user(phone: str, password: str) -> Tuple[User, Dict[str, str]]:
        """
        Connecte un utilisateur et génère les tokens JWT.

        Args:
            phone: Numéro de téléphone de l'utilisateur
            password: Mot de passe de l'utilisateur

        Returns:
            Tuple[User, Dict[str, str]]: Utilisateur et tokens JWT

        Raises:
            ValueError: Si l'authentification échoue
        """
        user = AuthService.authenticate_user(phone, password)

        if not user:
            raise ValueError("Numéro de téléphone ou mot de passe incorrect.")

        # Générer les tokens JWT
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        tokens = {"access": str(access), "refresh": str(refresh)}

        return user, tokens

    @staticmethod
    def get_user_profile(user: User) -> Dict[str, Any]:
        """
        Récupère le profil complet d'un utilisateur.

        Args:
            user: Instance de l'utilisateur

        Returns:
            Dict[str, Any]: Profil utilisateur sérialisé
        """
        serializer = UserSerializer(user)
        return serializer.data

    @staticmethod
    def validate_phone_uniqueness(
        phone: str, exclude_user_id: Optional[int] = None
    ) -> bool:
        """
        Valide l'unicité d'un numéro de téléphone.

        Args:
            phone: Numéro de téléphone à vérifier
            exclude_user_id: ID d'utilisateur à exclure de la vérification

        Returns:
            bool: True si le numéro est unique
        """
        # Nettoyer et formater le numéro de téléphone au format international
        cleaned_phone = "".join(filter(str.isdigit, phone))
        international_phone = "+" + cleaned_phone

        queryset = User.objects.filter(phone=international_phone)

        if exclude_user_id:
            queryset = queryset.exclude(id=exclude_user_id)

        return not queryset.exists()

    @staticmethod
    def refresh_user_tokens(refresh_token: str) -> Tuple[User, Dict[str, str]]:
        """
        Rafraîchit les tokens JWT d'un utilisateur.

        Args:
            refresh_token: Token de rafraîchissement

        Returns:
            Tuple[User, Dict[str, str]]: Utilisateur et nouveaux tokens

        Raises:
            ValueError: Si le token n'est pas valide
        """
        try:
            refresh = RefreshToken(refresh_token)
            user = User.objects.get(id=refresh["user_id"])

            # Générer de nouveaux tokens
            new_refresh = RefreshToken.for_user(user)
            new_access = new_refresh.access_token

            tokens = {"access": str(new_access), "refresh": str(new_refresh)}

            return user, tokens

        except Exception as e:
            raise ValueError(f"Token invalide: {str(e)}")


class ResponseService:
    """
    Service pour la standardisation des réponses API.

    Implémente le format de réponse JSON normalisé
    pour toutes les endpoints d'authentification.
    """

    @staticmethod
    def success_response(
        message: str, data: Optional[Dict[str, Any]] = None, status_code: int = 200
    ) -> Dict[str, Any]:
        """
        Génère une réponse de succès standardisée.

        Args:
            message: Message de succès
            data: Données à retourner
            status_code: Code de statut HTTP

        Returns:
            Dict[str, Any]: Réponse standardisée
        """
        response = {"status": "success", "message": message, "data": data or {}}

        return response

    @staticmethod
    def error_response(
        message: str, errors: Optional[Dict[str, Any]] = None, status_code: int = 400
    ) -> Dict[str, Any]:
        """
        Génère une réponse d'erreur standardisée.

        Args:
            message: Message d'erreur
            errors: Détails des erreurs
            status_code: Code de statut HTTP

        Returns:
            Dict[str, Any]: Réponse d'erreur standardisée
        """
        response = {"status": "error", "message": message, "data": errors or {}}

        return response


class ActivationService:
    """
    Service de gestion des codes d'activation par SMS.

    Implémente la logique métier pour la création, envoi et vérification
    des codes d'activation avec gestion des limites et de la sécurité.
    """

    @staticmethod
    def create_and_send_activation_code(user: User) -> str:
        """
        Crée un token d'activation et envoie le code par SMS.

        OPÉRATION ATOMIQUE : Si l'envoi SMS échoue, le token n'est pas créé.

        Args:
            user: Utilisateur pour lequel créer le token

        Returns:
            str: Code d'activation généré (pour les logs)

        Raises:
            ValueError: Si l'envoi échoue
        """
        try:
            # Générer le code avant de créer le token
            code = str(ActivationToken.generate_code())

            # OPÉRATION ATOMIQUE : Vérifier d'abord si on peut envoyer le SMS
            sms_gateway = get_sms_gateway()

            # Pré-vérifier la disponibilité du gateway SMS
            if not sms_gateway.is_available():
                raise ValueError("Service SMS temporairement indisponible")

            # Essayer d'envoyer le SMS AVANT de créer le token
            if not sms_gateway.send_activation_code(user.phone, code):
                raise ValueError("Échec de l'envoi du SMS")

            # Si l'envoi SMS réussit, créer le token d'activation
            token = ActivationToken.create_token(user)

            # Mettre à jour le hash avec le bon code
            token.code_hash = ActivationToken.hash_code(code)
            token.save(update_fields=["code_hash"])

            logger.info(f"Code d'activation envoyé à {user.phone}")
            return code

        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du code d'activation: {str(e)}")
            raise ValueError(f"Erreur lors de l'envoi du code d'activation: {str(e)}")

    @staticmethod
    def verify_activation_code(phone: str, code: str) -> User:
        """
        Vérifie un code d'activation et active l'utilisateur.

        Args:
            phone: Numéro de téléphone de l'utilisateur
            code: Code d'activation à vérifier

        Returns:
            User: Utilisateur activé

        Raises:
            ValueError: Si la vérification échoue
        """
        try:
            # Nettoyer et formater le numéro de téléphone au format international
            cleaned_phone = "".join(filter(str.isdigit, phone))
            international_phone = "+" + cleaned_phone

            # Récupérer l'utilisateur
            try:
                user = User.objects.get(phone=international_phone)
            except User.DoesNotExist:
                raise ValueError("Utilisateur non trouvé")

            # Vérifier si l'utilisateur est déjà activé
            if user.is_active:
                raise ValueError("Ce compte est déjà activé")

            # Récupérer le token d'activation
            try:
                token = user.activation_token
            except ActivationToken.DoesNotExist:
                raise ValueError("Aucun code d'activation en attente")

            # Vérifier le code
            if not token.verify_code(code):
                if token.is_expired():
                    raise ValueError("Le code d'activation a expiré")
                elif token.is_locked:
                    raise ValueError(
                        "Trop de tentatives échouées. Demandez un nouveau code."
                    )
                else:
                    raise ValueError("Code d'activation incorrect")

            # Activer l'utilisateur (supprime automatiquement le token)
            token.activate_user()

            logger.info(f"Utilisateur activé avec succès: {user.phone}")
            return user

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du code: {str(e)}")
            raise ValueError(f"Erreur lors de la vérification du code: {str(e)}")

    @staticmethod
    def resend_activation_code(phone: str) -> None:
        """
        Renvoie un code d'activation pour un utilisateur.

        Args:
            phone: Numéro de téléphone de l'utilisateur

        Raises:
            ValueError: Si le renvoi n'est pas possible
        """
        try:
            # Nettoyer et formater le numéro de téléphone au format international
            cleaned_phone = "".join(filter(str.isdigit, phone))
            international_phone = "+" + cleaned_phone

            # Récupérer l'utilisateur
            try:
                user = User.objects.get(phone=international_phone)
            except User.DoesNotExist:
                raise ValueError("Utilisateur non trouvé")

            # Vérifier si l'utilisateur est déjà activé
            if user.is_active:
                raise ValueError("Ce compte est déjà activé")

            # Récupérer ou créer le token d'activation
            try:
                token = user.activation_token

                # Vérifier si un nouveau code peut être envoyé
                if not token.can_send_new_code():
                    if token.is_locked:
                        raise ValueError("Compte verrouillé. Contactez le support.")
                    else:
                        raise ValueError("Attendez avant de demander un nouveau code.")

                # Mettre à jour le token pour le renvoi
                token.send_count += 1
                token.last_sent_at = timezone.now()
                token.save(update_fields=["send_count", "last_sent_at"])

            except ActivationToken.DoesNotExist:
                # Créer un nouveau token
                token = ActivationToken.create_token(user)

            # Générer un nouveau code et mettre à jour le token
            code = str(ActivationToken.generate_code())
            token.code_hash = ActivationToken.hash_code(code)
            token.save(update_fields=["code_hash"])

            # Envoyer le SMS
            sms_gateway = get_sms_gateway()
            if not sms_gateway.send_activation_code(user.phone, code):
                raise ValueError("Échec de l'envoi du SMS")

            logger.info(f"Code d'activation renvoyé à {user.phone}")

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors du renvoi du code: {str(e)}")
            raise ValueError(f"Erreur lors du renvoi du code: {str(e)}")


class RateLimitService:
    """
    Service de gestion des limites de taux pour l'activation.

    Implémente la logique de limitation des tentatives et envois
    pour éviter les abus et attaques.
    """

    @staticmethod
    def check_activation_limits(phone: str) -> Dict[str, Any]:
        """
        Vérifie les limites d'activation pour un numéro de téléphone.

        Args:
            phone: Numéro de téléphone à vérifier

        Returns:
            Dict[str, Any]: Informations sur les limites
        """
        # Nettoyer et formater au format international
        cleaned_phone = "".join(filter(str.isdigit, phone))
        international_phone = "+" + cleaned_phone

        try:
            user = User.objects.get(phone=international_phone)
            token = user.activation_token

            return {
                "can_send": token.can_send_new_code(),
                "is_locked": token.is_locked,
                "attempts": token.attempts,
                "send_count": token.send_count,
                "last_sent": token.last_sent_at,
                "expires_at": token.expires_at,
            }
        except (User.DoesNotExist, ActivationToken.DoesNotExist):
            return {
                "can_send": True,
                "is_locked": False,
                "attempts": 0,
                "send_count": 0,
                "last_sent": None,
                "expires_at": None,
            }
