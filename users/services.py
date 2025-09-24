"""
Services d'authentification pour WaterBill API.

Ce module implémente la logique métier pour l'inscription,
connexion, activation et gestion des utilisateurs.
"""

import logging
from typing import Dict, Any, Optional, Tuple
from django.utils import timezone
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, ActivationToken
from .gateways.sms import get_sms_gateway

logger = logging.getLogger(__name__)

# Constantes pour les messages d'erreur
SMS_SEND_FAILED_ERROR = "Échec de l'envoi du SMS"
CODE_VERIFICATION_ERROR = "Code de vérification incorrect ou expiré"
USER_TOKEN_NOT_FOUND_ERROR = "Utilisateur associé au token introuvable"


class AuthService:
    """
    Service d'authentification centralisé.

    Implémente la logique métier pour l'inscription et connexion
    des utilisateurs avec gestion des erreurs et validation.
    """

    @staticmethod
    def register_user(user_data: Dict[str, Any]) -> User:
        """
        Enregistre un nouvel utilisateur inactif et génère un token d'activation.

        OPÉRATION ATOMIQUE : Si l'envoi SMS échoue, l'utilisateur n'est pas créé.

        Args:
            user_data: Dictionnaire contenant les données utilisateur

        Returns:
            User: Utilisateur créé (inactif)

        Raises:
            ValueError: Si les données ne sont pas valides
            ValidationError: Si la création échoue
        """
        try:
            # Supprimer password_confirm des données avant création
            user_data_clean = user_data.copy()
            user_data_clean.pop("password_confirm", None)

            # OPÉRATION ATOMIQUE : Transaction qui annule tout si une étape échoue
            with transaction.atomic():
                # 1. Créer l'utilisateur (inactif par défaut)
                user = User.objects.create_user(**user_data_clean)

                # 2. Créer le token d'activation et envoyer le SMS
                # Si cette étape échoue, la transaction entière est annulée
                ActivationService.create_and_send_activation_code(user)

                # 3. Si tout s'est bien passé, valider la transaction
                logger.info(
                    f"Utilisateur créé et code d'activation envoyé: {user.phone}"
                )
                return user

        except Exception as e:
            # En cas d'erreur, la transaction est automatiquement annulée
            logger.error(f"Erreur lors de l'inscription atomique: {str(e)}")
            raise ValueError(f"Erreur lors de l'inscription: {str(e)}")

    @staticmethod
    def authenticate_user(phone: str, password: str) -> Optional[User]:
        """
        Authentifie un utilisateur par téléphone et mot de passe.

        Args:
            phone: Numéro de téléphone de l'utilisateur
            password: Mot de passe de l'utilisateur

        Returns:
            Optional[User]: Utilisateur authentifié ou None
        """
        # Nettoyer et formater le numéro de téléphone au format international
        cleaned_phone = "".join(filter(str.isdigit, phone))
        international_phone = "+" + cleaned_phone

        try:
            # Récupérer l'utilisateur par téléphone (format international)
            user = User.objects.get(phone=international_phone)

            # Vérifier le mot de passe
            if user.check_password(password) and user.is_active:
                # Mettre à jour la dernière connexion
                user.last_login = timezone.now()
                user.save(update_fields=["last_login"])
                return user

        except User.DoesNotExist:
            pass

        return None

    @staticmethod
    def login_user(phone: str, password: str) -> Tuple[User, Dict[str, str]]:
        """
        Connecte un utilisateur et génère les tokens JWT.

        Args:
            phone: Numéro de téléphone de l'utilisateur
            password: Mot de passe de l'utilisateur

        Returns:
            Tuple[User, Dict[str, str]]: Utilisateur et tokens JWT

        Raises:
            ValueError: Si l'authentification échoue
        """
        user = AuthService.authenticate_user(phone, password)

        if not user:
            raise ValueError("Numéro de téléphone ou mot de passe incorrect.")

        # Générer les tokens JWT
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        tokens = {"access": str(access), "refresh": str(refresh)}

        return user, tokens

    @staticmethod
    def get_user_profile(user: User) -> Dict[str, Any]:
        """
        Récupère le profil complet d'un utilisateur.

        Args:
            user: Instance de l'utilisateur

        Returns:
            Dict[str, Any]: Profil utilisateur sérialisé
        """
        # Créer les données utilisateur manuellement pour éviter les problèmes avec DRF Spectacular
        return {
            "id": user.id,
            "phone": user.phone,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.get_full_name(),
            "email": user.email,
            "address": user.address,
            "apartment_name": user.apartment_name,
            "date_joined": user.date_joined,
            "is_active": user.is_active,
        }

    @staticmethod
    def validate_phone_uniqueness(
        phone: str, exclude_user_id: Optional[int] = None
    ) -> bool:
        """
        Valide l'unicité d'un numéro de téléphone.

        Args:
            phone: Numéro de téléphone à vérifier
            exclude_user_id: ID d'utilisateur à exclure de la vérification

        Returns:
            bool: True si le numéro est unique
        """
        # Nettoyer et formater le numéro de téléphone au format international
        cleaned_phone = "".join(filter(str.isdigit, phone))
        international_phone = "+" + cleaned_phone

        queryset = User.objects.filter(phone=international_phone)

        if exclude_user_id:
            queryset = queryset.exclude(id=exclude_user_id)

        return not queryset.exists()

    @staticmethod
    def refresh_user_tokens(refresh_token: str) -> Tuple[User, Dict[str, str]]:
        """
        Rafraîchit les tokens JWT d'un utilisateur.

        Args:
            refresh_token: Token de rafraîchissement

        Returns:
            Tuple[User, Dict[str, str]]: Utilisateur et nouveaux tokens

        Raises:
            ValueError: Si le token n'est pas valide
        """
        try:
            refresh = RefreshToken(refresh_token)
            user = User.objects.get(id=refresh["user_id"])

            # Générer de nouveaux tokens
            new_refresh = RefreshToken.for_user(user)
            new_access = new_refresh.access_token

            tokens = {"access": str(new_access), "refresh": str(new_refresh)}

            return user, tokens

        except Exception as e:
            raise ValueError(f"Token invalide: {str(e)}")


