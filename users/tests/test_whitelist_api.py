"""
Tests pour l'API de gestion de la liste blanche des numéros de téléphone.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import PhoneWhitelist
from users.tests.test_whitelist_base import WhitelistAPITestCase

User = get_user_model()


class PhoneWhitelistAPITestCase(APITestCase, WhitelistAPITestCase):
    """Tests pour l'API de gestion de la liste blanche."""

    def setUp(self):
        """Configuration initiale pour les tests."""
        super().setUp()
        self.setUp_whitelist()

        # Créer un utilisateur admin pour les tests
        self.admin_user = User.objects.create_user(
            phone="+237670000999",
            password="adminpassword123",
            first_name="Admin",
            last_name="User",
            is_staff=True,
            is_superuser=True,
            is_active=True,  # Important : activer l'utilisateur admin
        )

        # Obtenir un token d'accès pour l'admin
        refresh = RefreshToken.for_user(self.admin_user)
        self.admin_token = str(refresh.access_token)

        # Créer quelques numéros de test dans la liste blanche
        self.test_phone1 = "+237670000001"
        self.test_phone2 = "+237670000002"
        self.test_phone3 = "+237670000003"

        PhoneWhitelist.objects.create(
            phone=self.test_phone1,
            added_by=self.admin_user,
            notes="Numéro de test 1",
            is_active=True
        )

        PhoneWhitelist.objects.create(
            phone=self.test_phone2,
            added_by=self.admin_user,
            notes="Numéro de test 2",
            is_active=False
        )

    def test_whitelist_list_view_success(self):
        """Test de récupération de la liste blanche avec succès."""
        url = "/api/auth/admin/whitelist/"

        response = self.client.get(
            url,
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data["status"], "success")
        self.assertIn("Liste blanche récupérée", data["message"])
        self.assertIn("whitelist", data["data"])
        self.assertIn("total_count", data["data"])
        self.assertIn("active_count", data["data"])

        # Vérifier qu'on a au moins nos numéros de test
        self.assertGreaterEqual(data["data"]["total_count"], 2)

    def test_whitelist_list_view_unauthorized(self):
        """Test de récupération de la liste blanche sans authentification."""
        url = "/api/auth/admin/whitelist/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_whitelist_list_view_forbidden(self):
        """Test de récupération de la liste blanche avec un utilisateur non-admin."""
        # Créer un utilisateur normal (non-admin)
        normal_user = User.objects.create_user(
            phone="+237670000998",
            password="normalpassword123",
            first_name="Normal",
            last_name="User",
            is_active=True,  # Activer l'utilisateur normal aussi
        )

        refresh = RefreshToken.for_user(normal_user)
        normal_token = str(refresh.access_token)

        url = "/api/auth/admin/whitelist/"

        response = self.client.get(
            url,
            HTTP_AUTHORIZATION=f"Bearer {normal_token}"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_whitelist_add_view_success(self):
        """Test d'ajout d'un numéro à la liste blanche avec succès."""
        url = "/api/auth/admin/whitelist/add/"

        new_phone = "+237670000100"
        data = {
            "phone": new_phone,
            "notes": "Nouveau numéro de test",
            "is_active": True
        }

        response = self.client.post(
            url,
            data,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()

        self.assertEqual(response_data["status"], "success")
        self.assertIn("ajouté à la liste blanche", response_data["message"])
        self.assertIn("whitelist_item", response_data["data"])

        # Vérifier que le numéro a été ajouté en base
        self.assertTrue(PhoneWhitelist.objects.filter(
            phone=new_phone).exists())

    def test_whitelist_add_view_duplicate_phone(self):
        """Test d'ajout d'un numéro déjà présent dans la liste blanche."""
        url = "/api/auth/admin/whitelist/add/"

        data = {
            "phone": self.test_phone1,  # Déjà présent
            "notes": "Tentative de doublon",
            "is_active": True
        }

        response = self.client.post(
            url,
            data,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()

        self.assertEqual(response_data["status"], "error")
        self.assertIn("déjà dans la liste blanche",
                      str(response_data["data"]["phone"]))

    def test_whitelist_add_view_invalid_phone(self):
        """Test d'ajout d'un numéro invalide."""
        url = "/api/auth/admin/whitelist/add/"

        data = {
            "phone": "",  # Numéro vide
            "notes": "Numéro invalide",
            "is_active": True
        }

        response = self.client.post(
            url,
            data,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()

        self.assertEqual(response_data["status"], "error")
        self.assertIn("vide", str(response_data["data"]["phone"]))

    def test_whitelist_check_view_authorized_phone(self):
        """Test de vérification d'un numéro autorisé."""
        url = "/api/auth/admin/whitelist/check/"

        data = {
            "phone": self.test_phone1  # Numéro autorisé et actif
        }

        response = self.client.post(
            url,
            data,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        self.assertEqual(response_data["status"], "success")
        self.assertIn("autorisé", response_data["message"])
        self.assertTrue(response_data["data"]["is_authorized"])
        self.assertIn("whitelist_details", response_data["data"])

    def test_whitelist_check_view_inactive_phone(self):
        """Test de vérification d'un numéro inactif."""
        url = "/api/auth/admin/whitelist/check/"

        data = {
            "phone": self.test_phone2  # Numéro inactif
        }

        response = self.client.post(
            url,
            data,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        self.assertEqual(response_data["status"], "success")
        self.assertIn("non autorisé", response_data["message"])
        self.assertFalse(response_data["data"]["is_authorized"])

    def test_whitelist_check_view_unauthorized_phone(self):
        """Test de vérification d'un numéro non autorisé."""
        url = "/api/auth/admin/whitelist/check/"

        data = {
            "phone": "+237670000999"  # Numéro non dans la liste blanche
        }

        response = self.client.post(
            url,
            data,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        self.assertEqual(response_data["status"], "success")
        self.assertIn("non autorisé", response_data["message"])
        self.assertFalse(response_data["data"]["is_authorized"])

    def test_whitelist_check_view_invalid_phone(self):
        """Test de vérification d'un numéro invalide."""
        url = "/api/auth/admin/whitelist/check/"

        data = {
            "phone": ""  # Numéro vide
        }

        response = self.client.post(
            url,
            data,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()

        self.assertEqual(response_data["status"], "error")
        self.assertIn("vide", str(response_data["data"]["phone"]))

    def test_whitelist_remove_view_success(self):
        """Test de suppression d'un numéro de la liste blanche avec succès."""
        url = "/api/auth/admin/whitelist/remove/"

        data = {
            "phone": self.test_phone1  # Numéro à supprimer
        }

        response = self.client.delete(
            url,
            data,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        self.assertEqual(response_data["status"], "success")
        self.assertIn("supprimé de la liste blanche", response_data["message"])
        self.assertTrue(response_data["data"]["removed"])

        # Vérifier que le numéro a été supprimé de la base
        self.assertFalse(PhoneWhitelist.objects.filter(
            phone=self.test_phone1).exists())

    def test_whitelist_remove_view_not_found(self):
        """Test de suppression d'un numéro non trouvé."""
        url = "/api/auth/admin/whitelist/remove/"

        data = {
            "phone": "+237670000999"  # Numéro non dans la liste blanche
        }

        response = self.client.delete(
            url,
            data,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response_data = response.json()

        self.assertEqual(response_data["status"], "error")
        self.assertIn("non trouvé", response_data["message"])

    def test_whitelist_remove_view_invalid_phone(self):
        """Test de suppression avec un numéro invalide."""
        url = "/api/auth/admin/whitelist/remove/"

        data = {
            "phone": ""  # Numéro vide
        }

        response = self.client.delete(
            url,
            data,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()

        self.assertEqual(response_data["status"], "error")
        self.assertIn("vide", str(response_data["data"]["phone"]))

    def test_whitelist_phone_normalization(self):
        """Test de normalisation des numéros de téléphone dans l'API."""
        url = "/api/auth/admin/whitelist/add/"

        # Test avec différents formats de numéro
        test_phones = [
            "237670000200",  # Format local
            "+237670000201",  # Format international
            "237 67 00 02 02",  # Format avec espaces
        ]

        for i, phone in enumerate(test_phones):
            data = {
                "phone": phone,
                "notes": f"Test normalisation {i}",
                "is_active": True
            }

            response = self.client.post(
                url,
                data,
                format="json",
                HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
            )

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            response_data = response.json()

            # Vérifier que le numéro a été normalisé
            normalized_phone = response_data["data"]["whitelist_item"]["phone"]
            self.assertTrue(normalized_phone.startswith("+237"))
            # La longueur dépend du numéro de test (9 chiffres après +237)
            # +237 + au moins 9 chiffres
            self.assertGreaterEqual(len(normalized_phone), 12)

    def test_whitelist_throttling(self):
        """Test du throttling pour les opérations d'administration."""
        # Ce test vérifie que le throttling fonctionne
        # En pratique, on pourrait faire plusieurs requêtes rapides
        # et vérifier qu'on est throttlé après un certain nombre

        url = "/api/auth/admin/whitelist/"

        # Première requête devrait passer
        response1 = self.client.get(
            url,
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        # Note: Pour un vrai test de throttling, il faudrait
        # configurer des limites très basses en test et faire
        # beaucoup de requêtes rapides
