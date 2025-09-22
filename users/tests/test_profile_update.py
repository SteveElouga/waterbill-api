"""
Tests pour la mise à jour du profil utilisateur.

Ce module teste les fonctionnalités de mise à jour du profil
(nom, prénom, email, adresse, apartment_name).
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch

from users.models import User
from users.tests.test_settings import MockedAPITestCase


class ProfileUpdateTestCase(MockedAPITestCase):
    """
    Tests pour la mise à jour du profil utilisateur.
    """

    def setUp(self):
        super().setUp()
        self.client = APIClient()

        # Créer un utilisateur de test
        self.user = User.objects.create_user(
            phone="+237670000000",
            first_name="Test",
            last_name="User",
            email="test@example.com",
            address="123 Test Street",
            apartment_name="A1",
            password="testpassword123"
        )
        self.user.is_active = True
        self.user.save()

        # Obtenir un token JWT pour l'authentification
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        # Données de test
        self.update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "email": "updated@example.com",
            "address": "456 Updated Street",
            "apartment_name": "B2"
        }

    def test_profile_update_success(self):
        """Test de mise à jour du profil réussie."""
        url = reverse("users:profile_update")

        # Authentifier la requête
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        with patch('users.services.ProfileService.update_profile') as mock_service:
            mock_service.return_value = {
                "success": True,
                "message": "Votre profil a été mis à jour avec succès.",
                "user": {
                    "id": self.user.id,
                    "phone": self.user.phone,
                    "first_name": "Updated",
                    "last_name": "Name",
                    "email": "updated@example.com",
                    "address": "456 Updated Street",
                    "apartment_name": "B2"
                }
            }

            response = self.client.put(url, self.update_data, format="json")

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["status"], "success")
            self.assertIn("mis à jour", response.data["message"])
            mock_service.assert_called_once_with(self.user, self.update_data)

    def test_profile_update_partial(self):
        """Test de mise à jour partielle du profil."""
        url = reverse("users:profile_update")

        # Authentifier la requête
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        # Mettre à jour seulement le prénom
        partial_data = {"first_name": "NewFirst"}

        with patch('users.services.ProfileService.update_profile') as mock_service:
            mock_service.return_value = {
                "success": True,
                "message": "Votre profil a été mis à jour avec succès.",
                "user": {
                    "id": self.user.id,
                    "phone": self.user.phone,
                    "first_name": "NewFirst",
                    "last_name": "User",
                    "email": "test@example.com",
                    "address": "123 Test Street",
                    "apartment_name": "A1"
                }
            }

            response = self.client.put(url, partial_data, format="json")

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["status"], "success")
            mock_service.assert_called_once_with(self.user, partial_data)

    def test_profile_update_unauthenticated(self):
        """Test de mise à jour sans authentification."""
        url = reverse("users:profile_update")

        response = self.client.put(url, self.update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_update_invalid_email(self):
        """Test de mise à jour avec email invalide."""
        url = reverse("users:profile_update")

        # Authentifier la requête
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        data = {"email": "invalid-email"}

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")

    def test_profile_update_duplicate_email(self):
        """Test de mise à jour avec email déjà utilisé."""
        # Créer un autre utilisateur avec un email
        other_user = User.objects.create_user(
            phone="+237670000001",
            first_name="Other",
            last_name="User",
            email="other@example.com",
            password="testpassword123"
        )

        url = reverse("users:profile_update")

        # Authentifier la requête
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        data = {"email": "other@example.com"}

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")
        self.assertIn("déjà utilisée", str(response.data["data"]))

    def test_profile_update_apartment_name_too_long(self):
        """Test de mise à jour avec nom d'appartement trop long."""
        url = reverse("users:profile_update")

        # Authentifier la requête
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        data = {"apartment_name": "ABCD"}  # Plus de 3 caractères

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")
        self.assertIn("3", str(response.data["data"]))

    def test_profile_update_empty_data(self):
        """Test de mise à jour avec données vides."""
        url = reverse("users:profile_update")

        # Authentifier la requête
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        data = {}

        with patch('users.services.ProfileService.update_profile') as mock_service:
            mock_service.return_value = {
                "success": True,
                "message": "Votre profil a été mis à jour avec succès.",
                "user": {
                    "id": self.user.id,
                    "phone": self.user.phone,
                    "first_name": "Test",
                    "last_name": "User",
                    "email": "test@example.com",
                    "address": "123 Test Street",
                    "apartment_name": "A1"
                }
            }

            response = self.client.put(url, data, format="json")

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["status"], "success")
            mock_service.assert_called_once_with(self.user, {})

    def test_profile_update_phone_not_modifiable(self):
        """Test que le numéro de téléphone ne peut pas être modifié via cet endpoint."""
        url = reverse("users:profile_update")

        # Authentifier la requête
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        data = {"phone": "+237999999999"}

        with patch('users.services.ProfileService.update_profile') as mock_service:
            mock_service.return_value = {
                "success": True,
                "message": "Votre profil a été mis à jour avec succès.",
                "user": {
                    "id": self.user.id,
                    "phone": self.user.phone,  # Le numéro ne change pas
                    "first_name": "Test",
                    "last_name": "User",
                    "email": "test@example.com",
                    "address": "123 Test Street",
                    "apartment_name": "A1"
                }
            }

            response = self.client.put(url, data, format="json")

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # Le service ne devrait pas recevoir le champ phone
            call_args = mock_service.call_args[0]
            self.assertNotIn("phone", call_args[1])


