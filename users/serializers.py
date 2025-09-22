"""
Serializers pour l'authentification des utilisateurs WaterBill.

Ce module définit les serializers pour l'inscription, connexion
et gestion des utilisateurs avec validation des données.
"""

from .utils.phone_utils import normalize_phone, validate_phone_length
from .models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers

# Messages d'erreur constants
PHONE_REQUIRED_ERROR = "Le numéro de téléphone est obligatoire."
PHONE_INVALID_ERROR = "Le numéro de téléphone est invalide."
PHONE_LENGTH_ERROR = "Le numéro de téléphone doit contenir entre 9 et 15 chiffres."
PHONE_HELP_TEXT = "Numéro de téléphone (minimum 9 chiffres)"
STATUS_HELP_TEXT = "Statut de la réponse"
MESSAGE_HELP_TEXT = "Message de confirmation"


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer pour la représentation des utilisateurs.

    Utilisé pour retourner les informations utilisateur
    après inscription ou connexion.
    """

    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "phone",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "address",
            "apartment_name",
            "date_joined",
            "is_active",
        ]
        read_only_fields = ["id", "date_joined", "is_active"]


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'inscription des utilisateurs.

    Valide les données d'inscription et crée un nouvel utilisateur.
    """

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
        help_text="Mot de passe (minimum 8 caractères)",
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        help_text="Confirmation du mot de passe",
    )

    class Meta:
        model = User
        fields = [
            "phone",
            "first_name",
            "last_name",
            "email",
            "address",
            "apartment_name",
            "password",
            "password_confirm",
        ]
        extra_kwargs = {
            "phone": {
                "help_text": "Numéro de téléphone unique (ex: 670000000) - minimum 9 chiffres"
            },
            "first_name": {"help_text": "Prénom de l'utilisateur"},
            "last_name": {"help_text": "Nom de famille"},
            "email": {"required": False, "help_text": "Adresse email (optionnelle)"},
            "address": {
                "required": False,
                "help_text": "Adresse physique (optionnelle)",
            },
            "apartment_name": {
                "required": False,
                "help_text": "Nom de l'appartement (maximum 3 caractères)",
            },
        }

    def validate_phone(self, value: str) -> str:
        """
        Valide et nettoie le numéro de téléphone au format international.

        Args:
            value: Numéro de téléphone à valider

        Returns:
            str: Numéro de téléphone au format international (+XXXXXXXXX)

        Raises:
            ValidationError: Si le numéro n'est pas valide
        """
        if not value:
            raise serializers.ValidationError(PHONE_REQUIRED_ERROR)

        # Normaliser le numéro avec l'utilitaire
        international_phone = normalize_phone(value)

        if not international_phone:
            raise serializers.ValidationError(PHONE_INVALID_ERROR)

        # Validation de la longueur après normalisation
        if not validate_phone_length(international_phone, min_length=9, max_length=15):
            raise serializers.ValidationError(PHONE_LENGTH_ERROR)

        # Vérifier l'unicité avec le format international
        if User.objects.filter(phone=international_phone).exists():
            raise serializers.ValidationError(
                "Un utilisateur avec ce numéro de téléphone existe déjà."
            )

        return international_phone

    def validate_password(self, value: str) -> str:
        """
        Valide le mot de passe.

        Args:
            value: Mot de passe à valider

        Returns:
            str: Mot de passe validé

        Raises:
            ValidationError: Si le mot de passe n'est pas valide
        """
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)

        return value

    def validate_apartment_name(self, value: str) -> str:
        """
        Valide le nom de l'appartement.

        Args:
            value: Nom de l'appartement à valider

        Returns:
            str: Nom validé

        Raises:
            ValidationError: Si le nom n'est pas valide
        """
        if value and len(value) > 3:
            raise serializers.ValidationError(
                "Le nom de l'appartement ne peut pas dépasser 3 caractères."
            )
        return value

    def validate(self, attrs: dict) -> dict:
        """
        Valide les données complètes d'inscription.

        Args:
            attrs: Dictionnaire des données à valider

        Returns:
            dict: Données validées

        Raises:
            ValidationError: Si les données ne sont pas valides
        """
        password = attrs.get("password")
        password_confirm = attrs.get("password_confirm")

        if password != password_confirm:
            raise serializers.ValidationError(
                {"password_confirm": "Les mots de passe ne correspondent pas."}
            )

        return attrs

    def create(self, validated_data: dict) -> User:
        """
        Crée un nouvel utilisateur.

        Args:
            validated_data: Données validées pour la création

        Returns:
            User: Instance de l'utilisateur créé
        """
        # Supprimer password_confirm des données
        validated_data.pop("password_confirm")

        # Créer l'utilisateur
        user = User.objects.create_user(**validated_data)

        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer pour la connexion des utilisateurs.

    Valide les données de connexion (téléphone + mot de passe).
    """

    phone = serializers.CharField(help_text=PHONE_HELP_TEXT)
    password = serializers.CharField(
        write_only=True, style={"input_type": "password"}, help_text="Mot de passe"
    )

    def validate_phone(self, value: str) -> str:
        """
        Valide et nettoie le numéro de téléphone au format international.

        Args:
            value: Numéro de téléphone à valider

        Returns:
            str: Numéro de téléphone au format international (+XXXXXXXXX)
        """
        if not value:
            raise serializers.ValidationError(PHONE_REQUIRED_ERROR)

        # Normaliser le numéro avec l'utilitaire
        international_phone = normalize_phone(value)

        if not international_phone:
            raise serializers.ValidationError(PHONE_INVALID_ERROR)

        # Validation de la longueur après normalisation
        if not validate_phone_length(international_phone, min_length=9, max_length=15):
            raise serializers.ValidationError(PHONE_LENGTH_ERROR)

        return international_phone


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer JWT personnalisé pour l'authentification.

    Ajoute les informations utilisateur aux tokens JWT.
    """

    @classmethod
    def get_token(cls, user: User):
        """
        Génère les tokens JWT avec les informations utilisateur.

        Args:
            user: Instance de l'utilisateur

        Returns:
            Token: Token JWT avec claims personnalisés
        """
        token = super().get_token(user)

        # Ajouter des informations personnalisées au token
        token["phone"] = user.phone
        token["first_name"] = user.first_name
        token["last_name"] = user.last_name
        token["full_name"] = user.get_full_name()

        return token


