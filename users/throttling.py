"""
Classes de throttling personnalisées pour l'authentification.

Ce module contient des classes de throttling spécialisées pour protéger
les endpoints d'authentification contre les attaques par force brute.
"""

from rest_framework.throttling import (
    SimpleRateThrottle,
)
from typing import Optional


class LoginRateThrottle(SimpleRateThrottle):
    """
    Throttling pour les tentatives de connexion.

    Limite les tentatives de connexion par IP pour prévenir
    les attaques par force brute.
    """

    scope = "login"

    def get_cache_key(self, request, view):
        """Génère une clé de cache basée sur l'IP."""
        if request.user.is_authenticated:
            return None  # Pas de throttling pour les utilisateurs connectés

        return f"login_throttle_{self.get_ident(request)}"


class RegisterRateThrottle(SimpleRateThrottle):
    """
    Throttling pour les inscriptions.

    Limite les inscriptions par IP pour prévenir
    les inscriptions abusives.
    """

    scope = "register"

    def get_cache_key(self, request, view):
        """Génère une clé de cache basée sur l'IP."""
        if request.user.is_authenticated:
            return None  # Pas de throttling pour les utilisateurs connectés

        return f"register_throttle_{self.get_ident(request)}"


class AuthRateThrottle(SimpleRateThrottle):
    """
    Throttling général pour tous les endpoints d'authentification.

    Applique une limite plus stricte pour tous les endpoints
    d'authentification (login, register, refresh).
    """

    scope = "auth"

    def get_cache_key(self, request, view):
        """Génère une clé de cache basée sur l'IP."""
        if request.user.is_authenticated:
            return None  # Pas de throttling pour les utilisateurs connectés

        return f"auth_throttle_{self.get_ident(request)}"


class CustomAnonRateThrottle(SimpleRateThrottle):
    """
    Throttling personnalisé pour les utilisateurs anonymes.

    Applique des limites plus strictes que le throttling par défaut
    pour les utilisateurs non authentifiés.
    """

    scope = "anon"

    def get_cache_key(self, request, view):
        """Génère une clé de cache basée sur l'IP."""
        if request.user.is_authenticated:
            return None

        return f"anon_throttle_{self.get_ident(request)}"


class CustomUserRateThrottle(SimpleRateThrottle):
    """
    Throttling personnalisé pour les utilisateurs authentifiés.

    Applique des limites appropriées pour les utilisateurs
    authentifiés.
    """

    scope = "user"

    def get_cache_key(self, request, view):
        """Génère une clé de cache basée sur l'ID utilisateur."""
        if request.user.is_authenticated:
            return f"user_throttle_{request.user.id}"

        return None


class BurstRateThrottle(SimpleRateThrottle):
    """
    Throttling pour les pics de trafic (burst).

    Permet un nombre limité de requêtes rapides, puis applique
    une limite plus stricte.
    """

    scope = "burst"

    def get_cache_key(self, request, view):
        """Génère une clé de cache basée sur l'IP."""
        return f"burst_throttle_{self.get_ident(request)}"

    def parse_rate(self, rate):
        """
        Parse le taux de throttling.

        Format: "X/second" ou "X/minute" ou "X/hour"
        """
        if rate is None:
            return (None, None)

        num, period = rate.split("/")
        num_requests = int(num)

        if period == "second":
            duration = 1
        elif period == "minute":
            duration = 60
        elif period == "hour":
            duration = 3600
        else:
            raise ValueError(f"Période non reconnue: {period}")

        return (num_requests, duration)


class ActivateRateThrottle(SimpleRateThrottle):
    """
    Throttling pour les tentatives d'activation.

    Limite les tentatives de vérification de code d'activation
    pour prévenir les attaques par force brute.
    """

    scope = "activate"

    def get_cache_key(self, request, view) -> Optional[str]:
        """
        Génère une clé de cache basée sur l'IP.

        Args:
            request: Requête HTTP
            view: Vue appelée

        Returns:
            str: Clé de cache pour le throttling
        """
        if self.rate is None:
            return None

        self.num_requests, self.duration = self.parse_rate(self.rate)

        return f"activate_{self.get_ident(request)}"


class ResendCodeRateThrottle(SimpleRateThrottle):
    """
    Throttling pour les demandes de renvoi de code.

    Limite les demandes de renvoi de code d'activation
    pour éviter le spam et les abus.
    """

    scope = "resend_code"

    def get_cache_key(self, request, view) -> Optional[str]:
        """
        Génère une clé de cache basée sur l'IP.

        Args:
            request: Requête HTTP
            view: Vue appelée

        Returns:
            str: Clé de cache pour le throttling
        """
        if self.rate is None:
            return None

        self.num_requests, self.duration = self.parse_rate(self.rate)

        return f"resend_{self.get_ident(request)}"


class PhoneBasedThrottle(SimpleRateThrottle):
    """
    Throttling basé sur le numéro de téléphone.

    Limite les tentatives par numéro de téléphone
    plutôt que par IP pour une meilleure sécurité.
    """

    scope = "phone_based"

    def get_cache_key(self, request, view) -> Optional[str]:
        """
        Génère une clé de cache basée sur le numéro de téléphone.

        Args:
            request: Requête HTTP
            view: Vue appelée

        Returns:
            str: Clé de cache pour le throttling
        """
        if self.rate is None:
            return None

        self.num_requests, self.duration = self.parse_rate(self.rate)

        # Extraire le numéro de téléphone des données de la requête
        phone = request.data.get("phone", "")
        if phone:
            # Nettoyer le numéro
            cleaned_phone = "".join(filter(str.isdigit, phone))
            return f"phone_{cleaned_phone}"

        # Fallback sur l'IP si pas de téléphone
        return f"phone_ip_{self.get_ident(request)}"
