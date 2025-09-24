"""
Commande Django pour gérer la liste blanche des numéros de téléphone.

Usage:
    python manage.py whitelist_phone add +237670000000 "Notes optionnelles"
    python manage.py whitelist_phone remove +237670000000
    python manage.py whitelist_phone list
    python manage.py whitelist_phone check +237670000000
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from users.models import PhoneWhitelist
from users.utils.phone_utils import normalize_phone

User = get_user_model()


class Command(BaseCommand):
    help = "Gère la liste blanche des numéros de téléphone autorisés"

    def add_arguments(self, parser):
        parser.add_argument(
            "action",
            choices=["add", "remove", "list", "check"],
            help="Action à effectuer sur la liste blanche",
        )
        parser.add_argument(
            "phone",
            nargs="?",
            help="Numéro de téléphone (format international ou local)",
        )
        parser.add_argument(
            "--notes", type=str, default="", help="Notes optionnelles pour le numéro"
        )
        parser.add_argument(
            "--admin-user",
            type=str,
            help="Nom d'utilisateur ou téléphone de l'admin qui ajoute le numéro",
        )

    def handle(self, *args, **options):
        action = options["action"]

        if action == "list":
            self.list_whitelist()
        elif action in ["add", "remove", "check"]:
            if not options["phone"]:
                raise CommandError(
                    "Le numéro de téléphone est requis pour cette action"
                )

            phone = options["phone"]
            normalized_phone = normalize_phone(phone)

            if not normalized_phone:
                raise CommandError(f"Numéro de téléphone invalide: {phone}")

            if action == "add":
                self.add_phone(
                    normalized_phone, options["notes"], options["admin_user"]
                )
            elif action == "remove":
                self.remove_phone(normalized_phone)
            elif action == "check":
                self.check_phone(normalized_phone)

    def list_whitelist(self):
        """Affiche tous les numéros de la liste blanche."""
        whitelist = PhoneWhitelist.objects.select_related("added_by").order_by(
            "-added_at"
        )

        if not whitelist.exists():
            self.stdout.write(self.style.WARNING("Aucun numéro dans la liste blanche."))
            return

        self.stdout.write(
            self.style.SUCCESS(f"Liste blanche ({whitelist.count()} numéros):")
        )

        for item in whitelist:
            status = "✅ Actif" if item.is_active else "❌ Inactif"
            admin_name = item.added_by.get_full_name() or item.added_by.phone
            notes = f" - {item.notes}" if item.notes else ""

            self.stdout.write(
                f"  {item.phone} {status} (ajouté par {admin_name} le {item.added_at.strftime('%d/%m/%Y %H:%M')}){notes}"
            )

    def add_phone(self, phone, notes, admin_user_identifier):
        """Ajoute un numéro à la liste blanche."""
        # Trouver l'utilisateur admin
        admin_user = self.get_admin_user(admin_user_identifier)

        try:
            whitelist_item, created = PhoneWhitelist.objects.get_or_create(
                phone=phone,
                defaults={"added_by": admin_user, "notes": notes, "is_active": True},
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Numéro {phone} ajouté à la liste blanche.")
                )
            else:
                # Réactiver si désactivé
                if not whitelist_item.is_active:
                    whitelist_item.is_active = True
                    whitelist_item.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ Numéro {phone} réactivé dans la liste blanche."
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️  Numéro {phone} déjà présent dans la liste blanche."
                        )
                    )

        except Exception as e:
            raise CommandError(f"Erreur lors de l'ajout du numéro: {e}")

    def remove_phone(self, phone):
        """Supprime un numéro de la liste blanche."""
        try:
            whitelist_item = PhoneWhitelist.objects.get(phone=phone)
            whitelist_item.delete()
            self.stdout.write(
                self.style.SUCCESS(f"✅ Numéro {phone} supprimé de la liste blanche.")
            )
        except PhoneWhitelist.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  Numéro {phone} non trouvé dans la liste blanche."
                )
            )
        except Exception as e:
            raise CommandError(f"Erreur lors de la suppression: {e}")

    def check_phone(self, phone):
        """Vérifie si un numéro est dans la liste blanche."""
        is_authorized = PhoneWhitelist.is_phone_authorized(phone)

        if is_authorized:
            whitelist_item = PhoneWhitelist.objects.get(phone=phone, is_active=True)
            admin_name = (
                whitelist_item.added_by.get_full_name() or whitelist_item.added_by.phone
            )
            notes = f" - {whitelist_item.notes}" if whitelist_item.notes else ""

            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Numéro {phone} AUTORISÉ (ajouté par {admin_name} le {whitelist_item.added_at.strftime('%d/%m/%Y %H:%M')}){notes}"
                )
            )
        else:
            self.stdout.write(self.style.ERROR(f"❌ Numéro {phone} NON AUTORISÉ"))

    def get_admin_user(self, admin_user_identifier):
        """Trouve l'utilisateur admin par téléphone ou nom d'utilisateur."""
        if not admin_user_identifier:
            # Utiliser le premier superutilisateur par défaut
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                raise CommandError(
                    "Aucun superutilisateur trouvé. Utilisez --admin-user pour spécifier un admin."
                )
            return admin_user

        # Chercher par téléphone
        if admin_user_identifier.startswith("+"):
            admin_user = User.objects.filter(phone=admin_user_identifier).first()
        else:
            # Chercher par téléphone sans le +
            normalized_identifier = normalize_phone(admin_user_identifier)
            if normalized_identifier:
                admin_user = User.objects.filter(phone=normalized_identifier).first()
            else:
                # Chercher par prénom/nom
                admin_user = User.objects.filter(
                    first_name__icontains=admin_user_identifier
                ).first()

        if not admin_user:
            raise CommandError(f"Utilisateur admin non trouvé: {admin_user_identifier}")

        if not admin_user.is_staff:
            raise CommandError(
                f"L'utilisateur {admin_user.phone} n'est pas un administrateur."
            )

        return admin_user