# Serializers pour les réponses API (documentation Swagger)
class TokenSerializer(serializers.Serializer):
    """Serializer pour les tokens JWT dans les réponses."""

    access = serializers.CharField(help_text="Token d'accès JWT")
    refresh = serializers.CharField(help_text="Token de rafraîchissement JWT")


class AuthResponseSerializer(serializers.Serializer):
    """Serializer pour les réponses d'authentification."""

    status = serializers.CharField(help_text="Statut de la réponse (success/error)")
    message = serializers.CharField(help_text="Message descriptif")
    data = serializers.DictField(help_text="Données de la réponse")


class AuthDataSerializer(serializers.Serializer):
    """Serializer pour les données d'authentification."""

    user = UserSerializer(help_text="Informations de l'utilisateur")
    tokens = TokenSerializer(help_text="Tokens JWT (access et refresh)")


class RegisterResponseSerializer(serializers.Serializer):
    """Serializer pour les réponses d'inscription."""

    status = serializers.CharField(help_text=STATUS_HELP_TEXT)
    message = serializers.CharField(help_text=MESSAGE_HELP_TEXT)
    data = serializers.JSONField(
        help_text="Données de la réponse (message simple)",
        required=False,
        allow_null=True,
    )


class LoginResponseSerializer(serializers.Serializer):
    """Serializer pour les réponses de connexion."""

    status = serializers.CharField(help_text=STATUS_HELP_TEXT)
    message = serializers.CharField(help_text=MESSAGE_HELP_TEXT)
    data = AuthDataSerializer(help_text="Données utilisateur et tokens")


class ProfileDataSerializer(serializers.Serializer):
    """Serializer pour les données de profil."""

    user = UserSerializer(help_text="Informations complètes du profil utilisateur")


class ProfileResponseSerializer(serializers.Serializer):
    """Serializer pour les réponses de profil."""

    status = serializers.CharField(help_text=STATUS_HELP_TEXT)
    message = serializers.CharField(help_text=MESSAGE_HELP_TEXT)
    data = ProfileDataSerializer(help_text="Données du profil utilisateur")


class ActivateSerializer(serializers.Serializer):
    """
    Serializer pour la vérification du code d'activation.

    Valide le numéro de téléphone et le code d'activation.
    """

    phone = serializers.CharField(help_text=PHONE_HELP_TEXT)
    code = serializers.CharField(
        min_length=6,
        max_length=6,
        help_text="Code d'activation à 6 chiffres",
    )

    def validate_phone(self, value: str) -> str:
        """
        Valide et nettoie le numéro de téléphone au format international.

        Args:
            value: Numéro de téléphone à valider

        Returns:
            str: Numéro de téléphone au format international (+XXXXXXXXX)
        """
        if not value:
            raise serializers.ValidationError(PHONE_REQUIRED_ERROR)

        # Normaliser le numéro avec l'utilitaire
        international_phone = normalize_phone(value)

        if not international_phone:
            raise serializers.ValidationError(PHONE_INVALID_ERROR)

        # Validation de la longueur après normalisation
        if not validate_phone_length(international_phone, min_length=9, max_length=15):
            raise serializers.ValidationError(PHONE_LENGTH_ERROR)

        return international_phone

    def validate_code(self, value: str) -> str:
        """
        Valide le format du code d'activation.

        Args:
            value: Code à valider

        Returns:
            str: Code validé
        """
        if not value.isdigit():
            raise serializers.ValidationError(
                "Le code d'activation doit contenir uniquement des chiffres."
            )

        if len(value) != 6:
            raise serializers.ValidationError(
                "Le code d'activation doit contenir exactement 6 chiffres."
            )

        return value


