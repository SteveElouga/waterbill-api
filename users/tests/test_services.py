"""
Tests unitaires pour les services d'authentification.

Ce module teste la logique métier des services d'inscription,
connexion et gestion des utilisateurs.
"""

from users.services import AuthService, ResponseService
from users.models import User
from .test_settings import MockedTestCase


class AuthServiceTestCase(MockedTestCase):
    """Tests pour AuthService."""

    def setUp(self) -> None:
        """Configuration initiale pour les tests."""
        super().setUp()
        self.user_data = {
            "phone": "670000000",  # Format local - sera normalisé en +670000000
            "first_name": "John",
            "last_name": "Doe",
            "password": "testpassword123",
            "email": "john.doe@example.com",
        }

    def tearDown(self) -> None:
        """Nettoyage après chaque test."""
        User.objects.all().delete()

    def test_register_user_success(self) -> None:
        """Test d'inscription réussie d'un utilisateur."""
        user = AuthService.register_user(self.user_data)

        self.assertIsInstance(user, User)
        self.assertEqual(user.phone, "+670000000")  # Format international
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")
        self.assertTrue(user.check_password("testpassword123"))
        self.assertFalse(user.is_active)  # Utilisateur inactif par défaut

        # Vérifier que le SMS a été envoyé
        self.assertEqual(len(self.mock_sms.sent_messages), 1)
        self.assertEqual(self.mock_sms.sent_messages[0]["phone"], "+670000000")

    def test_register_user_duplicate_phone(self) -> None:
        """Test d'inscription avec numéro de téléphone déjà utilisé."""
        # Créer un utilisateur existant
        User.objects.create_user(**self.user_data)

        # Tenter de créer un autre utilisateur avec le même numéro
        with self.assertRaises(ValueError) as context:
            AuthService.register_user(self.user_data)

        self.assertIn("existe déjà", str(context.exception))

    def test_authenticate_user_success(self) -> None:
        """Test d'authentification réussie."""
        user = User.objects.create_user(**self.user_data)
        user.is_active = True  # Activer l'utilisateur pour l'authentification
        user.save()

        authenticated_user = AuthService.authenticate_user(
            "670000000", "testpassword123"
        )

        self.assertEqual(authenticated_user, user)
        self.assertIsNotNone(authenticated_user.last_login)

    def test_authenticate_user_wrong_password(self) -> None:
        """Test d'authentification avec mauvais mot de passe."""
        User.objects.create_user(**self.user_data)

        authenticated_user = AuthService.authenticate_user(
            "670000000", "wrongpassword")

        self.assertIsNone(authenticated_user)

    def test_authenticate_user_wrong_phone(self) -> None:
        """Test d'authentification avec mauvais numéro."""
        User.objects.create_user(**self.user_data)

        authenticated_user = AuthService.authenticate_user(
            "670000001", "testpassword123"
        )

        self.assertIsNone(authenticated_user)

    def test_authenticate_user_inactive(self) -> None:
        """Test d'authentification avec utilisateur inactif."""
        user = User.objects.create_user(**self.user_data)
        user.is_active = False
        user.save()

        authenticated_user = AuthService.authenticate_user(
            "670000000", "testpassword123"
        )

        self.assertIsNone(authenticated_user)

    def test_login_user_success(self) -> None:
        """Test de connexion réussie."""
        user = User.objects.create_user(**self.user_data)
        user.is_active = True  # Activer l'utilisateur pour la connexion
        user.save()

        logged_user, tokens = AuthService.login_user(
            "670000000", "testpassword123")

        self.assertEqual(logged_user, user)
        self.assertIn("access", tokens)
        self.assertIn("refresh", tokens)

    def test_login_user_failure(self) -> None:
        """Test de connexion échouée."""
        User.objects.create_user(**self.user_data)

        with self.assertRaises(ValueError) as context:
            AuthService.login_user("670000000", "wrongpassword")

        self.assertIn("incorrect", str(context.exception))

    def test_get_user_profile(self) -> None:
        """Test de récupération du profil utilisateur."""
        user = User.objects.create_user(**self.user_data)

        profile = AuthService.get_user_profile(user)

        self.assertIn("phone", profile)
        self.assertIn("first_name", profile)
        self.assertIn("last_name", profile)
        self.assertIn("full_name", profile)
        # Format international
        self.assertEqual(profile["phone"], "+670000000")
        self.assertEqual(profile["first_name"], "John")

    def test_validate_phone_uniqueness(self) -> None:
        """Test de validation de l'unicité du numéro de téléphone."""
        # Test avec numéro unique
        is_unique = AuthService.validate_phone_uniqueness("670000000")
        self.assertTrue(is_unique)

        # Créer un utilisateur
        user = User.objects.create_user(**self.user_data)

        # Test avec numéro existant
        is_unique = AuthService.validate_phone_uniqueness("670000000")
        self.assertFalse(is_unique)

        # Test avec exclusion d'utilisateur (utiliser l'ID réel)
        is_unique = AuthService.validate_phone_uniqueness(
            "670000000", exclude_user_id=user.id
        )
        self.assertTrue(is_unique)


class ResponseServiceTestCase(MockedTestCase):
    """Tests pour ResponseService."""

    def setUp(self):
        """Configuration initiale pour les tests."""
        super().setUp()

    def test_success_response(self) -> None:
        """Test de génération d'une réponse de succès."""
        response = ResponseService.success_response(
            message="Test réussi", data={"key": "value"}
        )

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["message"], "Test réussi")
        self.assertEqual(response["data"], {"key": "value"})

    def test_success_response_no_data(self) -> None:
        """Test de génération d'une réponse de succès sans données."""
        response = ResponseService.success_response(message="Test réussi")

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["message"], "Test réussi")
        self.assertEqual(response["data"], {})

    def test_error_response(self) -> None:
        """Test de génération d'une réponse d'erreur."""
        response = ResponseService.error_response(
            message="Erreur test", errors={"field": ["Erreur de validation"]}
        )

        self.assertEqual(response["status"], "error")
        self.assertEqual(response["message"], "Erreur test")
        self.assertEqual(response["data"], {"field": ["Erreur de validation"]})

    def test_error_response_no_errors(self) -> None:
        """Test de génération d'une réponse d'erreur sans détails."""
        response = ResponseService.error_response(message="Erreur test")

        self.assertEqual(response["status"], "error")
        self.assertEqual(response["message"], "Erreur test")
        self.assertEqual(response["data"], {})
