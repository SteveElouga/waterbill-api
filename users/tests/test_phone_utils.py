"""
Tests pour les utilitaires de gestion des numéros de téléphone.

Ce module teste toutes les fonctions utilitaires pour la normalisation,
validation et nettoyage des numéros de téléphone.
"""

from users.utils.phone_utils import (
    normalize_phone,
    validate_phone_length,
    clean_phone_for_display,
)


class TestNormalizePhone:
    """Tests pour la fonction normalize_phone."""

    def test_normalize_phone_empty_string(self):
        """Test avec chaîne vide."""
        result = normalize_phone("")
        assert result is None

    def test_normalize_phone_none(self):
        """Test avec None."""
        result = normalize_phone(None)
        assert result is None

    def test_normalize_phone_with_spaces(self):
        """Test avec espaces."""
        result = normalize_phone("675 799 750")
        assert result == "+675799750"

    def test_normalize_phone_with_dashes(self):
        """Test avec tirets."""
        result = normalize_phone("675-799-751")
        assert result == "+675799751"

    def test_normalize_phone_with_parentheses(self):
        """Test avec parenthèses."""
        result = normalize_phone("(675) 799-752")
        assert result == "+675799752"

    def test_normalize_phone_already_international(self):
        """Test avec format international déjà présent."""
        result = normalize_phone("+675799749")
        assert result == "+675799749"

    def test_normalize_phone_mixed_special_chars(self):
        """Test avec mélange de caractères spéciaux."""
        result = normalize_phone("+237 (658) 552-294")
        assert result == "+237658552294"

    def test_normalize_phone_only_digits(self):
        """Test avec seulement des chiffres."""
        result = normalize_phone("675799743")
        assert result == "+675799743"

    def test_normalize_phone_with_plus_no_digits(self):
        """Test avec seulement un +."""
        result = normalize_phone("+")
        assert result == "+"

    def test_normalize_phone_whitespace_only(self):
        """Test avec seulement des espaces."""
        result = normalize_phone("   ")
        assert result == "+"

    def test_normalize_phone_special_chars_only(self):
        """Test avec seulement des caractères spéciaux."""
        result = normalize_phone("()[]{}")
        assert result == "+"


class TestValidatePhoneLength:
    """Tests pour la fonction validate_phone_length."""

    def test_validate_phone_length_empty_string(self):
        """Test avec chaîne vide."""
        result = validate_phone_length("")
        assert result is False

    def test_validate_phone_length_none(self):
        """Test avec None."""
        result = validate_phone_length(None)
        assert result is False

    def test_validate_phone_length_valid_min(self):
        """Test avec longueur minimale valide."""
        result = validate_phone_length("+123456789")
        assert result is True

    def test_validate_phone_length_valid_max(self):
        """Test avec longueur maximale valide."""
        result = validate_phone_length("+123456789012345")
        assert result is True

    def test_validate_phone_length_too_short(self):
        """Test avec numéro trop court."""
        result = validate_phone_length("+12345678")  # 8 chiffres
        assert result is False

    def test_validate_phone_length_too_long(self):
        """Test avec numéro trop long."""
        result = validate_phone_length("+1234567890123456")  # 16 chiffres
        assert result is False

    def test_validate_phone_length_with_special_chars(self):
        """Test avec caractères spéciaux (doit ignorer)."""
        result = validate_phone_length("+237-658-552-294")  # 12 chiffres
        assert result is True

    def test_validate_phone_length_custom_min_max(self):
        """Test avec limites personnalisées."""
        result = validate_phone_length("+1234567890", min_length=10, max_length=12)
        assert result is True

        result = validate_phone_length("+123456789", min_length=10, max_length=12)
        assert result is False

        result = validate_phone_length("+1234567890123", min_length=10, max_length=12)
        assert result is False

    def test_validate_phone_length_only_digits(self):
        """Test avec seulement des chiffres."""
        result = validate_phone_length("237658552294")
        assert result is True

    def test_validate_phone_length_edge_cases(self):
        """Test des cas limites."""
        # Exactement 9 chiffres
        result = validate_phone_length("+123456789")
        assert result is True

        # Exactement 15 chiffres
        result = validate_phone_length("+123456789012345")
        assert result is True


