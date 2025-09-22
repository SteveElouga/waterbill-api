"""
Modèles utilisateur pour WaterBill API.

Ce module définit le modèle User personnalisé basé sur AbstractBaseUser
pour l'authentification par numéro de téléphone et le système d'activation par SMS.
"""

import hashlib
import secrets
import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.timezone import timedelta

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Modèle utilisateur personnalisé pour WaterBill.

    Utilise le numéro de téléphone comme identifiant unique
    au lieu du nom d'utilisateur traditionnel.
    """

    # Champs obligatoires
    phone = models.CharField(
        max_length=15,
        unique=True,
        help_text="Numéro de téléphone unique (ex: +237670000000)",
    )
    first_name = models.CharField(
        max_length=150, help_text="Prénom de l'utilisateur")
    last_name = models.CharField(
        max_length=150, help_text="Nom de famille de l'utilisateur"
    )

    # Champs optionnels
    email = models.EmailField(
        max_length=254, blank=True, null=True, help_text="Adresse email optionnelle"
    )
    address = models.TextField(
        blank=True, null=True, help_text="Adresse physique optionnelle"
    )
    apartment_name = models.CharField(
        max_length=3,
        blank=True,
        null=True,
        help_text="Nom de l'appartement (maximum 3 caractères)",
    )

    # Champs système Django
    is_active = models.BooleanField(
        default=False, help_text="Indique si l'utilisateur peut se connecter"
    )
    is_staff = models.BooleanField(
        default=False, help_text="Indique si l'utilisateur peut accéder à l'admin"
    )
    is_superuser = models.BooleanField(
        default=False, help_text="Indique si l'utilisateur a tous les droits"
    )
    date_joined = models.DateTimeField(
        default=timezone.now, help_text="Date de création du compte"
    )
    last_login = models.DateTimeField(
        blank=True, null=True, help_text="Dernière connexion"
    )

    # Configuration du modèle
    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        db_table = "users_user"
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        """Représentation string de l'utilisateur."""
        return f"{self.first_name} {self.last_name} ({self.phone})"

    def get_full_name(self) -> str:
        """Retourne le nom complet de l'utilisateur."""
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self) -> str:
        """Retourne le prénom de l'utilisateur."""
        return self.first_name

    @property
    def is_admin(self) -> bool:
        """Vérifie si l'utilisateur est administrateur."""
        return self.is_staff or self.is_superuser


