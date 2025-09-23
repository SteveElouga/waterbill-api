from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import User, VerificationToken, ActivationToken, PhoneWhitelist


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour le modèle User.
    """
    
    list_display = [
        "phone",
        "first_name", 
        "last_name",
        "email",
        "is_active",
        "is_staff",
        "date_joined"
    ]
    
    list_filter = ["is_active", "is_staff", "date_joined"]
    
    search_fields = ["phone", "first_name", "last_name", "email"]
    
    readonly_fields = ["date_joined", "last_login"]
    
    fieldsets = (
        ("Informations personnelles", {
            "fields": ("phone", "first_name", "last_name", "email")
        }),
        ("Informations de contact", {
            "fields": ("address", "apartment_name")
        }),
        ("Permissions", {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")
        }),
        ("Dates importantes", {
            "fields": ("date_joined", "last_login"),
            "classes": ("collapse",)
        }),
    )


@admin.register(PhoneWhitelist)
class PhoneWhitelistAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour la liste blanche des numéros de téléphone.
    
    Permet aux administrateurs de gérer les numéros autorisés à créer un compte.
    """
    
    list_display = [
        "phone",
        "added_by_display",
        "added_at",
        "is_active",
        "notes_preview"
    ]
    
    list_filter = ["is_active", "added_at", "added_by"]
    
    search_fields = ["phone", "notes", "added_by__phone", "added_by__first_name"]
    
    readonly_fields = ["added_at"]
    
    fieldsets = (
        ("Numéro de téléphone", {
            "fields": ("phone", "is_active")
        }),
        ("Informations d'ajout", {
            "fields": ("added_by", "added_at"),
            "classes": ("collapse",)
        }),
        ("Notes", {
            "fields": ("notes",)
        }),
    )
    
    def added_by_display(self, obj):
        """
        Affiche l'utilisateur qui a ajouté le numéro avec un lien.
        """
        if obj.added_by:
            url = reverse("admin:users_user_change", args=[obj.added_by.pk])
            return format_html(
                '<a href="{}">{}</a>',
                url,
                obj.added_by.get_full_name() or obj.added_by.phone
            )
        return "-"
    added_by_display.short_description = "Ajouté par"
    added_by_display.admin_order_field = "added_by"
    
    def notes_preview(self, obj):
        """
        Affiche un aperçu des notes (50 caractères max).
        """
        if obj.notes:
            preview = obj.notes[:50]
            if len(obj.notes) > 50:
                preview += "..."
            return preview
        return "-"
    notes_preview.short_description = "Notes"
    
    def get_queryset(self, request):
        """
        Optimise les requêtes pour l'affichage en liste.
        """
        return super().get_queryset(request).select_related("added_by")
    
    def save_model(self, request, obj, form, change):
        """
        S'assure que l'utilisateur qui ajoute le numéro est enregistré.
        """
        if not change:  # Nouvelle création
            obj.added_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(VerificationToken)
class VerificationTokenAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour les tokens de vérification.
    """
    
    list_display = [
        "token",
        "user",
        "verification_type",
        "created_at",
        "expires_at",
        "is_used"
    ]
    
    list_filter = ["verification_type", "is_used", "created_at"]
    
    search_fields = ["token", "user__phone", "phone"]
    
    readonly_fields = ["token", "created_at", "expires_at"]
    
    fieldsets = (
        ("Token", {
            "fields": ("token", "user", "phone")
        }),
        ("Type et statut", {
            "fields": ("verification_type", "is_used")
        }),
        ("Dates", {
            "fields": ("created_at", "expires_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(ActivationToken)
class ActivationTokenAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour les tokens d'activation.
    """
    
    list_display = [
        "user",
        "code_hash_display",
        "created_at",
        "expires_at",
        "is_locked",
        "attempts"
    ]
    
    list_filter = ["is_locked", "created_at", "attempts"]
    
    search_fields = ["user__phone", "code_hash"]
    
    readonly_fields = ["created_at", "expires_at", "code_hash"]
    
    fieldsets = (
        ("Token d'activation", {
            "fields": ("user", "code_hash")
        }),
        ("Statut", {
            "fields": ("is_locked", "attempts", "send_count")
        }),
        ("Dates", {
            "fields": ("created_at", "expires_at", "last_sent_at"),
            "classes": ("collapse",)
        }),
    )
    
    def code_hash_display(self, obj):
        """
        Affiche un aperçu du hash du code.
        """
        return f"{obj.code_hash[:8]}..." if obj.code_hash else "-"
    code_hash_display.short_description = "Code Hash"
