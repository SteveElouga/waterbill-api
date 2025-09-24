"""
Vues API pour la gestion de la liste blanche des numéros de téléphone.

Ce module implémente les endpoints d'administration pour gérer
la liste blanche des numéros autorisés à créer un compte.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.request import Request
from drf_spectacular.utils import extend_schema

from .throttling import AdminRateThrottle
from .serializers import (
    PhoneWhitelistSerializer,
    PhoneWhitelistAddSerializer,
    PhoneWhitelistCheckSerializer,
    PhoneWhitelistResponseSerializer,
    ErrorResponseSerializer,
)
from .services import ResponseService

# Constantes pour les messages d'erreur
INVALID_DATA_ERROR_MESSAGE = "Données invalides"


@extend_schema(
    summary="Liste tous les numéros de la liste blanche",
    description="""
    Récupère tous les numéros de téléphone autorisés à créer un compte.
    Nécessite des droits d'administrateur.
    """,
    responses={
        200: PhoneWhitelistResponseSerializer,
        403: ErrorResponseSerializer,
    },
    tags=["Administration"],
    auth=[{"jwtAuth": []}],
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
@throttle_classes([AdminRateThrottle])
def phone_whitelist_list_view(request: Request) -> Response:
    """
    Liste tous les numéros de la liste blanche.
    """
    try:
        from .models import PhoneWhitelist

        whitelist_items = PhoneWhitelist.objects.select_related("added_by").order_by(
            "-added_at"
        )
        serializer = PhoneWhitelistSerializer(whitelist_items, many=True)

        return Response(
            ResponseService.success_response(
                message=f"Liste blanche récupérée ({len(serializer.data)} numéros)",
                data={
                    "whitelist": serializer.data,
                    "total_count": len(serializer.data),
                    "active_count": len(
                        [item for item in serializer.data if item["is_active"]]
                    ),
                },
            ),
            status=status.HTTP_200_OK,
        )

    except Exception:
        return Response(
            ResponseService.error_response(
                message="Erreur lors de la récupération de la liste blanche",
                errors={"detail": "Erreur interne du serveur"},
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@extend_schema(
    summary="Ajoute un numéro à la liste blanche",
    description="""
    Ajoute un nouveau numéro de téléphone à la liste blanche.
    Nécessite des droits d'administrateur.
    """,
    request=PhoneWhitelistAddSerializer,
    responses={
        201: PhoneWhitelistResponseSerializer,
        400: ErrorResponseSerializer,
        403: ErrorResponseSerializer,
    },
    tags=["Administration"],
    auth=[{"jwtAuth": []}],
)
@api_view(["POST"])
@permission_classes([IsAdminUser])
@throttle_classes([AdminRateThrottle])
def phone_whitelist_add_view(request: Request) -> Response:
    """
    Ajoute un numéro à la liste blanche.
    """
    try:
        from .models import PhoneWhitelist

        serializer = PhoneWhitelistAddSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                ResponseService.error_response(
                    message=INVALID_DATA_ERROR_MESSAGE,
                    errors=serializer.errors,
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_data = serializer.validated_data
        whitelist_item = PhoneWhitelist.objects.create(
            phone=validated_data["phone"],
            added_by=request.user,
            notes=validated_data.get("notes", ""),
            is_active=validated_data.get("is_active", True),
        )

        response_serializer = PhoneWhitelistSerializer(whitelist_item)

        return Response(
            ResponseService.success_response(
                message=f"Numéro {validated_data['phone']} ajouté à la liste blanche",
                data={"whitelist_item": response_serializer.data},
            ),
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        return Response(
            ResponseService.error_response(
                message="Erreur lors de l'ajout du numéro",
                errors={"detail": str(e)},
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@extend_schema(
    summary="Vérifie si un numéro est dans la liste blanche",
    description="""
    Vérifie si un numéro de téléphone est autorisé à créer un compte.
    Nécessite des droits d'administrateur.
    """,
    request=PhoneWhitelistCheckSerializer,
    responses={
        200: PhoneWhitelistResponseSerializer,
        400: ErrorResponseSerializer,
        403: ErrorResponseSerializer,
    },
    tags=["Administration"],
    auth=[{"jwtAuth": []}],
)
@api_view(["POST"])
@permission_classes([IsAdminUser])
@throttle_classes([AdminRateThrottle])
def phone_whitelist_check_view(request: Request) -> Response:
    """
    Vérifie si un numéro est dans la liste blanche.
    """
    try:
        from .models import PhoneWhitelist

        serializer = PhoneWhitelistCheckSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                ResponseService.error_response(
                    message=INVALID_DATA_ERROR_MESSAGE,
                    errors=serializer.errors,
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        phone = serializer.validated_data["phone"]
        is_authorized = PhoneWhitelist.is_phone_authorized(phone)

        # Récupérer les détails si le numéro est autorisé
        whitelist_item = None
        if is_authorized:
            try:
                whitelist_item = PhoneWhitelist.objects.select_related("added_by").get(
                    phone=phone, is_active=True
                )
            except PhoneWhitelist.DoesNotExist:
                is_authorized = False

        response_data = {
            "phone": phone,
            "is_authorized": is_authorized,
        }

        if whitelist_item:
            response_data["whitelist_details"] = PhoneWhitelistSerializer(
                whitelist_item
            ).data

        status_text = "autorisé" if is_authorized else "non autorisé"

        return Response(
            ResponseService.success_response(
                message=f"Numéro {phone} est {status_text}",
                data=response_data,
            ),
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        return Response(
            ResponseService.error_response(
                message="Erreur lors de la vérification du numéro",
                errors={"detail": str(e)},
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@extend_schema(
    summary="Supprime un numéro de la liste blanche",
    description="""
    Supprime un numéro de téléphone de la liste blanche.
    Nécessite des droits d'administrateur.
    """,
    request=PhoneWhitelistCheckSerializer,
    responses={
        200: PhoneWhitelistResponseSerializer,
        400: ErrorResponseSerializer,
        403: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
    },
    tags=["Administration"],
    auth=[{"jwtAuth": []}],
)
@api_view(["DELETE"])
@permission_classes([IsAdminUser])
@throttle_classes([AdminRateThrottle])
def phone_whitelist_remove_view(request: Request) -> Response:
    """
    Supprime un numéro de la liste blanche.
    """
    try:
        from .models import PhoneWhitelist

        serializer = PhoneWhitelistCheckSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                ResponseService.error_response(
                    message=INVALID_DATA_ERROR_MESSAGE,
                    errors=serializer.errors,
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        phone = serializer.validated_data["phone"]

        try:
            whitelist_item = PhoneWhitelist.objects.get(phone=phone)
            whitelist_item.delete()

            return Response(
                ResponseService.success_response(
                    message=f"Numéro {phone} supprimé de la liste blanche",
                    data={"phone": phone, "removed": True},
                ),
                status=status.HTTP_200_OK,
            )

        except PhoneWhitelist.DoesNotExist:
            return Response(
                ResponseService.error_response(
                    message=f"Numéro {phone} non trouvé dans la liste blanche",
                    errors={"detail": "Numéro non trouvé"},
                ),
                status=status.HTTP_404_NOT_FOUND,
            )

    except Exception as e:
        return Response(
            ResponseService.error_response(
                message="Erreur lors de la suppression du numéro",
                errors={"detail": str(e)},
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
