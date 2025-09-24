"""
Classe de base pour les tests qui nécessitent la liste blanche des numéros de téléphone.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from users.models import PhoneWhitelist
from users.utils.phone_utils import normalize_phone

User = get_user_model()


class WhitelistTestCase(TestCase):
    """
    Classe de base pour les tests nécessitant la liste blanche.

    Fournit automatiquement :
    - Un administrateur pour ajouter des numéros à la liste blanche
    - Méthodes utilitaires pour gérer la liste blanche dans les tests
    """

    @classmethod
    def setUpClass(cls):
        """Configuration de classe pour tous les tests."""
        super().setUpClass()

        # Créer un administrateur pour les tests
        cls.admin_user = User.objects.create_user(
            phone="+237670000000",
            first_name="Test",
            last_name="Admin",
            password="adminpassword123",
        )
        cls.admin_user.is_staff = True
        cls.admin_user.save()

    def setUp(self):
        """Configuration initiale pour chaque test."""
        super().setUp()

        # Nettoyer la liste blanche avant chaque test
        PhoneWhitelist.objects.all().delete()

    def tearDown(self):
        """Nettoyage après chaque test."""
        PhoneWhitelist.objects.all().delete()
        super().tearDown()

    def add_phone_to_whitelist(
        self, phone: str, notes: str = "Numéro de test"
    ) -> PhoneWhitelist:
        """
        Ajoute un numéro à la liste blanche pour les tests.

        Args:
            phone: Numéro de téléphone (format local ou international)
            notes: Notes optionnelles

        Returns:
            PhoneWhitelist: Instance créée
        """
        # Normaliser le numéro
        normalized_phone = normalize_phone(phone)
        if not normalized_phone:
            raise ValueError(f"Numéro de téléphone invalide: {phone}")

        return PhoneWhitelist.objects.create(
            phone=normalized_phone,
            added_by=self.admin_user,
            notes=notes,
            is_active=True,
        )

    def remove_phone_from_whitelist(self, phone: str) -> bool:
        """
        Supprime un numéro de la liste blanche.

        Args:
            phone: Numéro de téléphone

        Returns:
            bool: True si supprimé, False si non trouvé
        """
        normalized_phone = normalize_phone(phone)
        if not normalized_phone:
            return False

        try:
            PhoneWhitelist.objects.get(phone=normalized_phone).delete()
            return True
        except PhoneWhitelist.DoesNotExist:
            return False

    def is_phone_whitelisted(self, phone: str) -> bool:
        """
        Vérifie si un numéro est dans la liste blanche.

        Args:
            phone: Numéro de téléphone

        Returns:
            bool: True si dans la liste blanche
        """
        normalized_phone = normalize_phone(phone)
        if not normalized_phone:
            return False

        return PhoneWhitelist.is_phone_authorized(normalized_phone)

    def create_test_whitelist(self):
        """
        Crée une liste blanche de base avec des numéros de test.

        Returns:
            list: Liste des numéros ajoutés
        """
        test_phones = [
            ("237658552294", "Numéro utilisé dans les tests d'inscription"),
            ("237658552295", "Numéro utilisé dans les tests de connexion"),
            ("237670000001", "Numéro de test secondaire"),
            ("237670000002", "Numéro de test pour changement"),
        ]

        added_phones = []
        for phone, notes in test_phones:
            whitelist_item = self.add_phone_to_whitelist(phone, notes)
            added_phones.append(whitelist_item.phone)

        return added_phones


class WhitelistAPITestCase:
    """
    Mixin pour les tests d'API nécessitant la liste blanche.

    À utiliser avec APITestCase.
    """

    def setUp_whitelist(self):
        """Configuration pour les tests d'API avec liste blanche."""
        # Créer un administrateur si pas déjà fait
        if not hasattr(self, "admin_user"):
            self.admin_user = User.objects.create_user(
                phone="+237670000000",
                first_name="Test",
                last_name="Admin",
                password="adminpassword123",
            )
            self.admin_user.is_staff = True
            self.admin_user.save()

        # Nettoyer la liste blanche
        PhoneWhitelist.objects.all().delete()

    def tearDown(self):
        """Nettoyage après les tests d'API."""
        PhoneWhitelist.objects.all().delete()
        super().tearDown()

    def add_phone_to_whitelist(
        self, phone: str, notes: str = "Numéro de test"
    ) -> PhoneWhitelist:
        """Ajoute un numéro à la liste blanche."""
        normalized_phone = normalize_phone(phone)
        if not normalized_phone:
            raise ValueError(f"Numéro de téléphone invalide: {phone}")

        return PhoneWhitelist.objects.create(
            phone=normalized_phone,
            added_by=self.admin_user,
            notes=notes,
            is_active=True,
        )

    def create_test_whitelist(self):
        """Crée une liste blanche de base pour les tests."""
        test_phones = [
            ("237658552294", "Numéro utilisé dans les tests d'inscription"),
            ("237658552295", "Numéro utilisé dans les tests de connexion"),
            ("237670000001", "Numéro de test secondaire"),
            ("237670000002", "Numéro de test pour changement"),
        ]

        added_phones = []
        for phone, notes in test_phones:
            whitelist_item = self.add_phone_to_whitelist(phone, notes)
            added_phones.append(whitelist_item.phone)

        return added_phones
