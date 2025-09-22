"""
Tests pour le changement de mot de passe.

Ce module teste les fonctionnalités de changement de mot de passe
pour utilisateurs authentifiés via SMS.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch, MagicMock

from users.models import User, VerificationToken
from users.tests.test_settings import MockedAPITestCase


class PasswordChangeTestCase(MockedAPITestCase):
    """
    Tests pour le changement de mot de passe.
    """

    def setUp(self):
        super().setUp()
        self.client = APIClient()

        # Créer un utilisateur de test
        self.user = User.objects.create_user(
            phone="+237670000000",
            first_name="Test",
            last_name="User",
            password="oldpassword123"
        )
        self.user.is_active = True
        self.user.save()

        # Obtenir un token JWT pour l'authentification
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        # Données de test
        self.request_data = {
            "current_password": "oldpassword123"
        }

        self.confirm_data = {
            "token": "",
            "code": "123456",
            "new_password": "newpassword123",
            "new_password_confirm": "newpassword123"
        }

    def test_password_change_request_success(self):
        """Test de demande de changement de mot de passe réussie."""
        url = reverse("users:password_change_request")

        # Authentifier la requête
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        with patch('users.services.PasswordChangeService.request_password_change') as mock_service:
            mock_service.return_value = {
                "success": True,
                "message": "Un code de vérification a été envoyé par SMS."
            }

            response = self.client.post(url, self.request_data, format="json")

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["status"], "success")
            self.assertIn("vérification", response.data["message"])
            mock_service.assert_called_once_with(self.user, "oldpassword123")

    def test_password_change_request_wrong_password(self):
        """Test de demande avec mauvais mot de passe actuel."""
        url = reverse("users:password_change_request")

        # Authentifier la requête
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        data = {"current_password": "wrongpassword"}

        with patch('users.services.PasswordChangeService.request_password_change') as mock_service:
            mock_service.side_effect = ValueError(
                "Le mot de passe actuel est incorrect")

            response = self.client.post(url, data, format="json")

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data["status"], "error")
            self.assertIn("incorrect", str(response.data["data"]))

    def test_password_change_request_unauthenticated(self):
        """Test de demande sans authentification."""
        url = reverse("users:password_change_request")

        response = self.client.post(url, self.request_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_password_change_request_missing_password(self):
        """Test de demande sans mot de passe actuel."""
        url = reverse("users:password_change_request")

        # Authentifier la requête
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        data = {}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")

    def test_password_change_confirm_success(self):
        """Test de confirmation de changement de mot de passe réussie."""
        # Créer un token de test
        token = VerificationToken.create_token(
            verification_type='password_change',
            user=self.user
        )

        url = reverse("users:password_change_confirm")

        self.confirm_data["token"] = str(token.token)

        with patch('users.services.PasswordChangeService.confirm_password_change') as mock_service:
            mock_service.return_value = {
                "success": True,
                "message": "Votre mot de passe a été changé avec succès."
            }

            response = self.client.post(url, self.confirm_data, format="json")

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["status"], "success")
            # Vérifier que le service a été appelé avec les bons paramètres
            call_args = mock_service.call_args[0]
            self.assertEqual(str(call_args[0]), str(token.token))
            self.assertEqual(call_args[1], "123456")
            self.assertEqual(call_args[2], "newpassword123")

    def test_password_change_confirm_invalid_token(self):
        """Test de confirmation avec token invalide."""
        url = reverse("users:password_change_confirm")

        self.confirm_data["token"] = "00000000-0000-0000-0000-000000000000"

        with patch('users.services.PasswordChangeService.confirm_password_change') as mock_service:
            mock_service.side_effect = ValueError(
                "Token de changement invalide ou expiré")

            response = self.client.post(url, self.confirm_data, format="json")

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data["status"], "error")
            self.assertIn("invalide", response.data["data"]["detail"])

    def test_password_change_confirm_invalid_code(self):
        """Test de confirmation avec code invalide."""
        # Créer un token de test
        token = VerificationToken.create_token(
            verification_type='password_change',
            user=self.user
        )

        url = reverse("users:password_change_confirm")

        self.confirm_data["token"] = str(token.token)
        self.confirm_data["code"] = "000000"  # Code incorrect

        with patch('users.services.PasswordChangeService.confirm_password_change') as mock_service:
            mock_service.side_effect = ValueError(
                "Code de vérification incorrect ou expiré")

            response = self.client.post(url, self.confirm_data, format="json")

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data["status"], "error")
            self.assertIn("incorrect", response.data["data"]["detail"])

    def test_password_change_confirm_password_mismatch(self):
        """Test de confirmation avec mots de passe différents."""
        url = reverse("users:password_change_confirm")

        data = {
            "token": "00000000-0000-0000-0000-000000000000",
            "code": "123456",
            "new_password": "newpassword123",
            "new_password_confirm": "differentpassword123"
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")
        self.assertIn("correspondent pas", str(response.data["data"]))

    def test_password_change_confirm_weak_password(self):
        """Test de confirmation avec mot de passe faible."""
        url = reverse("users:password_change_confirm")

        data = {
            "token": "00000000-0000-0000-0000-000000000000",
            "code": "123456",
            "new_password": "123",  # Mot de passe trop court
            "new_password_confirm": "123"
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")

    def test_password_change_confirm_missing_fields(self):
        """Test de confirmation avec champs manquants."""
        url = reverse("users:password_change_confirm")

        data = {
            "token": "00000000-0000-0000-0000-000000000000"
            # Manque code, new_password, new_password_confirm
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")

    def test_password_change_confirm_invalid_code_format(self):
        """Test de confirmation avec format de code invalide."""
        url = reverse("users:password_change_confirm")

        data = {
            "token": "00000000-0000-0000-0000-000000000000",
            "code": "12345",  # Code trop court
            "new_password": "newpassword123",
            "new_password_confirm": "newpassword123"
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")
        self.assertIn("6", str(response.data["data"]))


class PasswordChangeServiceTestCase(MockedAPITestCase):
    """
    Tests pour le service de changement de mot de passe.
    """

    def setUp(self):
        super().setUp()

        # Créer un utilisateur de test
        self.user = User.objects.create_user(
            phone="+237670000000",
            first_name="Test",
            last_name="User",
            password="oldpassword123"
        )
        self.user.is_active = True
        self.user.save()

    def test_request_password_change_success(self):
        """Test de demande de changement de mot de passe réussie."""
        from users.services import PasswordChangeService

        with patch('users.services.get_sms_gateway') as mock_gateway:
            mock_sms = MagicMock()
            mock_sms.send_activation_code.return_value = True
            mock_gateway.return_value = mock_sms

            result = PasswordChangeService.request_password_change(
                self.user, "oldpassword123"
            )

            self.assertTrue(result["success"])
            self.assertIn("vérification", result["message"])
            self.assertIn("token", result)

            # Vérifier qu'un token a été créé
            token = VerificationToken.objects.get(
                verification_type='password_change',
                user=self.user
            )
            self.assertIsNotNone(token)
            # Vérifier que le SMS a été envoyé
            mock_sms.send_activation_code.assert_called_once()
            # Vérifier que le premier argument est le numéro de téléphone
            call_args = mock_sms.send_activation_code.call_args[0]
            self.assertEqual(call_args[0], self.user.phone)

    def test_request_password_change_wrong_password(self):
        """Test de demande avec mauvais mot de passe actuel."""
        from users.services import PasswordChangeService

        with self.assertRaises(ValueError) as context:
            PasswordChangeService.request_password_change(
                self.user, "wrongpassword"
            )

        self.assertIn("incorrect", str(context.exception))

    def test_confirm_password_change_success(self):
        """Test de confirmation de changement de mot de passe réussie."""
        from users.services import PasswordChangeService

        # Créer un token de test
        token = VerificationToken.create_token(
            verification_type='password_change',
            user=self.user
        )

        # Simuler un code correct en mockant la méthode verify_code
        with patch.object(VerificationToken, 'verify_code', return_value=True):
            result = PasswordChangeService.confirm_password_change(
                str(token.token), "123456", "newpassword123"
            )

            self.assertTrue(result["success"])
            self.assertIn("changé", result["message"])

            # Vérifier que le mot de passe a été changé
            self.user.refresh_from_db()
            self.assertTrue(self.user.check_password("newpassword123"))

            # Vérifier que le token a été marqué comme utilisé
            token.refresh_from_db()
            self.assertTrue(token.is_used)

    def test_confirm_password_change_invalid_token(self):
        """Test de confirmation avec token invalide."""
        from users.services import PasswordChangeService

        with self.assertRaises(ValueError) as context:
            PasswordChangeService.confirm_password_change(
                "00000000-0000-0000-0000-000000000000", "123456", "newpassword123"
            )

        self.assertIn("invalide", str(context.exception))

    def test_confirm_password_change_invalid_code(self):
        """Test de confirmation avec code invalide."""
        from users.services import PasswordChangeService

        # Créer un token de test
        token = VerificationToken.create_token(
            verification_type='password_change',
            user=self.user
        )

        # Simuler un code incorrect
        with patch.object(token, 'verify_code', return_value=False):
            with self.assertRaises(ValueError) as context:
                PasswordChangeService.confirm_password_change(
                    str(token.token), "000000", "newpassword123"
                )

            self.assertIn("incorrect", str(context.exception))

    def test_confirm_password_change_expired_token(self):
        """Test de confirmation avec token expiré."""
        from users.services import PasswordChangeService

        # Créer un token de test
        token = VerificationToken.create_token(
            verification_type='password_change',
            user=self.user
        )

        # Simuler un token expiré
        with patch.object(token, 'verify_code', return_value=False):
            with self.assertRaises(ValueError) as context:
                PasswordChangeService.confirm_password_change(
                    str(token.token), "123456", "newpassword123"
                )

            self.assertIn("incorrect", str(context.exception))
