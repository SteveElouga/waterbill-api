"""
Tests pour la gestion des tokens JWT (refresh et logout).

Ce module teste les fonctionnalités de rafraîchissement de token
et de déconnexion avec blacklist.
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from users.models import User


@pytest.mark.django_db
class TestTokenRefresh:
    """Tests pour le rafraîchissement de token JWT."""

    def setup_method(self):
        """Configuration initiale pour chaque test."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone="+675799743",
            first_name="John",
            last_name="Doe",
            password="password123",
        )
        self.user.is_active = True
        self.user.save()

        # Générer des tokens JWT
        self.refresh_token = RefreshToken.for_user(self.user)
        self.access_token = self.refresh_token.access_token

    def test_token_refresh_success(self):
        """Test du rafraîchissement de token avec succès."""
        url = reverse("users:token_refresh")
        data = {"refresh": str(self.refresh_token)}

        response = self.client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert isinstance(response.data["access"], str)
        assert len(response.data["access"]) > 0

    def test_token_refresh_invalid_token(self):
        """Test du rafraîchissement avec un token invalide."""
        url = reverse("users:token_refresh")
        data = {"refresh": "invalid_token"}

        response = self.client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["status"] == "error"
        assert "invalide" in response.data["message"].lower()

    def test_token_refresh_missing_token(self):
        """Test du rafraîchissement sans token."""
        url = reverse("users:token_refresh")
        data = {}

        response = self.client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["status"] == "error"

    def test_token_refresh_empty_token(self):
        """Test du rafraîchissement avec un token vide."""
        url = reverse("users:token_refresh")
        data = {"refresh": ""}

        response = self.client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["status"] == "error"

    def test_token_refresh_blacklisted_token(self):
        """Test du rafraîchissement avec un token blacklisté."""
        # Blacklister le token
        self.refresh_token.blacklist()

        url = reverse("users:token_refresh")
        data = {"refresh": str(self.refresh_token)}

        response = self.client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["status"] == "error"


@pytest.mark.django_db
class TestLogout:
    """Tests pour la déconnexion avec blacklist."""

    def setup_method(self):
        """Configuration initiale pour chaque test."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone="+675799743",
            first_name="John",
            last_name="Doe",
            password="password123",
        )
        self.user.is_active = True
        self.user.save()

        # Générer des tokens JWT
        self.refresh_token = RefreshToken.for_user(self.user)
        self.access_token = self.refresh_token.access_token

    def test_logout_success(self):
        """Test de déconnexion avec succès."""
        url = reverse("users:logout")
        data = {"refresh": str(self.refresh_token)}

        response = self.client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "success"
        assert "Déconnexion réussie" in response.data["message"]

    def test_logout_blacklists_token(self):
        """Test que la déconnexion blackliste effectivement le token."""
        url = reverse("users:logout")
        data = {"refresh": str(self.refresh_token)}

        # Vérifier qu'il n'y a pas de token blacklisté avant
        blacklisted_count_before = BlacklistedToken.objects.count()

        response = self.client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK

        # Vérifier qu'un token a été blacklisté
        blacklisted_count_after = BlacklistedToken.objects.count()
        assert blacklisted_count_after == blacklisted_count_before + 1

    def test_logout_invalid_token(self):
        """Test de déconnexion avec un token invalide."""
        url = reverse("users:logout")
        data = {"refresh": "invalid_token"}

        response = self.client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["status"] == "error"
        assert "invalide" in response.data["message"].lower()

    def test_logout_missing_token(self):
        """Test de déconnexion sans token."""
        url = reverse("users:logout")
        data = {}

        response = self.client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["status"] == "error"

    def test_logout_empty_token(self):
        """Test de déconnexion avec un token vide."""
        url = reverse("users:logout")
        data = {"refresh": ""}

        response = self.client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["status"] == "error"

    def test_logout_already_blacklisted_token(self):
        """Test de déconnexion avec un token déjà blacklisté."""
        # Blacklister le token d'abord
        self.refresh_token.blacklist()

        url = reverse("users:logout")
        data = {"refresh": str(self.refresh_token)}

        response = self.client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["status"] == "error"
        # Le message peut être "Données invalides" car le serializer rejette le token blacklisté
        # ou contenir des détails sur le token blacklisté dans les erreurs
        assert (
            "données invalides" in response.data["message"].lower()
            or "blacklisté" in response.data["message"].lower()
            or "blacklisté" in str(response.data.get("data", {})).lower()
        )

    def test_token_unusable_after_logout(self):
        """Test qu'un token ne peut plus être utilisé après déconnexion."""
        # Se déconnecter
        logout_url = reverse("users:logout")
        logout_data = {"refresh": str(self.refresh_token)}

        logout_response = self.client.post(logout_url, logout_data, format="json")
        assert logout_response.status_code == status.HTTP_200_OK

        # Essayer d'utiliser le token pour rafraîchir
        refresh_url = reverse("users:token_refresh")
        refresh_data = {"refresh": str(self.refresh_token)}

        refresh_response = self.client.post(refresh_url, refresh_data, format="json")

        assert refresh_response.status_code == status.HTTP_400_BAD_REQUEST
        assert refresh_response.data["status"] == "error"