class ResponseService:
    """
    Service pour la standardisation des réponses API.

    Implémente le format de réponse JSON normalisé
    pour toutes les endpoints d'authentification.
    """

    @staticmethod
    def success_response(
        message: str, data: Optional[Dict[str, Any]] = None, status_code: int = 200
    ) -> Dict[str, Any]:
        """
        Génère une réponse de succès standardisée.

        Args:
            message: Message de succès
            data: Données à retourner
            status_code: Code de statut HTTP

        Returns:
            Dict[str, Any]: Réponse standardisée
        """
        response = {"status": "success", "message": message, "data": data or {}}

        return response

    @staticmethod
    def error_response(
        message: str, errors: Optional[Dict[str, Any]] = None, status_code: int = 400
    ) -> Dict[str, Any]:
        """
        Génère une réponse d'erreur standardisée.

        Args:
            message: Message d'erreur
            errors: Détails des erreurs
            status_code: Code de statut HTTP

        Returns:
            Dict[str, Any]: Réponse d'erreur standardisée
        """
        response = {"status": "error", "message": message, "data": errors or {}}

        return response


class ActivationService:
    """
    Service de gestion des codes d'activation par SMS.

    Implémente la logique métier pour la création, envoi et vérification
    des codes d'activation avec gestion des limites et de la sécurité.
    """

    @staticmethod
    def create_and_send_activation_code(user: User) -> str:
        """
        Crée un token d'activation et envoie le code par SMS.

        OPÉRATION ATOMIQUE : Si l'envoi SMS échoue, le token n'est pas créé.

        Args:
            user: Utilisateur pour lequel créer le token

        Returns:
            str: Code d'activation généré (pour les logs)

        Raises:
            ValueError: Si l'envoi échoue
        """
        try:
            # Générer le code avant de créer le token
            code = str(ActivationToken.generate_code())

            # OPÉRATION ATOMIQUE : Vérifier d'abord si on peut envoyer le SMS
            sms_gateway = get_sms_gateway()

            # Pré-vérifier la disponibilité du gateway SMS
            if not sms_gateway.is_available():
                raise ValueError("Service SMS temporairement indisponible")

            # Essayer d'envoyer le SMS AVANT de créer le token
            if not sms_gateway.send_activation_code(user.phone, code):
                raise ValueError(SMS_SEND_FAILED_ERROR)

            # Si l'envoi SMS réussit, créer le token d'activation
            token = ActivationToken.create_token(user)

            # Mettre à jour le hash avec le bon code
            token.code_hash = ActivationToken.hash_code(code)
            token.save(update_fields=["code_hash"])

            logger.info(f"Code d'activation envoyé à {user.phone}")
            return code

        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du code d'activation: {str(e)}")
            raise ValueError(f"Erreur lors de l'envoi du code d'activation: {str(e)}")

    @staticmethod
    def verify_activation_code(phone: str, code: str) -> User:
        """
        Vérifie un code d'activation et active l'utilisateur.

        Args:
            phone: Numéro de téléphone de l'utilisateur
            code: Code d'activation à vérifier

        Returns:
            User: Utilisateur activé

        Raises:
            ValueError: Si la vérification échoue
        """
        try:
            # Nettoyer et formater le numéro de téléphone au format international
            cleaned_phone = "".join(filter(str.isdigit, phone))
            international_phone = "+" + cleaned_phone

            # Récupérer l'utilisateur
            try:
                user = User.objects.get(phone=international_phone)
            except User.DoesNotExist:
                raise ValueError("Utilisateur non trouvé")

            # Vérifier si l'utilisateur est déjà activé
            if user.is_active:
                raise ValueError("Ce compte est déjà activé")

            # Récupérer le token d'activation
            try:
                token = user.activation_token
            except ActivationToken.DoesNotExist:
                raise ValueError("Aucun code d'activation en attente")

            # Vérifier le code
            if not token.verify_code(code):
                if token.is_expired():
                    raise ValueError("Le code d'activation a expiré")
                elif token.is_locked:
                    raise ValueError(
                        "Trop de tentatives échouées. Demandez un nouveau code."
                    )
                else:
                    raise ValueError("Code d'activation incorrect")

            # Activer l'utilisateur (supprime automatiquement le token)
            token.activate_user()

            logger.info(f"Utilisateur activé avec succès: {user.phone}")
            return user

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du code: {str(e)}")
            raise ValueError(f"Erreur lors de la vérification du code: {str(e)}")

    @staticmethod
    def resend_activation_code(phone: str) -> None:
        """
        Renvoie un code d'activation pour un utilisateur.

        Args:
            phone: Numéro de téléphone de l'utilisateur

        Raises:
            ValueError: Si le renvoi n'est pas possible
        """
        try:
            # Nettoyer et formater le numéro de téléphone au format international
            cleaned_phone = "".join(filter(str.isdigit, phone))
            international_phone = "+" + cleaned_phone

            # Récupérer l'utilisateur
            try:
                user = User.objects.get(phone=international_phone)
            except User.DoesNotExist:
                raise ValueError("Utilisateur non trouvé")

            # Vérifier si l'utilisateur est déjà activé
            if user.is_active:
                raise ValueError("Ce compte est déjà activé")

            # Récupérer ou créer le token d'activation
            try:
                token = user.activation_token

                # Vérifier si un nouveau code peut être envoyé
                if not token.can_send_new_code():
                    if token.is_locked:
                        raise ValueError("Compte verrouillé. Contactez le support.")
                    else:
                        raise ValueError("Attendez avant de demander un nouveau code.")

                # Mettre à jour le token pour le renvoi
                token.send_count += 1
                token.last_sent_at = timezone.now()
                token.save(update_fields=["send_count", "last_sent_at"])

            except ActivationToken.DoesNotExist:
                # Créer un nouveau token
                token = ActivationToken.create_token(user)

            # Générer un nouveau code et mettre à jour le token
            code = str(ActivationToken.generate_code())
            token.code_hash = ActivationToken.hash_code(code)
            token.save(update_fields=["code_hash"])

            # Envoyer le SMS
            sms_gateway = get_sms_gateway()
            if not sms_gateway.send_activation_code(user.phone, code):
                raise ValueError(SMS_SEND_FAILED_ERROR)

            logger.info(f"Code d'activation renvoyé à {user.phone}")

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors du renvoi du code: {str(e)}")
            raise ValueError(f"Erreur lors du renvoi du code: {str(e)}")


