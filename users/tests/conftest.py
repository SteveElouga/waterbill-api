"""
Configuration globale des mocks pour les tests WaterBill.

Ce fichier configure automatiquement les mocks pour tous les tests
afin d'éviter les appels réels aux services externes (Twilio, etc.).
"""

import pytest
from unittest.mock import patch
from users.tests.mocks import MockSmsGateway


@pytest.fixture(autouse=True)
def mock_external_services():
    """
    Fixture automatique qui mock tous les services externes.

    Cette fixture s'applique automatiquement à tous les tests
    pour éviter les appels réels à Twilio, etc.
    """
    mock_sms = MockSmsGateway(should_succeed=True)

    with patch("users.gateways.sms.get_sms_gateway", return_value=mock_sms), \
            patch("users.services.get_sms_gateway", return_value=mock_sms), \
            patch("users.gateways.sms.TwilioSmsGateway") as mock_twilio:

        mock_twilio.return_value = mock_sms
        yield mock_sms


@pytest.fixture
def mock_sms_failure():
    """
    Fixture pour simuler des échecs SMS dans les tests spécifiques.
    """
    mock_sms = MockSmsGateway(should_succeed=False,
                              error_message="Service SMS indisponible")

    with patch("users.gateways.sms.get_sms_gateway", return_value=mock_sms), \
            patch("users.services.get_sms_gateway", return_value=mock_sms), \
            patch("users.gateways.sms.TwilioSmsGateway") as mock_twilio:

        mock_twilio.return_value = mock_sms
        yield mock_sms


@pytest.fixture
def mock_sms_unavailable():
    """
    Fixture pour simuler un service SMS indisponible.
    """
    mock_sms = MockSmsGateway(
        should_succeed=False, error_message="Service SMS temporairement indisponible")

    with patch("users.gateways.sms.get_sms_gateway", return_value=mock_sms), \
            patch("users.services.get_sms_gateway", return_value=mock_sms), \
            patch("users.gateways.sms.TwilioSmsGateway") as mock_twilio:

        mock_twilio.return_value = mock_sms
        yield mock_sms