@pytest.mark.django_db
class TestTokenManagementIntegration:
    """Tests d'intégration pour la gestion des tokens."""

    def setup_method(self):
        """Configuration initiale pour chaque test."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone="+675799743",
            first_name="John",
            last_name="Doe",
            password="password123",
        )
        self.user.is_active = True
        self.user.save()

    def test_full_authentication_flow(self):
        """Test du flux complet d'authentification avec tokens."""
        # 1. Se connecter
        login_url = reverse("users:login")
        login_data = {"phone": "+675799743", "password": "password123"}

        login_response = self.client.post(login_url, login_data, format="json")
        assert login_response.status_code == status.HTTP_200_OK

        tokens = login_response.data["data"]["tokens"]
        refresh_token = tokens["refresh"]
        access_token = tokens["access"]

        # 2. Utiliser l'access token pour accéder au profil
        profile_url = reverse("users:profile")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        profile_response = self.client.get(profile_url)
        assert profile_response.status_code == status.HTTP_200_OK

        # 3. Rafraîchir le token
        refresh_url = reverse("users:token_refresh")
        refresh_data = {"refresh": refresh_token}

        refresh_response = self.client.post(refresh_url, refresh_data, format="json")
        assert refresh_response.status_code == status.HTTP_200_OK

        new_access_token = refresh_response.data["access"]
        assert new_access_token != access_token

        # 4. Utiliser le nouveau access token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {new_access_token}")

        profile_response2 = self.client.get(profile_url)
        assert profile_response2.status_code == status.HTTP_200_OK

        # 5. Se déconnecter
        logout_url = reverse("users:logout")
        logout_data = {"refresh": refresh_token}

        logout_response = self.client.post(logout_url, logout_data, format="json")
        assert logout_response.status_code == status.HTTP_200_OK

        # 6. Vérifier que le refresh token ne peut plus être utilisé
        refresh_response2 = self.client.post(refresh_url, refresh_data, format="json")
        assert refresh_response2.status_code == status.HTTP_400_BAD_REQUEST

    def test_multiple_refresh_tokens(self):
        """Test avec plusieurs refresh tokens pour le même utilisateur."""
        # Créer plusieurs tokens
        refresh_token1 = RefreshToken.for_user(self.user)
        refresh_token2 = RefreshToken.for_user(self.user)

        # Rafraîchir avec le premier token
        refresh_url = reverse("users:token_refresh")
        refresh_data1 = {"refresh": str(refresh_token1)}

        refresh_response1 = self.client.post(refresh_url, refresh_data1, format="json")
        assert refresh_response1.status_code == status.HTTP_200_OK

        # Rafraîchir avec le deuxième token
        refresh_data2 = {"refresh": str(refresh_token2)}

        refresh_response2 = self.client.post(refresh_url, refresh_data2, format="json")
        assert refresh_response2.status_code == status.HTTP_200_OK

        # Se déconnecter avec le premier token
        logout_url = reverse("users:logout")
        logout_data = {"refresh": str(refresh_token1)}

        logout_response = self.client.post(logout_url, logout_data, format="json")
        assert logout_response.status_code == status.HTTP_200_OK

        # Le premier token ne doit plus fonctionner
        refresh_response3 = self.client.post(refresh_url, refresh_data1, format="json")
        assert refresh_response3.status_code == status.HTTP_400_BAD_REQUEST

        # Le deuxième token doit encore fonctionner
        refresh_response4 = self.client.post(refresh_url, refresh_data2, format="json")
        assert refresh_response4.status_code == status.HTTP_200_OK