class RateLimitService:
    """
    Service de gestion des limites de taux pour l'activation.

    Implémente la logique de limitation des tentatives et envois
    pour éviter les abus et attaques.
    """

    @staticmethod
    def check_activation_limits(phone: str) -> Dict[str, Any]:
        """
        Vérifie les limites d'activation pour un numéro de téléphone.

        Args:
            phone: Numéro de téléphone à vérifier

        Returns:
            Dict[str, Any]: Informations sur les limites
        """
        # Nettoyer et formater au format international
        cleaned_phone = "".join(filter(str.isdigit, phone))
        international_phone = "+" + cleaned_phone

        try:
            user = User.objects.get(phone=international_phone)
            token = user.activation_token

            return {
                "can_send": token.can_send_new_code(),
                "is_locked": token.is_locked,
                "attempts": token.attempts,
                "send_count": token.send_count,
                "last_sent": token.last_sent_at,
                "expires_at": token.expires_at,
            }
        except (User.DoesNotExist, ActivationToken.DoesNotExist):
            return {
                "can_send": True,
                "is_locked": False,
                "attempts": 0,
                "send_count": 0,
                "last_sent": None,
                "expires_at": None,
            }


# =============================================================================
# NOUVEAUX SERVICES POUR LES FONCTIONNALITÉS ÉTENDUES
# =============================================================================


