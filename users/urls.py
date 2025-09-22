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
]
