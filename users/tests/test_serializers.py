"""
Tests unitaires pour les serializers d'authentification.

Ce module teste la validation et sérialisation des données
d'inscription et de connexion.
"""

from django.contrib.auth import get_user_model

from users.serializers import RegisterSerializer, LoginSerializer, UserSerializer
from .test_settings import MockedTestCase
from .test_whitelist_base import WhitelistTestCase

User = get_user_model()


class RegisterSerializerTestCase(MockedTestCase, WhitelistTestCase):
    """Tests pour le RegisterSerializer."""

    def setUp(self) -> None:
        """Configuration initiale pour les tests."""
        super().setUp()
        self.valid_data = {
            "phone": "670000000",
            "first_name": "John",
            "last_name": "Doe",
            "password": "testpassword123",
            "password_confirm": "testpassword123",
            "email": "john.doe@example.com",
            "address": "123 Main St, City",
        }

    def tearDown(self) -> None:
        """Nettoyage après chaque test."""
        User.objects.all().delete()

    def test_valid_registration_data(self) -> None:
        """Test avec des données d'inscription valides."""
        # Ajouter le numéro à la liste blanche
        self.add_phone_to_whitelist(
            self.valid_data["phone"], "Numéro de test serializer"
        )

        serializer = RegisterSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())

        user = serializer.save()
        self.assertEqual(user.phone, "+670000000")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")
        self.assertEqual(user.email, "john.doe@example.com")
        self.assertTrue(user.check_password("testpassword123"))

    def test_phone_validation(self) -> None:
        """Test de validation du numéro de téléphone."""
        # Test avec numéro trop court
        data = self.valid_data.copy()
        data["phone"] = "123"
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("phone", serializer.errors)

        # Test avec numéro trop long
        data["phone"] = "123456789012345678"
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("phone", serializer.errors)

    def test_password_validation(self) -> None:
        """Test de validation du mot de passe."""
        # Test avec mot de passe trop court
        data = self.valid_data.copy()
        data["password"] = "123"
        data["password_confirm"] = "123"
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    def test_password_confirmation_mismatch(self) -> None:
        """Test de non-correspondance des mots de passe."""
        # Ajouter le numéro à la liste blanche
        self.add_phone_to_whitelist(self.valid_data["phone"], "Numéro de test mismatch")

        data = self.valid_data.copy()
        data["password_confirm"] = "differentpassword"
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password_confirm", serializer.errors)

    def test_phone_uniqueness(self) -> None:
        """Test de l'unicité du numéro de téléphone."""
        # Créer un utilisateur existant
        User.objects.create_user(
            phone="670000000",
            first_name="Jane",
            last_name="Doe",
            password="testpassword123",
        )

        # Tenter de créer un autre utilisateur avec le même numéro
        serializer = RegisterSerializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("phone", serializer.errors)

    def test_phone_cleaning(self) -> None:
        """Test du nettoyage du numéro de téléphone."""
        # Utiliser des données complètement uniques pour éviter les conflits
        data = {
            "phone": "+237 67 00 001",  # Numéro plus court avec format varié
            "first_name": "PhoneTest",
            "last_name": "User",
            "password": "TestPass123!",
            "password_confirm": "TestPass123!",
            "email": "phonetest@example.com",  # Email unique
            "address": "Test Address",
        }

        # Ajouter le numéro à la liste blanche
        self.add_phone_to_whitelist(data["phone"], "Numéro de test nettoyage")

        serializer = RegisterSerializer(data=data)

        # Debug: Afficher l'erreur si la validation échoue
        if not serializer.is_valid():
            print(f"Erreur de validation pour {data['phone']}:")
            print(f"Erreurs: {serializer.errors}")
            print(f"Data: {data}")

        self.assertTrue(serializer.is_valid())

        user = serializer.save()
        # Numéro unique normalisé
        self.assertEqual(user.phone, "+2376700001")


class LoginSerializerTestCase(MockedTestCase):
    """Tests pour le LoginSerializer."""

    def setUp(self) -> None:
        """Configuration initiale pour les tests."""
        super().setUp()
        self.user = User.objects.create_user(
            phone="670000000",
            first_name="John",
            last_name="Doe",
            password="testpassword123",
        )

        self.valid_data = {"phone": "670000000", "password": "testpassword123"}

    def tearDown(self) -> None:
        """Nettoyage après chaque test."""
        User.objects.all().delete()

    def test_valid_login_data(self) -> None:
        """Test avec des données de connexion valides."""
        serializer = LoginSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())

    def test_phone_cleaning(self) -> None:
        """Test du nettoyage du numéro de téléphone."""
        data = self.valid_data.copy()
        data["phone"] = "+237 67 00 00 000"

        serializer = LoginSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["phone"], "+237670000000")

    def test_invalid_phone(self) -> None:
        """Test avec un numéro de téléphone invalide."""
        data = self.valid_data.copy()
        data["phone"] = "123"  # Trop court

        serializer = LoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("phone", serializer.errors)


class UserSerializerTestCase(MockedTestCase):
    """Tests pour le UserSerializer."""

    def setUp(self) -> None:
        """Configuration initiale pour les tests."""
        super().setUp()
        self.user = User.objects.create_user(
            phone="670000000",
            first_name="John",
            last_name="Doe",
            password="testpassword123",
            email="john.doe@example.com",
            address="123 Main St, City",
        )

    def test_user_serialization(self) -> None:
        """Test de sérialisation d'un utilisateur."""
        serializer = UserSerializer(self.user)
        data = serializer.data

        self.assertEqual(data["phone"], "+670000000")
        self.assertEqual(data["first_name"], "John")
        self.assertEqual(data["last_name"], "Doe")
        self.assertEqual(data["full_name"], "John Doe")
        self.assertEqual(data["email"], "john.doe@example.com")
        self.assertEqual(data["address"], "123 Main St, City")
        # Les utilisateurs sont inactifs par défaut
        self.assertFalse(data["is_active"])

    def test_read_only_fields(self) -> None:
        """Test des champs en lecture seule."""
        serializer = UserSerializer(self.user)
        data = serializer.data

        # Ces champs ne doivent pas être modifiables
        read_only_fields = ["id", "date_joined", "is_active"]
        for field in read_only_fields:
            self.assertIn(field, data)

    def test_full_name_property(self) -> None:
        """Test de la propriété full_name."""
        serializer = UserSerializer(self.user)
        data = serializer.data

        self.assertEqual(data["full_name"], "John Doe")
