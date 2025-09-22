"""
Configuration des mocks pour les tests Django (TestCase).

Ce module fournit des classes de base pour les tests Django
avec les mocks automatiquement configurés.
"""

from django.test import TestCase
from unittest.mock import patch
from users.tests.mocks import MockSmsGateway


class MockedTestCase(TestCase):
    """
    Classe de base pour les tests Django avec mocks automatiques.

    Tous les tests héritant de cette classe auront automatiquement
    les services externes mockés.
    """

    def setUp(self):
        """Configuration automatique des mocks."""
        super().setUp()

        # Créer le mock SMS
        self.mock_sms = MockSmsGateway(should_succeed=True)

        # Patcher les services externes
        self.sms_patcher = patch(
            "users.gateways.sms.get_sms_gateway", return_value=self.mock_sms)
        self.services_patcher = patch(
            "users.services.get_sms_gateway", return_value=self.mock_sms)
        self.twilio_patcher = patch("users.gateways.sms.TwilioSmsGateway")

        # Démarrer les patches
        self.sms_patcher.start()
        self.services_patcher.start()
        self.twilio_mock = self.twilio_patcher.start()
        self.twilio_mock.return_value = self.mock_sms

    def tearDown(self):
        """Nettoyage des mocks."""
        super().tearDown()

        # Arrêter les patches s'ils existent
        if hasattr(self, 'sms_patcher'):
            self.sms_patcher.stop()
        if hasattr(self, 'services_patcher'):
            self.services_patcher.stop()
        if hasattr(self, 'twilio_patcher'):
            self.twilio_patcher.stop()


class MockedAPITestCase(MockedTestCase):
    """
    Classe de base pour les tests d'API avec mocks automatiques.

    Hérite de MockedTestCase et ajoute le client API Django REST Framework.
    """

    def setUp(self):
        """Configuration avec client API."""
        super().setUp()
        from rest_framework.test import APIClient
        self.client = APIClient()
