"""
Tests pour le système d'activation par SMS.

Ce module teste les fonctionnalités d'activation des comptes utilisateurs
avec codes SMS, gestion des tentatives et limites de taux.
"""

from datetime import timedelta
from django.utils import timezone
from rest_framework import status

from users.models import User, ActivationToken
from users.services import ActivationService, RateLimitService
from .test_settings import MockedTestCase, MockedAPITestCase
from .test_whitelist_base import WhitelistAPITestCase


class ActivationTokenModelTest(MockedTestCase):
    """Tests pour le modèle ActivationToken."""

    def setUp(self):
        """Configuration initiale pour les tests."""
        self.user = User.objects.create_user(
            phone="670000000",
            first_name="Test",
            last_name="User",
            password="testpass123",
        )

    def test_activation_token_creation(self):
        """Test de création d'un token d'activation."""
        token = ActivationToken.create_token(self.user)

        self.assertEqual(token.user, self.user)
        self.assertIsNotNone(token.code_hash)
        self.assertGreater(token.expires_at, timezone.now())
        self.assertEqual(token.attempts, 0)
        self.assertEqual(token.send_count, 1)
        self.assertFalse(token.is_locked)
        # Vérifier que le code hash est bien généré
        self.assertEqual(len(token.code_hash), 64)  # SHA256 hash length

    def test_code_generation(self):
        """Test de génération de codes d'activation."""
        code = ActivationToken.generate_code()

        self.assertEqual(len(str(code)), 6)
        self.assertTrue(str(code).isdigit())
        self.assertGreaterEqual(int(code), 100000)
        self.assertLessEqual(int(code), 999999)

    def test_code_hashing(self):
        """Test de hashage des codes d'activation."""
        code = "123456"
        hash1 = ActivationToken.hash_code(code)
        hash2 = ActivationToken.hash_code(code)

        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)  # SHA256 length
        self.assertNotEqual(hash1, code)

    def test_token_expiration(self):
        """Test de vérification d'expiration du token."""
        token = ActivationToken.create_token(self.user)

        # Token non expiré
        self.assertFalse(token.is_expired())

        # Simuler l'expiration
        token.expires_at = timezone.now() - timedelta(minutes=1)
        token.save()

        self.assertTrue(token.is_expired())

    def test_max_attempts_check(self):
        """Test de vérification du nombre maximum de tentatives."""
        token = ActivationToken.create_token(self.user)

        # Tentatives normales
        self.assertFalse(token.is_max_attempts_reached())

        # Atteindre le maximum
        token.attempts = 5
        token.save()

        self.assertTrue(token.is_max_attempts_reached())

    def test_code_verification_success(self):
        """Test de vérification réussie d'un code."""
        token = ActivationToken.create_token(self.user)
        original_code = "123456"
        token.code_hash = ActivationToken.hash_code(original_code)
        token.save()

        result = token.verify_code(original_code)

        self.assertTrue(result)

    def test_code_verification_failure(self):
        """Test de vérification échouée d'un code."""
        token = ActivationToken.create_token(self.user)
        original_code = "123456"
        token.code_hash = ActivationToken.hash_code(original_code)
        token.save()

        result = token.verify_code("654321")

        self.assertFalse(result)
        self.assertEqual(token.attempts, 1)

    def test_user_activation(self):
        """Test d'activation d'un utilisateur."""
        token = ActivationToken.create_token(self.user)

        self.assertFalse(self.user.is_active)

        token.activate_user()

        # Vérifier que l'utilisateur est activé
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

        # Vérifier que le token est supprimé
        self.assertFalse(ActivationToken.objects.filter(
            user=self.user).exists())


