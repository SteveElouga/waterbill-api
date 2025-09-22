"""
Tests unitaires pour les modèles utilisateur.

Ce module teste la création et validation des utilisateurs
avec le modèle User personnalisé.
"""

from users.models import User
from .test_settings import MockedTestCase


class UserModelTestCase(MockedTestCase):
    """Tests pour le modèle User personnalisé."""

    def setUp(self) -> None:
        """Configuration initiale pour les tests."""
        super().setUp()
        self.user_data = {
            "phone": "670000000",
            "first_name": "John",
            "last_name": "Doe",
            "password": "testpassword123",
        }

    def test_create_user_with_valid_data(self) -> None:
        """Test de création d'un utilisateur avec des données valides."""
        user = User.objects.create_user(**self.user_data)

        self.assertEqual(user.phone, "+670000000")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")
        self.assertTrue(user.check_password("testpassword123"))
        # Les utilisateurs sont inactifs par défaut
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_user_str_representation(self) -> None:
        """Test de la représentation string de l'utilisateur."""
        user = User.objects.create_user(**self.user_data)
        expected = "John Doe (+670000000)"
        self.assertEqual(str(user), expected)

    def test_get_full_name(self) -> None:
        """Test de la méthode get_full_name."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_full_name(), "John Doe")

    def test_get_short_name(self) -> None:
        """Test de la méthode get_short_name."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_short_name(), "John")

    def test_is_admin_property(self) -> None:
        """Test de la propriété is_admin."""
        user = User.objects.create_user(**self.user_data)
        self.assertFalse(user.is_admin)

        user.is_staff = True
        self.assertTrue(user.is_admin)

        user.is_staff = False
        user.is_superuser = True
        self.assertTrue(user.is_admin)

    def test_phone_uniqueness(self) -> None:
        """Test de l'unicité du numéro de téléphone."""
        User.objects.create_user(**self.user_data)

        with self.assertRaises(Exception):  # IntegrityError ou ValidationError
            User.objects.create_user(**self.user_data)

    def test_required_fields_validation(self) -> None:
        """Test de validation des champs obligatoires."""
        # Test sans prénom
        with self.assertRaises(Exception):
            User.objects.create_user(
                phone="670000001",
                first_name="",
                last_name="Doe",
                password="testpassword123",
            )

        # Test sans nom
        with self.assertRaises(Exception):
            User.objects.create_user(
                phone="670000002",
                first_name="John",
                last_name="",
                password="testpassword123",
            )

    def test_phone_cleaning(self) -> None:
        """Test du nettoyage du numéro de téléphone."""
        user_data = self.user_data.copy()
        # Format avec espaces et préfixe
        user_data["phone"] = "+237 67 00 00 000"

        user = User.objects.create_user(**user_data)
        self.assertEqual(user.phone, "+237670000000")  # Format international

    def test_create_superuser(self) -> None:
        """Test de création d'un superutilisateur."""
        superuser = User.objects.create_superuser(**self.user_data)

        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_active)

    def test_optional_fields(self) -> None:
        """Test des champs optionnels."""
        user_data = self.user_data.copy()
        user_data.update(
            {"email": "john.doe@example.com", "address": "123 Main St, City"}
        )

        user = User.objects.create_user(**user_data)

        self.assertEqual(user.email, "john.doe@example.com")
        self.assertEqual(user.address, "123 Main St, City")
