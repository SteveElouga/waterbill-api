"""
Tests pour la réinitialisation de mot de passe.

Ce module teste les fonctionnalités de réinitialisation de mot de passe
via SMS avec le nouveau modèle VerificationToken.
"""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock

from users.models import User, VerificationToken
from users.tests.test_settings import MockedAPITestCase


class PasswordResetTestCase(MockedAPITestCase):
    """
    Tests pour la réinitialisation de mot de passe.
    """

    def setUp(self):
        super().setUp()
        self.client = APIClient()

        # Créer un utilisateur de test
        self.user = User.objects.create_user(
            phone="+237670000000",
            first_name="Test",
            last_name="User",
            password="oldpassword123",
        )
        self.user.is_active = True
        self.user.save()

        # Données de test
        self.forgot_data = {"phone": "+237670000000"}

        self.reset_data = {
            "token": "",
            "code": "123456",
            "new_password": "newpassword123",
            "new_password_confirm": "newpassword123",
        }

    def test_password_forgot_success(self):
        """Test de demande de réinitialisation réussie."""
        url = reverse("users:password_forgot")

        with patch(
            "users.services.PasswordResetService.request_password_reset"
        ) as mock_service:
            mock_service.return_value = {
                "success": True,
                "message": "Un code de réinitialisation a été envoyé par SMS.",
            }

            response = self.client.post(url, self.forgot_data, format="json")

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["status"], "success")
            self.assertIn("réinitialisation", response.data["message"])
            mock_service.assert_called_once_with("+237670000000")

    def test_password_forgot_user_not_exists(self):
        """Test de demande de réinitialisation pour utilisateur inexistant."""
        url = reverse("users:password_forgot")

        # Utiliser un numéro qui n'existe pas
        data = {"phone": "+237999999999"}

        with patch(
            "users.services.PasswordResetService.request_password_reset"
        ) as mock_service:
            mock_service.return_value = {
                "success": True,
                "message": "Si ce numéro est associé à un compte, vous recevrez un SMS.",
            }

            response = self.client.post(url, data, format="json")

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["status"], "success")
            mock_service.assert_called_once_with("+237999999999")

    def test_password_forgot_invalid_phone(self):
        """Test de demande de réinitialisation avec numéro invalide."""
        url = reverse("users:password_forgot")

        data = {"phone": "123"}  # Numéro trop court

        response = self.client.post(url, data, format="json")

        # Le service retourne toujours un succès pour des raisons de sécurité
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertIn("Si ce numéro est associé", response.data["message"])

    def test_password_forgot_missing_phone(self):
        """Test de demande de réinitialisation sans numéro."""
        url = reverse("users:password_forgot")

        data = {}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")

    def test_password_reset_confirm_success(self):
        """Test de confirmation de réinitialisation réussie."""
        # Créer un token de test
        token = VerificationToken.create_token(
            verification_type="password_reset", user=self.user
        )

        url = reverse("users:password_reset_confirm")

        self.reset_data["token"] = str(token.token)

        with patch(
            "users.services.PasswordResetService.confirm_password_reset"
        ) as mock_service:
            mock_service.return_value = {
                "success": True,
                "message": "Votre mot de passe a été réinitialisé avec succès.",
            }

            response = self.client.post(url, self.reset_data, format="json")

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["status"], "success")
            # Vérifier que le service a été appelé avec les bons paramètres
            call_args = mock_service.call_args[0]
            self.assertEqual(str(call_args[0]), str(token.token))
            self.assertEqual(call_args[1], "123456")
            self.assertEqual(call_args[2], "newpassword123")

    def test_password_reset_confirm_invalid_token(self):
        """Test de confirmation avec token invalide."""
        url = reverse("users:password_reset_confirm")

        self.reset_data["token"] = "00000000-0000-0000-0000-000000000000"

        with patch(
            "users.services.PasswordResetService.confirm_password_reset"
        ) as mock_service:
            mock_service.side_effect = ValueError(
                "Token de réinitialisation invalide ou expiré"
            )

            response = self.client.post(url, self.reset_data, format="json")

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data["status"], "error")
            self.assertIn("invalide", response.data["data"]["detail"])

    def test_password_reset_confirm_invalid_code(self):
        """Test de confirmation avec code invalide."""
        # Créer un token de test
        token = VerificationToken.create_token(
            verification_type="password_reset", user=self.user
        )

        url = reverse("users:password_reset_confirm")

        self.reset_data["token"] = str(token.token)
        self.reset_data["code"] = "000000"  # Code incorrect

        with patch(
            "users.services.PasswordResetService.confirm_password_reset"
        ) as mock_service:
            mock_service.side_effect = ValueError(
                "Code de vérification incorrect ou expiré"
            )

            response = self.client.post(url, self.reset_data, format="json")

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data["status"], "error")
            self.assertIn("incorrect", response.data["data"]["detail"])

    def test_password_reset_confirm_password_mismatch(self):
        """Test de confirmation avec mots de passe différents."""
        url = reverse("users:password_reset_confirm")

        data = {
            "token": "00000000-0000-0000-0000-000000000000",
            "code": "123456",
            "new_password": "newpassword123",
            "new_password_confirm": "differentpassword123",
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")
        self.assertIn("correspondent pas", str(response.data["data"]))

    def test_password_reset_confirm_weak_password(self):
        """Test de confirmation avec mot de passe faible."""
        url = reverse("users:password_reset_confirm")

        data = {
            "token": "00000000-0000-0000-0000-000000000000",
            "code": "123456",
            "new_password": "123",  # Mot de passe trop court
            "new_password_confirm": "123",
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")

    def test_password_reset_confirm_missing_fields(self):
        """Test de confirmation avec champs manquants."""
        url = reverse("users:password_reset_confirm")

        data = {
            "token": "00000000-0000-0000-0000-000000000000"
            # Manque code, new_password, new_password_confirm
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")

    def test_password_reset_confirm_invalid_code_format(self):
        """Test de confirmation avec format de code invalide."""
        url = reverse("users:password_reset_confirm")

        data = {
            "token": "00000000-0000-0000-0000-000000000000",
            "code": "12345",  # Code trop court
            "new_password": "newpassword123",
            "new_password_confirm": "newpassword123",
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")
        self.assertIn("6", str(response.data["data"]))

    def test_password_reset_confirm_invalid_token_format(self):
        """Test de confirmation avec format de token invalide."""
        url = reverse("users:password_reset_confirm")

        data = {
            "token": "invalid-uuid",
            "code": "123456",
            "new_password": "newpassword123",
            "new_password_confirm": "newpassword123",
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")


class PasswordResetServiceTestCase(MockedAPITestCase):
    """
    Tests pour le service de réinitialisation de mot de passe.
    """

    def setUp(self):
        super().setUp()

        # Créer un utilisateur de test
        self.user = User.objects.create_user(
            phone="+237670000000",
            first_name="Test",
            last_name="User",
            password="oldpassword123",
        )
        self.user.is_active = True
        self.user.save()

    def test_request_password_reset_existing_user(self):
        """Test de demande de réinitialisation pour utilisateur existant."""
        from users.services import PasswordResetService

        with patch("users.services.get_sms_gateway") as mock_gateway:
            mock_sms = MagicMock()
            mock_sms.send_activation_code.return_value = True
            mock_gateway.return_value = mock_sms

            result = PasswordResetService.request_password_reset("+237670000000")

            self.assertTrue(result["success"])
            self.assertIn("réinitialisation", result["message"])
            self.assertIn("token", result)

            # Vérifier qu'un token a été créé
            token = VerificationToken.objects.get(
                verification_type="password_reset", user=self.user
            )
            self.assertIsNotNone(token)
            mock_sms.send_activation_code.assert_called_once()
            # Vérifier que le premier argument est le numéro de téléphone
            call_args = mock_sms.send_activation_code.call_args[0]
            self.assertEqual(call_args[0], "+237670000000")

    def test_request_password_reset_nonexistent_user(self):
        """Test de demande de réinitialisation pour utilisateur inexistant."""
        from users.services import PasswordResetService

        result = PasswordResetService.request_password_reset("+237999999999")

        self.assertTrue(result["success"])
        self.assertIn("Si ce numéro est associé", result["message"])
        self.assertNotIn("token", result)

    def test_confirm_password_reset_success(self):
        """Test de confirmation de réinitialisation réussie."""
        from users.services import PasswordResetService

        # Créer un token de test
        token = VerificationToken.create_token(
            verification_type="password_reset", user=self.user
        )

        # Simuler un code correct en mockant la méthode verify_code
        with patch.object(VerificationToken, "verify_code", return_value=True):
            result = PasswordResetService.confirm_password_reset(
                str(token.token), "123456", "newpassword123"
            )

            self.assertTrue(result["success"])
            self.assertIn("réinitialisé", result["message"])

            # Vérifier que le mot de passe a été changé
            self.user.refresh_from_db()
            self.assertTrue(self.user.check_password("newpassword123"))

            # Vérifier que le token a été marqué comme utilisé
            token.refresh_from_db()
            self.assertTrue(token.is_used)

    def test_confirm_password_reset_invalid_token(self):
        """Test de confirmation avec token invalide."""
        from users.services import PasswordResetService

        with self.assertRaises(ValueError) as context:
            PasswordResetService.confirm_password_reset(
                "00000000-0000-0000-0000-000000000000", "123456", "newpassword123"
            )

        self.assertIn("invalide", str(context.exception))

    def test_confirm_password_reset_invalid_code(self):
        """Test de confirmation avec code invalide."""
        from users.services import PasswordResetService

        # Créer un token de test
        token = VerificationToken.create_token(
            verification_type="password_reset", user=self.user
        )

        # Simuler un code incorrect en mockant la méthode verify_code
        with patch.object(VerificationToken, "verify_code", return_value=False):
            with self.assertRaises(ValueError) as context:
                PasswordResetService.confirm_password_reset(
                    str(token.token), "000000", "newpassword123"
                )

            self.assertIn("incorrect", str(context.exception))