class ActivationServiceTest(MockedTestCase):
    """Tests pour le service d'activation."""

    def setUp(self):
        """Configuration initiale pour les tests."""
        super().setUp()
        self.user = User.objects.create_user(
            phone="670000000",
            first_name="Test",
            last_name="User",
            password="testpass123",
        )

    def test_create_and_send_activation_code(self):
        """Test de création et envoi d'un code d'activation."""
        # Mock du gateway SMS
        with self.settings(DEBUG=True):  # Utilise DummySmsGateway
            code = ActivationService.create_and_send_activation_code(self.user)

            self.assertIsNotNone(code)
            self.assertEqual(len(code), 6)

            # Vérifier que le token existe
            token = ActivationToken.objects.get(user=self.user)
            self.assertIsNotNone(token)

    def test_verify_activation_code_success(self):
        """Test de vérification réussie d'un code d'activation."""
        # Créer un token avec un code connu
        token = ActivationToken.create_token(self.user)
        code = "123456"
        token.code_hash = ActivationToken.hash_code(code)
        token.save()

        user = ActivationService.verify_activation_code(self.user.phone, code)

        self.assertEqual(user, self.user)
        self.assertTrue(user.is_active)

        # Vérifier que le token est supprimé
        self.assertFalse(ActivationToken.objects.filter(
            user=self.user).exists())

    def test_verify_activation_code_wrong_code(self):
        """Test de vérification avec un code incorrect."""
        token = ActivationToken.create_token(self.user)
        code = "123456"
        token.code_hash = ActivationToken.hash_code(code)
        token.save()

        with self.assertRaises(ValueError) as context:
            ActivationService.verify_activation_code(self.user.phone, "654321")

        self.assertIn("Code d'activation incorrect", str(context.exception))

    def test_verify_activation_code_expired(self):
        """Test de vérification avec un code expiré."""
        token = ActivationToken.create_token(self.user)
        code = "123456"
        token.code_hash = ActivationToken.hash_code(code)
        token.expires_at = timezone.now() - timedelta(minutes=1)
        token.save()

        with self.assertRaises(ValueError) as context:
            ActivationService.verify_activation_code(self.user.phone, code)

        self.assertIn("Le code d'activation a expiré", str(context.exception))

    def test_verify_activation_code_user_not_found(self):
        """Test de vérification avec un utilisateur inexistant."""
        with self.assertRaises(ValueError) as context:
            ActivationService.verify_activation_code("670999999", "123456")

        self.assertIn("Utilisateur non trouvé", str(context.exception))

    def test_resend_activation_code(self):
        """Test de renvoi d'un code d'activation."""
        token = ActivationToken.create_token(self.user)

        # Simuler qu'il y a eu du temps depuis le dernier envoi (plus de 60 secondes)
        from datetime import timedelta

        token.last_sent_at = timezone.now() - timedelta(seconds=70)
        token.save(update_fields=["last_sent_at"])

        ActivationService.resend_activation_code(self.user.phone)

        # Vérifier que le compteur d'envois est incrémenté
        token.refresh_from_db()
        self.assertEqual(token.send_count, 2)


