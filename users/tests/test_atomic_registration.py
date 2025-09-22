"""
Tests pour vérifier que l'inscription d'utilisateur est atomique.
"""

from unittest.mock import patch, MagicMock

from users.models import User, ActivationToken
from users.services import AuthService, ActivationService
from .test_settings import MockedTestCase


class AtomicRegistrationTestCase(MockedTestCase):
    """Tests pour vérifier l'atomicité de l'inscription d'utilisateur."""

    def setUp(self):
        """Configuration des tests."""
        super().setUp()
        self.user_data = {
            "phone": "670123456",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "password": "password123",
            "password_confirm": "password123",
        }

    def test_successful_registration_is_atomic(self):
        """Test qu'une inscription réussie crée bien l'utilisateur et le token."""
        # Mock du gateway SMS pour simuler un envoi réussi
        with patch("users.services.get_sms_gateway") as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_gateway.is_available.return_value = True
            mock_gateway.send_activation_code.return_value = True
            mock_get_gateway.return_value = mock_gateway

            # Inscription de l'utilisateur
            user = AuthService.register_user(self.user_data)

            # Vérifications
            self.assertIsNotNone(user)
            self.assertEqual(user.phone, "+670123456")
            self.assertFalse(user.is_active)  # Utilisateur inactif par défaut

            # Vérifier qu'un token d'activation a été créé
            token = ActivationToken.objects.get(user=user)
            self.assertIsNotNone(token)

            # Vérifier que le SMS a été envoyé
            mock_gateway.send_activation_code.assert_called_once()

    def test_sms_failure_rolls_back_user_creation(self):
        """Test qu'un échec d'envoi SMS annule la création d'utilisateur."""
        # Mock du gateway SMS pour simuler un échec d'envoi
        with patch("users.services.get_sms_gateway") as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_gateway.is_available.return_value = True
            mock_gateway.send_activation_code.return_value = False
            mock_get_gateway.return_value = mock_gateway

            # Vérifier qu'aucun utilisateur n'existe avant
            initial_count = User.objects.count()

            # Tentative d'inscription qui doit échouer
            with self.assertRaises(ValueError) as context:
                AuthService.register_user(self.user_data)

            # Vérifier le message d'erreur
            self.assertIn(
                "Erreur lors de l'envoi du code d'activation", str(context.exception)
            )

            # Vérifier qu'aucun utilisateur n'a été créé
            final_count = User.objects.count()
            self.assertEqual(initial_count, final_count)

            # Vérifier qu'aucun token d'activation n'a été créé
            token_count = ActivationToken.objects.count()
            self.assertEqual(token_count, 0)

    def test_sms_service_unavailable_rolls_back_user_creation(self):
        """Test qu'un service SMS indisponible annule la création d'utilisateur."""
        # Mock du gateway SMS pour simuler un service indisponible
        with patch("users.services.get_sms_gateway") as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_gateway.is_available.return_value = False
            mock_get_gateway.return_value = mock_gateway

            # Vérifier qu'aucun utilisateur n'existe avant
            initial_count = User.objects.count()

            # Tentative d'inscription qui doit échouer
            with self.assertRaises(ValueError) as context:
                AuthService.register_user(self.user_data)

            # Vérifier le message d'erreur
            self.assertIn(
                "Service SMS temporairement indisponible", str(context.exception)
            )

            # Vérifier qu'aucun utilisateur n'a été créé
            final_count = User.objects.count()
            self.assertEqual(initial_count, final_count)

    def test_sms_exception_rolls_back_user_creation(self):
        """Test qu'une exception SMS annule la création d'utilisateur."""
        # Mock du gateway SMS pour simuler une exception
        with patch("users.services.get_sms_gateway") as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_gateway.is_available.return_value = True
            mock_gateway.send_activation_code.side_effect = Exception(
                "Erreur réseau SMS"
            )
            mock_get_gateway.return_value = mock_gateway

            # Vérifier qu'aucun utilisateur n'existe avant
            initial_count = User.objects.count()

            # Tentative d'inscription qui doit échouer
            with self.assertRaises(ValueError) as context:
                AuthService.register_user(self.user_data)

            # Vérifier le message d'erreur
            self.assertIn(
                "Erreur lors de l'envoi du code d'activation", str(context.exception)
            )

            # Vérifier qu'aucun utilisateur n'a été créé
            final_count = User.objects.count()
            self.assertEqual(initial_count, final_count)

    def test_duplicate_phone_rolls_back_everything(self):
        """Test qu'un téléphone dupliqué annule toute l'opération."""
        # Créer un utilisateur existant
        existing_user = User.objects.create_user(
            phone="+670123456",
            first_name="Existing",
            last_name="User",
            password="password123",
        )

        # Mock du gateway SMS (ne devrait même pas être appelé)
        with patch("users.services.get_sms_gateway") as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_get_gateway.return_value = mock_gateway

            # Tentative d'inscription avec le même téléphone
            with self.assertRaises(Exception):
                AuthService.register_user(self.user_data)

            # Vérifier que le SMS n'a pas été envoyé
            mock_gateway.send_activation_code.assert_not_called()

            # Vérifier qu'un seul utilisateur existe (l'original)
            user_count = User.objects.count()
            self.assertEqual(user_count, 1)
            self.assertEqual(User.objects.first(), existing_user)

    def test_transaction_isolation(self):
        """Test que les transactions sont bien isolées."""
        # Mock du gateway SMS pour le premier utilisateur (succès)
        with patch("users.services.get_sms_gateway") as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_gateway.is_available.return_value = True
            mock_gateway.send_activation_code.return_value = True
            mock_get_gateway.return_value = mock_gateway

            # Créer le premier utilisateur
            user1 = AuthService.register_user(self.user_data)

            # Vérifier qu'il existe
            self.assertIsNotNone(user1)
            self.assertTrue(User.objects.filter(phone="+670123456").exists())

        # Mock du gateway SMS pour le deuxième utilisateur (échec)
        user_data2 = self.user_data.copy()
        user_data2["phone"] = "670654321"
        user_data2["email"] = "user2@example.com"

        with patch("users.services.get_sms_gateway") as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_gateway.is_available.return_value = True
            mock_gateway.send_activation_code.return_value = False
            mock_get_gateway.return_value = mock_gateway

            # Tentative de création du deuxième utilisateur (doit échouer)
            with self.assertRaises(ValueError):
                AuthService.register_user(user_data2)

            # Vérifier que seul le premier utilisateur existe
            user_count = User.objects.count()
            self.assertEqual(user_count, 1)
            self.assertTrue(User.objects.filter(phone="+670123456").exists())
            self.assertFalse(User.objects.filter(phone="670654321").exists())

    def test_activation_service_is_atomic(self):
        """Test que le service d'activation est atomique."""
        # Créer un utilisateur sans token d'activation
        user = User.objects.create_user(
            phone="670999888",
            first_name="Test",
            last_name="User",
            password="password123",
        )

        # Mock du gateway SMS pour simuler un échec
        with patch("users.services.get_sms_gateway") as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_gateway.is_available.return_value = True
            mock_gateway.send_activation_code.return_value = False
            mock_get_gateway.return_value = mock_gateway

            # Vérifier qu'aucun token n'existe avant
            initial_token_count = ActivationToken.objects.count()

            # Tentative d'envoi de code d'activation qui doit échouer
            with self.assertRaises(ValueError) as context:
                ActivationService.create_and_send_activation_code(user)

            # Vérifier le message d'erreur
            self.assertIn("Échec de l'envoi du SMS", str(context.exception))

            # Vérifier qu'aucun token n'a été créé
            final_token_count = ActivationToken.objects.count()
            self.assertEqual(initial_token_count, final_token_count)

    def test_activation_service_success_creates_token(self):
        """Test qu'un envoi SMS réussi crée bien le token."""
        # Créer un utilisateur sans token d'activation
        user = User.objects.create_user(
            phone="670777666",
            first_name="Success",
            last_name="User",
            password="password123",
        )

        # Mock du gateway SMS pour simuler un succès
        with patch("users.services.get_sms_gateway") as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_gateway.is_available.return_value = True
            mock_gateway.send_activation_code.return_value = True
            mock_get_gateway.return_value = mock_gateway

            # Vérifier qu'aucun token n'existe avant
            initial_token_count = ActivationToken.objects.count()

            # Envoi de code d'activation qui doit réussir
            code = ActivationService.create_and_send_activation_code(user)

            # Vérifier qu'un token a été créé
            final_token_count = ActivationToken.objects.count()
            self.assertEqual(final_token_count, initial_token_count + 1)

            # Vérifier que le token existe et est lié à l'utilisateur
            token = ActivationToken.objects.get(user=user)
            self.assertIsNotNone(token)
            self.assertIsNotNone(code)
            self.assertEqual(len(code), 6)  # Code à 6 chiffres
