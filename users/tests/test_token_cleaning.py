"""
Tests pour le nettoyage automatique des tokens UUID.

Ce module teste la fonctionnalité de nettoyage des caractères invisibles
dans les tokens de vérification.
"""

import pytest
import uuid
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users.models import User, VerificationToken
from users.gateways.sms import clean_token, generate_redirect_url


@pytest.mark.django_db
class TestTokenCleaning:
    """Tests pour le nettoyage des tokens UUID."""

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

    def test_clean_token_basic(self):
        """Test du nettoyage de base d'un token."""
        # Token avec caractères invisibles
        dirty_token = "9320ee31-d452-42c8-92d4-70c6ee434fc0⁠⁠"

        cleaned = clean_token(dirty_token)

        assert cleaned == "9320ee31-d452-42c8-92d4-70c6ee434fc0"
        assert len(cleaned) == 36  # Longueur standard UUID
        assert len(dirty_token) == 38  # Longueur avec caractères invisibles

    def test_clean_token_word_joiner(self):
        """Test du nettoyage des WORD JOINER."""
        dirty_token = "550e8400-e29b-41d4-a716-446655440000\u2060"
        cleaned = clean_token(dirty_token)
        assert cleaned == "550e8400-e29b-41d4-a716-446655440000"

    def test_clean_token_zero_width_space(self):
        """Test du nettoyage des ZERO WIDTH SPACE."""
        dirty_token = "550e8400-e29b-41d4-a716-446655440000\u200B"
        cleaned = clean_token(dirty_token)
        assert cleaned == "550e8400-e29b-41d4-a716-446655440000"

    def test_clean_token_zero_width_non_joiner(self):
        """Test du nettoyage des ZERO WIDTH NON-JOINER."""
        dirty_token = "550e8400-e29b-41d4-a716-446655440000\u200C"
        cleaned = clean_token(dirty_token)
        assert cleaned == "550e8400-e29b-41d4-a716-446655440000"

    def test_clean_token_zero_width_joiner(self):
        """Test du nettoyage des ZERO WIDTH JOINER."""
        dirty_token = "550e8400-e29b-41d4-a716-446655440000\u200D"
        cleaned = clean_token(dirty_token)
        assert cleaned == "550e8400-e29b-41d4-a716-446655440000"

    def test_clean_token_bom(self):
        """Test du nettoyage du BOM (Byte Order Mark)."""
        dirty_token = "550e8400-e29b-41d4-a716-446655440000\uFEFF"
        cleaned = clean_token(dirty_token)
        assert cleaned == "550e8400-e29b-41d4-a716-446655440000"

    def test_clean_token_spaces(self):
        """Test du nettoyage des espaces."""
        dirty_token = " 550e8400-e29b-41d4-a716-446655440000 "
        cleaned = clean_token(dirty_token)
        assert cleaned == "550e8400-e29b-41d4-a716-446655440000"

    def test_clean_token_tabs(self):
        """Test du nettoyage des tabs."""
        dirty_token = "550e8400-e29b-41d4-a716-446655440000\t"
        cleaned = clean_token(dirty_token)
        assert cleaned == "550e8400-e29b-41d4-a716-446655440000"

    def test_clean_token_newlines(self):
        """Test du nettoyage des newlines."""
        dirty_token = "550e8400-e29b-41d4-a716-446655440000\n"
        cleaned = clean_token(dirty_token)
        assert cleaned == "550e8400-e29b-41d4-a716-446655440000"

    def test_clean_token_multiple_invisible_chars(self):
        """Test du nettoyage de plusieurs caractères invisibles."""
        dirty_token = "\u2060\u200B 550e8400-e29b-41d4-a716-446655440000 \u200C\u200D\uFEFF"
        cleaned = clean_token(dirty_token)
        assert cleaned == "550e8400-e29b-41d4-a716-446655440000"

    def test_clean_token_already_clean(self):
        """Test qu'un token déjà propre reste inchangé."""
        clean_token_value = "550e8400-e29b-41d4-a716-446655440000"
        result = clean_token(clean_token_value)
        assert result == clean_token_value

    def test_clean_token_empty(self):
        """Test du nettoyage d'un token vide."""
        result = clean_token("")
        assert result == ""

    def test_clean_token_none(self):
        """Test du nettoyage d'un token None."""
        result = clean_token(None)
        assert result is None

    def test_generate_redirect_url_with_dirty_token(self):
        """Test de la génération d'URL avec un token sale."""
        dirty_token = "9320ee31-d452-42c8-92d4-70c6ee434fc0⁠⁠"

        url = generate_redirect_url(dirty_token, "password_reset")

        # L'URL doit contenir le token nettoyé
        assert "token=9320ee31-d452-42c8-92d4-70c6ee434fc0" in url
        assert "token=9320ee31-d452-42c8-92d4-70c6ee434fc0⁠⁠" not in url
        assert url.endswith("?token=9320ee31-d452-42c8-92d4-70c6ee434fc0")

    def test_generate_redirect_url_password_reset(self):
        """Test de la génération d'URL pour reset password."""
        token = str(uuid.uuid4())
        url = generate_redirect_url(token, "password_reset")
        assert "/reset-password?token=" in url

    def test_generate_redirect_url_password_change(self):
        """Test de la génération d'URL pour changement de mot de passe."""
        token = str(uuid.uuid4())
        url = generate_redirect_url(token, "password_change")
        assert "/change-password?token=" in url

    def test_generate_redirect_url_phone_change(self):
        """Test de la génération d'URL pour changement de numéro."""
        token = str(uuid.uuid4())
        url = generate_redirect_url(token, "phone_change")
        assert "/change-phone?token=" in url

    def test_generate_redirect_url_unknown_operation(self):
        """Test de la génération d'URL pour opération inconnue."""
        token = str(uuid.uuid4())
        url = generate_redirect_url(token, "unknown_operation")
        assert "/verify?token=" in url


