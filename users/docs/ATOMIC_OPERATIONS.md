# 🔒 Opérations Atomiques - WaterBill API

## 📋 Vue d'ensemble

Les opérations de création d'utilisateur dans WaterBill API sont **atomiques** (transactionnelles). Cela signifie que si une erreur survient à n'importe quel moment du processus, **aucune donnée n'est persistée** et toute l'opération est annulée.

## 🎯 Objectif

Assurer la **cohérence des données** et éviter les états incohérents :

- ❌ **Avant** : Utilisateur créé mais SMS non envoyé → Utilisateur "orphelin" inactif
- ✅ **Après** : Tout ou rien → Soit l'utilisateur est créé ET le SMS envoyé, soit rien

## 🔄 Flux Atomique d'Inscription

### 1. **Début de Transaction**

```python
with transaction.atomic():
    # Toute opération dans ce bloc est atomique
```

### 2. **Création de l'Utilisateur**

```python
user = User.objects.create_user(**user_data_clean)
# Utilisateur créé en mémoire (pas encore persisté)
```

### 3. **Envoi du SMS d'Activation**

```python
# Vérification préalable de la disponibilité du service SMS
if not sms_gateway.is_available():
    raise ValueError("Service SMS temporairement indisponible")

# Tentative d'envoi du SMS
if not sms_gateway.send_activation_code(user.phone, code):
    raise ValueError("Échec de l'envoi du SMS")
```

### 4. **Création du Token d'Activation**

```python
# Si le SMS a été envoyé avec succès
token = ActivationToken.create_token(user)
token.code_hash = ActivationToken.hash_code(code)
token.save()
```

### 5. **Validation de la Transaction**

```python
# Si tout s'est bien passé, la transaction est validée
# L'utilisateur et le token sont persistés en base
return user
```

## ⚠️ Gestion des Erreurs

### **Cas d'Échec - Transaction Annulée**

| Étape                | Erreur                 | Résultat                |
| -------------------- | ---------------------- | ----------------------- |
| Création utilisateur | Validation échoue      | ❌ Aucune donnée créée  |
| Envoi SMS            | Service indisponible   | ❌ Utilisateur non créé |
| Envoi SMS            | Échec d'envoi          | ❌ Utilisateur non créé |
| Envoi SMS            | Exception réseau       | ❌ Utilisateur non créé |
| Création token       | Erreur base de données | ❌ Utilisateur non créé |

### **Exemple de Rollback**

```python
# Tentative d'inscription avec SMS indisponible
try:
    user = AuthService.register_user({
        "phone": "670123456",
        "first_name": "John",
        "last_name": "Doe",
        "password": "password123",
        "password_confirm": "password123"
    })
except ValueError as e:
    # L'utilisateur n'a PAS été créé
    # Aucun token d'activation n'existe
    print(f"Échec atomique : {e}")
```

## 🧪 Tests d'Atomicité

### **Test d'Échec SMS**

```python
def test_sms_failure_rolls_back_user_creation(self):
    # Mock SMS pour simuler un échec
    with patch('users.services.get_sms_gateway') as mock_get_gateway:
        mock_gateway = MagicMock()
        mock_gateway.send_activation_code.return_value = False

        # Tentative d'inscription
        with self.assertRaises(ValueError):
            AuthService.register_user(user_data)

        # Vérifier qu'aucun utilisateur n'a été créé
        self.assertEqual(User.objects.count(), 0)
```

### **Test de Succès**

```python
def test_successful_registration_is_atomic(self):
    # Mock SMS pour simuler un succès
    with patch('users.services.get_sms_gateway') as mock_get_gateway:
        mock_gateway = MagicMock()
        mock_gateway.send_activation_code.return_value = True

        # Inscription réussie
        user = AuthService.register_user(user_data)

        # Vérifier que tout a été créé
        self.assertIsNotNone(user)
        self.assertTrue(ActivationToken.objects.filter(user=user).exists())
```

## 🔧 Implémentation Technique

### **Transaction Django**

```python
from django.db import transaction

@staticmethod
def register_user(user_data: Dict[str, Any]) -> User:
    try:
        with transaction.atomic():
            # 1. Créer l'utilisateur
            user = User.objects.create_user(**user_data_clean)

            # 2. Envoyer le SMS (peut échouer)
            ActivationService.create_and_send_activation_code(user)

            # 3. Si tout réussit, valider la transaction
            return user
    except Exception as e:
        # Transaction automatiquement annulée
        raise ValueError(f"Erreur lors de l'inscription: {str(e)}")
```

### **Pré-vérification SMS**

```python
@staticmethod
def create_and_send_activation_code(user: User) -> str:
    # Vérifier la disponibilité AVANT de créer le token
    sms_gateway = get_sms_gateway()

    if not sms_gateway.is_available():
        raise ValueError("Service SMS temporairement indisponible")

    # Essayer d'envoyer AVANT de créer le token
    if not sms_gateway.send_activation_code(user.phone, code):
        raise ValueError("Échec de l'envoi du SMS")

    # Si SMS réussi, créer le token
    token = ActivationToken.create_token(user)
    return code
```

## 📊 Avantages

### **Cohérence des Données**

- ✅ Aucun utilisateur "orphelin" sans token d'activation
- ✅ Aucun token sans utilisateur correspondant
- ✅ Base de données toujours dans un état cohérent

### **Expérience Utilisateur**

- ✅ Messages d'erreur clairs et précis
- ✅ Possibilité de réessayer l'inscription
- ✅ Pas de confusion avec des comptes "semi-créés"

### **Maintenance**

- ✅ Plus facile de déboguer les problèmes
- ✅ Logs clairs sur les échecs
- ✅ Tests automatisés pour vérifier l'atomicité

## 🚀 Commandes de Test

```bash
# Lancer tous les tests d'atomicité
python manage.py test users.tests.test_atomic_registration -v

# Lancer un test spécifique
python manage.py test users.tests.test_atomic_registration.AtomicRegistrationTestCase.test_sms_failure_rolls_back_user_creation -v

# Tests avec couverture
pytest users/tests/test_atomic_registration.py --cov=users.services
```

## 📝 Logs et Monitoring

### **Succès**

```
INFO -- Utilisateur créé et code d'activation envoyé: 670123456
INFO -- Code d'activation envoyé à 670123456
```

### **Échec**

```
ERROR -- Erreur lors de l'inscription atomique: Échec de l'envoi du SMS
ERROR -- Erreur lors de l'envoi du code d'activation: Service SMS temporairement indisponible
```

---

**🎯 Résultat : L'inscription d'utilisateur est maintenant 100% atomique !**
