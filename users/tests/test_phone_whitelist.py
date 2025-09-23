"""
Tests pour la fonctionnalité de liste blanche des numéros de téléphone.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import PhoneWhitelist
from users.utils.phone_utils import normalize_phone

User = get_user_model()


class PhoneWhitelistModelTestCase(TestCase):
    """
    Tests pour le modèle PhoneWhitelist.
    """

    def setUp(self):
        """Configuration initiale pour les tests."""
        self.admin_user = User.objects.create_user(
            phone="+237670000000",
            first_name="Admin",
            last_name="Test",
            password="adminpassword123",
        )
        self.admin_user.is_staff = True
        self.admin_user.save()

    def test_create_whitelist_item(self):
        """Test de création d'un élément de liste blanche."""
        whitelist_item = PhoneWhitelist.objects.create(
            phone="+237670000001",
            added_by=self.admin_user,
            notes="Numéro de test",
            is_active=True
        )
        
        self.assertEqual(whitelist_item.phone, "+237670000001")
        self.assertEqual(whitelist_item.added_by, self.admin_user)
        self.assertEqual(whitelist_item.notes, "Numéro de test")
        self.assertTrue(whitelist_item.is_active)
        self.assertIsNotNone(whitelist_item.added_at)

    def test_is_phone_authorized_active(self):
        """Test de vérification d'un numéro autorisé et actif."""
        PhoneWhitelist.objects.create(
            phone="+237670000001",
            added_by=self.admin_user,
            is_active=True
        )
        
        self.assertTrue(PhoneWhitelist.is_phone_authorized("+237670000001"))

    def test_is_phone_authorized_inactive(self):
        """Test de vérification d'un numéro autorisé mais inactif."""
        PhoneWhitelist.objects.create(
            phone="+237670000001",
            added_by=self.admin_user,
            is_active=False
        )
        
        self.assertFalse(PhoneWhitelist.is_phone_authorized("+237670000001"))

    def test_is_phone_authorized_not_found(self):
        """Test de vérification d'un numéro non trouvé."""
        self.assertFalse(PhoneWhitelist.is_phone_authorized("+237999999999"))

    def test_authorize_phone_new(self):
        """Test d'ajout d'un nouveau numéro à la liste blanche."""
        whitelist_item = PhoneWhitelist.authorize_phone(
            "+237670000001",
            self.admin_user,
            "Nouveau numéro"
        )
        
        self.assertEqual(whitelist_item.phone, "+237670000001")
        self.assertEqual(whitelist_item.added_by, self.admin_user)
        self.assertEqual(whitelist_item.notes, "Nouveau numéro")
        self.assertTrue(whitelist_item.is_active)

    def test_authorize_phone_existing(self):
        """Test d'ajout d'un numéro déjà existant."""
        # Créer un numéro existant
        existing_item = PhoneWhitelist.objects.create(
            phone="+237670000001",
            added_by=self.admin_user,
            is_active=False
        )
        
        # Essayer d'ajouter le même numéro
        whitelist_item = PhoneWhitelist.authorize_phone(
            "+237670000001",
            self.admin_user,
            "Numéro réactivé"
        )
        
        # Devrait retourner l'élément existant
        self.assertEqual(whitelist_item.id, existing_item.id)
        self.assertEqual(whitelist_item.phone, "+237670000001")