class PasswordResetService:
    """
    Service pour la réinitialisation de mot de passe.

    Gère la demande et la confirmation de réinitialisation
    via SMS avec le nouveau modèle VerificationToken.
    """

    @staticmethod
    def request_password_reset(phone: str) -> Dict[str, Any]:
        """
        Demande une réinitialisation de mot de passe.

        Args:
            phone: Numéro de téléphone de l'utilisateur

        Returns:
            Dict[str, Any]: Résultat de la demande

        Raises:
            ValueError: Si la demande échoue
        """
        try:
            # Vérifier si l'utilisateur existe
            try:
                user = User.objects.get(phone=phone)
            except User.DoesNotExist:
                # Pour la sécurité, on retourne toujours un succès
                # même si l'utilisateur n'existe pas
                logger.info(f"Demande de reset pour numéro inexistant: {phone}")
                return {
                    "success": True,
                    "message": "Si ce numéro est associé à un compte, vous recevrez un SMS.",
                }

            # Créer un token de réinitialisation
            from .models import VerificationToken

            token = VerificationToken.create_token(
                verification_type="password_reset", user=user
            )

            # Générer le code et l'envoyer
            code = VerificationToken.generate_code()
            token.code_hash = VerificationToken.hash_code(code)
            token.save(update_fields=["code_hash"])

            # Envoyer le SMS avec lien de redirection
            sms_gateway = get_sms_gateway()
            from .gateways.sms import generate_redirect_url

            redirect_url = generate_redirect_url(str(token.token), "password_reset")

            if not sms_gateway.send_verification_code(
                phone, code, "password_reset", redirect_url
            ):
                raise ValueError(SMS_SEND_FAILED_ERROR)

            logger.info(f"Code de réinitialisation envoyé à {phone}")

            return {
                "success": True,
                "message": "Un code de réinitialisation a été envoyé par SMS.",
                "token": str(token.token),
            }

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la demande de reset: {str(e)}")
            raise ValueError(f"Erreur lors de la demande de réinitialisation: {str(e)}")

    @staticmethod
    def confirm_password_reset(
        token_uuid: str, code: str, new_password: str
    ) -> Dict[str, Any]:
        """
        Confirme la réinitialisation de mot de passe.

        Args:
            token_uuid: UUID du token de réinitialisation
            code: Code SMS de vérification
            new_password: Nouveau mot de passe

        Returns:
            Dict[str, Any]: Résultat de la confirmation

        Raises:
            ValueError: Si la confirmation échoue
        """
        try:
            from .models import VerificationToken

            # Récupérer le token
            try:
                token = VerificationToken.objects.get(
                    token=token_uuid, verification_type="password_reset", is_used=False
                )
            except VerificationToken.DoesNotExist:
                raise ValueError("Token de réinitialisation invalide ou expiré")

            # Vérifier le code
            if not token.verify_code(code):
                raise ValueError(CODE_VERIFICATION_ERROR)

            # Vérifier que l'utilisateur existe
            if not token.user:
                raise ValueError(USER_TOKEN_NOT_FOUND_ERROR)

            # Changer le mot de passe
            token.user.set_password(new_password)
            token.user.save(update_fields=["password"])

            # Marquer le token comme utilisé
            token.mark_as_used()

            # Envoyer SMS de confirmation
            sms_gateway = get_sms_gateway()
            try:
                sms_gateway.send_confirmation_message(
                    token.user.phone, "password_reset"
                )
            except Exception as e:
                # Log l'erreur mais ne pas faire échouer l'opération
                logger.warning(
                    f"Échec envoi SMS de confirmation pour {token.user.phone}: {str(e)}"
                )

            logger.info(f"Mot de passe réinitialisé pour {token.user.phone}")

            return {
                "success": True,
                "message": "Votre mot de passe a été réinitialisé avec succès.",
            }

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la confirmation de reset: {str(e)}")
            raise ValueError(f"Erreur lors de la réinitialisation: {str(e)}")


