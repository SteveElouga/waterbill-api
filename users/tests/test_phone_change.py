"""
Tests pour le changement de numéro de téléphone.

Ce module teste les fonctionnalités de changement de numéro de téléphone
via SMS avec vérification sur le nouveau numéro.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch, MagicMock

from users.models import User, VerificationToken
from users.tests.test_settings import MockedAPITestCase


class PhoneChangeTestCase(MockedAPITestCase):
    """
    Tests pour le changement de numéro de téléphone.
    """

    def setUp(self):
        super().setUp()
        self.client = APIClient()

        # Créer un utilisateur de test
        self.user = User.objects.create_user(
            phone="+237670000000",
            first_name="Test",
            last_name="User",
            password="testpassword123"
        )
        self.user.is_active = True
        self.user.save()

        # Obtenir un token JWT pour l'authentification
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        # Données de test
        self.request_data = {
            "new_phone": "+237670000001"
        }

        self.confirm_data = {
            "token": "",
            "code": "123456"
        }

    def test_phone_change_request_success(self):
        """Test de demande de changement de numéro réussie."""
        url = reverse("users:phone_change_request")

        # Authentifier la requête
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        with patch('users.services.PhoneChangeService.request_phone_change') as mock_service:
            mock_service.return_value = {
                "success": True,
                "message": "Un code de vérification a été envoyé sur votre nouveau numéro."
            }

            response = self.client.post(url, self.request_data, format="json")

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["status"], "success")
            self.assertIn("nouveau numéro", response.data["message"])
            mock_service.assert_called_once_with(self.user, "+237670000001")

    def test_phone_change_request_duplicate_phone(self):
        """Test de demande avec numéro déjà utilisé."""
        # Créer un autre utilisateur avec le numéro cible
        other_user = User.objects.create_user(
            phone="+237670000001",
            first_name="Other",
            last_name="User",
            password="testpassword123"
        )

        url = reverse("users:phone_change_request")

        # Authentifier la requête
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        with patch('users.services.PhoneChangeService.request_phone_change') as mock_service:
            mock_service.side_effect = ValueError(
                "Ce numéro de téléphone est déjà utilisé")

            response = self.client.post(url, self.request_data, format="json")

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data["status"], "error")
            self.assertIn("déjà utilisé", str(response.data["data"]))

    def test_phone_change_request_invalid_phone(self):
        """Test de demande avec numéro invalide."""
        url = reverse("users:phone_change_request")

        # Authentifier la requête
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        data = {"new_phone": "123"}  # Numéro trop court

        response = self.client.post(url, data, format="json")

        # Le serializer valide le numéro et retourne une erreur 400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")

    def test_phone_change_request_unauthenticated(self):
        """Test de demande sans authentification."""
        url = reverse("users:phone_change_request")

        response = self.client.post(url, self.request_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_phone_change_request_missing_phone(self):
        """Test de demande sans nouveau numéro."""
        url = reverse("users:phone_change_request")

        # Authentifier la requête
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        data = {}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")

    def test_phone_change_confirm_success(self):
        """Test de confirmation de changement de numéro réussie."""
        # Créer un token de test
        token = VerificationToken.create_token(
            verification_type='phone_change',
            user=self.user,
            phone="+237670000001"
        )

        url = reverse("users:phone_change_confirm")

        self.confirm_data["token"] = str(token.token)

        with patch('users.services.PhoneChangeService.confirm_phone_change') as mock_service:
            mock_service.return_value = {
                "success": True,
                "message": "Votre numéro de téléphone a été changé avec succès.",
                "new_phone": "+237670000001"
            }

            response = self.client.post(url, self.confirm_data, format="json")

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["status"], "success")
            self.assertIn("changé", response.data["message"])
            self.assertEqual(response.data["data"]
                             ["new_phone"], "+237670000001")
            # Vérifier que le service a été appelé avec les bons paramètres
            call_args = mock_service.call_args[0]
            self.assertEqual(str(call_args[0]), str(token.token))
            self.assertEqual(call_args[1], "123456")

    def test_phone_change_confirm_invalid_token(self):
        """Test de confirmation avec token invalide."""
        url = reverse("users:phone_change_confirm")

        self.confirm_data["token"] = "00000000-0000-0000-0000-000000000000"

        with patch('users.services.PhoneChangeService.confirm_phone_change') as mock_service:
            mock_service.side_effect = ValueError(
                "Token de changement invalide ou expiré")

            response = self.client.post(url, self.confirm_data, format="json")

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data["status"], "error")
            self.assertIn("invalide", response.data["data"]["detail"])

    def test_phone_change_confirm_invalid_code(self):
        """Test de confirmation avec code invalide."""
        # Créer un token de test
        token = VerificationToken.create_token(
            verification_type='phone_change',
            user=self.user,
            phone="+237670000001"
        )

        url = reverse("users:phone_change_confirm")

        self.confirm_data["token"] = str(token.token)
        self.confirm_data["code"] = "000000"  # Code incorrect

        with patch('users.services.PhoneChangeService.confirm_phone_change') as mock_service:
            mock_service.side_effect = ValueError(
                "Code de vérification incorrect ou expiré")

            response = self.client.post(url, self.confirm_data, format="json")

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data["status"], "error")
            self.assertIn("incorrect", response.data["data"]["detail"])

    def test_phone_change_confirm_missing_fields(self):
        """Test de confirmation avec champs manquants."""
        url = reverse("users:phone_change_confirm")

        data = {
            "token": "00000000-0000-0000-0000-000000000000"
            # Manque code
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")

    def test_phone_change_confirm_invalid_code_format(self):
        """Test de confirmation avec format de code invalide."""
        url = reverse("users:phone_change_confirm")

        data = {
            "token": "00000000-0000-0000-0000-000000000000",
            "code": "12345"  # Code trop court
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")
        self.assertIn("6", str(response.data["data"]))

    def test_phone_change_confirm_invalid_token_format(self):
        """Test de confirmation avec format de token invalide."""
        url = reverse("users:phone_change_confirm")

        data = {
            "token": "invalid-uuid",
            "code": "123456"
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")


class PhoneChangeServiceTestCase(MockedAPITestCase):
    """
    Tests pour le service de changement de numéro de téléphone.
    """

    def setUp(self):
        super().setUp()

        # Créer un utilisateur de test
        self.user = User.objects.create_user(
            phone="+237670000000",
            first_name="Test",
            last_name="User",
            password="testpassword123"
        )
        self.user.is_active = True
        self.user.save()

    def test_request_phone_change_success(self):
        """Test de demande de changement de numéro réussie."""
        from users.services import PhoneChangeService

        with patch('users.services.get_sms_gateway') as mock_gateway:
            mock_sms = MagicMock()
            mock_sms.send_activation_code.return_value = True
            mock_gateway.return_value = mock_sms

            result = PhoneChangeService.request_phone_change(
                self.user, "+237670000001"
            )

            self.assertTrue(result["success"])
            self.assertIn("nouveau numéro", result["message"])
            self.assertIn("token", result)

            # Vérifier qu'un token a été créé
            token = VerificationToken.objects.get(
                verification_type='phone_change',
                user=self.user
            )
            self.assertIsNotNone(token)
            self.assertEqual(token.phone, "+237670000001")
            mock_sms.send_activation_code.assert_called_once()
            # Vérifier que le premier argument est le nouveau numéro de téléphone
            call_args = mock_sms.send_activation_code.call_args[0]
            self.assertEqual(call_args[0], "+237670000001")

    def test_request_phone_change_duplicate_phone(self):
        """Test de demande avec numéro déjà utilisé."""
        from users.services import PhoneChangeService

        # Créer un autre utilisateur avec le numéro cible
        other_user = User.objects.create_user(
            phone="+237670000001",
            first_name="Other",
            last_name="User",
            password="testpassword123"
        )

        with self.assertRaises(ValueError) as context:
            PhoneChangeService.request_phone_change(
                self.user, "+237670000001"
            )

        self.assertIn("déjà utilisé", str(context.exception))

    def test_confirm_phone_change_success(self):
        """Test de confirmation de changement de numéro réussie."""
        from users.services import PhoneChangeService

        # Créer un token de test
        token = VerificationToken.create_token(
            verification_type='phone_change',
            user=self.user,
            phone="+237670000001"
        )

        # Simuler un code correct en mockant la méthode verify_code
        with patch.object(VerificationToken, 'verify_code', return_value=True):
            result = PhoneChangeService.confirm_phone_change(
                str(token.token), "123456"
            )

            self.assertTrue(result["success"])
            self.assertIn("changé", result["message"])
            self.assertEqual(result["new_phone"], "+237670000001")

            # Vérifier que le numéro a été changé
            self.user.refresh_from_db()
            self.assertEqual(self.user.phone, "+237670000001")

            # Vérifier que le token a été marqué comme utilisé
            token.refresh_from_db()
            self.assertTrue(token.is_used)

    def test_confirm_phone_change_invalid_token(self):
        """Test de confirmation avec token invalide."""
        from users.services import PhoneChangeService

        with self.assertRaises(ValueError) as context:
            PhoneChangeService.confirm_phone_change(
                "00000000-0000-0000-0000-000000000000", "123456"
            )

        self.assertIn("invalide", str(context.exception))

    def test_confirm_phone_change_invalid_code(self):
        """Test de confirmation avec code invalide."""
        from users.services import PhoneChangeService

        # Créer un token de test
        token = VerificationToken.create_token(
            verification_type='phone_change',
            user=self.user,
            phone="+237670000001"
        )

        # Simuler un code incorrect en mockant la méthode verify_code
        with patch.object(VerificationToken, 'verify_code', return_value=False):
            with self.assertRaises(ValueError) as context:
                PhoneChangeService.confirm_phone_change(
                    str(token.token), "000000"
                )

            self.assertIn("incorrect", str(context.exception))

    def test_confirm_phone_change_phone_now_used(self):
        """Test de confirmation quand le numéro est maintenant utilisé par un autre compte."""
        from users.services import PhoneChangeService

        # Créer un token de test
        token = VerificationToken.create_token(
            verification_type='phone_change',
            user=self.user,
            phone="+237670000001"
        )

        # Créer un autre utilisateur avec le numéro cible après la création du token
        other_user = User.objects.create_user(
            phone="+237670000001",
            first_name="Other",
            last_name="User",
            password="testpassword123"
        )

        # Simuler un code correct en mockant la méthode verify_code
        with patch.object(VerificationToken, 'verify_code', return_value=True):
            with self.assertRaises(ValueError) as context:
                PhoneChangeService.confirm_phone_change(
                    str(token.token), "123456"
                )

            self.assertIn("maintenant utilisé", str(context.exception))

    def test_confirm_phone_change_expired_token(self):
        """Test de confirmation avec token expiré."""
        from users.services import PhoneChangeService

        # Créer un token de test
        token = VerificationToken.create_token(
            verification_type='phone_change',
            user=self.user,
            phone="+237670000001"
        )

        # Simuler un token expiré en mockant la méthode verify_code
        with patch.object(VerificationToken, 'verify_code', return_value=False):
            with self.assertRaises(ValueError) as context:
                PhoneChangeService.confirm_phone_change(
                    str(token.token), "123456"
                )

            self.assertIn("incorrect", str(context.exception))
