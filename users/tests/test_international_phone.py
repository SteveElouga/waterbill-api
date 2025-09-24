"""
Tests pour vérifier que les numéros de téléphone sont au format international.
"""

import time
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock

from users.utils.phone_utils import normalize_phone
from .test_whitelist_base import WhitelistAPITestCase

User = get_user_model()


class InternationalPhoneTestCase(APITestCase, WhitelistAPITestCase):
    """Tests pour vérifier le format international des numéros de téléphone."""

    def setUp(self):
        """Configuration des tests."""
        self.setUp_whitelist()
        self.register_url = "/api/auth/register/"
        self.login_url = "/api/auth/login/"
        self.activate_url = "/api/auth/activate/"
        self.resend_url = "/api/auth/resend-code/"

    def tearDown(self):
        """Nettoyage après chaque test."""
        # Supprimer tous les utilisateurs créés pendant les tests
        User.objects.all().delete()

    def test_register_with_international_phone_format(self):
        """Test que l'inscription formate le numéro au format international."""
        # Mock du gateway SMS pour simuler un succès
        with patch("users.services.get_sms_gateway") as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_gateway.is_available.return_value = True
            mock_gateway.send_activation_code.return_value = True
            mock_get_gateway.return_value = mock_gateway

            # Données avec numéro sans préfixe + (unique avec timestamp)
            # 6 derniers chiffres du timestamp
            unique_suffix = str(int(time.time() * 1000))[-6:]
            phone_number = f"675799{unique_suffix}"

            # Ajouter le numéro à la liste blanche
            self.add_phone_to_whitelist(
                phone_number, f"Numéro de test international {unique_suffix}"
            )

            data = {
                "phone": phone_number,  # Sans le + - numéro unique
                "first_name": "John",
                "last_name": "Doe",
                "password": f"TestPass{unique_suffix}!",
                "password_confirm": f"TestPass{unique_suffix}!",
                "email": f"john{unique_suffix}@example.com",
            }

            # Envoyer la requête
            response = self.client.post(self.register_url, data, format="json")

            # Vérifier que la requête a réussi
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            # Vérifier que l'utilisateur a été créé avec le format international
            user = User.objects.get(first_name="John")
            self.assertEqual(user.phone, f"+{phone_number}")  # Avec le +

    def test_register_with_plus_prefix(self):
        """Test que l'inscription fonctionne même avec le préfixe +."""
        # Mock du gateway SMS pour simuler un succès
        with patch("users.services.get_sms_gateway") as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_gateway.is_available.return_value = True
            mock_gateway.send_activation_code.return_value = True
            mock_get_gateway.return_value = mock_gateway

            # Données avec numéro avec préfixe + (unique avec timestamp)
            # 6 derniers chiffres du timestamp
            unique_suffix = str(int(time.time() * 1000))[-6:]
            phone_number = f"675799{unique_suffix}"

            # Ajouter le numéro à la liste blanche (sans le +)
            self.add_phone_to_whitelist(
                phone_number, f"Numéro de test plus {unique_suffix}"
            )

            data = {
                "phone": f"+{phone_number}",  # Avec le + - numéro unique
                "first_name": "Jane",
                "last_name": "Doe",
                "password": f"TestPass{unique_suffix}!",
                "password_confirm": f"TestPass{unique_suffix}!",
                "email": f"jane{unique_suffix}@example.com",
            }

            # Envoyer la requête
            response = self.client.post(self.register_url, data, format="json")

            # Vérifier que la requête a réussi
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            # Vérifier que l'utilisateur a été créé avec le format international
            user = User.objects.get(first_name="Jane")
            self.assertEqual(user.phone, f"+{phone_number}")

    def test_login_with_international_phone_format(self):
        """Test que la connexion fonctionne avec le format international."""
        # Créer un utilisateur avec format international
        User.objects.create_user(
            phone="+675799745",
            first_name="Test",
            last_name="User",
            password="TestPass123!",
            is_active=True,
        )

        # Données de connexion avec numéro sans préfixe +
        data = {"phone": "675799745", "password": "TestPass123!"}  # Sans le +

        # Envoyer la requête de connexion
        response = self.client.post(self.login_url, data, format="json")

        # Vérifier que la connexion a réussi
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data["data"]["tokens"])

    def test_activate_with_international_phone_format(self):
        """Test que l'activation fonctionne avec le format international."""
        # Créer un utilisateur inactif avec format international
        user = User.objects.create_user(
            phone="+675799746",
            first_name="Test",
            last_name="User",
            password="TestPass123!",
            is_active=False,
        )

        # Mock du gateway SMS pour simuler un envoi réussi
        with patch("users.services.get_sms_gateway") as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_gateway.is_available.return_value = True
            mock_gateway.send_activation_code.return_value = True
            mock_get_gateway.return_value = mock_gateway

            # Créer un token d'activation
            from users.models import ActivationToken

            token = ActivationToken.create_token(user)
            code = "123456"
            token.code_hash = ActivationToken.hash_code(code)
            token.save()

            # Données d'activation avec numéro sans préfixe +
            data = {"phone": "675799746", "code": "123456"}  # Sans le +

            # Envoyer la requête d'activation
            response = self.client.post(self.activate_url, data, format="json")

            # Vérifier que l'activation a réussi
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # Vérifier que l'utilisateur est activé (pas de tokens lors de l'activation)
            self.assertTrue(response.data["data"]["user"]["is_active"])

    def test_resend_code_with_international_phone_format(self):
        """Test que le renvoi de code fonctionne avec le format international."""
        # Créer un utilisateur inactif avec format international
        user = User.objects.create_user(
            phone="+675799747",
            first_name="Test",
            last_name="User",
            password="TestPass123!",
            is_active=False,
        )

        # Mock du gateway SMS pour simuler un envoi réussi
        with patch("users.services.get_sms_gateway") as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_gateway.is_available.return_value = True
            mock_gateway.send_activation_code.return_value = True
            mock_get_gateway.return_value = mock_gateway

            # Créer un token d'activation
            from users.models import ActivationToken
            from django.utils import timezone
            from datetime import timedelta

            token = ActivationToken.create_token(user)

            # Simuler qu'il y a eu du temps depuis le dernier envoi (plus de 60 secondes)
            token.last_sent_at = timezone.now() - timedelta(seconds=70)
            token.save(update_fields=["last_sent_at"])

            # Données de renvoi avec numéro sans préfixe +
            data = {"phone": "675799747"}  # Sans le +

            # Envoyer la requête de renvoi
            response = self.client.post(self.resend_url, data, format="json")

            # Vérifier que le renvoi a réussi
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_phone_validation_accepts_various_formats(self):
        """Test que la validation accepte différents formats de numéros."""
        # Mock du gateway SMS pour simuler un succès
        with patch("users.services.get_sms_gateway") as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_gateway.is_available.return_value = True
            mock_gateway.send_activation_code.return_value = True
            mock_get_gateway.return_value = mock_gateway

            # Générer des numéros uniques avec timestamp
            base_timestamp = int(time.time() * 1000)
            test_cases = [
                f"{675799800 + base_timestamp % 10000}",  # Format simple
                f"+{675799801 + base_timestamp % 10000}",  # Avec préfixe +
                # Avec espaces
                f"675 {799 + base_timestamp % 100} {802 + base_timestamp % 100}",
                # Avec tirets
                f"675-{799 + base_timestamp % 100}-{803 + base_timestamp % 100}",
                # Avec parenthèses
                f"(675) {799 + base_timestamp % 100}-{804 + base_timestamp % 100}",
            ]

            for i, phone in enumerate(test_cases):
                with self.subTest(phone=phone):
                    unique_id = base_timestamp + i

                    # Ajouter le numéro à la liste blanche
                    self.add_phone_to_whitelist(
                        phone, f"Numéro de test format {unique_id}"
                    )

                    data = {
                        "phone": phone,
                        "first_name": f"Test{unique_id}",
                        "last_name": "User",
                        "password": f"TestPass{unique_id}!",
                        "password_confirm": f"TestPass{unique_id}!",
                        "email": f"test{unique_id}@example.com",
                    }

                    # Envoyer la requête
                    response = self.client.post(self.register_url, data, format="json")

                    # Vérifier que la requête a réussi
                    self.assertEqual(response.status_code, status.HTTP_201_CREATED)

                    # Vérifier que l'utilisateur a été créé avec le format international
                    # Utiliser l'utilitaire pour normaliser
                    expected_phone = normalize_phone(phone)
                    user = User.objects.get(first_name=f"Test{unique_id}")
                    self.assertEqual(user.phone, expected_phone)
