"""
Gateways SMS pour WaterBill API.

Ce module définit l'interface et les implémentations
pour l'envoi de SMS d'activation.
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Union

logger = logging.getLogger(__name__)


class ISmsGateway(ABC):
    """
    Interface abstraite pour l'envoi de SMS.

    Définit le contrat que doivent respecter toutes les implémentations
    de gateways SMS (Twilio, etc.).
    """

    @abstractmethod
    def send_activation_code(self, phone: str, code: str) -> bool:
        """
        Envoie un code d'activation par SMS.

        Args:
            phone: Numéro de téléphone de destination
            code: Code d'activation à envoyer

        Returns:
            bool: True si l'envoi a réussi, False sinon

        Raises:
            Exception: En cas d'erreur d'envoi
        """
        pass

    @abstractmethod
    def send_verification_code(
        self, phone: str, code: str, operation_type: str, redirect_url: str = None
    ) -> bool:
        """
        Envoie un code de vérification par SMS pour une opération spécifique.

        Args:
            phone: Numéro de téléphone de destination
            code: Code de vérification à envoyer
            operation_type: Type d'opération (password_reset, password_change, phone_change)
            redirect_url: URL de redirection avec token (optionnel)

        Returns:
            bool: True si l'envoi a réussi, False sinon

        Raises:
            Exception: En cas d'erreur d'envoi
        """
        pass

    @abstractmethod
    def send_confirmation_message(
        self, phone: str, operation_type: str, details: str = None
    ) -> bool:
        """
        Envoie un SMS de confirmation après une opération réussie.

        Args:
            phone: Numéro de téléphone de destination
            operation_type: Type d'opération effectuée
            details: Détails supplémentaires (optionnel)

        Returns:
            bool: True si l'envoi a réussi, False sinon

        Raises:
            Exception: En cas d'erreur d'envoi
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Vérifie si le gateway SMS est disponible.

        Returns:
            bool: True si disponible, False sinon
        """
        pass


class DummySmsGateway(ISmsGateway):
    """
    Implémentation mock du gateway SMS pour le développement.

    En mode développement, les SMS sont loggés au lieu d'être envoyés.
    """

    def send_activation_code(self, phone: str, code: str) -> bool:
        """
        Simule l'envoi d'un SMS d'activation.

        Args:
            phone: Numéro de téléphone de destination
            code: Code d'activation à envoyer

        Returns:
            bool: True (simulation d'envoi réussi)
        """
        logger.info(f"📱 SMS SIMULÉ - Code d'activation pour {phone}: {code}")
        print(f"🔐 Code d'activation pour {phone}: {code}")
        return True

    def send_verification_code(
        self, phone: str, code: str, operation_type: str, redirect_url: str = None
    ) -> bool:
        """
        Simule l'envoi d'un SMS de vérification.

        Args:
            phone: Numéro de téléphone de destination
            code: Code de vérification à envoyer
            operation_type: Type d'opération
            redirect_url: URL de redirection avec token (optionnel)

        Returns:
            bool: True (simulation d'envoi réussi)
        """
        messages = {
            "password_reset": "réinitialisation de mot de passe",
            "password_change": "changement de mot de passe",
            "phone_change": "changement de numéro de téléphone",
        }

        operation_name = messages.get(operation_type, operation_type)

        if redirect_url:
            logger.info(
                f"📱 SMS SIMULÉ - Code de vérification pour {operation_name} - {phone}: {code}"
            )
            logger.info(f"🔗 Lien de redirection: {redirect_url}")
            print(f"🔐 Code de vérification pour {operation_name} - {phone}: {code}")
            print(f"🔗 Lien: {redirect_url}")
        else:
            logger.info(
                f"📱 SMS SIMULÉ - Code de vérification pour {operation_name} - {phone}: {code}"
            )
            print(f"🔐 Code de vérification pour {operation_name} - {phone}: {code}")

        return True

    def send_confirmation_message(
        self, phone: str, operation_type: str, details: str = None
    ) -> bool:
        """
        Simule l'envoi d'un SMS de confirmation.

        Args:
            phone: Numéro de téléphone de destination
            operation_type: Type d'opération effectuée
            details: Détails supplémentaires (optionnel)

        Returns:
            bool: True (simulation d'envoi réussi)
        """
        messages = {
            "password_reset": "Votre mot de passe a été réinitialisé avec succès.",
            "password_change": "Votre mot de passe a été changé avec succès.",
            "phone_change": "Votre numéro de téléphone a été changé avec succès.",
        }

        message = messages.get(operation_type, f"Opération {operation_type} confirmée.")

        if details:
            message += f" {details}"

        logger.info(f"📱 SMS SIMULÉ - Confirmation - {phone}: {message}")
        print(f"✅ Confirmation - {phone}: {message}")
        return True

    def is_available(self) -> bool:
        """
        Vérifie si le gateway est disponible.

        Returns:
            bool: True (toujours disponible en mode développement)
        """
        return True


class TwilioSmsGateway(ISmsGateway):
    """
    Implémentation Twilio pour l'envoi de SMS réels.

    Cette implémentation nécessite la configuration Twilio
    dans les variables d'environnement.
    """

    def __init__(self):
        """
        Initialise le gateway Twilio.

        Raises:
            ImportError: Si twilio n'est pas installé
            ValueError: Si les credentials ne sont pas configurés
        """
        try:
            from twilio.rest import Client
        except ImportError:
            raise ImportError(
                "Twilio n'est pas installé. Installez avec: pip install twilio"
            )

        # Configuration depuis les variables d'environnement
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_number = os.getenv("TWILIO_FROM_NUMBER")

        print(f"account_sid: {account_sid}")
        print(f"auth_token: {auth_token}")
        print(f"from_number: {from_number}")

        if not all([account_sid, auth_token, from_number]):
            raise ValueError(
                "Variables d'environnement Twilio manquantes: "
                "TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER"
            )

        self.client = Client(account_sid, auth_token)
        self.from_number = from_number

    def send_activation_code(self, phone: str, code: str) -> bool:
        """
        Envoie un code d'activation via Twilio.

        Args:
            phone: Numéro de téléphone de destination
            code: Code d'activation à envoyer

        Returns:
            bool: True si l'envoi a réussi

        Raises:
            Exception: En cas d'erreur Twilio
        """
        try:
            message = (
                f"Votre code d'activation WaterBill est: {code}. "
                f"Ce code expire dans 10 minutes. Ne partagez pas ce code."
            )

            message = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=phone,
            )

            logger.info(
                f"SMS envoyé via Twilio - SID: {message.sid}, Destinataire: {phone}"
            )
            return True

        except Exception as e:
            logger.error(f"Erreur envoi SMS Twilio pour {phone}: {str(e)}")
            raise

    def send_verification_code(
        self, phone: str, code: str, operation_type: str, redirect_url: str = None
    ) -> bool:
        """
        Envoie un code de vérification via Twilio.

        Args:
            phone: Numéro de téléphone de destination
            code: Code de vérification à envoyer
            operation_type: Type d'opération
            redirect_url: URL de redirection avec token (optionnel)

        Returns:
            bool: True si l'envoi a réussi

        Raises:
            Exception: En cas d'erreur Twilio
        """
        try:
            messages = {
                "password_reset": "réinitialisation de mot de passe",
                "password_change": "changement de mot de passe",
                "phone_change": "changement de numéro de téléphone",
            }

            operation_name = messages.get(operation_type, operation_type)

            if redirect_url:
                message = (
                    f"Votre code de vérification pour {operation_name} WaterBill est: {code}. "
                    f"Lien de redirection: {redirect_url}. "
                    f"Ce code expire dans 10 minutes. Ne partagez pas ce code."
                )
            else:
                message = (
                    f"Votre code de vérification pour {operation_name} WaterBill est: {code}. "
                    f"Ce code expire dans 10 minutes. Ne partagez pas ce code."
                )

            message = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=phone,
            )

            logger.info(
                f"SMS de vérification envoyé via Twilio - SID: {message.sid}, "
                f"Destinataire: {phone}, Opération: {operation_type}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Erreur envoi SMS de vérification Twilio pour {phone}: {str(e)}"
            )
            raise

    def send_confirmation_message(
        self, phone: str, operation_type: str, details: str = None
    ) -> bool:
        """
        Envoie un SMS de confirmation via Twilio.

        Args:
            phone: Numéro de téléphone de destination
            operation_type: Type d'opération effectuée
            details: Détails supplémentaires (optionnel)

        Returns:
            bool: True si l'envoi a réussi

        Raises:
            Exception: En cas d'erreur Twilio
        """
        try:
            messages = {
                "password_reset": "Votre mot de passe a été réinitialisé avec succès.",
                "password_change": "Votre mot de passe a été changé avec succès.",
                "phone_change": "Votre numéro de téléphone a été changé avec succès.",
            }

            message = messages.get(
                operation_type, f"Opération {operation_type} confirmée."
            )

            if details:
                message += f" {details}"

            # Ajouter un message de sécurité
            message += (
                " Si vous n'avez pas effectué cette action, contactez le support."
            )

            message = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=phone,
            )

            logger.info(
                f"SMS de confirmation envoyé via Twilio - SID: {message.sid}, "
                f"Destinataire: {phone}, Opération: {operation_type}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Erreur envoi SMS de confirmation Twilio pour {phone}: {str(e)}"
            )
            raise

    def is_available(self) -> bool:
        """
        Vérifie si Twilio est disponible.

        Returns:
            bool: True si les credentials sont configurés
        """
        try:
            # Test simple de connexion
            self.client.api.accounts(self.client.auth[0]).fetch()
            return True
        except Exception:
            return False


def clean_token(token: Union[str, None]) -> Union[str, None]:
    """
    Nettoie un token UUID des caractères invisibles et espaces.

    Args:
        token: Token UUID potentiellement pollué

    Returns:
        str | None: Token nettoyé et prêt à l'utilisation
    """
    if not token:
        return token

    # Supprimer les caractères invisibles Unicode courants
    invisible_chars = [
        "\u2060",  # WORD JOINER
        "\u200B",  # ZERO WIDTH SPACE
        "\u200C",  # ZERO WIDTH NON-JOINER
        "\u200D",  # ZERO WIDTH JOINER
        "\uFEFF",  # ZERO WIDTH NO-BREAK SPACE (BOM)
        " ",  # SPACE normal
        "\t",  # TAB
        "\n",  # NEWLINE
        "\r",  # CARRIAGE RETURN
    ]

    cleaned_token = str(token)
    for char in invisible_chars:
        cleaned_token = cleaned_token.replace(char, "")

    return cleaned_token


def generate_redirect_url(token: str, operation_type: str, base_url: str = None) -> str:
    """
    Génère une URL de redirection avec token nettoyé pour les opérations de sécurité.

    Args:
        token: Token UUID de l'opération (sera automatiquement nettoyé)
        operation_type: Type d'opération (password_reset, password_change, phone_change)
        base_url: URL de base de l'application (optionnel)

    Returns:
        str: URL de redirection complète avec token nettoyé
    """
    # Nettoyer le token automatiquement
    clean_token_value = clean_token(token)

    if not base_url:
        from django.conf import settings

        # Utiliser l'URL de base depuis les settings ou une valeur par défaut
        base_url = getattr(settings, "FRONTEND_URL", "https://waterbill.app")

    endpoints = {
        "password_reset": "/reset-password",
        "password_change": "/change-password",
        "phone_change": "/change-phone",
    }

    endpoint = endpoints.get(operation_type, "/verify")
    return f"{base_url}{endpoint}?token={clean_token_value}"


def get_sms_gateway() -> ISmsGateway:
    """
    Factory function pour obtenir le gateway SMS approprié.

    Retourne DummySmsGateway en développement et TwilioSmsGateway
    en production selon la configuration.

    Returns:
        ISmsGateway: Instance du gateway SMS
    """
    from django.conf import settings

    # En mode développement ou si Twilio n'est pas configuré
    if settings.DEBUG or not all(
        [
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN"),
            os.getenv("TWILIO_FROM_NUMBER"),
        ]
    ):
        return DummySmsGateway()

    # En production avec Twilio configuré
    try:
        return TwilioSmsGateway()
    except (ImportError, ValueError) as e:
        logger.warning(f"Twilio non disponible, utilisation du dummy: {e}")
        return DummySmsGateway()
