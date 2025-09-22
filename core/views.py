"""
Views pour l'application core
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request


@api_view(["GET"])
@permission_classes([AllowAny])
def ping_view(request: Request) -> Response:
    """
    Endpoint de test pour vérifier que l'API fonctionne

    Returns:
        Response: {"message": "pong"}
    """
    return Response({"message": "pong"}, status=status.HTTP_200_OK)
