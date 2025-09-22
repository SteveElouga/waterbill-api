"""
URLs pour l'application core
"""

from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.ping_view, name="ping"),
]