class VerificationToken(models.Model):
    """
    Modèle unifié pour tous les tokens de vérification (activation, reset password, etc.).

    Utilise un UUID pour l'identification et un code SMS hashé pour la sécurité.
    Supporte différents types de vérification avec TTL et limitation des tentatives.
    """

    # Types de vérification supportés
    VERIFICATION_TYPES = [
        ("activation", "Activation de compte"),
        ("password_reset", "Réinitialisation de mot de passe"),
        ("password_change", "Changement de mot de passe"),
        ("phone_change", "Changement de numéro de téléphone"),
    ]

    # UUID unique pour l'identification du token
    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text="UUID unique du token de vérification",
    )

    # Type de vérification
    verification_type = models.CharField(
        max_length=20,
        choices=VERIFICATION_TYPES,
        help_text="Type de vérification demandée",
    )

    # Utilisateur associé (peut être null pour password_reset si user n'existe pas)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="verification_tokens",
        null=True,
        blank=True,
        help_text="Utilisateur associé au token",
    )

    # Numéro de téléphone pour les cas où user est null
    phone = models.CharField(
        max_length=15,
        blank=True,
        help_text="Numéro de téléphone pour password_reset",
    )

    # Code SMS hashé
    code_hash = models.CharField(
        max_length=64, help_text="Hash SHA256 du code SMS")

    # Expiration
    expires_at = models.DateTimeField(
        help_text="Date d'expiration du token (10 minutes)"
    )

    # Limitation des tentatives
    attempts = models.PositiveIntegerField(
        default=0, help_text="Nombre de tentatives de vérification (max 5)"
    )

    # Gestion des envois
    last_sent_at = models.DateTimeField(
        help_text="Dernière fois que le code a été envoyé"
    )
    send_count = models.PositiveIntegerField(
        default=1, help_text="Nombre d'envois aujourd'hui (max 5/24h)"
    )

    # État du token
    is_locked = models.BooleanField(
        default=False, help_text="Token verrouillé après 5 tentatives échouées"
    )
    is_used = models.BooleanField(
        default=False, help_text="Token utilisé (one-shot)")

    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="Date de création du token"
    )
    updated_at = models.DateTimeField(
        auto_now=True, help_text="Date de dernière modification"
    )

    class Meta:
        db_table = "users_verification_token"
        verbose_name = "Token de vérification"
        verbose_name_plural = "Tokens de vérification"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["token"]),
            models.Index(fields=["verification_type", "user"]),
            models.Index(fields=["phone"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self) -> str:
        """Représentation string du token."""
        user_info = self.user.phone if self.user else self.phone
        return (
            f"Token {self.verification_type} pour {user_info} (exp: {self.expires_at})"
        )

    @classmethod
    def generate_code(cls) -> str:
        """
        Génère un code de vérification de 6 chiffres.

        Returns:
            str: Code de 6 chiffres
        """
        return str(secrets.randbelow(900000) + 100000)

    @classmethod
    def hash_code(cls, code: str) -> str:
        """
        Hache un code de vérification avec SHA256.

        Args:
            code: Code de vérification en clair

        Returns:
            str: Hash SHA256 du code
        """
        return hashlib.sha256(code.encode()).hexdigest()

    @classmethod
    def create_token(
        cls, verification_type: str, user: User = None, phone: str = None
    ) -> "VerificationToken":
        """
        Crée un nouveau token de vérification.

        Args:
            verification_type: Type de vérification
            user: Utilisateur associé (optionnel)
            phone: Numéro de téléphone (requis si user est None)

        Returns:
            VerificationToken: Token créé

        Raises:
            ValueError: Si les paramètres ne sont pas valides
        """
        if not user and not phone:
            raise ValueError("Either user or phone must be provided")

        # Supprimer les anciens tokens du même type pour cet utilisateur/numéro
        if user:
            cls.objects.filter(
                verification_type=verification_type, user=user, is_used=False
            ).delete()
        else:
            cls.objects.filter(
                verification_type=verification_type, phone=phone, is_used=False
            ).delete()

        # Générer un nouveau code
        code = cls.generate_code()
        code_hash = cls.hash_code(str(code))

        # Calculer l'expiration (10 minutes)
        expires_at = timezone.now() + timedelta(minutes=10)

        # Créer le token
        token = cls.objects.create(
            verification_type=verification_type,
            user=user,
            phone=phone,
            code_hash=code_hash,
            expires_at=expires_at,
            last_sent_at=timezone.now(),
            send_count=1,
        )

        return token

    def is_expired(self) -> bool:
        """
        Vérifie si le token est expiré.

        Returns:
            bool: True si expiré
        """
        return timezone.now() > self.expires_at

    def is_max_attempts_reached(self) -> bool:
        """
        Vérifie si le nombre maximum de tentatives est atteint.

        Returns:
            bool: True si max atteint
        """
        return self.attempts >= 5

    def can_send_new_code(self) -> bool:
        """
        Vérifie si un nouveau code peut être envoyé.

        Returns:
            bool: True si possible
        """
        # Vérifier le cooldown de 60 secondes
        time_since_last = timezone.now() - self.last_sent_at
        if time_since_last.total_seconds() < 60:
            return False

        # Vérifier le quota de 5 envois par jour
        if self.send_count >= 5:
            # Réinitialiser le compteur si c'est un nouveau jour
            today = timezone.now().date()
            last_sent_date = self.last_sent_at.date()
            if today > last_sent_date:
                self.send_count = 0
                self.save(update_fields=["send_count"])
                return True
            return False

        return True

    def increment_attempts(self) -> None:
        """
        Incrémente le nombre de tentatives et verrouille si nécessaire.
        """
        self.attempts += 1
        if self.attempts >= 5:
            self.is_locked = True
        self.save(update_fields=["attempts", "is_locked"])

    def verify_code(self, code: str) -> bool:
        """
        Vérifie un code de vérification.

        Args:
            code: Code à vérifier

        Returns:
            bool: True si le code est correct
        """
        if self.is_expired():
            return False

        if self.is_max_attempts_reached() or self.is_locked or self.is_used:
            return False

        code_hash = self.hash_code(code)
        is_valid = code_hash == self.code_hash

        if not is_valid:
            self.increment_attempts()

        return is_valid

    def mark_as_used(self) -> None:
        """
        Marque le token comme utilisé (one-shot).
        """
        self.is_used = True
        self.save(update_fields=["is_used"])

    def get_user_or_phone(self) -> str:
        """
        Retourne l'utilisateur ou le numéro de téléphone associé.

        Returns:
            str: Phone de l'utilisateur ou numéro direct
        """
        return self.user.phone if self.user else self.phone


class ActivationToken(models.Model):
    """
    Modèle pour les tokens d'activation par SMS.

    Stocke les codes d'activation avec hashage sécurisé,
    expiration et limitation des tentatives.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="activation_token",
        help_text="Utilisateur associé au token d'activation",
    )
    code_hash = models.CharField(
        max_length=64,
        help_text="Hash SHA256 du code d'activation",
    )
    expires_at = models.DateTimeField(
        help_text="Date d'expiration du token (10 minutes)"
    )
    attempts = models.PositiveIntegerField(
        default=0,
        help_text="Nombre de tentatives de vérification (max 5)",
    )
    last_sent_at = models.DateTimeField(
        help_text="Dernière fois que le code a été envoyé",
    )
    send_count = models.PositiveIntegerField(
        default=1,
        help_text="Nombre d'envois aujourd'hui (max 5/24h)",
    )
    is_locked = models.BooleanField(
        default=False,
        help_text="Token verrouillé après 5 tentatives échouées",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date de création du token",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Date de dernière modification",
    )

    class Meta:
        db_table = "users_activation_token"
        verbose_name = "Token d'activation"
        verbose_name_plural = "Tokens d'activation"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Représentation string du token."""
        return f"Token activation pour {self.user.phone} (exp: {self.expires_at})"

    @classmethod
    def generate_code(cls) -> str:
        """
        Génère un code d'activation de 6 chiffres.

        Returns:
            str: Code de 6 chiffres
        """
        return str(secrets.randbelow(900000) + 100000)

    @classmethod
    def hash_code(cls, code: str) -> str:
        """
        Hache un code d'activation avec SHA256.

        Args:
            code: Code d'activation en clair

        Returns:
            str: Hash SHA256 du code
        """
        return hashlib.sha256(code.encode()).hexdigest()

    @classmethod
    def create_token(cls, user: User) -> "ActivationToken":
        """
        Crée un nouveau token d'activation pour un utilisateur.

        Args:
            user: Utilisateur pour lequel créer le token

        Returns:
            ActivationToken: Token créé
        """
        # Supprimer l'ancien token s'il existe
        cls.objects.filter(user=user).delete()

        # Générer un nouveau code
        code = cls.generate_code()
        code_hash = cls.hash_code(str(code))

        # Calculer l'expiration (10 minutes)
        expires_at = timezone.now() + timedelta(minutes=10)

        # Créer le token
        token = cls.objects.create(
            user=user,
            code_hash=code_hash,
            expires_at=expires_at,
            last_sent_at=timezone.now(),
            send_count=1,
        )

        return token

    def is_expired(self) -> bool:
        """
        Vérifie si le token est expiré.

        Returns:
            bool: True si expiré
        """
        return timezone.now() > self.expires_at

    def is_max_attempts_reached(self) -> bool:
        """
        Vérifie si le nombre maximum de tentatives est atteint.

        Returns:
            bool: True si max atteint
        """
        return self.attempts >= 5

    def can_send_new_code(self) -> bool:
        """
        Vérifie si un nouveau code peut être envoyé.

        Returns:
            bool: True si possible
        """
        # Vérifier le cooldown de 60 secondes
        time_since_last = timezone.now() - self.last_sent_at
        if time_since_last.total_seconds() < 60:
            return False

        # Vérifier le quota de 5 envois par jour
        if self.send_count >= 5:
            # Réinitialiser le compteur si c'est un nouveau jour
            today = timezone.now().date()
            last_sent_date = self.last_sent_at.date()
            if today > last_sent_date:
                self.send_count = 0
                self.save(update_fields=["send_count"])
                return True
            return False

        return True

    def increment_attempts(self) -> None:
        """
        Incrémente le nombre de tentatives et verrouille si nécessaire.
        """
        self.attempts += 1
        if self.attempts >= 5:
            self.is_locked = True
        self.save(update_fields=["attempts", "is_locked"])

    def verify_code(self, code: str) -> bool:
        """
        Vérifie un code d'activation.

        Args:
            code: Code à vérifier

        Returns:
            bool: True si le code est correct
        """
        if self.is_expired():
            return False

        if self.is_max_attempts_reached() or self.is_locked:
            return False

        code_hash = self.hash_code(code)
        is_valid = code_hash == self.code_hash

        if not is_valid:
            self.increment_attempts()

        return is_valid

    def activate_user(self) -> None:
        """
        Active l'utilisateur et supprime le token.
        """
        self.user.is_active = True
        self.user.save(update_fields=["is_active"])
        self.delete()