@pytest.mark.django_db
class TestSerializerTokenCleaning:
    """Tests pour le nettoyage des tokens dans les serializers."""

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

    def test_password_change_confirm_serializer_with_dirty_token(self):
        """Test du serializer de confirmation de changement de mot de passe avec token sale."""
        from users.serializers import PasswordChangeConfirmSerializer

        dirty_token = "9320ee31-d452-42c8-92d4-70c6ee434fc0⁠⁠"

        data = {
            "token": dirty_token,
            "code": "123456",
            "new_password": "newpassword123",
            "new_password_confirm": "newpassword123"
        }

        serializer = PasswordChangeConfirmSerializer(data=data)
        assert serializer.is_valid()

        # Le token validé doit être nettoyé
        validated_token = serializer.validated_data["token"]
        assert str(validated_token) == "9320ee31-d452-42c8-92d4-70c6ee434fc0"
        assert isinstance(validated_token, uuid.UUID)

    def test_password_reset_confirm_serializer_with_dirty_token(self):
        """Test du serializer de confirmation de reset avec token sale."""
        from users.serializers import PasswordResetConfirmSerializer

        dirty_token = "9320ee31-d452-42c8-92d4-70c6ee434fc0⁠⁠"

        data = {
            "token": dirty_token,
            "code": "123456",
            "new_password": "newpassword123",
            "new_password_confirm": "newpassword123"
        }

        serializer = PasswordResetConfirmSerializer(data=data)
        assert serializer.is_valid()

        # Le token validé doit être nettoyé
        validated_token = serializer.validated_data["token"]
        assert str(validated_token) == "9320ee31-d452-42c8-92d4-70c6ee434fc0"
        assert isinstance(validated_token, uuid.UUID)

    def test_phone_change_confirm_serializer_with_dirty_token(self):
        """Test du serializer de confirmation de changement de numéro avec token sale."""
        from users.serializers import PhoneChangeConfirmSerializer

        dirty_token = "9320ee31-d452-42c8-92d4-70c6ee434fc0⁠⁠"

        data = {
            "token": dirty_token,
            "code": "123456"
        }

        serializer = PhoneChangeConfirmSerializer(data=data)
        assert serializer.is_valid()

        # Le token validé doit être nettoyé
        validated_token = serializer.validated_data["token"]
        assert str(validated_token) == "9320ee31-d452-42c8-92d4-70c6ee434fc0"
        assert isinstance(validated_token, uuid.UUID)

    def test_serializer_rejects_invalid_token_after_cleaning(self):
        """Test que le serializer rejette un token invalide même après nettoyage."""
        from users.serializers import PhoneChangeConfirmSerializer

        # Token invalide même après nettoyage
        invalid_token = "not-a-valid-uuid⁠⁠"

        data = {
            "token": invalid_token,
            "code": "123456"
        }

        serializer = PhoneChangeConfirmSerializer(data=data)
        assert not serializer.is_valid()
        assert "Token UUID invalide" in str(serializer.errors["token"][0])

    def test_serializer_handles_empty_token(self):
        """Test que le serializer gère un token vide."""
        from users.serializers import PhoneChangeConfirmSerializer

        data = {
            "token": "",
            "code": "123456"
        }

        serializer = PhoneChangeConfirmSerializer(data=data)
        assert not serializer.is_valid()
        assert "vide" in str(serializer.errors["token"][0]).lower()


@pytest.mark.django_db
class TestTokenCleaningIntegration:
    """Tests d'intégration pour le nettoyage des tokens."""

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

    def test_password_change_flow_with_dirty_token(self):
        """Test du flux complet de changement de mot de passe avec token sale."""
        # 1. Demander un changement de mot de passe
        request_url = reverse("users:password_change_request")
        self.client.force_authenticate(user=self.user)

        request_data = {
            "current_password": "password123",
            "new_phone": "+675799744"  # Simuler une demande
        }

        # Créer un token de changement de mot de passe
        token = VerificationToken.create_token(
            verification_type="password_change",
            user=self.user,
            phone=self.user.phone  # Ajouter le phone requis
        )
        code = VerificationToken.generate_code()
        token.code_hash = VerificationToken.hash_code(code)
        token.save(update_fields=["code_hash"])

        # 2. Simuler un token avec caractères invisibles (comme dans les SMS)
        dirty_token = str(token.token) + "\u2060\u2060"

        # 3. Confirmer avec le token sale
        confirm_url = reverse("users:password_change_confirm")
        confirm_data = {
            "token": dirty_token,
            "code": code,
            "new_password": "newpassword123",
            "new_password_confirm": "newpassword123"
        }

        response = self.client.post(confirm_url, confirm_data, format="json")

        # La requête doit réussir car le token est nettoyé automatiquement
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "success"

    def test_phone_change_flow_with_dirty_token(self):
        """Test du flux complet de changement de numéro avec token sale."""
        # Créer un token de changement de numéro
        token = VerificationToken.create_token(
            verification_type="phone_change",
            user=self.user,
            phone="+675799744"
        )
        code = VerificationToken.generate_code()
        token.code_hash = VerificationToken.hash_code(code)
        token.save(update_fields=["code_hash"])

        # Simuler un token avec caractères invisibles
        dirty_token = str(token.token) + "\u2060\u2060"

        # Confirmer avec le token sale
        confirm_url = reverse("users:phone_change_confirm")
        confirm_data = {
            "token": dirty_token,
            "code": code
        }

        response = self.client.post(confirm_url, confirm_data, format="json")

        # La requête doit réussir car le token est nettoyé automatiquement
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "success"
