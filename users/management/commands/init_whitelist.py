"""
Commande Django pour initialiser la liste blanche avec des numéros de test.

Usage:
    python manage.py init_whitelist
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from users.models import PhoneWhitelist

User = get_user_model()


class Command(BaseCommand):
    help = "Initialise la liste blanche avec des numéros de test"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force l'initialisation même si des numéros existent déjà",
        )

    def handle(self, *args, **options):
        force = options["force"]
        admin_user = self._get_admin_user()
        test_phones = self._get_test_phones()

        added_count, skipped_count = self._process_phones(
            test_phones, admin_user, force
        )
        self._display_summary(added_count, skipped_count)

    def _get_admin_user(self):
        """Trouve un superutilisateur pour ajouter les numéros."""
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            raise CommandError(
                "Aucun superutilisateur trouvé. Créez d'abord un superutilisateur avec "
                "python manage.py createsuperuser"
            )
        return admin_user

    def _get_test_phones(self):
        """Retourne la liste des numéros de test."""
        return [
            "+237670000000",  # Numéro de test principal
            "+237670000001",  # Numéro de test secondaire
            "+237670000002",  # Numéro de test pour changement
            "+237658552295",  # Numéro utilisé dans les tests
        ]

    def _process_phones(self, test_phones, admin_user, force):
        """Traite chaque numéro de téléphone."""
        added_count = 0
        skipped_count = 0

        for phone in test_phones:
            try:
                added, skipped = self._process_single_phone(phone, admin_user, force)
                added_count += added
                skipped_count += skipped
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Erreur pour {phone}: {e}"))

        return added_count, skipped_count

    def _process_single_phone(self, phone, admin_user, force):
        """Traite un seul numéro de téléphone."""
        whitelist_item, created = PhoneWhitelist.objects.get_or_create(
            phone=phone,
            defaults={
                "added_by": admin_user,
                "notes": "Numéro de test ajouté automatiquement",
                "is_active": True,
            },
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f"✅ {phone} ajouté à la liste blanche")
            )
            return 1, 0

        return self._handle_existing_phone(whitelist_item, phone, force)

    def _handle_existing_phone(self, whitelist_item, phone, force):
        """Gère un numéro déjà existant."""
        if not force:
            self.stdout.write(self.style.WARNING(f"⚠️  {phone} déjà présent (ignoré)"))
            return 0, 1

        if not whitelist_item.is_active:
            whitelist_item.is_active = True
            whitelist_item.save()
            self.stdout.write(
                self.style.SUCCESS(f"✅ {phone} réactivé dans la liste blanche")
            )
            return 1, 0
        else:
            self.stdout.write(self.style.WARNING(f"⚠️  {phone} déjà présent (ignoré)"))
            return 0, 1

    def _display_summary(self, added_count, skipped_count):
        """Affiche le résumé de l'opération."""
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("Initialisation terminée:"))
        self.stdout.write(f"  - Numéros ajoutés: {added_count}")
        self.stdout.write(f"  - Numéros ignorés: {skipped_count}")
        self.stdout.write(f"  - Total dans la liste: {PhoneWhitelist.objects.count()}")

        if added_count > 0:
            self.stdout.write(
                self.style.SUCCESS("\n✅ Liste blanche initialisée avec succès !")
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠️  Aucun nouveau numéro ajouté. Utilisez --force pour réactiver les numéros existants."
                )
            )
