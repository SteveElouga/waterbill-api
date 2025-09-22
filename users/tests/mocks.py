"""
Mocks pour les tests unitaires de WaterBill API.

Ce module fournit des mocks pour tous les services externes
utilisés dans l'application (SMS, etc.).
"""

from unittest.mock import patch


class MockSmsGateway:
    """
    Mock pour le gateway SMS.

    Simule l'envoi de SMS sans faire d'appels réels à Twilio.
    """

    def __init__(self, should_succeed: bool = True, error_message: str = None):
        """
        Initialise le mock SMS gateway.

        Args:
            should_succeed: Si True, simule un envoi réussi
            error_message: Message d'erreur à retourner si should_succeed=False
        """
        self.should_succeed = should_succeed
        self.error_message = error_message
        self.sent_messages = []  # Pour vérifier les messages envoyés

    def send_activation_code(self, phone: str, code: str) -> bool:
        """
        Simule l'envoi d'un code d'activation par SMS.

        Args:
            phone: Numéro de téléphone de destination
            code: Code d'activation à envoyer

        Returns:
            bool: True si l'envoi a réussi, False sinon
        """
        # Enregistrer le message envoyé pour les tests
        self.sent_messages.append(
            {
                "phone": phone,
                "code": code,
                "timestamp": None,  # Peut être ajouté si nécessaire
            }
        )

        if not self.should_succeed:
            if self.error_message:
                raise ValueError(self.error_message)
            return False

        return True

    def is_available(self) -> bool:
        """
        Simule la disponibilité du service SMS.

        Returns:
            bool: True si disponible, False sinon
        """
        return self.should_succeed


def patch_sms_gateway(should_succeed: bool = True, error_message: str = None):
    """
    Décorateur pour patcher le gateway SMS dans les tests.

    Args:
        should_succeed: Si True, simule un envoi réussi
        error_message: Message d'erreur à retourner si should_succeed=False

    Returns:
        Decorator function
    """

    def decorator(test_func):
        def wrapper(*args, **kwargs):
            mock_gateway = MockSmsGateway(should_succeed, error_message)

            with patch("users.gateways.sms.get_sms_gateway", return_value=mock_gateway):
                # Passer le mock au test pour vérifications
                return test_func(*args, **kwargs, mock_gateway=mock_gateway)

        return wrapper

    return decorator


def patch_twilio_gateway(should_succeed: bool = True, error_message: str = None):
    """
    Décorateur pour patcher spécifiquement le gateway Twilio.

    Args:
        should_succeed: Si True, simule un envoi réussi
        error_message: Message d'erreur à retourner si should_succeed=False

    Returns:
        Decorator function
    """

    def decorator(test_func):
        def wrapper(*args, **kwargs):
            mock_gateway = MockSmsGateway(should_succeed, error_message)

            with patch("users.gateways.sms.TwilioSmsGateway") as mock_twilio:
                mock_twilio.return_value = mock_gateway
                with patch("users.services.get_sms_gateway", return_value=mock_gateway):
                    return test_func(*args, **kwargs, mock_gateway=mock_gateway)

        return wrapper

    return decorator


class MockServices:
    """
    Classe utilitaire pour mocker plusieurs services à la fois.
    """

    @staticmethod
    def patch_all_external_services():
        """
        Patch tous les services externes utilisés dans les tests.

        Returns:
            Context manager
        """
        from contextlib import contextmanager

        @contextmanager
        def patcher():
            mock_sms = MockSmsGateway(should_succeed=True)

            with patch(
                "users.gateways.sms.get_sms_gateway", return_value=mock_sms
            ), patch("users.services.get_sms_gateway", return_value=mock_sms), patch(
                "users.gateways.sms.TwilioSmsGateway"
            ) as mock_twilio:

                mock_twilio.return_value = mock_sms
                yield mock_sms

        return patcher()