class ActivationAPITest(MockedAPITestCase, WhitelistAPITestCase):
    """Tests pour les endpoints d'activation."""

    def setUp(self):
        """Configuration initiale pour les tests."""
        super().setUp()
        self.setUp_whitelist()
        self.user = User.objects.create_user(
            phone="670000000",
            first_name="Test",
            last_name="User",
            password="testpass123",
        )

    def test_register_creates_inactive_user(self):
        """Test que l'inscription crée un utilisateur inactif."""
        # Ajouter le numéro à la liste blanche
        self.add_phone_to_whitelist("670111111", "Numéro de test activation")

        user_data = {
            "phone": "670111111",
            "first_name": "New",
            "last_name": "User",
            "password": "testpass123",
            "password_confirm": "testpass123",
        }

        with self.settings(DEBUG=True):  # Utilise DummySmsGateway
            response = self.client.post(
                "/api/auth/register/", user_data, format="json")

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            # Vérifier que l'utilisateur est créé et inactif (format international)
            user = User.objects.get(phone="+670111111")
            self.assertFalse(user.is_active)

            # Vérifier qu'un token d'activation existe
            self.assertTrue(ActivationToken.objects.filter(user=user).exists())

    def test_activate_user_success(self):
        """Test d'activation réussie d'un utilisateur."""
        token = ActivationToken.create_token(self.user)
        code = "123456"
        token.code_hash = ActivationToken.hash_code(code)
        token.save()

        activation_data = {
            "phone": self.user.phone,
            "code": code,
        }

        response = self.client.post(
            "/api/auth/activate/", activation_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier que l'utilisateur est activé
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

        # Vérifier la réponse
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("user", data["data"])
        # Vérifier que l'utilisateur est activé (pas de tokens lors de l'activation)
        self.assertTrue(data["data"]["user"]["is_active"])

    def test_activate_user_wrong_code(self):
        """Test d'activation avec un code incorrect."""
        ActivationToken.create_token(self.user)

        activation_data = {
            "phone": self.user.phone,
            "code": "654321",
        }

        response = self.client.post(
            "/api/auth/activate/", activation_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Vérifier que l'utilisateur reste inactif
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_resend_code_success(self):
        """Test de renvoi réussi d'un code."""
        token = ActivationToken.create_token(self.user)

        # Simuler qu'il y a eu du temps depuis le dernier envoi (plus de 60 secondes)
        from datetime import timedelta

        token.last_sent_at = timezone.now() - timedelta(seconds=70)
        token.save(update_fields=["last_sent_at"])

        resend_data = {
            "phone": self.user.phone,
        }

        with self.settings(DEBUG=True):  # Utilise DummySmsGateway
            response = self.client.post(
                "/api/auth/resend-code/", resend_data, format="json"
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # Vérifier que le compteur d'envois est incrémenté
            token.refresh_from_db()
            self.assertEqual(token.send_count, 2)

    def test_login_inactive_user(self):
        """Test de connexion d'un utilisateur inactif."""
        login_data = {
            "phone": self.user.phone,
            "password": "testpass123",
        }

        response = self.client.post(
            "/api/auth/login/", login_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertIn(
            "Numéro de téléphone ou mot de passe incorrect", data["message"])

    def test_login_active_user(self):
        """Test de connexion d'un utilisateur activé."""
        # Activer l'utilisateur
        self.user.is_active = True
        self.user.save()

        login_data = {
            "phone": self.user.phone,
            "password": "testpass123",
        }

        response = self.client.post(
            "/api/auth/login/", login_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("tokens", data["data"])


class RateLimitServiceTest(MockedTestCase):
    """Tests pour le service de limitation de taux."""

    def setUp(self):
        """Configuration initiale pour les tests."""
        super().setUp()
        self.user = User.objects.create_user(
            phone="670000000",
            first_name="Test",
            last_name="User",
            password="testpass123",
        )

    def test_check_activation_limits_with_token(self):
        """Test de vérification des limites avec token existant."""
        token = ActivationToken.create_token(self.user)

        # Simuler qu'il y a eu du temps depuis le dernier envoi (plus de 60 secondes)
        from datetime import timedelta

        token.last_sent_at = timezone.now() - timedelta(seconds=70)
        token.save(update_fields=["last_sent_at"])

        limits = RateLimitService.check_activation_limits(self.user.phone)

        self.assertTrue(limits["can_send"])
        self.assertFalse(limits["is_locked"])
        self.assertEqual(limits["attempts"], 0)
        self.assertEqual(limits["send_count"], 1)
        self.assertIsNotNone(limits["last_sent"])
        self.assertIsNotNone(limits["expires_at"])

    def test_check_activation_limits_without_token(self):
        """Test de vérification des limites sans token."""
        limits = RateLimitService.check_activation_limits("670999999")

        self.assertTrue(limits["can_send"])
        self.assertFalse(limits["is_locked"])
        self.assertEqual(limits["attempts"], 0)
        self.assertEqual(limits["send_count"], 0)
        self.assertIsNone(limits["last_sent"])
        self.assertIsNone(limits["expires_at"])
