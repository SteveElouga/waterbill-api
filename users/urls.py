"""
Configuration des URLs pour l'authentification des utilisateurs WaterBill.

Ce module définit les routes d'authentification et de gestion
des profils utilisateurs.
"""

from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    # Authentification
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    # Gestion des tokens JWT
    path("token/refresh/", views.token_refresh_view, name="token_refresh"),
    # Activation par SMS
    path("activate/", views.activate_view, name="activate"),
    path("resend-code/", views.resend_code_view, name="resend_code"),
    # Profil utilisateur
    path("profile/", views.profile_view, name="profile"),
    # Nouvelles fonctionnalités
    # Mot de passe oublié
    path("password/forgot/", views.password_forgot_view, name="password_forgot"),
    path(
        "password/reset/confirm/",
        views.password_reset_confirm_view,
        name="password_reset_confirm",
    ),
    # Changement de mot de passe
    path(
        "password/change/request/",
        views.password_change_request_view,
        name="password_change_request",
    ),
    path(
        "password/change/confirm/",
        views.password_change_confirm_view,
        name="password_change_confirm",
    ),
    # Mise à jour du profil
    path("me/", views.profile_update_view, name="profile_update"),
    # Changement de numéro
    path(
        "phone/change/request/",
        views.phone_change_request_view,
        name="phone_change_request",
    ),
    path(
        "phone/change/confirm/",
        views.phone_change_confirm_view,
        name="phone_change_confirm",
    ),
]
