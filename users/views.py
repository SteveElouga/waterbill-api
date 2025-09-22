"""
Vues API pour l'authentification des utilisateurs WaterBill.

Ce module implémente les endpoints d'inscription et connexion
avec gestion des erreurs et documentation OpenAPI.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.request import Request
from drf_spectacular.utils import extend_schema

from .throttling import (
    LoginRateThrottle,
    RegisterRateThrottle,
    AuthRateThrottle,
    ActivateRateThrottle,
    ResendCodeRateThrottle,
    PhoneBasedThrottle,
)

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    ActivateSerializer,
    ResendCodeSerializer,
    RegisterResponseSerializer,
    LoginResponseSerializer,
    ActivationResponseSerializer,
    SimpleResponseSerializer,
    ProfileResponseSerializer,
    ErrorResponseSerializer,
    TokenRefreshSerializer,
    TokenRefreshResponseSerializer,
    LogoutSerializer,
    LogoutResponseSerializer,
)
from .services import AuthService, ActivationService, ResponseService


@extend_schema(
    summary="Inscription d'un nouvel utilisateur",
    description="""
    Crée un nouveau compte utilisateur inactif avec authentification par numéro de téléphone.
    Un code d'activation est envoyé par SMS pour activer le compte.

    **Endpoint:** `POST /api/auth/register/`

    **Champs obligatoires:**
    - `phone`: Numéro de téléphone unique (ex: 670000000) - minimum 9 chiffres
    - `first_name`: Prénom de l'utilisateur
    - `last_name`: Nom de famille
    - `password`: Mot de passe (minimum 8 caractères)
    - `password_confirm`: Confirmation du mot de passe

    **Champs optionnels:**
    - `email`: Adresse email
    - `address`: Adresse physique
    - `apartment_name`: Nom de l'appartement (maximum 3 caractères)

    **Retourne:**
    - Message de confirmation
    - Code d'activation envoyé par SMS (à vérifier via /api/auth/activate/)
    """,
    request=RegisterSerializer,
    responses={201: RegisterResponseSerializer, 400: ErrorResponseSerializer},
    tags=["Authentification"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([RegisterRateThrottle, AuthRateThrottle])
def register_view(request: Request) -> Response:
    """
    Endpoint d'inscription d'un nouvel utilisateur.

    Crée un nouveau compte utilisateur inactif et envoie un code d'activation par SMS.

    Args:
        request: Requête HTTP contenant les données d'inscription

    Returns:
        Response: Réponse JSON avec message de confirmation
    """
    serializer = RegisterSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            ResponseService.error_response(
                message="Données d'inscription invalides", errors=serializer.errors
            ),
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        # Créer l'utilisateur inactif et envoyer le code d'activation
        user = AuthService.register_user(serializer.validated_data)

        return Response(
            ResponseService.success_response(
                message="Compte créé avec succès. Un code d'activation a été envoyé par SMS.",
                data={"phone": user.phone},
            ),
            status=status.HTTP_201_CREATED,
        )

    except ValueError as e:
        return Response(
            ResponseService.error_response(message=str(e)),
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception:
        return Response(
            ResponseService.error_response(message="Erreur interne du serveur"),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@extend_schema(
    summary="Connexion d'un utilisateur",
    description="""
    Authentifie un utilisateur existant avec son numéro de téléphone et mot de passe.
    Refuse la connexion si le compte n'est pas activé.

    **Endpoint:** `POST /api/auth/login/`

    **Champs obligatoires:**
    - `phone`: Numéro de téléphone de l'utilisateur (minimum 9 chiffres)
    - `password`: Mot de passe

    **Retourne:**
    - Informations utilisateur
    - Tokens JWT (access + refresh)

    **Erreurs possibles:**
    - Compte non activé (utilisez /api/auth/activate/ pour activer)
    - Identifiants incorrects
    """,
    request=LoginSerializer,
    responses={200: LoginResponseSerializer, 400: ErrorResponseSerializer},
    tags=["Authentification"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle, AuthRateThrottle])
def login_view(request: Request) -> Response:
    """
    Endpoint de connexion d'un utilisateur.

    Authentifie un utilisateur existant et retourne
    ses informations + tokens JWT.

    Args:
        request: Requête HTTP contenant les données de connexion

    Returns:
        Response: Réponse JSON avec statut et données
    """
    serializer = LoginSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            ResponseService.error_response(
                message="Données de connexion invalides", errors=serializer.errors
            ),
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        # Authentifier l'utilisateur et générer les tokens
        user, tokens = AuthService.login_user(
            phone=serializer.validated_data["phone"],
            password=serializer.validated_data["password"],
        )

        # Sérialiser les données utilisateur
        user_data = UserSerializer(user).data

        # Préparer la réponse
        response_data = {"user": user_data, "tokens": tokens}

        return Response(
            ResponseService.success_response(
                message="Connexion réussie", data=response_data
            ),
            status=status.HTTP_200_OK,
        )

    except ValueError as e:
        return Response(
            ResponseService.error_response(message=str(e)),
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception:
        return Response(
            ResponseService.error_response(message="Erreur interne du serveur"),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@extend_schema(
    summary="Profil utilisateur connecté",
    description="""
    Récupère les informations du profil de l'utilisateur connecté.

    **Endpoint:** `GET /api/auth/profile/`

    **Authentification requise:**
    - Token JWT dans l'en-tête Authorization: Bearer <token>

    **Retourne:**
    - Informations complètes du profil utilisateur
    """,
    responses={200: ProfileResponseSerializer, 401: ErrorResponseSerializer},
    tags=["Profil"],
)
@api_view(["GET"])
def profile_view(request: Request) -> Response:
    """
    Endpoint pour récupérer le profil de l'utilisateur connecté.

    Retourne les informations complètes du profil utilisateur
    authentifié via JWT.

    Args:
        request: Requête HTTP avec utilisateur authentifié

    Returns:
        Response: Réponse JSON avec le profil utilisateur
    """
    user_data = AuthService.get_user_profile(request.user)

    return Response(
        ResponseService.success_response(
            message="Profil récupéré avec succès", data={"user": user_data}
        ),
        status=status.HTTP_200_OK,
    )


@extend_schema(
    summary="Activation du compte utilisateur",
    description="""
    Active un compte utilisateur avec le code d'activation reçu par SMS.

    **Endpoint:** `POST /api/auth/activate/`

    **Champs obligatoires:**
    - `phone`: Numéro de téléphone de l'utilisateur (minimum 9 chiffres)
    - `code`: Code d'activation à 6 chiffres reçu par SMS

    **Retourne:**
    - Utilisateur activé
    - Message de confirmation

    **Erreurs possibles:**
    - Code incorrect ou expiré
    - Trop de tentatives échouées (compte verrouillé)
    - Utilisateur déjà activé
    """,
    request=ActivateSerializer,
    responses={200: ActivationResponseSerializer, 400: ErrorResponseSerializer},
    tags=["Authentification"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([ActivateRateThrottle, PhoneBasedThrottle])
def activate_view(request: Request) -> Response:
    """
    Endpoint d'activation du compte utilisateur.

    Vérifie le code d'activation et active le compte utilisateur.

    Args:
        request: Requête HTTP contenant le téléphone et le code

    Returns:
        Response: Réponse JSON avec utilisateur activé
    """
    serializer = ActivateSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            ResponseService.error_response(
                message="Données d'activation invalides", errors=serializer.errors
            ),
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        # Vérifier le code et activer l'utilisateur
        user = ActivationService.verify_activation_code(
            phone=serializer.validated_data["phone"],
            code=serializer.validated_data["code"],
        )

        # Sérialiser les données utilisateur
        user_data = UserSerializer(user).data

        # Préparer la réponse (sans tokens JWT)
        response_data = {"user": user_data}

        return Response(
            ResponseService.success_response(
                message="Compte activé avec succès. Vous pouvez maintenant vous connecter.",
                data=response_data,
            ),
            status=status.HTTP_200_OK,
        )

    except ValueError as e:
        return Response(
            ResponseService.error_response(message=str(e)),
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception:
        return Response(
            ResponseService.error_response(message="Erreur interne du serveur"),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@extend_schema(
    summary="Renvoi du code d'activation",
    description="""
    Renvoie un nouveau code d'activation par SMS pour un utilisateur.

    **Endpoint:** `POST /api/auth/resend-code/`

    **Champs obligatoires:**
    - `phone`: Numéro de téléphone de l'utilisateur (minimum 9 chiffres)

    **Limites:**
    - 1 envoi par minute maximum
    - 5 envois par jour maximum

    **Retourne:**
    - Message de confirmation

    **Erreurs possibles:**
    - Trop de demandes (respectez les limites)
    - Utilisateur déjà activé
    - Compte verrouillé
    """,
    request=ResendCodeSerializer,
    responses={200: SimpleResponseSerializer, 400: ErrorResponseSerializer},
    tags=["Authentification"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([ResendCodeRateThrottle, PhoneBasedThrottle])
def resend_code_view(request: Request) -> Response:
    """
    Endpoint de renvoi du code d'activation.

    Renvoie un nouveau code d'activation par SMS avec respect des limites.

    Args:
        request: Requête HTTP contenant le téléphone

    Returns:
        Response: Réponse JSON avec message de confirmation
    """
    serializer = ResendCodeSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            ResponseService.error_response(
                message="Données invalides", errors=serializer.errors
            ),
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        # Renvoyer le code d'activation
        ActivationService.resend_activation_code(
            phone=serializer.validated_data["phone"]
        )

        return Response(
            ResponseService.success_response(
                message="Code d'activation renvoyé avec succès",
                data={"phone": serializer.validated_data["phone"]},
            ),
            status=status.HTTP_200_OK,
        )

    except ValueError as e:
        return Response(
            ResponseService.error_response(message=str(e)),
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception:
        return Response(
            ResponseService.error_response(message="Erreur interne du serveur"),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@extend_schema(
    summary="Rafraîchissement du token JWT",
    description="""
    Génère un nouveau access token à partir d'un refresh token valide.

    **Endpoint:** `POST /api/auth/token/refresh/`

    **Champs obligatoires:**
    - `refresh`: Refresh token JWT valide

    **Retourne:**
    - Nouveau access token JWT (durée: 15 minutes)

    **Erreurs possibles:**
    - Refresh token invalide ou expiré
    - Refresh token blacklisté
    """,
    request=TokenRefreshSerializer,
    responses={200: TokenRefreshResponseSerializer, 400: ErrorResponseSerializer},
    tags=["Authentification"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def token_refresh_view(request: Request) -> Response:
    """
    Vue pour rafraîchir un token JWT.

    Args:
        request: Requête HTTP contenant le refresh token

    Returns:
        Response: Nouveau access token ou erreur
    """
    try:
        serializer = TokenRefreshSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                ResponseService.error_response(
                    message="Données invalides",
                    errors=serializer.errors,
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Générer un nouveau access token
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh_token = RefreshToken(serializer.validated_data["refresh"])
        access_token = refresh_token.access_token

        return Response(
            {"access": str(access_token)},
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        return Response(
            ResponseService.error_response(
                message=f"Erreur lors du rafraîchissement: {str(e)}"
            ),
            status=status.HTTP_400_BAD_REQUEST,
        )


@extend_schema(
    summary="Déconnexion utilisateur",
    description="""
    Déconnecte un utilisateur en ajoutant son refresh token à la blacklist.

    **Endpoint:** `POST /api/auth/logout/`

    **Champs obligatoires:**
    - `refresh`: Refresh token JWT à blacklister

    **Action:**
    - Ajoute le refresh token dans la blacklist
    - Empêche toute utilisation future de ce token

    **Retourne:**
    - Message de confirmation de déconnexion

    **Erreurs possibles:**
    - Refresh token invalide
    - Refresh token déjà blacklisté
    """,
    request=LogoutSerializer,
    responses={200: LogoutResponseSerializer, 400: ErrorResponseSerializer},
    tags=["Authentification"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def logout_view(request: Request) -> Response:
    """
    Vue pour déconnecter un utilisateur.

    Args:
        request: Requête HTTP contenant le refresh token à blacklister

    Returns:
        Response: Message de confirmation ou erreur
    """
    try:
        serializer = LogoutSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                ResponseService.error_response(
                    message="Données invalides",
                    errors=serializer.errors,
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Blacklister le refresh token
        serializer.save()

        return Response(
            ResponseService.success_response(message="Déconnexion réussie"),
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        return Response(
            ResponseService.error_response(
                message=f"Erreur lors de la déconnexion: {str(e)}"
            ),
            status=status.HTTP_400_BAD_REQUEST,
        )