class PhoneWhitelistAPITestCase(APITestCase):
    """
    Tests pour l'API d'inscription avec validation de liste blanche.
    """

    def setUp(self):
        """Configuration initiale pour les tests."""
        super().setUp()
        
        # Créer un admin pour ajouter des numéros à la liste blanche
        self.admin_user = User.objects.create_user(
            phone="+237670000000",
            first_name="Admin",
            last_name="Test",
            password="adminpassword123",
        )
        self.admin_user.is_staff = True
        self.admin_user.save()

    def tearDown(self):
        """Nettoyage après chaque test."""
        User.objects.all().delete()
        PhoneWhitelist.objects.all().delete()

    def test_register_authorized_phone_success(self):
        """Test d'inscription avec un numéro autorisé."""
        from unittest.mock import patch
        
        # Ajouter le numéro à la liste blanche
        PhoneWhitelist.objects.create(
            phone="+237670000001",
            added_by=self.admin_user,
            notes="Numéro de test autorisé",
            is_active=True
        )
        
        # Données d'inscription
        register_data = {
            "phone": "237670000001",  # Format local
            "first_name": "John",
            "last_name": "Doe",
            "password": "testpassword123",
            "password_confirm": "testpassword123",
            "email": "john.doe@example.com",
        }
        
        # Mocker le service SMS
        with patch("users.services.get_sms_gateway") as mock_gateway:
            mock_sms = mock_gateway.return_value
            mock_sms.send_activation_code.return_value = True
            
            url = reverse("users:register")
            response = self.client.post(url, register_data, format="json")
            
            # Debug: afficher la réponse en cas d'erreur
            if response.status_code != status.HTTP_201_CREATED:
                print(f"Response status: {response.status_code}")
                print(f"Response data: {response.json()}")
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
            data = response.json()
            self.assertEqual(data["status"], "success")
            self.assertIn("Compte créé", data["message"])
            
            # Vérifier que l'utilisateur a été créé
            user = User.objects.get(phone="+237670000001")
            self.assertEqual(user.first_name, "John")
            self.assertEqual(user.last_name, "Doe")

    def test_register_unauthorized_phone_failure(self):
        """Test d'inscription avec un numéro non autorisé."""
        # Ne pas ajouter le numéro à la liste blanche
        
        # Données d'inscription
        register_data = {
            "phone": "237999999999",  # Numéro non autorisé
            "first_name": "John",
            "last_name": "Doe",
            "password": "testpassword123",
            "password_confirm": "testpassword123",
            "email": "john.doe@example.com",
        }
        
        url = reverse("users:register")
        response = self.client.post(url, register_data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("phone", data["data"])
        self.assertIn("pas autorisé", str(data["data"]["phone"]))
        self.assertIn("contacter le service client", str(data["data"]["phone"]))

    def test_register_inactive_phone_failure(self):
        """Test d'inscription avec un numéro autorisé mais inactif."""
        # Ajouter le numéro à la liste blanche mais inactif
        PhoneWhitelist.objects.create(
            phone="+237670000001",
            added_by=self.admin_user,
            notes="Numéro désactivé",
            is_active=False
        )
        
        # Données d'inscription
        register_data = {
            "phone": "237670000001",
            "first_name": "John",
            "last_name": "Doe",
            "password": "testpassword123",
            "password_confirm": "testpassword123",
            "email": "john.doe@example.com",
        }
        
        url = reverse("users:register")
        response = self.client.post(url, register_data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("phone", data["data"])
        self.assertIn("pas autorisé", str(data["data"]["phone"]))

    def test_register_existing_authorized_phone_failure(self):
        """Test d'inscription avec un numéro autorisé mais déjà utilisé."""
        # Ajouter le numéro à la liste blanche
        PhoneWhitelist.objects.create(
            phone="+237670000001",
            added_by=self.admin_user,
            is_active=True
        )
        
        # Créer un utilisateur existant avec ce numéro
        User.objects.create_user(
            phone="+237670000001",
            first_name="Existing",
            last_name="User",
            password="existingpassword123",
        )
        
        # Données d'inscription
        register_data = {
            "phone": "237670000001",
            "first_name": "John",
            "last_name": "Doe",
            "password": "testpassword123",
            "password_confirm": "testpassword123",
            "email": "john.doe@example.com",
        }
        
        url = reverse("users:register")
        response = self.client.post(url, register_data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("phone", data["data"])
        self.assertIn("existe déjà", str(data["data"]["phone"]))
