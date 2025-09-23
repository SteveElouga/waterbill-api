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
            help="Force l'initialisation même si des numéros existent déjà"
        )

    def handle(self, *args, **options):
        force = options["force"]

        # Numéros de test pour le développement
        test_phones = [
            "+237670000000",  # Numéro de test principal
            "+237670000001",  # Numéro de test secondaire
            "+237670000002",  # Numéro de test pour changement
            "+237658552295",  # Numéro utilisé dans les tests
        ]

        # Trouver un superutilisateur pour ajouter les numéros
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            raise CommandError(
                "Aucun superutilisateur trouvé. Créez d'abord un superutilisateur avec "
                "python manage.py createsuperuser"
            )

        added_count = 0
        skipped_count = 0

        for phone in test_phones:
            try:
                whitelist_item, created = PhoneWhitelist.objects.get_or_create(
                    phone=phone,
                    defaults={
                        "added_by": admin_user,
                        "notes": f"Numéro de test ajouté automatiquement",
                        "is_active": True
                    }
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ {phone} ajouté à la liste blanche")
                    )
                    added_count += 1
                else:
                    if force:
                        # Réactiver si désactivé
                        if not whitelist_item.is_active:
                            whitelist_item.is_active = True
                            whitelist_item.save()
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"✅ {phone} réactivé dans la liste blanche")
                            )
                            added_count += 1
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"⚠️  {phone} déjà présent (ignoré)")
                            )
                            skipped_count += 1
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"⚠️  {phone} déjà présent (ignoré)")
                        )
                        skipped_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Erreur pour {phone}: {e}")
                )

        # Résumé
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS(f"Initialisation terminée:"))
        self.stdout.write(f"  - Numéros ajoutés: {added_count}")
        self.stdout.write(f"  - Numéros ignorés: {skipped_count}")
        self.stdout.write(
            f"  - Total dans la liste: {PhoneWhitelist.objects.count()}")

        if added_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "\n✅ Liste blanche initialisée avec succès !"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠️  Aucun nouveau numéro ajouté. Utilisez --force pour réactiver les numéros existants."
                )
            )
