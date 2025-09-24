"""
Tests supplémentaires pour améliorer la couverture des serializers.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import PhoneWhitelist
from users.tests.test_whitelist_base import WhitelistAPITestCase
from users.serializers import (
    PhoneWhitelistSerializer,
    PhoneWhitelistAddSerializer,
    PhoneWhitelistCheckSerializer,
    PhoneWhitelistResponseSerializer,
    RegisterSerializer,
    PasswordChangeConfirmSerializer,
    PasswordResetConfirmSerializer,
    PhoneChangeConfirmSerializer,
)
from users.utils.phone_utils import normalize_phone

User = get_user_model()


class SerializerCoverageTestCase(APITestCase, WhitelistAPITestCase):
    """Tests pour améliorer la couverture des serializers."""

    def setUp(self):
        super().setUp()
        self.setUp_whitelist()

    def test_phone_whitelist_serializer_fields(self):
        """Test des champs du PhoneWhitelistSerializer."""
        # Créer un numéro dans la liste blanche
        whitelist_item = self.add_phone_to_whitelist(
            "+237670000001", "Test serializer")

        serializer = PhoneWhitelistSerializer(whitelist_item)
        data = serializer.data

        # Vérifier tous les champs
        expected_fields = [
            "id", "phone", "added_by_display", "added_by_phone",
            "added_at", "notes", "is_active"
        ]

        for field in expected_fields:
            self.assertIn(field, data)

        self.assertEqual(data["phone"], "+237670000001")
        self.assertEqual(data["notes"], "Test serializer")
        self.assertTrue(data["is_active"])

    def test_phone_whitelist_add_serializer_validation(self):
        """Test de validation du PhoneWhitelistAddSerializer."""
        serializer = PhoneWhitelistAddSerializer(data={
            "phone": "+237670000002",
            "notes": "Test validation",
            "is_active": True
        })

        self.assertTrue(serializer.is_valid())
        validated_data = serializer.validated_data

        self.assertEqual(validated_data["phone"], "+237670000002")
        self.assertEqual(validated_data["notes"], "Test validation")
        self.assertTrue(validated_data["is_active"])

    def test_phone_whitelist_add_serializer_validation_duplicate_phone(self):
        """Test de validation avec numéro dupliqué."""
        # Créer un numéro existant
        self.add_phone_to_whitelist("+237670000003", "Numéro existant")

        serializer = PhoneWhitelistAddSerializer(data={
            "phone": "+237670000003",
            "notes": "Test duplicate",
            "is_active": True
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn("phone", serializer.errors)
        self.assertIn("déjà dans la liste blanche",
                      str(serializer.errors["phone"][0]))

    def test_phone_whitelist_add_serializer_validation_invalid_phone(self):
        """Test de validation avec numéro invalide."""
        serializer = PhoneWhitelistAddSerializer(data={
            "phone": "",  # Numéro vide pour déclencher une erreur
            "notes": "Test invalid",
            "is_active": True
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn("phone", serializer.errors)

    def test_phone_whitelist_check_serializer_validation(self):
        """Test de validation du PhoneWhitelistCheckSerializer."""
        serializer = PhoneWhitelistCheckSerializer(data={
            "phone": "+237670000004"
        })

        self.assertTrue(serializer.is_valid())
        validated_data = serializer.validated_data

        self.assertEqual(validated_data["phone"], "+237670000004")

    def test_phone_whitelist_check_serializer_validation_empty_phone(self):
        """Test de validation avec numéro vide."""
        serializer = PhoneWhitelistCheckSerializer(data={
            "phone": ""
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn("phone", serializer.errors)

    def test_register_serializer_whitelist_validation(self):
        """Test de validation du RegisterSerializer avec liste blanche."""
        # Ajouter le numéro à la liste blanche
        self.add_phone_to_whitelist("237670000005", "Test register")

        serializer = RegisterSerializer(data={
            "phone": "237670000005",
            "first_name": "John",
            "last_name": "Doe",
            "password": "testpassword123",
            "password_confirm": "testpassword123",
            "email": "john.doe@example.com",
        })

        self.assertTrue(serializer.is_valid())

    def test_register_serializer_whitelist_validation_unauthorized_phone(self):
        """Test de validation avec numéro non autorisé."""
        # Ne pas ajouter le numéro à la liste blanche

        serializer = RegisterSerializer(data={
            "phone": "237670000006",
            "first_name": "Jane",
            "last_name": "Doe",
            "password": "testpassword123",
            "password_confirm": "testpassword123",
            "email": "jane.doe@example.com",
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn("phone", serializer.errors)
        self.assertIn("pas autorisé", str(serializer.errors["phone"][0]))

    def test_password_change_confirm_serializer_token_validation(self):
        """Test de validation du token dans PasswordChangeConfirmSerializer."""
        # Test avec token valide
        serializer = PasswordChangeConfirmSerializer(data={
            "token": "123e4567-e89b-12d3-a456-426614174000",
            "code": "123456",
            "new_password": "newpassword123",
            "new_password_confirm": "newpassword123"
        })

        self.assertTrue(serializer.is_valid())

    def test_password_change_confirm_serializer_invalid_token(self):
        """Test avec token invalide."""
        serializer = PasswordChangeConfirmSerializer(data={
            "token": "invalid_token",
            "code": "123456",
            "new_password": "newpassword123",
            "new_password_confirm": "newpassword123"
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn("token", serializer.errors)

    def test_password_reset_confirm_serializer_token_validation(self):
        """Test de validation du token dans PasswordResetConfirmSerializer."""
        serializer = PasswordResetConfirmSerializer(data={
            "token": "123e4567-e89b-12d3-a456-426614174001",
            "code": "123456",
            "new_password": "newpassword123",
            "new_password_confirm": "newpassword123"
        })

        self.assertTrue(serializer.is_valid())

    def test_phone_change_confirm_serializer_token_validation(self):
        """Test de validation du token dans PhoneChangeConfirmSerializer."""
        serializer = PhoneChangeConfirmSerializer(data={
            "token": "123e4567-e89b-12d3-a456-426614174002",
            "code": "123456",
            "new_phone": "+237670000007"
        })

        self.assertTrue(serializer.is_valid())

    def test_serializers_with_dirty_tokens(self):
        """Test des serializers avec tokens sales (caractères invisibles)."""
        dirty_token = "123e4567\u200b-e89b\u200c-12d3\u200d-a456\u2060-426614174000"

        # Test PasswordChangeConfirmSerializer
        serializer = PasswordChangeConfirmSerializer(data={
            "token": dirty_token,
            "code": "123456",
            "new_password": "newpassword123",
            "new_password_confirm": "newpassword123"
        })

        self.assertTrue(serializer.is_valid())
        # Le token devrait être nettoyé et converti en UUID
        import uuid
        expected_uuid = uuid.UUID("123e4567-e89b-12d3-a456-426614174000")
        self.assertEqual(serializer.validated_data["token"], expected_uuid)

    def test_serializers_with_none_token(self):
        """Test des serializers avec token None."""
        serializer = PasswordChangeConfirmSerializer(data={
            "token": None,
            "code": "123456",
            "new_password": "newpassword123",
            "new_password_confirm": "newpassword123"
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn("token", serializer.errors)

    def test_serializers_with_empty_token(self):
        """Test des serializers avec token vide."""
        serializer = PasswordChangeConfirmSerializer(data={
            "token": "",
            "code": "123456",
            "new_password": "newpassword123",
            "new_password_confirm": "newpassword123"
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn("token", serializer.errors)

    def test_phone_whitelist_serializer_read_only_fields(self):
        """Test des champs en lecture seule du PhoneWhitelistSerializer."""
        whitelist_item = self.add_phone_to_whitelist(
            "+237670000008", "Test read-only")

        serializer = PhoneWhitelistSerializer(whitelist_item)

        # Vérifier que les champs read-only sont présents
        self.assertIn("added_by_display", serializer.data)
        self.assertIn("added_by_phone", serializer.data)
        self.assertIn("added_at", serializer.data)

    def test_phone_whitelist_add_serializer_default_values(self):
        """Test des valeurs par défaut du PhoneWhitelistAddSerializer."""
        serializer = PhoneWhitelistAddSerializer(data={
            "phone": "+237670000009"
            # notes et is_active non fournis
        })

        self.assertTrue(serializer.is_valid())
        validated_data = serializer.validated_data

        # Vérifier que les valeurs par défaut sont appliquées
        self.assertIn("is_active", validated_data)
        self.assertTrue(validated_data["is_active"])  # Valeur par défaut
        # notes n'est pas dans validated_data car il a une valeur par défaut dans le serializer

    def test_phone_whitelist_response_serializer(self):
        """Test du PhoneWhitelistResponseSerializer."""
        serializer = PhoneWhitelistResponseSerializer(data={
            "status": "success",
            "message": "Test message",
            "data": {"key": "value"}
        })

        self.assertTrue(serializer.is_valid())
        validated_data = serializer.validated_data

        self.assertEqual(validated_data["status"], "success")
        self.assertEqual(validated_data["message"], "Test message")
        self.assertEqual(validated_data["data"], {"key": "value"})
