"""
Tests pour le système de mocks de WaterBill.

Ce module teste toutes les fonctionnalités du système de mocks
utilisé pour isoler les tests des services externes.
"""

import pytest
from users.tests.mocks import (
    MockSmsGateway,
    patch_sms_gateway,
    patch_twilio_gateway,
    MockServices,
)


class TestMockSmsGateway:
    """Tests pour MockSmsGateway."""

    def test_mock_sms_gateway_init_success(self):
        """Test initialisation avec succès par défaut."""
        mock = MockSmsGateway()
        assert mock.should_succeed is True
        assert mock.error_message is None
        assert mock.sent_messages == []

    def test_mock_sms_gateway_init_with_error(self):
        """Test initialisation avec configuration d'erreur."""
        error_msg = "Service indisponible"
        mock = MockSmsGateway(should_succeed=False, error_message=error_msg)
        assert mock.should_succeed is False
        assert mock.error_message == error_msg
        assert mock.sent_messages == []

    def test_send_activation_code_success(self):
        """Test envoi réussi de code d'activation."""
        mock = MockSmsGateway(should_succeed=True)

        result = mock.send_activation_code("+237658552294", "123456")

        assert result is True
        assert len(mock.sent_messages) == 1
        assert mock.sent_messages[0]["phone"] == "+237658552294"
        assert mock.sent_messages[0]["code"] == "123456"
        assert mock.sent_messages[0]["timestamp"] is None

    def test_send_activation_code_failure_with_exception(self):
        """Test échec avec exception."""
        error_msg = "Erreur réseau"
        mock = MockSmsGateway(should_succeed=False, error_message=error_msg)

        with pytest.raises(Exception, match=error_msg):
            mock.send_activation_code("+237658552294", "123456")

        # Le message doit quand même être enregistré
        assert len(mock.sent_messages) == 1

    def test_send_activation_code_failure_without_exception(self):
        """Test échec sans exception."""
        mock = MockSmsGateway(should_succeed=False, error_message=None)

        result = mock.send_activation_code("+237658552294", "123456")

        assert result is False
        assert len(mock.sent_messages) == 1

    def test_is_available_success(self):
        """Test disponibilité avec succès."""
        mock = MockSmsGateway(should_succeed=True)
        assert mock.is_available() is True

    def test_is_available_failure(self):
        """Test indisponibilité."""
        mock = MockSmsGateway(should_succeed=False)
        assert mock.is_available() is False

    def test_multiple_messages(self):
        """Test envoi de plusieurs messages."""
        mock = MockSmsGateway()

        mock.send_activation_code("+237658552294", "111111")
        mock.send_activation_code("+237658552295", "222222")

        assert len(mock.sent_messages) == 2
        assert mock.sent_messages[0]["code"] == "111111"
        assert mock.sent_messages[1]["code"] == "222222"

    def test_empty_phone_number(self):
        """Test avec numéro de téléphone vide."""
        mock = MockSmsGateway()
        result = mock.send_activation_code("", "123456")
        assert result is True
        assert len(mock.sent_messages) == 1
        assert mock.sent_messages[0]["phone"] == ""

    def test_empty_code(self):
        """Test avec code vide."""
        mock = MockSmsGateway()
        result = mock.send_activation_code("+237658552294", "")
        assert result is True
        assert len(mock.sent_messages) == 1
        assert mock.sent_messages[0]["code"] == ""

    def test_none_values(self):
        """Test avec valeurs None."""
        mock = MockSmsGateway()
        # Convertir None en string pour respecter le type attendu
        result = mock.send_activation_code(str(None), str(None))
        assert result is True
        assert len(mock.sent_messages) == 1
        assert mock.sent_messages[0]["phone"] == "None"
        assert mock.sent_messages[0]["code"] == "None"

    def test_special_characters_in_phone(self):
        """Test avec caractères spéciaux dans le numéro."""
        mock = MockSmsGateway()
        special_phone = "+237-658-552-294"
        result = mock.send_activation_code(special_phone, "123456")
        assert result is True
        assert len(mock.sent_messages) == 1
        assert mock.sent_messages[0]["phone"] == special_phone

    def test_long_code(self):
        """Test avec code très long."""
        mock = MockSmsGateway()
        long_code = "12345678901234567890"
        result = mock.send_activation_code("+237658552294", long_code)
        assert result is True
        assert len(mock.sent_messages) == 1
        assert mock.sent_messages[0]["code"] == long_code


class TestPatchSmsGateway:
    """Tests pour le décorateur patch_sms_gateway."""

    def test_patch_sms_gateway_decorator_success(self):
        """Test du décorateur avec succès."""

        @patch_sms_gateway(should_succeed=True)
        def test_function(mock_gateway):
            result = mock_gateway.send_activation_code("+237658552294", "123456")
            assert result is True
            return "success"

        result = test_function()
        assert result == "success"

    def test_patch_sms_gateway_decorator_failure(self):
        """Test du décorateur avec échec."""

        @patch_sms_gateway(should_succeed=False, error_message="Service indisponible")
        def test_function(mock_gateway):
            with pytest.raises(Exception, match="Service indisponible"):
                mock_gateway.send_activation_code("+237658552294", "123456")
            return "failure"

        result = test_function()
        assert result == "failure"


class TestPatchTwilioGateway:
    """Tests pour le décorateur patch_twilio_gateway."""

    def test_patch_twilio_gateway_decorator(self):
        """Test du décorateur Twilio."""

        @patch_twilio_gateway(should_succeed=True)
        def test_function(mock_gateway):
            result = mock_gateway.send_activation_code("+237658552294", "123456")
            assert result is True
            return "success"

        result = test_function()
        assert result == "success"


class TestMockServices:
    """Tests pour MockServices."""

    def test_patch_all_external_services_context_manager(self):
        """Test du context manager patch_all_external_services."""
        with MockServices.patch_all_external_services() as mock_sms:
            assert isinstance(mock_sms, MockSmsGateway)
            assert mock_sms.should_succeed is True

            # Tester que le mock fonctionne
            result = mock_sms.send_activation_code("+237658552294", "123456")
            assert result is True
            assert len(mock_sms.sent_messages) == 1

    def test_patch_all_external_services_isolation(self):
        """Test que chaque utilisation est isolée."""
        # Premier contexte
        with MockServices.patch_all_external_services() as mock1:
            mock1.send_activation_code("+237658552294", "111111")
            assert len(mock1.sent_messages) == 1

        # Deuxième contexte (isolé)
        with MockServices.patch_all_external_services() as mock2:
            mock2.send_activation_code("+237658552295", "222222")
            assert len(mock2.sent_messages) == 1
            # Le mock2 ne doit pas voir les messages du mock1
            assert mock2.sent_messages[0]["phone"] == "+237658552295"
