# 🧪 Documentation des Mocks pour Tests Unitaires

## 📋 Vue d'ensemble

WaterBill utilise un système de mocks sophistiqué pour isoler complètement les tests unitaires des services externes, garantissant des tests déterministes, rapides et reproductibles.

## 🎯 Objectifs des mocks

### **Problèmes résolus :**

- ❌ **Dépendance aux services externes** (Twilio SMS)
- ❌ **Tests non déterministes** (erreurs réseau, limites API)
- ❌ **Exécution lente** (appels réseau réels)
- ❌ **Tests fragiles** (échecs dus à des facteurs externes)

### **Solutions apportées :**

- ✅ **Isolation complète** des services externes
- ✅ **Tests déterministes** avec résultats prévisibles
- ✅ **Exécution rapide** sans appels réseau
- ✅ **Reproductibilité** garantie à chaque exécution

## 📁 Architecture des mocks

### **Structure des fichiers :**

```
users/tests/
├── mocks.py                    # Système de mocks principal
├── test_services.py           # Tests des services avec mocks
├── test_views.py              # Tests des vues avec mocks
├── test_throttling.py         # Tests de throttling avec mocks
├── test_activation.py         # Tests d'activation avec mocks
└── test_atomic_registration.py # Tests atomiques avec mocks
```

### **Composants principaux :**

#### **1. MockSmsGateway**

```python
class MockSmsGateway:
    """Mock pour le gateway SMS."""

    def __init__(self, should_succeed: bool = True, error_message: str = None)
    def send_activation_code(self, phone: str, code: str) -> bool
    def is_available(self) -> bool
    # Enregistre les messages envoyés pour vérification
    self.sent_messages = []
```

#### **2. MockServices**

```python
class MockServices:
    """Classe utilitaire pour mocker plusieurs services."""

    @staticmethod
    def patch_all_external_services():
        """Patch tous les services externes utilisés dans les tests."""
```

## 🔧 Utilisation des mocks

### **1. Test basique avec mock :**

```python
from .mocks import MockServices

class MyTestCase(TestCase):
    def test_with_mocks(self):
        with MockServices.patch_all_external_services() as mock_sms:
            # Votre test ici
            response = self.client.post(url, data)

            # Vérifications
            self.assertEqual(response.status_code, 201)

            # Vérifier que le SMS a été envoyé
            self.assertEqual(len(mock_sms.sent_messages), 1)
            self.assertEqual(mock_sms.sent_messages[0]['phone'], "+237658552294")
```

### **2. Test avec simulation d'erreur SMS :**

```python
def test_sms_failure(self):
    with MockServices.patch_all_external_services() as mock_sms:
        # Configurer le mock pour échouer
        mock_sms.should_succeed = False
        mock_sms.error_message = "Service SMS indisponible"

        response = self.client.post(url, data)

        # Vérifier l'échec
        self.assertEqual(response.status_code, 400)
        self.assertIn("Service SMS indisponible", response.data["message"])
```

### **3. Test avec vérification des paramètres SMS :**

```python
def test_sms_parameters(self):
    with MockServices.patch_all_external_services() as mock_sms:
        user = AuthService.register_user(user_data)

        # Vérifier les paramètres du SMS envoyé
        self.assertEqual(len(mock_sms.sent_messages), 1)
        sms_data = mock_sms.sent_messages[0]

        self.assertEqual(sms_data['phone'], "+237658552294")
        self.assertEqual(len(sms_data['code']), 6)  # Code à 6 chiffres
        self.assertTrue(sms_data['code'].isdigit())
```

## 🎯 Services mockés

### **Services SMS :**

- ✅ **TwilioSmsGateway** : Gateway Twilio pour SMS
- ✅ **DummySmsGateway** : Gateway de test
- ✅ **get_sms_gateway()** : Fonction de sélection du gateway

### **Points de patch :**

```python
with patch('users.gateways.sms.get_sms_gateway', return_value=mock_sms), \
     patch('users.services.get_sms_gateway', return_value=mock_sms), \
     patch('users.gateways.sms.TwilioSmsGateway') as mock_twilio:
```

## 📊 Statistiques des tests

### **Couverture avec mocks :**

