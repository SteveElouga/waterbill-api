"""
Configuration globale des mocks pour les tests WaterBill.

Ce fichier configure automatiquement les mocks pour tous les tests
afin d'éviter les appels réels aux services externes (Twilio, etc.).
"""

import pytest
from unittest.mock import patch
from users.tests.mocks import MockSmsGateway

# Constantes pour les chemins de patch
SMS_GATEWAY_PATH = "users.gateways.sms.get_sms_gateway"
SMS_SERVICES_PATH = "users.services.get_sms_gateway"
TWILIO_SMS_GATEWAY_PATH = "users.gateways.sms.TwilioSmsGateway"


@pytest.fixture(autouse=True)
def mock_external_services():
    """
    Fixture automatique qui mock tous les services externes.

    Cette fixture s'applique automatiquement à tous les tests
    pour éviter les appels réels à Twilio, etc.
    """
    mock_sms = MockSmsGateway(should_succeed=True)

    with patch(SMS_GATEWAY_PATH, return_value=mock_sms), patch(
        SMS_SERVICES_PATH, return_value=mock_sms
    ), patch(TWILIO_SMS_GATEWAY_PATH) as mock_twilio:

        mock_twilio.return_value = mock_sms
        yield mock_sms


@pytest.fixture
def mock_sms_failure():
    """
    Fixture pour simuler des échecs SMS dans les tests spécifiques.
    """
    mock_sms = MockSmsGateway(
        should_succeed=False, error_message="Service SMS indisponible"
    )

    with patch(SMS_GATEWAY_PATH, return_value=mock_sms), patch(
        SMS_SERVICES_PATH, return_value=mock_sms
    ), patch(TWILIO_SMS_GATEWAY_PATH) as mock_twilio:

        mock_twilio.return_value = mock_sms
        yield mock_sms


@pytest.fixture
def mock_sms_unavailable():
    """
    Fixture pour simuler un service SMS indisponible.
    """
    mock_sms = MockSmsGateway(
        should_succeed=False, error_message="Service SMS temporairement indisponible"
    )

    with patch(SMS_GATEWAY_PATH, return_value=mock_sms), patch(
        SMS_SERVICES_PATH, return_value=mock_sms
    ), patch(TWILIO_SMS_GATEWAY_PATH) as mock_twilio:

        mock_twilio.return_value = mock_sms
        yield mock_sms