class TestCleanPhoneForDisplay:
    """Tests pour la fonction clean_phone_for_display."""

    def test_clean_phone_for_display_empty_string(self):
        """Test avec chaîne vide."""
        result = clean_phone_for_display("")
        assert result == ""

    def test_clean_phone_for_display_none(self):
        """Test avec None."""
        result = clean_phone_for_display(None)
        assert result == ""

    def test_clean_phone_for_display_with_spaces(self):
        """Test avec espaces."""
        result = clean_phone_for_display("675 799 750")
        assert result == "675799750"

    def test_clean_phone_for_display_with_dashes(self):
        """Test avec tirets."""
        result = clean_phone_for_display("675-799-751")
        assert result == "675799751"

    def test_clean_phone_for_display_with_parentheses(self):
        """Test avec parenthèses."""
        result = clean_phone_for_display("(675) 799-752")
        assert result == "675799752"

    def test_clean_phone_for_display_with_plus(self):
        """Test avec +."""
        result = clean_phone_for_display("+675799749")
        assert result == "+675799749"

    def test_clean_phone_for_display_mixed_special_chars(self):
        """Test avec mélange de caractères spéciaux."""
        result = clean_phone_for_display("+237 (658) 552-294")
        assert result == "+237658552294"

    def test_clean_phone_for_display_only_digits(self):
        """Test avec seulement des chiffres."""
        result = clean_phone_for_display("675799743")
        assert result == "675799743"

    def test_clean_phone_for_display_special_chars_only(self):
        """Test avec seulement des caractères spéciaux."""
        result = clean_phone_for_display("()[]{}")
        assert result == ""

    def test_clean_phone_for_display_whitespace_only(self):
        """Test avec seulement des espaces."""
        result = clean_phone_for_display("   ")
        assert result == ""

    def test_clean_phone_for_display_preserve_plus(self):
        """Test que le + est préservé."""
        result = clean_phone_for_display("+237-658-552-294")
        assert result == "+237658552294"

    def test_clean_phone_for_display_no_plus(self):
        """Test sans +."""
        result = clean_phone_for_display("237-658-552-294")
        assert result == "237658552294"

    def test_clean_phone_for_display_multiple_plus(self):
        """Test avec plusieurs +."""
        result = clean_phone_for_display("++237-658-552-294")
        assert result == "++237658552294"


class TestPhoneUtilsIntegration:
    """Tests d'intégration pour les utilitaires de téléphone."""

    def test_normalize_and_validate_workflow(self):
        """Test du workflow normalisation + validation."""
        # Numéro avec caractères spéciaux
        phone = "+237 (658) 552-294"

        # Normaliser
        normalized = normalize_phone(phone)
        assert normalized == "+237658552294"

        # Valider la longueur
        is_valid = validate_phone_length(normalized)
        assert is_valid is True

        # Nettoyer pour affichage
        cleaned = clean_phone_for_display(phone)
        assert cleaned == "+237658552294"

    def test_edge_case_workflow(self):
        """Test du workflow avec cas limites."""
        # Numéro très court
        short_phone = "+123"
        normalized = normalize_phone(short_phone)
        assert normalized == "+123"

        is_valid = validate_phone_length(normalized)
        assert is_valid is False

        # Numéro très long
        long_phone = "+12345678901234567890"
        normalized = normalize_phone(long_phone)
        assert normalized == "+12345678901234567890"

        is_valid = validate_phone_length(normalized)
        assert is_valid is False

    def test_consistency_between_functions(self):
        """Test de cohérence entre les fonctions."""
        test_cases = [
            "+237-658-552-294",
            "237 658 552 294",
            "(237) 658-552-294",
            "+237658552294",
        ]

        for phone in test_cases:
            normalized = normalize_phone(phone)
            cleaned = clean_phone_for_display(phone)

            # normalize_phone ajoute toujours le +, clean_phone_for_display le garde
            # Donc ils peuvent être différents si le numéro original n'a pas de +
            if phone.startswith("+"):
                assert normalized == cleaned
            else:
                # Si pas de + original, normalize_phone l'ajoute
                assert normalized == "+" + cleaned

            # La validation doit être cohérente
            is_valid = validate_phone_length(normalized)
            assert is_valid is True
