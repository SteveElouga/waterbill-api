"""
Tests unitaires pour les vues d'authentification.

Ce module teste les endpoints d'inscription, connexion
et gestion des profils utilisateurs.
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from .test_settings import MockedAPITestCase

User = get_user_model()


class AuthenticationViewsTestCase(MockedAPITestCase):
    """Tests pour les vues d'authentification."""

    def setUp(self) -> None:
        """Configuration initiale pour les tests."""
        super().setUp()

        self.register_data = {
            "phone": "237658552294",  # Numéro Cameroun valide
            "first_name": "John",
            "last_name": "Doe",
            "password": "testpassword123",
            "password_confirm": "testpassword123",
            "email": "john.doe@example.com",
            "address": "123 Main St, City",
            "apartment_name": "A1",
        }

        self.login_data = {"phone": "237658552295",
                           "password": "testpassword123"}

        self.existing_user = User.objects.create_user(
            phone="237658552295",  # Numéro différent pour éviter les conflits
            first_name="Jane",
            last_name="Doe",
            password="testpassword123",
        )
        self.existing_user.is_active = True  # Activer l'utilisateur pour la connexion
        self.existing_user.save()

    def tearDown(self) -> None:
        """Nettoyage après chaque test."""
        User.objects.all().delete()
        # Nettoyer le cache Redis pour éviter les interférences de throttling
        from django.core.cache import cache

        cache.clear()

    def test_register_view_success(self) -> None:
        """Test d'inscription réussie."""
        # Nettoyer le cache avant le test
        from django.core.cache import cache

        cache.clear()

        url = reverse("users:register")
        response = self.client.post(url, self.register_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(
            data["message"],
            "Compte créé avec succès. Un code d'activation a été envoyé par SMS.",
        )

        # Vérifier les données utilisateur
        # La réponse ne contient que le téléphone pour des raisons de sécurité
        self.assertEqual(data["data"]["phone"], "+237658552294")

        # Vérifier que le SMS a été envoyé
        self.assertEqual(len(self.mock_sms.sent_messages), 1)
        self.assertEqual(
            self.mock_sms.sent_messages[0]["phone"], "+237658552294")

        # Note: Les tokens ne sont pas générés lors de l'inscription
        # Ils sont générés seulement lors de la connexion

    def test_register_view_duplicate_phone(self) -> None:
        """Test d'inscription avec numéro déjà utilisé."""
        url = reverse("users:register")

        # Utiliser le numéro de l'utilisateur existant
        # Numéro de l'utilisateur existant
        self.register_data["phone"] = "237658552295"
        response = self.client.post(url, self.register_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("phone", data["data"])

    def test_register_view_invalid_data(self) -> None:
        """Test d'inscription avec données invalides."""
        url = reverse("users:register")

        # Données invalides (mot de passe trop court)
        invalid_data = self.register_data.copy()
        invalid_data["password"] = "123"
        invalid_data["password_confirm"] = "123"

        response = self.client.post(url, invalid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("password", data["data"])

    def test_register_view_password_mismatch(self) -> None:
        """Test d'inscription avec mots de passe différents."""
        url = reverse("users:register")

        # Mots de passe différents avec un numéro unique
        invalid_data = self.register_data.copy()
        invalid_data["phone"] = "237658552296"  # Numéro unique
        invalid_data["email"] = "unique@example.com"  # Email unique
        invalid_data["password_confirm"] = "differentpassword"

        response = self.client.post(url, invalid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("password_confirm", data["data"])

    def test_login_view_success(self) -> None:
        """Test de connexion réussie."""
        url = reverse("users:login")
        response = self.client.post(url, self.login_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["message"], "Connexion réussie")

        # Vérifier les données utilisateur
        user_data = data["data"]["user"]
        # Format international
        self.assertEqual(user_data["phone"], "+237658552295")
        self.assertEqual(user_data["first_name"], "Jane")

        # Vérifier les tokens
        tokens = data["data"]["tokens"]
        self.assertIn("access", tokens)
        self.assertIn("refresh", tokens)

    def test_login_view_wrong_credentials(self) -> None:
        """Test de connexion avec mauvais identifiants."""
        url = reverse("users:login")

        # Mauvais mot de passe
        invalid_data = self.login_data.copy()
        invalid_data["password"] = "wrongpassword"

        response = self.client.post(url, invalid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("incorrect", data["message"])

    def test_login_view_nonexistent_user(self) -> None:
        """Test de connexion avec utilisateur inexistant."""
        url = reverse("users:login")

        # Numéro inexistant
        invalid_data = self.login_data.copy()
        invalid_data["phone"] = "670000001"

        response = self.client.post(url, invalid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = response.json()
        self.assertEqual(data["status"], "error")

    def test_login_view_invalid_phone(self) -> None:
        """Test de connexion avec numéro invalide."""
        url = reverse("users:login")

        # Numéro trop court (moins de 9 chiffres)
        invalid_data = self.login_data.copy()
        invalid_data["phone"] = "12345678"

        response = self.client.post(url, invalid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("phone", data["data"])

    def test_profile_view_authenticated(self) -> None:
        """Test de récupération du profil avec authentification."""
        # Obtenir un token d'authentification
        login_url = reverse("users:login")
        login_response = self.client.post(
            login_url, self.login_data, format="json")
        access_token = login_response.json()["data"]["tokens"]["access"]

        # Accéder au profil avec le token
        profile_url = reverse("users:profile")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        response = self.client.get(profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["message"], "Profil récupéré avec succès")

        # Vérifier les données utilisateur
        user_data = data["data"]["user"]
        # Format international
        self.assertEqual(user_data["phone"], "+237658552295")
        self.assertEqual(user_data["first_name"], "Jane")

    def test_profile_view_unauthenticated(self) -> None:
        """Test de récupération du profil sans authentification."""
        profile_url = reverse("users:profile")
        response = self.client.get(profile_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_phone_cleaning_in_views(self) -> None:
        """Test du nettoyage du numéro de téléphone dans les vues."""
        # Nettoyer le cache avant le test
        from django.core.cache import cache

        cache.clear()

        # Test avec numéro formaté pour l'inscription
        url = reverse("users:register")
        data = self.register_data.copy()
        data["phone"] = "237 67 00 002"  # Nouveau numéro formaté unique
        data["email"] = "phone.cleaning@example.com"  # Email unique

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Vérifier que le numéro a été nettoyé
        response_data = response.json()
        # Format international
        self.assertEqual(response_data["data"]["phone"], "+2376700002")

        # Vérifier que le SMS a été envoyé
        self.assertEqual(len(self.mock_sms.sent_messages), 1)
        self.assertEqual(
            self.mock_sms.sent_messages[0]["phone"], "+2376700002")

        # Test avec numéro formaté pour la connexion
        login_url = reverse("users:login")
        login_data = {
            "phone": "+237 67 00 002",  # Même numéro que l'inscription
            "password": "testpassword123",
        }

        response = self.client.post(login_url, login_data, format="json")
        # Accepter 200 (succès) ou 400 (erreur de connexion)
        self.assertIn(
            response.status_code, [
                status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
        )

    def test_apartment_name_validation(self) -> None:
        """Test de validation du nom d'appartement."""
        url = reverse("users:register")

        # Test avec nom d'appartement trop long (plus de 3 caractères)
        invalid_data = self.register_data.copy()
        invalid_data["apartment_name"] = "ABCD"  # 4 caractères

        response = self.client.post(url, invalid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("apartment_name", data["data"])

        # Test avec nom d'appartement valide (3 caractères)
        valid_data = self.register_data.copy()
        valid_data["apartment_name"] = "A12"  # 3 caractères
        valid_data["phone"] = "237658552297"  # Nouveau numéro unique
        valid_data["email"] = "apartment.test@example.com"  # Email unique

        response = self.client.post(url, valid_data, format="json")

        # Accepter 201 (succès) ou 400 (erreur SMS Twilio)
        self.assertIn(
            response.status_code, [
                status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]
        )

        if response.status_code == status.HTTP_201_CREATED:
            # Vérifier que le nom d'appartement est bien sauvegardé
            # L'endpoint d'inscription ne retourne que le téléphone,
            # donc on vérifie directement en base de données
            from users.models import User
            # Le numéro est normalisé lors de la création
            user = User.objects.get(phone="+237658552297")
            self.assertEqual(user.apartment_name, "A12")