class PasswordChangeService:
    """
    Service pour le changement de mot de passe (utilisateur authentifié).

    Gère la demande et la confirmation de changement de mot de passe
    avec vérification de l'ancien mot de passe.
    """

    @staticmethod
    def request_password_change(user: User, current_password: str) -> Dict[str, Any]:
        """
        Demande un changement de mot de passe.

        Args:
            user: Utilisateur authentifié
            current_password: Mot de passe actuel

        Returns:
            Dict[str, Any]: Résultat de la demande

        Raises:
            ValueError: Si la demande échoue
        """
        try:
            # Le mot de passe actuel est déjà validé dans le serializer
            # Créer un token de changement
            from .models import VerificationToken

            token = VerificationToken.create_token(
                verification_type="password_change", user=user
            )

            # Générer le code et l'envoyer
            code = VerificationToken.generate_code()
            token.code_hash = VerificationToken.hash_code(code)
            token.save(update_fields=["code_hash"])

            # Envoyer le SMS avec lien de redirection
            sms_gateway = get_sms_gateway()
            from .gateways.sms import generate_redirect_url

            redirect_url = generate_redirect_url(str(token.token), "password_change")

            if not sms_gateway.send_verification_code(
                user.phone, code, "password_change", redirect_url
            ):
                raise ValueError(SMS_SEND_FAILED_ERROR)

            logger.info(f"Code de changement de mot de passe envoyé à {user.phone}")

            return {
                "success": True,
                "message": "Un code de vérification a été envoyé par SMS.",
                "token": str(token.token),
            }

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la demande de changement: {str(e)}")
            raise ValueError(f"Erreur lors de la demande de changement: {str(e)}")

    @staticmethod
    def confirm_password_change(
        token_uuid: str, code: str, new_password: str
    ) -> Dict[str, Any]:
        """
        Confirme le changement de mot de passe.

        Args:
            token_uuid: UUID du token de changement
            code: Code SMS de vérification
            new_password: Nouveau mot de passe

        Returns:
            Dict[str, Any]: Résultat de la confirmation

        Raises:
            ValueError: Si la confirmation échoue
        """
        try:
            from .models import VerificationToken

            # Récupérer le token
            try:
                token = VerificationToken.objects.get(
                    token=token_uuid, verification_type="password_change", is_used=False
                )
            except VerificationToken.DoesNotExist:
                raise ValueError("Token de changement invalide ou expiré")

            # Vérifier le code
            if not token.verify_code(code):
                raise ValueError(CODE_VERIFICATION_ERROR)

            # Vérifier que l'utilisateur existe
            if not token.user:
                raise ValueError(USER_TOKEN_NOT_FOUND_ERROR)

            # Changer le mot de passe
            token.user.set_password(new_password)
            token.user.save(update_fields=["password"])

            # Marquer le token comme utilisé
            token.mark_as_used()

            # Envoyer SMS de confirmation
            sms_gateway = get_sms_gateway()
            try:
                sms_gateway.send_confirmation_message(
                    token.user.phone, "password_change"
                )
            except Exception as e:
                # Log l'erreur mais ne pas faire échouer l'opération
                logger.warning(
                    f"Échec envoi SMS de confirmation pour {token.user.phone}: {str(e)}"
                )

            logger.info(f"Mot de passe changé pour {token.user.phone}")

            return {
                "success": True,
                "message": "Votre mot de passe a été changé avec succès.",
            }

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la confirmation de changement: {str(e)}")
            raise ValueError(f"Erreur lors du changement: {str(e)}")


