# 🧪 Documentation des Tests - WaterBill API

## 📋 Table des matières

- [⚠️ IMPORTANT : Utilisation du script de test](#-important--utilisation-du-script-de-test)
- [🔧 Configuration du throttling](#-configuration-du-throttling)
- [📊 Couverture de tests](#-couverture-de-tests)
- [🎯 Types de tests](#-types-de-tests)
- [🛠️ Scripts de test](#️-scripts-de-test)
- [🔍 Bonnes pratiques](#-bonnes-pratiques)
- [🐛 Dépannage](#-dépannage)

---

## ⚠️ **IMPORTANT : Utilisation du script de test**

### 🚫 **NE PAS utiliser `pytest` directement**

```bash
# ❌ INCORRECT - Ne pas faire cela
pytest users/tests/
pytest users/tests/test_password_reset.py

# ✅ CORRECT - Utiliser le script de test
./scripts/test.sh unit
./scripts/test.sh specific "users/tests/test_password_reset.py"
```

### 🎯 **Pourquoi utiliser le script ?**

Le script `./scripts/test.sh` configure automatiquement :

1. **Limites de throttling élevées** : Évite les erreurs 429 (Too Many Requests)
2. **Mocking automatique** : Services externes (SMS) mockés
3. **Configuration d'environnement** : Variables d'environnement de test
4. **Exclusion intelligente** : Tests de throttling exclus du mode test

---

## 🔧 Configuration du throttling

### 📊 Limites de production vs test

| Endpoint         | Mode Production | Mode Test   | Amélioration | Protection  |
| ---------------- | --------------- | ----------- | ------------ | ----------- |
| `login`          | 15/minute       | 1000/minute | **67x**      | Brute force |
| `register`       | 10/minute       | 1000/minute | **100x**     | Spam        |
| `activate`       | 20/minute       | 1000/minute | **50x**      | Flood SMS   |
| `resend_code`    | 5/minute        | 1000/minute | **200x**     | Coût SMS    |
| `auth` (général) | 30/minute       | 1000/minute | **33x**      | DDoS        |
| `anon`           | 500/hour        | 10000/hour  | **20x**      | Anonyme     |
| `user`           | 2000/hour       | 10000/hour  | **5x**       | Authentifié |

### 🔄 Activation automatique

Le mode test est activé automatiquement via la variable d'environnement `DJANGO_TEST_MODE=1` :

```bash
# Le script configure automatiquement
DJANGO_TEST_MODE=1 pytest --tb=short -v
```

### 🚫 Tests de throttling exclus

Les tests de throttling (`test_throttling.py`) sont automatiquement exclus du mode test pour conserver leur comportement de throttling normal et valider le système de sécurité.

---

## 📊 Couverture de tests

### 📈 Statistiques actuelles

- **Total des tests** : 228 tests
- **Couverture** : > 95%
- **Modules testés** : 15 modules
- **Fonctionnalités couvertes** : 8 fonctionnalités principales

### 🎯 Modules testés

| Module                        | Tests | Couverture | Fonctionnalités         |
| ----------------------------- | ----- | ---------- | ----------------------- |
| `test_activation.py`          | 21    | 100%       | Activation SMS, tokens  |
| `test_password_reset.py`      | 17    | 100%       | Reset mot de passe      |
| `test_password_change.py`     | 17    | 100%       | Changement mot de passe |
| `test_profile_update.py`      | 14    | 100%       | Mise à jour profil      |
| `test_phone_change.py`        | 18    | 100%       | Changement numéro       |
| `test_throttling.py`          | 9     | 100%       | Limites de sécurité     |
| `test_views.py`               | 12    | 100%       | Endpoints API           |
| `test_services.py`            | 14    | 100%       | Logique métier          |
| `test_serializers.py`         | 12    | 100%       | Validation données      |
| `test_models.py`              | 10    | 100%       | Modèles Django          |
| `test_mocks.py`               | 16    | 100%       | Services externes       |
| `test_phone_utils.py`         | 33    | 100%       | Utilitaires téléphone   |
| `test_atomic_registration.py` | 8     | 100%       | Transactions atomiques  |
| `test_international_phone.py` | 6     | 100%       | Formats internationaux  |
| `test_token_management.py`    | 21    | 100%       | Gestion JWT             |

---

## 🎯 Types de tests

### 🧪 Tests unitaires

**Objectif** : Tester les composants individuels en isolation

```bash
# Tests unitaires (exclut throttling)
./scripts/test.sh unit
```

**Caractéristiques** :

- ✅ Mocks automatiques des services externes
- ✅ Limites de throttling élevées
- ✅ Tests isolés et reproductibles
- ✅ Validation des cas de succès et d'échec

### 🔗 Tests d'intégration

**Objectif** : Tester l'interaction entre plusieurs composants

```bash
# Tests d'intégration
./scripts/test.sh integration
```

**Caractéristiques** :

- ✅ Tests des flux complets
- ✅ Validation des interactions API
- ✅ Tests de cohérence des données

### 🛡️ Tests de sécurité

**Objectif** : Valider les mesures de sécurité

```bash
# Tests de throttling (sans mode test)
./scripts/test.sh specific "users/tests/test_throttling.py"
```

**Caractéristiques** :

- ✅ Tests des limites de throttling
- ✅ Validation de la protection DDoS
- ✅ Tests de brute force
- ✅ Validation des tokens JWT

---

## 🛠️ Scripts de test

### 📋 Commandes disponibles

```bash
# Tests unitaires (recommandé pour le développement)
./scripts/test.sh unit

# Tests d'intégration
./scripts/test.sh integration

# Rapport de couverture de code
./scripts/test.sh coverage

# Tests spécifiques par fichier
./scripts/test.sh specific "users/tests/test_password_reset.py"

# Tests spécifiques par classe
./scripts/test.sh specific "users/tests/test_password_reset.py::PasswordResetTestCase"

# Tests spécifiques par méthode
./scripts/test.sh specific "users/tests/test_password_reset.py::PasswordResetTestCase::test_password_forgot_success"

# Tous les tests avec couverture
./scripts/test.sh all

# Mode watch (tests automatiques sur modification)
./scripts/test.sh watch

# Nettoyage des fichiers de test
./scripts/test.sh clean
```

### 🔍 Exemples d'utilisation

#### Tests de développement rapide

```bash
# Tests unitaires rapides
./scripts/test.sh unit

# Test d'une fonctionnalité spécifique
./scripts/test.sh specific "users/tests/test_password_reset.py"
```

#### Tests de validation complète

```bash
# Tous les tests avec couverture
./scripts/test.sh all

# Tests de sécurité
./scripts/test.sh specific "users/tests/test_throttling.py"
```

#### Tests de débogage

```bash
# Test d'une méthode spécifique
./scripts/test.sh specific "users/tests/test_password_reset.py::PasswordResetTestCase::test_password_forgot_success"

# Mode watch pour développement
./scripts/test.sh watch
```

---

## 🔍 Bonnes pratiques

### ✅ **À faire**

1. **Utiliser le script de test** : Toujours utiliser `./scripts/test.sh`
2. **Tests isolés** : Chaque test doit être indépendant
3. **Validation complète** : Tester les cas de succès ET d'échec
4. **Mocking approprié** : Utiliser les mocks pour les services externes
5. **Noms descriptifs** : Noms de tests clairs et explicites

### ❌ **À éviter**

1. **Pytest direct** : Ne pas utiliser `pytest` directement
2. **Tests interdépendants** : Éviter les dépendances entre tests
3. **Services externes** : Ne pas appeler de vrais services en test
4. **Données partagées** : Éviter les données partagées entre tests
5. **Tests lents** : Optimiser les tests pour la vitesse

### 🎯 **Structure des tests**

```python
class FeatureTestCase(MockedAPITestCase):
    """Tests pour une fonctionnalité spécifique."""

    def setUp(self):
        """Configuration initiale."""
        super().setUp()
        # Configuration spécifique au test

    def test_feature_success(self):
        """Test du cas de succès."""
        # Arrange
        data = {"key": "value"}

        # Act
        response = self.client.post(url, data)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "success")

    def test_feature_failure(self):
        """Test du cas d'échec."""
        # Arrange
        invalid_data = {"key": "invalid"}

        # Act
        response = self.client.post(url, invalid_data)

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["status"], "error")
```

---

## 🐛 Dépannage

### ❌ Erreur 429 (Too Many Requests)

**Problème** : Les tests échouent avec des erreurs 429

**Solution** : Utiliser le script de test au lieu de pytest direct

```bash
# ❌ Problème
pytest users/tests/test_password_reset.py
# AssertionError: 429 != 200

# ✅ Solution
./scripts/test.sh specific "users/tests/test_password_reset.py"
```

### ❌ Services externes non mockés

**Problème** : Les tests appellent de vrais services SMS

**Solution** : Vérifier que les tests héritent de `MockedAPITestCase`

```python
# ✅ Correct
class MyTestCase(MockedAPITestCase):
    def setUp(self):
        super().setUp()  # Active les mocks automatiquement
```

### ❌ Tests de throttling qui échouent

**Problème** : Les tests de throttling ne déclenchent pas le throttling

**Solution** : Les tests de throttling sont automatiquement exclus du mode test

```bash
# ✅ Tests de throttling (sans mode test)
./scripts/test.sh specific "users/tests/test_throttling.py"
```

### ❌ Base de données de test corrompue

**Problème** : Données incohérentes entre les tests

**Solution** : Nettoyer la base de données de test

```bash
# Nettoyage complet
./scripts/test.sh clean

# Relancer les tests
./scripts/test.sh unit
```

---

## 📚 Ressources complémentaires

- [README.md](../../README.md) - Documentation principale
- [WATERBILL_FUNCTIONAL_DOCUMENTATION.md](../../WATERBILL_FUNCTIONAL_DOCUMENTATION.md) - Documentation fonctionnelle
- [USERS_API_DOCUMENTATION.md](USERS_API_DOCUMENTATION.md) - Documentation API
- [TESTS_MOCKS_DOCUMENTATION.md](TESTS_MOCKS_DOCUMENTATION.md) - Documentation des mocks

---

## 🎯 Résumé

**Les tests DOIVENT être lancés avec `./scripts/test.sh` pour :**

1. ✅ **Éviter les erreurs 429** : Limites de throttling élevées
2. ✅ **Mocking automatique** : Services externes mockés
3. ✅ **Configuration correcte** : Environnement de test optimisé
4. ✅ **Exclusion intelligente** : Tests de throttling préservés
5. ✅ **Reproductibilité** : Tests cohérents et fiables

**Utilisez toujours le script de test pour une expérience de test optimale !** 🚀