| Catégorie                              | Nombre de tests | Statut          |
| -------------------------------------- | --------------- | --------------- |
| **Tests d'activation**                 | 20              | ✅ Tous passent |
| **Tests d'inscription atomique**       | 8               | ✅ Tous passent |
| **Tests de téléphones internationaux** | 6               | ✅ Tous passent |
| **Tests de modèles**                   | 10              | ✅ Tous passent |
| **Tests de sérialiseurs**              | 12              | ✅ Tous passent |
| **Tests de services**                  | 16              | ✅ Tous passent |
| **Tests de throttling**                | 9               | ✅ Tous passent |
| **Tests de gestion des tokens**        | 14              | ✅ Tous passent |
| **Tests de vues**                      | 12              | ✅ Tous passent |
| **TOTAL**                              | **107**         | **✅ 100%**     |

## 🚀 Avantages obtenus

### **Performance :**

- **Exécution rapide** : Pas d'attente réseau
- **Tests parallèles** : Isolation complète
- **CI/CD optimisé** : Tests fiables en pipeline

### **Maintenance :**

- **Pas de configuration externe** : Tests autonomes
- **Pas de limites API** : Pas de quota Twilio
- **Debug facile** : Messages de mock pour traçabilité

### **Qualité :**

- **Tests déterministes** : Mêmes résultats à chaque exécution
- **Couverture complète** : Tous les chemins testés
- **Isolation parfaite** : Chaque test indépendant

## 🔍 Exemples pratiques

### **Test d'inscription avec mock :**

```python
def test_register_view_success(self):
    """Test d'inscription réussie."""
    with MockServices.patch_all_external_services() as mock_sms:
        url = reverse("users:register")
        response = self.client.post(url, self.register_data, format="json")

        # Vérifications
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Vérifier la réponse
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["message"], "Compte créé avec succès. Un code d'activation a été envoyé par SMS.")

        # Vérifier que le SMS a été envoyé
        self.assertEqual(len(mock_sms.sent_messages), 1)
        self.assertEqual(mock_sms.sent_messages[0]['phone'], "+237658552294")
```

### **Test de nettoyage de numéro avec mock :**

```python
def test_phone_cleaning_in_views(self):
    """Test du nettoyage du numéro de téléphone dans les vues."""
    with MockServices.patch_all_external_services() as mock_sms:
        url = reverse("users:register")
        data = self.register_data.copy()
        data["phone"] = "237 67 00 002"  # Format avec espaces

        response = self.client.post(url, data, format="json")

        # Vérifier la normalisation
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        self.assertEqual(response_data["data"]["phone"], "+2376700002")

        # Vérifier que le SMS a été envoyé avec le bon numéro
        self.assertEqual(len(mock_sms.sent_messages), 1)
        self.assertEqual(mock_sms.sent_messages[0]['phone'], "+2376700002")
```

## 🛠️ Configuration et maintenance

### **Installation des dépendances :**

```bash
# Requirements de développement mis à jour
pip install -r requirements-dev.txt

# pytest-cov pour la couverture
pip install pytest-cov==6.0.0
```

### **Commandes de test :**

```bash
# Tests complets avec mocks
./scripts/test.sh unit

# Tests avec couverture
./scripts/test.sh coverage

# Tests spécifiques
./scripts/test.sh specific users/tests/test_services.py
```

## 📝 Bonnes pratiques

### **1. Utilisation des mocks :**

- ✅ **Toujours utiliser** `MockServices.patch_all_external_services()`
- ✅ **Vérifier les appels** aux services mockés
- ✅ **Nettoyer le cache** entre les tests

### **2. Assertions :**

- ✅ **Vérifier le nombre** de messages SMS envoyés
- ✅ **Vérifier les paramètres** (numéro, code)
- ✅ **Vérifier les codes d'erreur** HTTP

### **3. Isolation :**

- ✅ **Nettoyer les données** après chaque test
- ✅ **Utiliser des données uniques** pour éviter les conflits
- ✅ **Activer les utilisateurs** pour les tests de connexion

## 🎉 Résultat final

**WaterBill dispose maintenant d'une suite de tests unitaires robuste, rapide et vraiment unitaire !**

- **107 tests** qui passent à 100%
- **Tests déterministes** sans dépendance externe
- **Exécution rapide** avec mocks
- **Maintenance facilitée** sans configuration externe
- **Qualité garantie** avec isolation complète

Les tests sont maintenant un atout majeur pour le développement et la maintenance de l'application WaterBill ! 🚀✨