class ResendCodeSerializer(serializers.Serializer):
    """
    Serializer pour la demande de renvoi de code d'activation.

    Valide le numéro de téléphone pour le renvoi.
    """

    phone = serializers.CharField(help_text=PHONE_HELP_TEXT)

    def validate_phone(self, value: str) -> str:
        """
        Valide et nettoie le numéro de téléphone au format international.

        Args:
            value: Numéro de téléphone à valider

        Returns:
            str: Numéro de téléphone au format international (+XXXXXXXXX)
        """
        if not value:
            raise serializers.ValidationError(PHONE_REQUIRED_ERROR)

        # Normaliser le numéro avec l'utilitaire
        international_phone = normalize_phone(value)

        if not international_phone:
            raise serializers.ValidationError(PHONE_INVALID_ERROR)

        # Validation de la longueur après normalisation
        if not validate_phone_length(international_phone, min_length=9, max_length=15):
            raise serializers.ValidationError(PHONE_LENGTH_ERROR)

        return international_phone


class ActivationDataSerializer(serializers.Serializer):
    """Serializer pour les données d'activation."""

    user = UserSerializer(help_text="Informations de l'utilisateur activé")


class ActivationResponseSerializer(serializers.Serializer):
    """Serializer pour les réponses d'activation."""

    status = serializers.CharField(help_text=STATUS_HELP_TEXT)
    message = serializers.CharField(help_text=MESSAGE_HELP_TEXT)
    data = ActivationDataSerializer(help_text="Données utilisateur")


class SimpleResponseSerializer(serializers.Serializer):
    """Serializer pour les réponses simples (sans données complexes)."""

    status = serializers.CharField(help_text=STATUS_HELP_TEXT)
    message = serializers.CharField(help_text=MESSAGE_HELP_TEXT)
    data = serializers.JSONField(
        help_text="Données de la réponse (peut être un objet vide)",
        required=False,
        allow_null=True,
    )


class ErrorResponseSerializer(serializers.Serializer):
    """Serializer pour les réponses d'erreur."""

    status = serializers.CharField(help_text="Statut de la réponse (error)")
    message = serializers.CharField(help_text="Message d'erreur")
    data = serializers.JSONField(
        help_text="Données d'erreur (peut être un objet vide ou des détails d'erreur)",
        required=False,
        allow_null=True,
    )


class TokenRefreshSerializer(serializers.Serializer):
    """
    Serializer pour le rafraîchissement de token JWT.
    """

    refresh = serializers.CharField(
        help_text="Refresh token JWT à utiliser pour obtenir un nouveau access token"
    )

    def validate_refresh(self, value: str) -> str:
        """
        Valide le refresh token.

        Args:
            value: Refresh token à valider

        Returns:
            str: Refresh token validé

        Raises:
            ValidationError: Si le token n'est pas valide
        """
        if not value:
            raise serializers.ValidationError("Le refresh token est obligatoire.")

        try:
            from rest_framework_simplejwt.tokens import RefreshToken

            RefreshToken(value)
        except Exception:
            raise serializers.ValidationError("Refresh token invalide ou expiré.")

        return value


class TokenRefreshResponseSerializer(serializers.Serializer):
    """
    Serializer pour la réponse de rafraîchissement de token.
    """

    access = serializers.CharField(help_text="Nouveau access token JWT")


class LogoutSerializer(serializers.Serializer):
    """
    Serializer pour la déconnexion avec blacklist du refresh token.
    """

    refresh = serializers.CharField(
        help_text="Refresh token JWT à ajouter à la blacklist"
    )

    def validate_refresh(self, value: str) -> str:
        """
        Valide le refresh token avant de le blacklister.

        Args:
            value: Refresh token à valider

        Returns:
            str: Refresh token validé

        Raises:
            ValidationError: Si le token n'est pas valide
        """
        if not value:
            raise serializers.ValidationError("Le refresh token est obligatoire.")

        try:
            from rest_framework_simplejwt.tokens import RefreshToken

            token = RefreshToken(value)
            # Vérifier que le token n'est pas déjà blacklisté
            token.check_blacklist()
        except Exception:
            raise serializers.ValidationError(
                "Refresh token invalide ou déjà blacklisté."
            )

        return value

    def save(self):
        """
        Blackliste le refresh token.
        """
        try:
            from rest_framework_simplejwt.tokens import RefreshToken

            token = RefreshToken(self.validated_data["refresh"])
            token.blacklist()
        except Exception as e:
            raise serializers.ValidationError(
                f"Erreur lors de la déconnexion: {str(e)}"
            )


class LogoutResponseSerializer(serializers.Serializer):
    """
    Serializer pour la réponse de déconnexion.
    """

    status = serializers.CharField(help_text=STATUS_HELP_TEXT)
    message = serializers.CharField(help_text=MESSAGE_HELP_TEXT)