class ProfileService:
    """
    Service pour la gestion du profil utilisateur.

    Gère la mise à jour des informations du profil
    (nom, prénom, email, adresse, apartment_name).
    """

    @staticmethod
    def update_profile(user: User, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour le profil utilisateur.

        Args:
            user: Utilisateur authentifié
            profile_data: Données du profil à mettre à jour

        Returns:
            Dict[str, Any]: Résultat de la mise à jour

        Raises:
            ValueError: Si la mise à jour échoue
        """
        try:
            # Valider les données avec le serializer
            from .serializers import ProfileUpdateSerializer

            serializer = ProfileUpdateSerializer(user, data=profile_data, partial=True)

            if not serializer.is_valid():
                raise ValueError(f"Données invalides: {serializer.errors}")

            # Mettre à jour et sauvegarder
            user = serializer.save()

            logger.info(f"Profil mis à jour pour {user.phone}")

            # Créer les données utilisateur manuellement pour éviter les problèmes avec DRF Spectacular
            user_data = {
                "id": user.id,
                "phone": user.phone,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.get_full_name(),
                "email": user.email,
                "address": user.address,
                "apartment_name": user.apartment_name,
                "date_joined": user.date_joined,
                "is_active": user.is_active,
            }

            return {
                "success": True,
                "message": "Votre profil a été mis à jour avec succès.",
                "user": user_data,
            }

        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du profil: {str(e)}")
            raise ValueError(f"Erreur lors de la mise à jour du profil: {str(e)}")


class PhoneChangeService:
    """
    Service pour le changement de numéro de téléphone.

    Gère la demande et la confirmation de changement de numéro
    avec vérification par SMS sur le nouveau numéro.
    """

    @staticmethod
    def request_phone_change(user: User, new_phone: str) -> Dict[str, Any]:
        """
        Demande un changement de numéro de téléphone.

        Args:
            user: Utilisateur authentifié
            new_phone: Nouveau numéro de téléphone

        Returns:
            Dict[str, Any]: Résultat de la demande

        Raises:
            ValueError: Si la demande échoue
        """
        try:
            # Vérifier que le nouveau numéro n'est pas déjà utilisé
            # (validation dans le service pour éviter les conditions de course)
            if User.objects.filter(phone=new_phone).exists():
                raise ValueError("Ce numéro de téléphone est déjà utilisé")

            # Créer un token de changement de numéro
            from .models import VerificationToken

            token = VerificationToken.create_token(
                verification_type="phone_change",
                user=user,
                phone=new_phone,  # Stocker le nouveau numéro
            )

            # Générer le code et l'envoyer
            code = VerificationToken.generate_code()
            token.code_hash = VerificationToken.hash_code(code)
            token.save(update_fields=["code_hash"])

            # Envoyer le SMS sur le nouveau numéro avec lien de redirection
            sms_gateway = get_sms_gateway()
            from .gateways.sms import generate_redirect_url

            redirect_url = generate_redirect_url(str(token.token), "phone_change")

            if not sms_gateway.send_verification_code(
                new_phone, code, "phone_change", redirect_url
            ):
                raise ValueError(SMS_SEND_FAILED_ERROR)

            logger.info(f"Code de changement de numéro envoyé à {new_phone}")

            return {
                "success": True,
                "message": "Un code de vérification a été envoyé sur votre nouveau numéro.",
                "token": str(token.token),
            }

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la demande de changement de numéro: {str(e)}")
            raise ValueError(f"Erreur lors de la demande de changement: {str(e)}")

    @staticmethod
    def confirm_phone_change(token_uuid: str, code: str) -> Dict[str, Any]:
        """
        Confirme le changement de numéro de téléphone.

        Args:
            token_uuid: UUID du token de changement
            code: Code SMS de vérification

        Returns:
            Dict[str, Any]: Résultat de la confirmation

        Raises:
            ValueError: Si la confirmation échoue
        """
        try:
            from .models import VerificationToken

            # Récupérer le token
            try:
                token = VerificationToken.objects.get(
                    token=token_uuid, verification_type="phone_change", is_used=False
                )
            except VerificationToken.DoesNotExist:
                raise ValueError("Token de changement invalide ou expiré")

            # Vérifier le code
            if not token.verify_code(code):
                raise ValueError(CODE_VERIFICATION_ERROR)

            # Vérifier que l'utilisateur existe
            if not token.user:
                raise ValueError(USER_TOKEN_NOT_FOUND_ERROR)

            # Vérifier que le nouveau numéro n'est pas déjà utilisé
            if User.objects.filter(phone=token.phone).exists():
                raise ValueError(
                    "Ce numéro de téléphone est maintenant utilisé par un autre compte"
                )

            # Changer le numéro de téléphone
            old_phone = token.user.phone
            token.user.phone = token.phone
            token.user.save(update_fields=["phone"])

            # Marquer le token comme utilisé
            token.mark_as_used()

            # Envoyer SMS de confirmation sur l'ancien ET le nouveau numéro
            sms_gateway = get_sms_gateway()
            try:
                # Confirmation sur l'ancien numéro
                sms_gateway.send_confirmation_message(
                    old_phone,
                    "phone_change",
                    f"Votre nouveau numéro est: {token.phone}",
                )
                # Confirmation sur le nouveau numéro
                sms_gateway.send_confirmation_message(
                    token.phone,
                    "phone_change",
                    "Ce numéro est maintenant associé à votre compte WaterBill",
                )
            except Exception as e:
                # Log l'erreur mais ne pas faire échouer l'opération
                logger.warning(
                    f"Échec envoi SMS de confirmation pour changement de numéro: {str(e)}"
                )

            logger.info(
                f"Numéro changé de {old_phone} vers {token.phone} pour l'utilisateur {token.user.id}"
            )

            return {
                "success": True,
                "message": "Votre numéro de téléphone a été changé avec succès.",
                "new_phone": token.phone,
            }

        except ValueError:
            raise
        except Exception as e:
            logger.error(
                f"Erreur lors de la confirmation de changement de numéro: {str(e)}"
            )
            raise ValueError(f"Erreur lors du changement de numéro: {str(e)}")
