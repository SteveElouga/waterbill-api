"""
Gateways SMS pour WaterBill API.

Ce module définit l'interface et les implémentations
pour l'envoi de SMS d'activation.
"""

import logging
import os
from abc import ABC, abstractmethod

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