class ProfileServiceTestCase(MockedAPITestCase):
    """
    Tests pour le service de mise à jour du profil.
    """

    def setUp(self):
        super().setUp()

        # Créer un utilisateur de test
        self.user = User.objects.create_user(
            phone="+237670000000",
            first_name="Test",
            last_name="User",
            email="test@example.com",
            address="123 Test Street",
            apartment_name="A1",
            password="testpassword123"
        )
        self.user.is_active = True
        self.user.save()

    def test_update_profile_success(self):
        """Test de mise à jour du profil réussie."""
        from users.services import ProfileService

        profile_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "email": "updated@example.com",
            "address": "456 Updated Street",
            "apartment_name": "B2"
        }

        result = ProfileService.update_profile(self.user, profile_data)

        self.assertTrue(result["success"])
        self.assertIn("mis à jour", result["message"])
        self.assertIn("user", result)

        # Vérifier que les données ont été mises à jour
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")
        self.assertEqual(self.user.last_name, "Name")
        self.assertEqual(self.user.email, "updated@example.com")
        self.assertEqual(self.user.address, "456 Updated Street")
        self.assertEqual(self.user.apartment_name, "B2")

    def test_update_profile_partial(self):
        """Test de mise à jour partielle du profil."""
        from users.services import ProfileService

        profile_data = {
            "first_name": "NewFirst"
        }

        result = ProfileService.update_profile(self.user, profile_data)

        self.assertTrue(result["success"])

        # Vérifier que seul le prénom a été mis à jour
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "NewFirst")
        self.assertEqual(self.user.last_name, "User")  # Inchangé
        self.assertEqual(self.user.email, "test@example.com")  # Inchangé

    def test_update_profile_empty_data(self):
        """Test de mise à jour avec données vides."""
        from users.services import ProfileService

        result = ProfileService.update_profile(self.user, {})

        self.assertTrue(result["success"])

        # Vérifier qu'aucune donnée n'a changé
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Test")
        self.assertEqual(self.user.last_name, "User")
        self.assertEqual(self.user.email, "test@example.com")

    def test_update_profile_duplicate_email(self):
        """Test de mise à jour avec email déjà utilisé."""
        from users.services import ProfileService

        # Créer un autre utilisateur avec un email
        other_user = User.objects.create_user(
            phone="+237670000001",
            first_name="Other",
            last_name="User",
            email="other@example.com",
            password="testpassword123"
        )

        profile_data = {"email": "other@example.com"}

        # Le service lève maintenant une exception pour les données invalides
        with self.assertRaises(ValueError) as context:
            ProfileService.update_profile(self.user, profile_data)

        self.assertIn("déjà utilisée", str(context.exception))

        # Vérifions que l'email n'a pas été changé
        self.user.refresh_from_db()
        # Email original inchangé
        self.assertEqual(self.user.email, "test@example.com")

    def test_update_profile_apartment_name_too_long(self):
        """Test de mise à jour avec nom d'appartement trop long."""
        from users.services import ProfileService

        profile_data = {"apartment_name": "ABCD"}

        # Le service lève maintenant une exception pour les données invalides
        with self.assertRaises(ValueError) as context:
            ProfileService.update_profile(self.user, profile_data)

        self.assertIn("3", str(context.exception))

        # Vérifions que l'apartment_name n'a pas été changé
        self.user.refresh_from_db()
        # Apartment name original inchangé
        self.assertEqual(self.user.apartment_name, "A1")

    def test_update_profile_phone_not_modifiable(self):
        """Test que le numéro de téléphone ne peut pas être modifié via ce service."""
        from users.services import ProfileService

        original_phone = self.user.phone

        profile_data = {
            "phone": "+237999999999",  # Ce champ ne devrait pas être traité
            "first_name": "Updated"
        }

        result = ProfileService.update_profile(self.user, profile_data)

        self.assertTrue(result["success"])

        # Vérifier que le numéro de téléphone n'a pas changé
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, original_phone)
        self.assertEqual(self.user.first_name, "Updated")
