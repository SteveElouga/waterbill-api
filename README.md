# WaterBill API - Documentation

## 📑 Table des matières

- [📋 Description du projet](#-description-du-projet)
- [🏗️ Architecture](#️-architecture)
  - [Applications Django](#applications-django)
  - [Technologies utilisées](#technologies-utilisées)
  - [🔐 Système d'Authentification](#-système-dauthentification)
- [🚀 Installation et lancement](#-installation-et-lancement)
  - [🐍 Installation locale](#-installation-locale-recommandée-pour-le-développement)
  - [🐳 Installation Docker](#-installation-docker-automatique)
  - [🔧 Installation sélective](#-installation-sélective)
- [🐳 Gestion Docker](#-gestion-docker)
- [🛠️ Scripts et commandes automatisées](#️-scripts-et-commandes-automatisées)
- [🌐 Endpoints disponibles](#-endpoints-disponibles)
- [🔧 Configuration](#-configuration)
  - [Variables d'environnement](#variables-denvironnement-env)
  - [Configuration PostgreSQL](#configuration-postgresql-docker)
- [📁 Architecture détaillée du projet](#-architecture-détaillée-du-projet)
- [📝 Notes de développement](#-notes-de-développement)
- [🐛 Dépannage](#-dépannage)
- [🔄 Workflow de développement](#-workflow-de-développement)
- [🔒 Sécurité](#-sécurité)
- [📞 Support](#-support)
- [🚀 Commandes utiles](#-commandes-utiles---raccourcis)
- [📚 Documentation complémentaire](#-documentation-complémentaire)

---

## 📋 Description du projet

**WaterBill API** est une solution complète de gestion de facturation d'eau conçue spécifiquement pour les contextes où l'accès à l'email n'est pas universel. La plateforme utilise l'authentification par numéro de téléphone avec activation SMS, rendant le système accessible à tous les utilisateurs, indépendamment de leur niveau de connectivité internet.

### **🎯 Mission**

Fournir une solution de facturation d'eau moderne, sécurisée et accessible, adaptée aux besoins des pays en développement et des zones avec une connectivité internet limitée.

### **🌍 Vision**

Transformer la gestion de la facturation d'eau en une expérience numérique fluide et inclusive, en utilisant les technologies mobiles comme point d'entrée principal.

### **💡 Valeurs clés**

- **Accessibilité** : Interface adaptée aux utilisateurs avec peu d'expérience numérique
- **Sécurité** : Protection des données personnelles et financières
- **Fiabilité** : Système robuste fonctionnant dans des conditions réseau variables
- **Évolutivité** : Architecture modulaire permettant l'expansion future
- **Conformité** : Respect des réglementations locales et internationales

## 🏗️ Architecture

### Applications Django

- **`core`** : Configuration partagée, utilitaires et endpoints de base
- **`users`** : Gestion des utilisateurs, authentification JWT par téléphone avec activation SMS
- **`billing`** : Factures, index d'eau, génération PDF (en développement)

### **📱 Applications métier**

#### **1. 👥 Application Users (Authentification)**

- **Rôle** : Gestion des identités et accès
- **Fonctionnalités** :
  - Inscription par numéro de téléphone
  - Activation par SMS sécurisée
  - Authentification JWT
  - Gestion des profils utilisateurs
  - Support multi-rôles (client, gestionnaire, technicien, admin)

#### **2. 💧 Application Core (Services partagés)**

- **Rôle** : Fonctionnalités transverses
- **Fonctionnalités** :
  - Configuration système
  - Utilitaires communs
  - Endpoints de santé (health checks)
  - Gestion des erreurs centralisée
  - Logging et monitoring

#### **3. 📊 Application Billing (Facturation)**

- **Rôle** : Gestion de la facturation d'eau
- **Fonctionnalités** :
  - Gestion des compteurs d'eau
  - Relevés d'index
  - Calcul automatique des factures
  - Génération de PDF
  - Historique de consommation
  - Gestion des tarifs

### Technologies utilisées

| Composant            | Technologie                   | Version | Rôle                         |
| -------------------- | ----------------------------- | ------- | ---------------------------- |
| **Framework**        | Django                        | 5.0.8   | Framework web principal      |
| **API**              | Django REST Framework         | 3.15.2  | API REST                     |
| **Authentification** | djangorestframework-simplejwt | 5.5.1   | JWT Tokens                   |
| **Base de données**  | PostgreSQL                    | 16+     | Stockage persistant          |
| **SMS Gateway**      | Twilio                        | 9.8.1   | Envoi SMS réels              |
| **Cache**            | Redis + django-redis          | 7+      | Throttling et cache optimisé |
| **Documentation**    | drf-spectacular               | 0.28.0  | OpenAPI/Swagger              |
| **Tests**            | pytest + pytest-django        | 8.0+    | Tests unitaires              |
| **Conteneurisation** | Docker + Docker Compose       | Latest  | Déploiement                  |

### **🏛️ Patterns architecturaux**

- **🎯 SOLID Principles** : Séparation des responsabilités
- **🔄 Service Layer** : Logique métier centralisée dans `services.py`
- **📋 Repository Pattern** : `UserManager` pour l'accès aux données
- **🛡️ Security by Design** : Validation, throttling, hachage
- **📱 Gateway Pattern** : Interface SMS abstraite avec implémentations

### 🔐 Système d'Authentification

Le projet utilise un système d'authentification personnalisé avec **activation par SMS** :

#### **📱 Flux d'activation par SMS**

1. **Inscription** (`POST /api/auth/register/`) :

   - Crée un utilisateur **inactif** (`is_active=False`)
   - Génère un code d'activation à 6 chiffres
   - Envoie le code par SMS (Twilio en production, console en développement)
   - **Ne retourne PAS de JWT** à ce stade

2. **Activation** (`POST /api/auth/activate/`) :

   - Vérifie le code d'activation reçu par SMS
   - Active le compte (`is_active=True`)
   - **Retourne l'utilisateur activé** (sans tokens JWT)
   - Supprime le token d'activation

3. **Connexion** (`POST /api/auth/login/`) :

   - **Refuse** les comptes non activés
   - Retourne les JWT pour les comptes activés

4. **Renvoi de code** (`POST /api/auth/resend-code/`) :
   - Renvoie un nouveau code d'activation
   - Respecte les limites (1/minute, 5/jour)

#### **🔒 Sécurité d'activation**

- **Codes jamais stockés en clair** (hashage SHA256)
- **Expiration 10 minutes** des codes
- **Limite 5 tentatives** avant verrouillage
- **Cooldown 60s** entre envois de code
- **Quota 5 envois/jour** maximum
- **Throttling multi-niveaux** (IP + téléphone)

#### **🔑 Configuration JWT**

| Paramètre                    | Valeur     | Description                                |
| ---------------------------- | ---------- | ------------------------------------------ |
| **Access Token Lifetime**    | 15 minutes | Durée de vie du token d'accès              |
| **Refresh Token Lifetime**   | 7 jours    | Durée de vie du token de rafraîchissement  |
| **Token Rotation**           | Activée    | Nouveau refresh token à chaque utilisation |
| **Blacklist After Rotation** | Activée    | Ancien token blacklisté après rotation     |
| **Algorithm**                | HS256      | Algorithme de signature                    |

#### **📱 Format International des Numéros de Téléphone**

Le système gère automatiquement le format international des numéros de téléphone :

**🔄 Formatage Automatique :**

- **Entrée utilisateur** : `675799743`, `+237658552294`, `675 799 743`
- **Traitement** : Nettoyage + validation + formatage
- **Stockage DB** : `+675799743`, `+237658552294`, `+675799743`
- **Envoi SMS** : Format international préservé

**🌍 Indicatifs Pays Supportés :**

| Pays                         | Indicatif | Exemple Entrée  | Format Final    |
| ---------------------------- | --------- | --------------- | --------------- |
| 🇵🇬 Papouasie-Nouvelle-Guinée | +675      | `675799743`     | `+675799743`    |
| 🇨🇲 Cameroun                  | +237      | `+237658552294` | `+237658552294` |
| 🇫🇷 France                    | +33       | `33123456789`   | `+33123456789`  |
| 🇺🇸 États-Unis                | +1        | `1234567890`    | `+11234567890`  |

**✅ Validation et Nettoyage :**

- **Longueur** : 9-15 chiffres (après nettoyage)
- **Nettoyage** : Suppression des espaces, tirets, parenthèses
- **Formatage** : Ajout automatique du préfixe `+`
- **Unicité** : Vérification en format international
- **SMS** : Envoi avec format international préservé

**🔧 Correction Récente :**

Un problème de formatage a été résolu dans le `UserManager` :

- **Avant** : Twilio recevait `237658552294` (sans le `+`)
- **Après** : Twilio reçoit `+237658552294` (format international correct)

#### **📞 Configuration SMS**

Le système utilise une architecture flexible avec deux gateways SMS :

**🔧 DummySmsGateway (Développement)**

- 📱 Affiche les codes SMS dans les logs Django
- 🚀 Aucune configuration requise
- 💻 Parfait pour le développement et les tests

**📞 TwilioSmsGateway (Production)**

- 📱 Envoie de vrais SMS via l'API Twilio
- 🔒 Configuration sécurisée via variables d'environnement
- 🌍 Support international

**⚙️ Variables d'environnement Twilio**

```env
# Configuration SMS Twilio (obligatoire en production)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_FROM_NUMBER=+1234567890
```

**🔄 Sélection automatique du gateway**

Le système choisit automatiquement le gateway selon le contexte :

```python
# En développement (DEBUG=True) ou si Twilio non configuré
→ DummySmsGateway (codes dans les logs)

# En production avec Twilio configuré
→ TwilioSmsGateway (SMS réels)

# En production sans Twilio
→ DummySmsGateway (fallback sécurisé)
```

**📋 Installation Twilio**

```bash
# Ajouté automatiquement dans requirements.txt
pip install twilio>=8.0.0
```

**🔐 Configuration Twilio SMS**

1. **Créer un compte Twilio** : https://console.twilio.com/
2. **Récupérer les identifiants** :
   - `Account SID` → `TWILIO_ACCOUNT_SID`
   - `Auth Token` → `TWILIO_AUTH_TOKEN`
   - `Phone Number` → `TWILIO_FROM_NUMBER`
3. **Ajouter dans le fichier `.env`**
4. **Redémarrer l'application**

Le système d'authentification personnalisé basé sur les numéros de téléphone :

#### **Modèle User personnalisé**

- ✅ **Authentification par téléphone** : `phone` comme `USERNAME_FIELD`
- ✅ **Champs obligatoires** : `phone`, `first_name`, `last_name`, `password`
- ✅ **Champs optionnels** : `email`, `address`, `apartment_name` (max 3 caractères)
- ✅ **Sécurité** : Hachage PBKDF2, validation unicité téléphone
- ✅ **Validation téléphone** : Minimum 9 chiffres, format international automatique (+XXXXXXXXX)
- ✅ **Manager personnalisé** : `UserManager` avec validation avancée
- ✅ **Protection throttling** : Limitation des tentatives d'authentification

#### **Architecture Clean (SOLID, KISS, DRY)**

- 🏗️ **SOLID** : Séparation des responsabilités (models, serializers, views, services)
- 🎯 **KISS** : Code simple et lisible, méthodes focalisées
- 🔄 **DRY** : Services centralisés, format de réponse standardisé

#### **Protection par Throttling**

Le système implémente une protection avancée contre les attaques par force brute :

- 🛡️ **LoginRateThrottle** : 15 tentatives de connexion par minute par IP
- 🛡️ **RegisterRateThrottle** : 10 inscriptions par minute par IP
- 🛡️ **AuthRateThrottle** : 30 requêtes par minute pour tous les endpoints d'authentification
- 🛡️ **AnonRateThrottle** : 500 requêtes par heure pour les utilisateurs anonymes
- 🛡️ **UserRateThrottle** : 2000 requêtes par heure pour les utilisateurs authentifiés
- 🛡️ **BurstRateThrottle** : 50 requêtes par seconde pour gérer les pics de trafic

**Réponses de throttling** :

```json
{
  "status": "error",
  "message": "Request was throttled. Expected available in 60 seconds.",
  "data": {}
}
```

**Headers de throttling** :

- `X-RateLimit-Limit` : Limite de requêtes autorisées
- `X-RateLimit-Remaining` : Nombre de requêtes restantes
- `Retry-After` : Secondes à attendre avant la prochaine requête

#### **Endpoints d'authentification**

```bash
# 1. Inscription (crée un compte inactif)
POST /api/auth/register/
{
  "phone": "675799743",
  "first_name": "John",
  "last_name": "Doe",
  "password": "password123",
  "password_confirm": "password123",
  "email": "john@example.com",
  "address": "123 Main St",
  "apartment_name": "A1"
}
# Réponse: Message de confirmation + code SMS envoyé
# Note: Le numéro est automatiquement formaté en +675799743

# 2. Activation du compte (avec code SMS)
POST /api/auth/activate/
{
  "phone": "675799743",
  "code": "123456"
}
# Réponse: Utilisateur activé (sans tokens JWT)
# Note: Le numéro est automatiquement formaté en +675799743

# 3. Renvoi du code d'activation
POST /api/auth/resend-code/
{
  "phone": "675799743"
}
# Réponse: Message de confirmation
# Note: Le numéro est automatiquement formaté en +675799743

# 4. Connexion (compte actif uniquement)
POST /api/auth/login/
{
  "phone": "675799743",
  "password": "password123"
}
# Réponse: JWT tokens + profil utilisateur
# Note: Le numéro est automatiquement formaté en +675799743

# 5. Profil utilisateur (authentifié)
GET /api/auth/profile/
Authorization: Bearer <access_token>
# Réponse: Informations du profil utilisateur

# 6. Rafraîchissement du token JWT
POST /api/auth/token/refresh/
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
# Réponse: {"access": "nouveau_access_token"}

# 7. Déconnexion (blacklist du refresh token)
POST /api/auth/logout/
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
# Réponse: {"status": "success", "message": "Déconnexion réussie"}
```

#### **Flux d'activation par SMS**

1. **Inscription** → Compte créé inactif (`is_active=False`)
2. **Code SMS** → Code 6 chiffres envoyé (expiration 10 minutes)
3. **Activation** → Vérification du code + activation du compte
4. **Connexion** → JWT émis uniquement pour les comptes actifs

#### **Réponse standardisée**

```json
{
  "status": "success|error",
  "message": "Message descriptif",
  "data": {
    "user": {
      "id": 1,
      "phone": "+675799743",
      "first_name": "John",
      "last_name": "Doe",
      "full_name": "John Doe",
      "email": "john@example.com",
      "address": "123 Main St",
      "apartment_name": "A1",
      "date_joined": "2025-09-15T10:30:00Z",
      "is_active": true
    },
    "tokens": {
      "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
  }
}
```

## 🚀 Installation et lancement

> **💡 Conseil** : Pour une configuration complète, consultez d'abord la section [🔧 Configuration](#-configuration).

### 🐳 Méthode Docker (Recommandée)

#### Prérequis

- Docker Desktop (Windows/Mac) ou Docker Engine (Linux)
- Git Bash ou WSL (Windows)

#### Installation rapide avec Docker

1. **Cloner le projet** (si applicable)
2. **Créer le fichier de configuration** :

   ```bash
   cp .env.example .env
   ```

3. **Donner les permissions d'exécution aux scripts** :

   ```bash
   chmod +x scripts/*.sh
   ```

4. **Lancer en mode développement** (avec hot-reload et DEBUG=True) :

   ```bash
   ./scripts/dev.sh up
   ```

   **Ou en mode production** (optimisé avec DEBUG=False) :

   ```bash
   ./scripts/prod.sh up
   ```

#### 🔄 Gestion automatique des modes

Le système gère automatiquement la configuration selon le mode :

- **Mode développement** (`./scripts/dev.sh`) :

  - ✅ `DEBUG=True` (forcé automatiquement)
  - 🔄 Hot-reload activé
  - 📱 `DummySmsGateway` (codes affichés dans les logs)
  - 📊 Logs détaillés

- **Mode production** (`./scripts/prod.sh`) :
  - ✅ `DEBUG=False` (forcé automatiquement)
  - 🚀 Gunicorn (performances optimisées)
  - 📱 Twilio SMS (si configuré) ou fallback DummySmsGateway
  - 🔒 Configuration sécurisée

#### Vérification de l'installation

1. **Vérifier l'état des conteneurs** :

   ```bash
   # Mode développement
   ./scripts/dev.sh status

   # Mode production
   ./scripts/prod.sh status
   ```

2. **Tester l'API** :

   ```bash
   curl http://localhost:8000/ping/
   # Réponse attendue : {"message": "pong"}
   ```

3. **Accéder à la documentation** :
   - Swagger UI : http://localhost:8000/api/docs/
   - Redoc : http://localhost:8000/api/redoc/

### 🐍 Méthode locale (Alternative)

#### Prérequis

- Python 3.12+
- PostgreSQL
- pip

#### Installation locale

1. **Créer un environnement virtuel** :

   ```bash
   python -m venv venv
   ```

2. **Activer l'environnement virtuel** :

   - Windows : `venv\Scripts\activate`
   - Linux/Mac : `source venv/bin/activate`

3. **Installer les dépendances** :

   ```bash
   # Option 1: Installation complète (production + développement)
   pip install -r requirements.txt -r requirements-dev.txt

   # Option 2: Installation séparée
   pip install -r requirements.txt        # Dépendances de production
   pip install -r requirements-dev.txt    # Outils de développement

   # Option 3: Production uniquement
   pip install -r requirements.txt        # Seulement les dépendances nécessaires
   ```

4. **Configurer la base de données** :

   - Créer une base PostgreSQL nommée `waterbill`
   - Copier `env.template` vers `.env`
   - Modifier les variables dans `.env` selon votre configuration

5. **Exécuter les migrations** :

   ```bash
   python manage.py migrate
   ```

6. **Créer un superutilisateur** :

   ```bash
   python manage.py createsuperuser
   ```

7. **Lancer le serveur de développement** :
   ```bash
   python manage.py runserver
   ```

## 🐳 Gestion Docker

### Commandes de base

#### Gestion des services

```bash
# Lancer les services (développement)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Lancer les services (production)
docker-compose -f docker-compose.yml up -d

# Arrêter les services
docker-compose down

# Redémarrer les services
docker-compose restart

# Voir l'état des conteneurs
docker-compose ps
```

#### Logs et débogage

```bash
# Voir les logs de l'application web
docker-compose logs web

# Voir les logs en temps réel
docker-compose logs -f web

# Voir les logs de la base de données
docker-compose logs db

# Voir tous les logs
docker-compose logs
```

#### Accès aux conteneurs

```bash
# Accéder au conteneur web (pour exécuter des commandes Django)
docker-compose exec web bash

# Accéder à la base de données PostgreSQL
docker-compose exec db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}

# Exécuter une commande Django sans entrer dans le conteneur
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

#### Rebuild et mise à jour

```bash
# Reconstruire les images (après modification du Dockerfile)
docker-compose build --no-cache

# Redémarrer avec reconstruction
docker-compose up -d --build
```

### Services Docker

#### Service `web` (Django API)

- **Port** : 8000
- **Image** : Construite depuis `Dockerfile` (prod) ou `Dockerfile.dev` (dev)
- **Variables d'environnement** : Via fichier `.env`
- **Volumes** : Code source monté pour le développement (hot-reload)
- **Multi-stage build** : Optimisation de la taille et des performances

#### Service `db` (PostgreSQL)

- **Port** : 5432
- **Image** : `postgres:16-alpine`
- **Base de données** : `waterbill`
- **Utilisateur** : `postgres` (configurable via `POSTGRES_USER`)
- **Mot de passe** : Configuré via `POSTGRES_PASSWORD` (avec fallback `defaultpassword`)
- **Host** : `waterbill-db` (nom du conteneur)

#### Service `pgadmin` (Optionnel)

- **Port** : 5050
- **Image** : `dpage/pgadmin4:8`
- **Email** : `admin@example.com` (configurable via `PGADMIN_EMAIL`)
- **Mot de passe** : `your-pgadmin-password` (configurable via `PGADMIN_PASSWORD`)
- **URL** : http://localhost:5050

## 🌐 Endpoints disponibles

### Base URL

```
http://localhost:8000/
```

### Endpoints actuels

#### Test de l'API

- **GET** `/ping/`
  - **Description** : Endpoint de test pour vérifier que l'API fonctionne
  - **Authentification** : Aucune
  - **Réponse** : `{"message": "pong"}`

#### Authentification

- **POST** `/api/auth/register/`

  - **Description** : Inscription d'un nouvel utilisateur (compte inactif)
  - **Authentification** : Aucune
  - **Payload** : `{"phone": "670000000", "first_name": "John", "last_name": "Doe", "password": "password123", "password_confirm": "password123"}`
  - **Note** : Le numéro est automatiquement formaté au format international (+670000000)
  - **Réponse** : Message de confirmation + code SMS envoyé
  - **Note** : Le compte reste inactif jusqu'à activation

- **POST** `/api/auth/activate/`

  - **Description** : Activation du compte avec le code SMS
  - **Authentification** : Aucune
  - **Payload** : `{"phone": "670000000", "code": "123456"}`
  - **Note** : Le numéro est automatiquement formaté au format international (+670000000)
  - **Réponse** : Utilisateur activé (sans tokens JWT)

- **POST** `/api/auth/resend-code/`

  - **Description** : Renvoi du code d'activation par SMS
  - **Authentification** : Aucune
  - **Payload** : `{"phone": "670000000"}`
  - **Note** : Le numéro est automatiquement formaté au format international (+670000000)
  - **Réponse** : Message de confirmation
  - **Limites** : 1/minute, 5/jour maximum

- **POST** `/api/auth/login/`

  - **Description** : Connexion d'un utilisateur activé
  - **Authentification** : Aucune
  - **Payload** : `{"phone": "670000000", "password": "password123"}`
  - **Note** : Le numéro est automatiquement formaté au format international (+670000000)
  - **Réponse** : Profil utilisateur + tokens JWT
  - **Note** : Refuse les comptes non activés

- **GET** `/api/auth/profile/`

  - **Description** : Profil de l'utilisateur connecté
  - **Authentification** : JWT requise
  - **Headers** : `Authorization: Bearer <access_token>`
  - **Réponse** : Informations complètes du profil

- **POST** `/api/auth/token/refresh/`

  - **Description** : Rafraîchissement du token JWT
  - **Authentification** : Aucune
  - **Payload** : `{"refresh": "jwt_refresh_token"}`
  - **Réponse** : `{"access": "nouveau_access_token"}`
  - **Durée access token** : 15 minutes
  - **Throttling** : 30 requêtes/minute par IP

- **POST** `/api/auth/logout/`
  - **Description** : Déconnexion avec blacklist du refresh token
  - **Authentification** : Aucune
  - **Payload** : `{"refresh": "jwt_refresh_token"}`
  - **Réponse** : `{"status": "success", "message": "Déconnexion réussie"}`
  - **Action** : Ajoute le refresh token dans la blacklist
  - **Throttling** : 30 requêtes/minute par IP

### Documentation de l'API

- **GET** `/api/schema/` : Schéma OpenAPI/Swagger
- **GET** `/api/docs/` : Interface Swagger UI interactive
- **GET** `/api/redoc/` : Documentation Redoc

### Endpoints à venir

#### Authentification (`/api/`)

- ✅ `POST /api/auth/logout/` : Déconnexion (implémenté)
- ✅ `POST /api/auth/token/refresh/` : Renouvellement du token (implémenté)

#### Gestion des utilisateurs (`/api/users/`)

- `GET /api/users/` : Liste des utilisateurs
- `GET /api/users/{id}/` : Détails d'un utilisateur
- `PUT /api/users/{id}/` : Modification d'un utilisateur

#### Facturation (`/api/billing/`)

- `GET /api/billing/invoices/` : Liste des factures
- `POST /api/billing/invoices/` : Créer une facture
- `GET /api/billing/invoices/{id}/` : Détails d'une facture
- `GET /api/billing/invoices/{id}/pdf/` : Générer PDF d'une facture
- `GET /api/billing/water-indexes/` : Liste des index d'eau
- `POST /api/billing/water-indexes/` : Ajouter un index d'eau

## 🔧 Configuration

> **📚 Voir aussi** : [🐳 Gestion Docker](#-gestion-docker) | [🔒 Sécurité](#-sécurité) | [🐛 Dépannage](#-dépannage)

### Variables d'environnement (.env)

```env
# Configuration de base pour WaterBill API

# Clé secrète Django (générée automatiquement)
SECRET_KEY={SECRET_KEY}

# Mode debug (True pour développement, False pour production)
DEBUG={DEBUG}

# Base de données PostgreSQL (Docker)
POSTGRES_DB={POSTGRES_DB}
POSTGRES_USER={POSTGRES_USER}
POSTGRES_PASSWORD={POSTGRES_PASSWORD}

# DATABASE_URL est générée automatiquement par Docker Compose
# DATABASE_URL=postgres://{POSTGRES_USER}:{POSTGRES_PASSWORD}@db:5432/{POSTGRES_DB}

# Configuration optionnelle
ALLOWED_HOSTS={ALLOWED_HOSTS}

# Superuser automatique (optionnel)
# DJANGO_SUPERUSER_USERNAME={DJANGO_SUPERUSER_USERNAME}
# DJANGO_SUPERUSER_EMAIL={DJANGO_SUPERUSER_EMAIL}

# Configuration SMS Twilio (optionnel - pour SMS réels en production)
# Obtenez ces valeurs sur https://console.twilio.com/
# TWILIO_ACCOUNT_SID={TWILIO_ACCOUNT_SID}
# TWILIO_AUTH_TOKEN={TWILIO_AUTH_TOKEN}
# TWILIO_FROM_NUMBER={TWILIO_FROM_NUMBER}

# Cache Redis (pour throttling optimisé)
# CACHE_URL=redis://redis:6379/1
# DJANGO_SUPERUSER_PASSWORD={DJANGO_SUPERUSER_PASSWORD}

# pgAdmin (optionnel)
PGADMIN_EMAIL={PGADMIN_EMAIL}
PGADMIN_PASSWORD={PGADMIN_PASSWORD}
```

> **⚠️ Important** : Les valeurs entre accolades `{VARIABLE}` sont des **placeholders** qui doivent être remplacés par les valeurs réelles dans votre fichier `.env`. Ne jamais commiter les vraies valeurs dans le code source !

### Configuration PostgreSQL (Docker)

- **Host** : `db` (nom du service Docker)
- **Port** : 5432
- **Database** : `waterbill` (configurable via `POSTGRES_DB`)
- **User** : `postgres` (configurable via `POSTGRES_USER`)
- **Password** : Configuré via `POSTGRES_PASSWORD` (obligatoire)

> **🗄️ Interface graphique** : Consultez la section [Configuration pgAdmin](#️-configuration-pgadmin) pour accéder à l'interface web de gestion de la base de données.

### Configuration PostgreSQL (Local)

- **Host** : localhost
- **Port** : 5432
- **Database** : `waterbill` (configurable via `POSTGRES_DB`)
- **User** : `postgres` (configurable via `POSTGRES_USER`)
- **Password** : Configuré via `POSTGRES_PASSWORD` (obligatoire)

### 📱 Configuration Twilio SMS (Optionnel)

Pour envoyer des SMS réels en production, configurez Twilio :

#### **1. Créer un compte Twilio**

- Allez sur [https://console.twilio.com/](https://console.twilio.com/)
- Créez un compte gratuit
- Récupérez vos credentials

#### **2. Variables d'environnement**

```env
# Dans votre fichier .env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_FROM_NUMBER=+1234567890  # Numéro Twilio (format international)
```

#### **3. Modes de fonctionnement**

- **Développement** (`DEBUG=True`) : Utilise `DummySmsGateway` (log dans console)
- **Production** (`DEBUG=False`) : Utilise `TwilioSmsGateway` (SMS réels)
- **Fallback** : Si Twilio non configuré → utilise `DummySmsGateway`

#### **4. Test des SMS**

```bash
# Voir les codes SMS dans les logs en développement
python manage.py runserver
# Les codes apparaîtront dans la console et les logs Django
```

## 📁 Architecture détaillée du projet

### 🗂️ Structure complète des fichiers et dossiers

```
waterbill/
├── 📄 Fichiers racine
│   ├── manage.py                    # Point d'entrée Django (commandes CLI)
│   ├── requirements.txt             # Dépendances Python de production
│   ├── requirements-dev.txt         # Dépendances Python de développement
│   ├── .env                         # Variables d'environnement (créé depuis env.example)
│   ├── env.example                  # Template des variables d'environnement
│   ├── .gitignore                   # Exclusions Git (fichiers à ignorer)
│   ├── .dockerignore                # Exclusions Docker (optimise les builds)
│   ├── .gitattributes               # Configuration Git (gestion fins de ligne)
│   └── README.md                    # Documentation complète du projet
│
├── 🐳 Configuration Docker
│   ├── Dockerfile                   # Image Docker optimisée (multi-stage build)
│   ├── Dockerfile.dev               # Image Docker pour développement
│   ├── docker-compose.yml           # Services Docker (production-safe)
│   ├── docker-compose.dev.yml       # Override pour développement (hot-reload)
│   ├── docker-compose.prod.yml      # Override pour production explicite
│   └── docker/
│       └── entrypoint.sh            # Script d'initialisation des conteneurs
│
├── 🐍 Configuration Python/Django
│   ├── pytest.ini                  # Configuration pytest (tests)
│   ├── mypy.ini                     # Configuration mypy (vérification de types)
│   ├── bandit.yaml                  # Configuration bandit (sécurité)
│   └── .pre-commit-config.yaml      # Hooks pre-commit (qualité de code)
│
├── 🚀 Scripts d'installation
│   ├── setup.sh                     # Script d'installation (Linux/WSL/Git Bash)
│   ├── setup.ps1                    # Script d'installation (PowerShell)
│   └── setup.bat                    # Script d'installation (Command Prompt)
│
├── 🐳 Scripts Docker
│   ├── dev.sh                       # Script de développement Docker
│   └── prod.sh                      # Script de production Docker
│
├── 🧪 Scripts Tests & Qualité
│   ├── test.sh                      # Script de gestion des tests
│   └── quality.sh                   # Script de qualité du code
│
├── 📋 Scripts Logs & Nettoyage
│   ├── logs.sh                      # Script de gestion des logs
│   └── clean.sh                     # Script de nettoyage
│
├── 🏠 Configuration Django principale
│   └── waterbill/                   # Package de configuration Django
│       ├── __init__.py              # Package Python
│       ├── settings.py              # Configuration Django (DRF + JWT + PostgreSQL)
│       ├── urls.py                  # URLs principales du projet
│       ├── wsgi.py                  # Configuration WSGI (déploiement)
│       ├── asgi.py                  # Configuration ASGI (WebSockets/async)
│       └── __pycache__/             # Cache Python (généré automatiquement)
│
├── 🧩 Applications Django
│   ├── core/                        # Application core (utilitaires partagés)
│   │   ├── __init__.py              # Package Python
│   │   ├── apps.py                  # Configuration de l'application
│   │   ├── models.py                # Modèles de données (vide pour l'instant)
│   │   ├── views.py                 # Endpoint /ping/ et autres vues
│   │   ├── urls.py                  # URLs de l'application core
│   │   ├── admin.py                 # Configuration interface d'administration
│   │   ├── tests.py                 # Tests unitaires de l'application
│   │   └── migrations/              # Migrations de base de données
│   │       └── __init__.py          # Package Python
│   │
│   ├── users/                       # Application utilisateurs (✅ Complète)
│   │   ├── __init__.py              # Package Python
│   │   ├── apps.py                  # Configuration de l'application
│   │   ├── models.py                # Modèle User personnalisé (AbstractBaseUser)
│   │   ├── managers.py              # UserManager pour gestion utilisateurs
│   │   ├── serializers.py           # Serializers register/login/profile
│   │   ├── views.py                 # Vues API d'authentification
│   │   ├── urls.py                  # Routes d'authentification
│   │   ├── services.py              # Logique métier centralisée
│   │   ├── throttling.py            # Classes de throttling personnalisées
│   │   ├── admin.py                 # Interface admin utilisateurs
│   │   ├── tests/                   # Tests unitaires complets
│   │   │   ├── __init__.py          # Package Python
│   │   │   ├── test_models.py       # Tests du modèle User
│   │   │   ├── test_serializers.py  # Tests des serializers
│   │   │   ├── test_services.py     # Tests des services
│   │   │   ├── test_views.py        # Tests des vues API
│   │   │   └── test_throttling.py   # Tests du système de throttling
│   │   └── migrations/              # Migrations utilisateurs
│   │       └── __init__.py          # Package Python
│   │
│   └── billing/                     # Application facturation (à développer)
│       ├── __init__.py              # Package Python
│       ├── apps.py                  # Configuration de l'application
│       ├── models.py                # Modèles factures/index (à développer)
│       ├── views.py                 # Vues facturation (à développer)
│       ├── urls.py                  # URLs facturation (à développer)
│       ├── admin.py                 # Interface admin facturation (à développer)
│       ├── tests.py                 # Tests facturation (à développer)
│       └── migrations/              # Migrations facturation
│           └── __init__.py          # Package Python
│
├── 📊 Logs et données
│   ├── logs/                        # Dossier des logs Django (créé automatiquement)
│   │   └── django.log               # Logs de l'application Django
│   └── venv/                        # Environnement virtuel Python (généré localement)
│       ├── pyvenv.cfg               # Configuration de l'environnement virtuel
│       ├── Scripts/                 # Scripts d'activation (Windows)
│       │   ├── activate.bat         # Activation CMD
│       │   ├── activate.ps1         # Activation PowerShell
│       │   ├── python.exe           # Python de l'environnement virtuel
│       │   ├── pip.exe              # Pip de l'environnement virtuel
│       │   └── django-admin.exe     # Django admin de l'environnement virtuel
│       └── Lib/                     # Bibliothèques Python installées
│           └── site-packages/       # Packages Python installés
└── 🔧 Fichiers générés automatiquement
    ├── db.sqlite3                   # Base de données SQLite (développement local)
    ├── staticfiles/                 # Fichiers statiques collectés (production)
    ├── media/                       # Fichiers média uploadés par les utilisateurs
    ├── htmlcov/                     # Rapports de couverture de code (tests)
    └── .coverage                    # Données de couverture de code
```

### 📋 Description détaillée des composants

#### 🗂️ **Fichiers de configuration**

| Fichier                | Description               | Usage                                                                    |
| ---------------------- | ------------------------- | ------------------------------------------------------------------------ |
| `manage.py`            | Point d'entrée Django     | Commandes CLI : `python manage.py runserver`, `python manage.py migrate` |
| `requirements.txt`     | Dépendances production    | Packages Python avec versions spécifiques pour la production             |
| `requirements-dev.txt` | Dépendances développement | Outils de qualité : black, ruff, mypy, pytest, bandit, pre-commit        |
| `.env`                 | Variables d'environnement | Configuration secrète (mots de passe, clés API)                          |
| `env.example`          | Template variables        | Guide pour créer le fichier `.env`                                       |

#### 🐳 **Configuration Docker**

| Fichier                   | Description            | Usage                                            |
| ------------------------- | ---------------------- | ------------------------------------------------ |
| `Dockerfile`              | Image Django optimisée | Multi-stage build pour production                |
| `Dockerfile.dev`          | Image Django dev       | Multi-stage build avec outils de développement   |
| `docker-compose.yml`      | Services production    | Configuration de base (sécurisée)                |
| `docker-compose.dev.yml`  | Override développement | Hot-reload, runserver, volumes                   |
| `docker-compose.prod.yml` | Override production    | Gunicorn, pas de volumes, optimisations          |
| `docker/entrypoint.sh`    | Script initialisation  | Attente DB, migrations, collectstatic, lancement |

#### 🧩 **Applications Django**

| Application | Rôle                 | Endpoints actuels                                               | À développer                                            |
| ----------- | -------------------- | --------------------------------------------------------------- | ------------------------------------------------------- |
| `core`      | Utilitaires partagés | `/ping/`                                                        | Utilitaires communs, helpers                            |
| `users`     | Gestion utilisateurs | `/api/auth/register/`, `/api/auth/login/`, `/api/auth/profile/` | Tests, admin interface                                  |
| `billing`   | Facturation eau      | -                                                               | `/api/billing/invoices/`, `/api/billing/water-indexes/` |

#### 🔧 **Outils de qualité de code**

| Outil                | Configuration | Rôle                                       |
| -------------------- | ------------- | ------------------------------------------ |
| **Black**            | Pre-commit    | Formatage automatique du code Python       |
| **Ruff**             | Pre-commit    | Linting rapide et corrections automatiques |
| **Pytest**           | `pytest.ini`  | Framework de tests avec couverture         |
| **Bandit**           | `bandit.yaml` | Détection de vulnérabilités de sécurité    |
| **Safety/pip-audit** | Pre-commit    | Vérification des dépendances vulnérables   |

#### 🚀 **Scripts d'installation**

| Script      | Plateforme         | Usage                                       |
| ----------- | ------------------ | ------------------------------------------- |
| `setup.sh`  | Linux/WSL/Git Bash | Installation complète avec vérifications    |
| `setup.ps1` | PowerShell         | Installation avec gestion d'erreurs avancée |
| `setup.bat` | Command Prompt     | Installation simple pour Windows natif      |

#### 🐳 **Scripts Docker**

| Script            | Usage              | Description                                     |
| ----------------- | ------------------ | ----------------------------------------------- |
| `scripts/dev.sh`  | Mode développement | Lancement avec hot-reload, volumes, runserver   |
| `scripts/prod.sh` | Mode production    | Lancement sécurisé avec gunicorn, vérifications |

## 📝 Notes de développement

### 🔄 Workflows de développement

#### Développement quotidien

1. **Modifier le code source** dans les applications Django
2. **Les changements sont automatiquement pris en compte** (hot-reload avec Docker)
3. **Vérifier les logs** : `docker-compose logs -f web`
4. **Tester l'API** : `curl http://localhost:8000/ping/`

#### 🆕 **Changements récents - Améliorations des tests et de la qualité**

**Script de qualité (`quality.sh`) :**
- **✅ Exécution locale** : Plus besoin de Docker pour les contrôles de qualité
- **✅ Fallback pip-audit** : Si `safety` échoue, utilise automatiquement `pip-audit`
- **✅ Suppression MyPy** : Plus de vérification de types (conflits résolus)
- **✅ 4 étapes** : Formatage → Linting → Sécurité → Dépendances
- **✅ Gestion d'erreurs** : Continue même si un outil échoue

**Système de tests amélioré :**
- **✅ Mocks automatiques** : Configuration globale pour tous les tests (162 tests)
- **✅ Fixture Pytest** : `conftest.py` avec mocks automatiques
- **✅ Classes de base** : `MockedTestCase` et `MockedAPITestCase`
- **✅ 100% de réussite** : Tous les tests passent sans SMS réels
- **✅ Dépendance ajoutée** : `argon2-cffi==25.1.0` pour le hachage des mots de passe

**Corrections récentes :**
- **✅ Email pgAdmin corrigé** : `admin@example.com` au lieu de `admin@waterbill.local`
- **✅ Fichiers requirements nettoyés** : Séparation claire prod/dev
- **✅ Dockerfiles mis à jour** : Utilisation des dépendances séparées
- **✅ .gitignore nettoyé** : Suppression des doublons et caractères corrompus
- **✅ Script entrypoint corrigé** : Création superuser avec paramètre `--phone`

**Installation requise** :

```bash
pip install -r requirements-dev.txt
```

#### Ajout de nouvelles dépendances

1. **Modifier `requirements.txt`** (production) ou `requirements-dev.txt` (développement)
2. **Reconstruire l'image** : `docker-compose build`
3. **Redémarrer** : `docker-compose up -d`

#### Gestion des versions

- ✅ **Versions spécifiques** dans `requirements.txt` pour la stabilité
- ✅ **Versions cohérentes** entre `requirements.txt` et `requirements-dev.txt`
- ✅ **PostgreSQL v3** (`psycopg[binary]`) pour les performances
- ✅ **Dernières versions** des packages de sécurité
- ✅ **Compatibilité mypy** : `django-stubs==5.1.1` compatible avec `djangorestframework-stubs==3.15.2`

#### 🐳 Optimisations Docker

- ✅ **Multi-stage build** : Séparation build/runtime pour réduire la taille
- ✅ **Cache des dépendances** : Optimisation des layers Docker
- ✅ **Environnement virtuel** : Isolation des packages Python
- ✅ **Images séparées** : `Dockerfile` (prod) et `Dockerfile.dev` (dev)
- ✅ **Dépendances runtime** : Seulement les packages nécessaires en production
- ✅ **Sécurité** : `requirements-dev.txt` exclu de la production (via `.dockerignore`)
- ✅ **Développement** : Dépendances dev installées directement dans `Dockerfile.dev`
- ✅ **Logs** : Dossier `logs/` créé automatiquement au démarrage
- ✅ **Builds propres** : Nettoyage automatique des logs avant build

#### Installation des dépendances

```bash
# 🐍 Installation locale (recommandée pour le développement)
source venv/bin/activate  # Activer l'environnement virtuel
pip install -r requirements.txt -r requirements-dev.txt

# 🐳 Installation Docker (automatique)
docker-compose build  # Installe automatiquement requirements.txt

# 🔧 Installation sélective
pip install -r requirements.txt        # Production uniquement
pip install -r requirements-dev.txt    # Développement uniquement

# 📱 Installation Twilio (optionnel - pour SMS réels)
pip install twilio>=8.0.0
```

#### 🐳 Scripts Docker pour le développement

```bash
# 🚀 Développement (recommandé)
./scripts/dev.sh up          # Lancer en mode développement
./scripts/dev.sh logs        # Voir les logs
./scripts/dev.sh shell       # Accéder au conteneur
./scripts/dev.sh test        # Lancer les tests
./scripts/dev.sh down        # Arrêter les services

# 🏭 Production (avec vérifications de sécurité)
./scripts/prod.sh up         # Lancer en mode production
./scripts/prod.sh status     # Vérifier le statut
./scripts/prod.sh backup     # Sauvegarder la DB
./scripts/prod.sh update     # Mise à jour complète
```

#### 🧪 Scripts Tests & Qualité

```bash
# 🧪 Tests
./scripts/test.sh unit        # Tests unitaires seulement
./scripts/test.sh integration # Tests d'intégration
./scripts/test.sh coverage    # Rapport de couverture de code
./scripts/test.sh watch       # Mode watch (tests automatiques)
./scripts/test.sh specific core/tests.py  # Tests spécifiques
./scripts/test.sh all         # Tous les tests avec couverture
./scripts/test.sh clean       # Nettoyage des fichiers de test

# 🔍 Qualité du code (exécution locale)
./scripts/quality.sh format   # Formatage avec Black
./scripts/quality.sh lint     # Analyse avec Ruff
./scripts/quality.sh security # Analyse de sécurité avec Bandit
./scripts/quality.sh deps     # Vérification des dépendances (Safety/pip-audit)
./scripts/quality.sh precommit # Exécution des hooks pre-commit
./scripts/quality.sh install-hooks # Installation des hooks pre-commit
./scripts/quality.sh all      # Tous les contrôles de qualité (4 étapes)
./scripts/quality.sh fix      # Corrections automatiques (format + lint)
./scripts/quality.sh clean    # Nettoyage des fichiers de qualité
```

#### 📋 Scripts Logs

```bash
# 📋 Gestion des logs
./scripts/logs.sh show        # Affiche les 50 dernières lignes des logs Django
./scripts/logs.sh follow      # Suit les logs Django en temps réel
./scripts/logs.sh errors      # Affiche uniquement les erreurs
./scripts/logs.sh clear       # Efface le fichier de logs
./scripts/logs.sh docker      # Affiche les logs du conteneur Docker
./scripts/logs.sh size        # Affiche la taille des fichiers de logs
```

#### 🧹 Scripts Nettoyage

```bash
# 🧹 Nettoyage
./scripts/clean.sh logs       # Supprime le dossier logs/
./scripts/clean.sh cache      # Supprime le cache Python (__pycache__, *.pyc)
./scripts/clean.sh docker     # Nettoyage complet Docker (conteneurs, images, volumes)
./scripts/clean.sh test       # Supprime les fichiers de test (htmlcov, .coverage, etc.)
./scripts/clean.sh all        # Nettoyage complet (logs + cache + test + docker optionnel)
./scripts/clean.sh prebuild   # Nettoyage minimal avant build (logs + cache)
```

#### Workflow qualité de code

1. **Pre-commit installé** : Les hooks s'exécutent automatiquement avant chaque commit
2. **Tests manuels** : `pytest`, `black`, `ruff`, `mypy`, `bandit`
3. **Couverture de code** : Générée automatiquement dans `htmlcov/`

#### 🚀 Workflows recommandés

**Développement quotidien :**

```bash
# 1. Lancer l'environnement
./scripts/dev.sh up

# 2. Développement avec hot-reload
# ... modifier le code ...

# 3. Tests rapides
./scripts/test.sh unit

# 4. Qualité du code
./scripts/quality.sh fix

# 5. Tests complets avant commit
./scripts/test.sh all
./scripts/quality.sh all
```

**Avant commit :**

```bash
# Installation des hooks (une seule fois)
./scripts/quality.sh install-hooks

# Vérification complète
./scripts/quality.sh precommit
./scripts/test.sh all
```

**Avant déploiement :**

```bash
# Tests et qualité complets
./scripts/test.sh all
./scripts/quality.sh all

# Déploiement en production
./scripts/prod.sh up
```

### 🔐 Commandes d'authentification

#### Migrations et base de données

```bash
# Générer les migrations pour l'app users (inclut ActivationToken)
python manage.py makemigrations users

# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Accéder à l'interface d'administration
# http://localhost:8000/admin/
```

#### 🆕 Migrations pour le système d'activation

```bash
# Créer les migrations pour le nouveau modèle ActivationToken
python manage.py makemigrations users --name create_activation_token

# Appliquer les migrations
python manage.py migrate

# Vérifier les tables créées
python manage.py dbshell
\dt users_*
\q
```

#### Tests d'authentification

```bash
# Lancer tous les tests de l'app users
pytest users/tests/

# Tests spécifiques
pytest users/tests/test_models.py      # Tests du modèle User
pytest users/tests/test_serializers.py # Tests des serializers
pytest users/tests/test_services.py    # Tests des services
pytest users/tests/test_views.py       # Tests des vues API
pytest users/tests/test_throttling.py  # Tests du système de throttling

# Tests avec couverture
pytest users/tests/ --cov=users --cov-report=html

# Tests spécifiques au système d'activation
pytest users/tests/test_activation.py -v
```

#### Test des endpoints

```bash
# 1. Inscription (crée un compte inactif + envoie SMS)
# Exemple avec numéro papouasien (formaté automatiquement en +675799743)
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "675799743",
    "first_name": "John",
    "last_name": "Doe",
    "password": "password123",
    "password_confirm": "password123",
    "email": "john@example.com",
    "address": "123 Main St",
    "apartment_name": "A1"
  }'

# Exemple avec numéro camerounais (formaté automatiquement en +237658552294)
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+237658552294",
    "first_name": "Alice",
    "last_name": "Ndongo",
    "password": "password123",
    "password_confirm": "password123",
    "email": "alice@example.com"
  }'

# 2. Activation (avec le code reçu par SMS - visible dans les logs)
curl -X POST http://localhost:8000/api/auth/activate/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "675799743",
    "code": "123456"
  }'

# 3. Renvoi de code (si nécessaire)
curl -X POST http://localhost:8000/api/auth/resend-code/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "675799743"
  }'

# 4. Connexion (seulement après activation)
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "675799743",
    "password": "password123"
  }'

# 5. Profil (avec token JWT)
curl -X GET http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Bearer <access_token>"
```

#### 📱 Test du système d'activation

```bash
# Voir les codes SMS dans les logs Django
tail -f logs/django.log | grep "Code d'activation"

# Ou dans la console du serveur Django
python manage.py runserver
# Les codes apparaissent dans la console : "🔐 Code d'activation pour 670000000: 123456"
```

### 🧩 Ajout de nouveaux endpoints

#### Étapes de développement

1. **Créer les modèles** dans `models.py` de l'app
2. **Générer les migrations** : `python manage.py makemigrations`
3. **Appliquer les migrations** : `python manage.py migrate`
4. **Créer les vues** dans `views.py` de l'app
5. **Ajouter les URLs** dans `urls.py` de l'app
6. **Inclure les URLs** dans `waterbill/urls.py`
7. **Écrire les tests** dans `tests.py`
8. **Mettre à jour la documentation** API

#### Exemple de structure d'endpoint

```python
# billing/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def list_invoices(request):
    return Response({"invoices": []})
```

```python
# billing/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('invoices/', views.list_invoices, name='invoice-list'),
]
```

### 🧪 Tests et qualité

#### Structure des tests

- **Tests unitaires** : `users/tests/` (162 tests avec mocks automatiques)
- **Tests d'intégration** : `tests/` (à créer)
- **Tests API** : Utiliser `pytest-django` et `factory-boy`
- **Mocks** : `users/tests/mocks.py` pour services externes

#### Tests unitaires avec mocks

WaterBill utilise un système de tests unitaires robustes avec des mocks pour isoler complètement les tests des services externes.

##### **🎯 Avantages des mocks :**

- **Tests déterministes** : Plus de dépendance aux services externes (Twilio)
- **Exécution rapide** : Pas d'appels réseau réels
- **Reproductibilité** : Mêmes résultats à chaque exécution
- **Isolation** : Chaque test teste seulement la logique métier
- **Mocks automatiques** : Configuration globale pour tous les tests

##### **🔧 Configuration automatique des mocks :**

Le système utilise deux approches complémentaires pour garantir que tous les services externes sont mockés :

**1. Fixture Pytest globale (`users/tests/conftest.py`) :**
```python
@pytest.fixture(autouse=True)
def mock_external_services():
    """Fixture Pytest pour mocker tous les services externes automatiquement."""
    with MockServices.patch_all_external_services() as mock_sms:
        yield mock_sms
```

**2. Classes de base pour Django TestCase (`users/tests/test_settings.py`) :**
```python
class MockedTestCase(TestCase):
    """Classe de base pour les tests Django TestCase avec mocks automatiques."""
    def setUp(self):
        super().setUp()
        # Configuration automatique des mocks pour tous les services externes

class MockedAPITestCase(MockedTestCase):
    """Classe de base pour les tests d'API avec mocks automatiques."""
    def setUp(self):
        super().setUp()
        self.client = APIClient()
```

##### **✅ Résultat :**

- **162 tests passent** avec 100% de réussite
- **Aucun SMS réel** n'est envoyé lors des tests
- **Configuration transparente** : Les mocks s'appliquent automatiquement
- **Maintenance simplifiée** : Plus besoin de gérer manuellement les mocks dans chaque test

#### Commandes de test

```bash
# Tests complets avec couverture (162 tests)
./scripts/test.sh unit

# Tests avec couverture de code
./scripts/test.sh coverage

# Tests spécifiques à une app
./scripts/test.sh specific users/tests/test_models.py

# Tests avec watch mode
./scripts/test.sh watch
```

#### Qualité de code

Le projet applique des standards de qualité stricts avec des corrections automatiques :

##### **🔧 Standards appliqués :**

- **Types cohérents** : Toutes les fonctions ont des type hints corrects
- **Constantes réutilisables** : Messages d'erreur centralisés dans `users/serializers.py`
- **Exceptions spécifiques** : `ValueError` au lieu d'exceptions génériques
- **Algorithme de hachage sécurisé** : Argon2 pour les mots de passe en tests
- **Concaténation de chaînes propre** : F-strings au lieu de concaténation implicite
- **Suppression des instructions inutiles** : Pas de `pass` inutiles

##### **📝 Exemples de constantes :**

```python
# Messages d'erreur constants dans users/serializers.py
PHONE_REQUIRED_ERROR = "Le numéro de téléphone est obligatoire."
PHONE_INVALID_ERROR = "Le numéro de téléphone est invalide."
PHONE_LENGTH_ERROR = "Le numéro de téléphone doit contenir entre 9 et 15 chiffres."
STATUS_HELP_TEXT = "Statut de la réponse"
MESSAGE_HELP_TEXT = "Message de confirmation"
```

##### **🛠️ Commandes de qualité :**

```bash
# Formatage automatique
black .

# Linting et corrections
ruff check --fix .

# Analyse de sécurité rapide (optimisée)
./scripts/quality.sh security-quick

# Analyse de sécurité complète
./scripts/quality.sh security

# Tous les contrôles de qualité
./scripts/quality.sh all

# Vérification des types
mypy .

# Sécurité
bandit -r .
```

#### ⚡ Optimisations de performance

**Script de qualité optimisé :**

- **Bandit** : 5-10x plus rapide avec exclusions intelligentes
- **Redis** : Cache optimisé pour le throttling DRF
- **Configuration** : Fichier `.bandit` pour exclure les faux positifs

**Commandes optimisées :**

```bash
# Analyse de sécurité rapide (15-30s)
./scripts/quality.sh security-quick

# Analyse complète avec rapport JSON (30-60s)
./scripts/quality.sh security

# Corrections automatiques
./scripts/quality.sh fix

# Nettoyage des fichiers temporaires
./scripts/quality.sh clean
```

### 🚀 Déploiement

#### Préparation production

1. **Variables d'environnement** : Configurer `.env` avec valeurs de production
2. **Base de données** : Migrer vers PostgreSQL en production
3. **Fichiers statiques** : Configurer `STATIC_ROOT` et `MEDIA_ROOT`
4. **Sécurité** : `DEBUG=False`, `SECRET_KEY` sécurisé

#### Checklist déploiement

- [ ] Variables d'environnement configurées
- [ ] Base de données PostgreSQL accessible
- [ ] Migrations appliquées
- [ ] Fichiers statiques collectés
- [ ] Tests passent
- [ ] Logs configurés
- [ ] Monitoring en place

### 🔐 Authentification

- **JWT (JSON Web Tokens)** : Authentification sécurisée
- **Endpoints protégés** : Header `Authorization: Bearer <token>`
- **Token d'accès** : Valide 1 heure
- **Token de rafraîchissement** : Valide 7 jours

### 🌐 CORS

- **Configuration** : Requêtes autorisées depuis ports 3000 et 8080
- **Modifiable** : Dans `settings.py` si nécessaire

### ⚙️ Configuration détaillée

#### Variables d'environnement essentielles

| Variable             | Description                     | Développement                | Production                         |
| -------------------- | ------------------------------- | ---------------------------- | ---------------------------------- |
| `SECRET_KEY`         | Clé secrète Django              | `django-insecure-...`        | Clé forte générée                  |
| `DEBUG`              | Mode debug                      | `True`                       | `False`                            |
| `DATABASE_URL`       | URL base de données             | `sqlite:///db.sqlite3`       | `postgres://...`                   |
| `POSTGRES_DB`        | Nom base PostgreSQL             | `waterbill`                  | `waterbill_prod`                   |
| `POSTGRES_USER`      | Utilisateur PostgreSQL          | `postgres`                   | `waterbill_user`                   |
| `POSTGRES_PASSWORD`  | Mot de passe PostgreSQL         | `postgres`                   | Mot de passe fort                  |
| `DJANGO_RUNSERVER`   | Mode serveur                    | `1` (runserver)              | `0` (gunicorn)                     |
| **SMS Twilio**       |                                 |                              |                                    |
| `TWILIO_ACCOUNT_SID` | Identifiant compte Twilio       | Non requis (DummySmsGateway) | `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxx`   |
| `TWILIO_AUTH_TOKEN`  | Token d'authentification Twilio | Non requis (DummySmsGateway) | `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| `TWILIO_FROM_NUMBER` | Numéro expéditeur Twilio        | Non requis (DummySmsGateway) | `+1234567890`                      |
| **Cache Redis**      | Cache optimisé pour throttling  | `redis://redis:6379/1`       | `redis://redis:6379/1`             |
| `CACHE_URL`          | URL du cache Redis              | `redis://redis:6379/1`       | `redis://redis:6379/1`             |

#### Configuration Django (settings.py)

| Section                  | Description                     | Valeurs                                               |
| ------------------------ | ------------------------------- | ----------------------------------------------------- |
| **INSTALLED_APPS**       | Applications Django             | Django, DRF, JWT, CORS, drf-spectacular, django-redis |
| **MIDDLEWARE**           | Middlewares                     | CORS, Security, Auth, Messages, Cache                 |
| **DATABASES**            | Configuration DB                | Via `env.db()` (PostgreSQL/SQLite)                    |
| **REST_FRAMEWORK**       | Configuration DRF               | JWT auth, permissions, pagination, throttling         |
| **SIMPLE_JWT**           | Configuration JWT               | Tokens, algorithmes, durées                           |
| **CORS_ALLOWED_ORIGINS** | Origines CORS                   | localhost:3000, localhost:8080                        |
| **SPECTACULAR_SETTINGS** | Documentation API               | Swagger/Redoc, schémas OpenAPI                        |
| **CACHES**               | Configuration Cache             | Redis optimisé pour throttling DRF                    |
| **AUTH_USER_MODEL**      | Modèle utilisateur personnalisé | `users.User` (authentification par téléphone)         |
| **THROTTLING**           | Limitation des requêtes         | Multi-niveaux (IP, utilisateur, téléphone)            |

### Mode développement vs production

#### 🐳 Configuration Docker sécurisée

Le projet utilise une configuration Docker sécurisée avec séparation dev/prod :

**Fichiers de configuration :**

- `docker-compose.yml` : Configuration de base (production-safe)
- `docker-compose.dev.yml` : Configuration explicite pour le développement
- `docker-compose.prod.yml` : Configuration explicite pour la production

#### 🚀 Commandes d'utilisation

**Développement (avec hot-reload) :**

```bash
# Script automatisé (recommandé)
./scripts/dev.sh up

# Ou commande manuelle
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Avec logs en temps réel
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Rebuild si modification du Dockerfile
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

**Production (sécurisé) :**

```bash
# Script automatisé (recommandé)
./scripts/prod.sh up

# Ou commandes manuelles
# Méthode 1: Configuration de base uniquement
docker-compose -f docker-compose.yml up -d

# Méthode 2: Force la configuration prod explicite
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Rebuild pour production
./scripts/prod.sh build
```

#### 🔧 Différences dev/prod

| Aspect          | Développement                           | Production                      |
| --------------- | --------------------------------------- | ------------------------------- |
| **Serveur**     | `DJANGO_RUNSERVER=1` (runserver)        | `DJANGO_RUNSERVER=0` (gunicorn) |
| **Code source** | Volume bind mount `.:/app` (hot-reload) | Copié dans l'image (sécurisé)   |
| **Restart**     | `restart: "no"`                         | `restart: always`               |
| **DEBUG**       | `DEBUG=True` (automatique)              | `DEBUG=False` (automatique)     |
| **SMS Gateway** | `DummySmsGateway` (logs console)        | `TwilioSmsGateway` (SMS réels)  |
| **Cache**       | Redis pour throttling                   | Redis pour throttling           |
| **Logs**        | Détaillés avec codes SMS                | Optimisés pour production       |
| **pgAdmin**     | Activé par défaut                       | Optionnel/désactivé             |

#### ✅ Vérifications

```bash
# Vérifier la configuration chargée (dev)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml config

# Vérifier la configuration chargée (prod)
docker-compose -f docker-compose.yml config

# Vérifier les volumes montés (dev doit montrer .:/app)
docker-compose exec web df -h

# Vérifier le mode serveur
docker-compose exec web env | grep DJANGO_RUNSERVER
```

#### 🏗️ Architecture Multi-stage Build

Le projet utilise une architecture Docker multi-stage optimisée :

**Production (`Dockerfile`)** :

```
Stage 1 (builder) → Stage 2 (runtime)
├── Installation des dépendances avec outils de build
├── Environnement virtuel Python
└── Copie vers l'image runtime (sans outils de build)
```

**Développement (`Dockerfile.dev`)** :

```
Stage 1 (dependencies) → Stage 2 (development)
├── Installation des dépendances de base + dev
├── Environnement virtuel Python
└── Outils de développement inclus (black, mypy, pytest, etc.)
```

**Avantages** :

- 🚀 **Taille réduite** : Image de production sans outils de build
- ⚡ **Cache optimisé** : Layers séparés pour les dépendances
- 🔒 **Sécurité** : `requirements-dev.txt` exclu de la production
- 🛠️ **Flexibilité** : Images séparées pour dev/prod

#### 📋 Configuration des Logs

Le projet utilise un système de logs Django configuré pour :

**Fichiers de logs** :

- `logs/django.log` - Logs de l'application Django
- Création automatique du dossier `logs/` au démarrage
- Exclusion du dossier `logs/` dans `.gitignore`

**Configuration Django** :

```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "django.log",
            "formatter": "verbose",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": False,
        },
        "waterbill": {
            "handlers": ["file", "console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
```

**Gestion des logs** :

- ✅ **Création automatique** du dossier au démarrage
- ✅ **Rotation des logs** (configurable)
- ✅ **Niveaux de log** différenciés (DEBUG pour l'app, INFO pour Django)
- ✅ **Sortie console** ET fichier
- ✅ **Scripts de gestion** pour consultation et maintenance

#### 🔨 Optimisation des Builds Docker

**Problème résolu** : Les logs ne sont plus copiés dans les images Docker.

**Solutions implémentées** :

1. **`.dockerignore`** : Exclusion du dossier `logs/`
2. **Scripts de build** : Nettoyage automatique avant build
3. **Script de nettoyage** : `./scripts/clean.sh prebuild`

**Commandes optimisées** :

```bash
# Builds avec nettoyage automatique
./scripts/dev.sh build        # Dev : logs nettoyés automatiquement
./scripts/prod.sh build       # Prod : logs nettoyés automatiquement
./scripts/prod.sh update      # Prod : nettoyage + build + restart

# Nettoyage manuel avant build
./scripts/clean.sh prebuild   # Nettoyage minimal (logs + cache)
./scripts/clean.sh all        # Nettoyage complet
```

**Avantages** :

- 🚀 **Images plus légères** : Pas de logs dans les images
- ⚡ **Builds plus rapides** : Moins de fichiers à copier
- 🔒 **Sécurité** : Pas de données sensibles dans les images
- 🧹 **Maintenance** : Nettoyage automatique et manuel

## 🐛 Dépannage

> **📚 Voir aussi** : [🔧 Configuration](#-configuration) | [🐳 Gestion Docker](#-gestion-docker) | [🔒 Sécurité](#-sécurité)

### Erreurs Docker courantes

1. **Erreur de permissions sur entrypoint.sh** :

   ```bash
   chmod +x docker/entrypoint.sh
   ```

2. **Erreur de fins de ligne (Windows)** :

   ```bash
   dos2unix docker/entrypoint.sh
   ```

3. **Conteneur web ne démarre pas** :

   ```bash
   docker-compose logs web
   ```

4. **Base de données non accessible** :
   ```bash
   docker-compose logs db
   docker-compose exec db pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}
   ```

### Erreurs de dépendances courantes

1. **Conflit de versions mypy** :

   ```bash
   ERROR: Cannot install django-stubs==5.0.0 and djangorestframework-stubs==3.15.2
   ```

   **Solution** : Utiliser `django-stubs==5.1.1` (déjà corrigé dans requirements-dev.txt)

2. **Conflit de versions pip** :
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt -r requirements-dev.txt
   ```

### Erreurs Django courantes

1. **Erreur de migration** :

   ```bash
   docker-compose exec web python manage.py migrate
   ```

2. **Erreur de dépendances** :

   ```bash
   docker-compose build --no-cache
   docker-compose up -d
   ```

3. **Erreur de configuration** :
   - Vérifier le fichier `.env`
   - Vérifier les variables d'environnement : `docker-compose exec web env`

### Erreurs de format de numéro de téléphone

1. **Erreur Twilio "Invalid 'To' Phone Number"** :

   ```
   ERROR: HTTP 400 error: Unable to create record: Invalid 'To' Phone Number: 23767579XXXX
   ```

   **Cause** : Le numéro n'est pas au format international (manque le `+`)

   **Solution** : Le problème a été corrigé dans le `UserManager`. Vérifiez que :

   - Le numéro est bien formaté avec le `+` dans la base de données
   - Le `UserManager.create_user()` utilise le format international
   - Le gateway SMS reçoit le numéro au bon format

2. **Erreur de validation de numéro** :

   ```
   ERROR: Le numéro de téléphone doit contenir au moins 9 chiffres
   ```

   **Cause** : Numéro trop court après nettoyage

   **Solution** : Vérifiez que le numéro contient au moins 9 chiffres

3. **Erreur d'unicité** :

   ```
   ERROR: Un utilisateur avec ce numéro de téléphone existe déjà
   ```

   **Cause** : Le numéro existe déjà en base de données

   **Solution** : Utilisez un numéro différent ou vérifiez l'unicité en format international

### Logs

- **Django** : `logs/django.log`
- **Docker** : `docker-compose logs web`
- **PostgreSQL** : `docker-compose logs db`

## 🔄 Workflow de développement

### Développement quotidien

1. Modifier le code source
2. Les changements sont automatiquement pris en compte (hot-reload)
3. Vérifier les logs : `docker-compose logs -f web`
4. Tester l'API : `curl http://localhost:8000/ping/`

### Ajout de nouvelles dépendances

1. Modifier `requirements.txt`
2. Reconstruire l'image : `docker-compose build`
3. Redémarrer : `docker-compose up -d`

### Mise en production

1. Modifier `docker-compose.yml` :
   - Retirer le volume `.:/app`
   - Changer `DJANGO_RUNSERVER=0`
2. Modifier `.env` :
   - `DEBUG=False`
   - Variables de production
3. Reconstruire et déployer

## 🔒 Sécurité

> **📚 Voir aussi** : [🔧 Configuration](#-configuration) | [🚀 Commandes utiles](#-commandes-utiles---raccourcis)

### Variables d'environnement sensibles

⚠️ **IMPORTANT** : Ne jamais commiter de mots de passe ou clés secrètes !

- Utilisez `env.example` comme template
- Générez des mots de passe forts pour la production
- Utilisez des variables d'environnement pour tous les secrets
- Le fichier `.env` est exclu de Git (voir `.gitignore`)

### Bonnes pratiques

- ✅ Clés secrètes via variables d'environnement
- ✅ Mots de passe PostgreSQL sécurisés
- ✅ `DEBUG=False` en production
- ✅ `SECRET_KEY` unique par environnement

### 🔑 Génération sécurisée des clés secrètes

#### Pour créer une clé secrète Django sécurisée :

```bash
# Option 1: Avec Django installé
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Option 2: Avec le script utilitaire du projet
python scripts/generate-secret-key.py

# Option 3: Avec OpenSSL
openssl rand -base64 32
```

#### Configuration initiale :

1. **Copier le template** : `cp env.example .env`
2. **Générer une clé** avec une des méthodes ci-dessus
3. **Remplacer** `your-secret-key-here` dans `.env` par la clé générée
4. **Ne jamais commiter** le fichier `.env` (déjà dans `.gitignore`)

#### 🛠️ Scripts de génération automatique :

Le projet inclut des scripts pour générer automatiquement les clés et mots de passe :

```bash
# Générer une clé secrète Django
python scripts/generate-secret-key.py

# Générer un mot de passe PostgreSQL sécurisé
python scripts/generate-db-password.py
```

Ces scripts génèrent des valeurs sécurisées et affichent les instructions d'utilisation.

### 🔐 Génération sécurisée des mots de passe PostgreSQL

#### Pour créer un mot de passe PostgreSQL sécurisé :

```bash
# Option 1: Avec le script utilitaire du projet
python scripts/generate-db-password.py

# Option 2: Avec OpenSSL
openssl rand -base64 32

# Option 3: Avec Python
python -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters + string.digits + '!@#$%^&*') for _ in range(16)))"
```

#### Configuration PostgreSQL :

1. **Générer un mot de passe** avec une des méthodes ci-dessus
2. **Définir** `POSTGRES_PASSWORD` dans votre fichier `.env`
3. **Vérifier** que `DATABASE_URL` utilise les variables d'environnement
4. **Ne jamais commiter** les mots de passe dans Git

## 📞 Support

Pour toute question ou problème, consultez :

- La documentation Django : https://docs.djangoproject.com/
- La documentation DRF : https://www.django-rest-framework.org/
- La documentation Docker : https://docs.docker.com/
- Les logs d'erreur dans `logs/django.log` ou `docker-compose logs`

## 🚀 Commandes utiles - Raccourcis

> **📚 Retour** : [📑 Table des matières](#-table-des-matières) | [🐳 Gestion Docker](#-gestion-docker)

## 🛠️ Scripts et commandes automatisées

### 📋 Scripts disponibles

Le projet inclut plusieurs scripts automatisés dans le dossier `scripts/` pour simplifier le développement et le déploiement :

#### 🐳 Scripts Docker

**Script de développement** (`./scripts/dev.sh`) :

- ✅ Lance le mode développement avec `DEBUG=True`
- 🔄 Active le hot-reload et les logs détaillés
- 📱 Utilise `DummySmsGateway` (codes SMS dans les logs)
- 💾 Sauvegarde automatique du fichier `.env` si `DEBUG=False`

**Script de production** (`./scripts/prod.sh`) :

- ✅ Lance le mode production avec `DEBUG=False`
- 🚀 Utilise Gunicorn pour de meilleures performances
- 📱 Utilise Twilio SMS (si configuré) ou fallback DummySmsGateway
- 💾 Sauvegarde automatique du fichier `.env` si `DEBUG=True`
- 🔒 Configuration sécurisée pour la production

#### 📱 Scripts utilitaires

**Scripts de test** (`./scripts/test.sh`) :

- 🧪 Lance les tests avec pytest
- 📊 Génère les rapports de couverture
- 🔍 Tests spécifiques par module

**Scripts de qualité** (`./scripts/quality.sh`) :

- 🎨 Formatage du code avec Black
- 🔍 Linting avec Ruff
- 🔒 Vérification de sécurité avec Bandit
- 📦 Audit des dépendances avec Safety/pip-audit

**Scripts de logs** (`./scripts/logs.sh`) :

- 📋 Affichage des logs en temps réel
- 🗂️ Gestion des fichiers de logs
- 🔍 Recherche dans les logs

**Scripts de nettoyage** (`./scripts/clean.sh`) :

- 🧹 Nettoyage des conteneurs Docker
- 🗑️ Suppression des volumes orphelins
- 📁 Nettoyage des fichiers temporaires

### 🔄 Gestion automatique de DEBUG

Les scripts gèrent automatiquement la valeur `DEBUG` selon le contexte :

#### Mode Développement

```bash
./scripts/dev.sh up
# ⚠️  DEBUG=False détecté, passage automatique à DEBUG=True pour le développement
# ✅ DEBUG=True appliqué automatiquement
# 🐳 Services de développement lancés !
```

#### Mode Production

```bash
./scripts/prod.sh up
# ⚠️  DEBUG=True détecté, passage automatique à DEBUG=False pour la production
# ✅ DEBUG=False appliqué automatiquement
# 🏭 Services de production lancés !
```

#### Restauration après production

```bash
./scripts/prod.sh down
# Êtes-vous sûr de vouloir arrêter les services de production ? (y/N): y
# ✅ Services arrêtés
# Restaurer le fichier .env original (avec DEBUG=True) ? (y/N): y
# ✅ Fichier .env restauré (DEBUG=True)
```

#### Restauration manuelle

```bash
./scripts/prod.sh restore-env
# 🔄 Restauration du fichier .env original...
# ✅ Fichier .env restauré (DEBUG=True)
# 💡 Vous pouvez maintenant lancer le mode développement
```

### 📁 Fichiers de sauvegarde

Les scripts créent automatiquement des sauvegardes :

- `.env.backup.YYYYMMDD_HHMMSS` (sauvegarde production)
- `.env.backup.dev.YYYYMMDD_HHMMSS` (sauvegarde développement)

---

## 🚀 Commandes utiles - Raccourcis

### 🐳 Docker - Développement

```bash
# 🚀 Script automatique (recommandé)
./scripts/dev.sh up          # Lancer en développement
./scripts/dev.sh logs        # Voir les logs
./scripts/dev.sh shell       # Accéder au conteneur
./scripts/dev.sh test        # Lancer les tests
./scripts/dev.sh down        # Arrêter les services

# 🔧 Commandes manuelles
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
docker-compose logs -f web
docker-compose exec web bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py shell
```

### 🐳 Docker - Production

```bash
# 🏭 Script automatique (recommandé)
./scripts/prod.sh up         # Lancer en production
./scripts/prod.sh status     # Vérifier le statut
./scripts/prod.sh backup     # Sauvegarder la DB
./scripts/prod.sh update     # Mise à jour complète
./scripts/prod.sh logs       # Voir les logs
./scripts/prod.sh down       # Arrêter les services

# 🔧 Commandes manuelles
docker-compose -f docker-compose.yml up -d
docker-compose -f docker-compose.yml build --no-cache
docker-compose -f docker-compose.yml config
```

### 🐍 Django - Local

```bash
# Activer l'environnement virtuel
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Migrations
python manage.py makemigrations
python manage.py migrate

# Serveur de développement
python manage.py runserver

# Shell Django
python manage.py shell

# Collecter les fichiers statiques
python manage.py collectstatic
```

### 🧪 Tests et qualité

```bash
# Tests complets
pytest

# Tests avec couverture
pytest --cov=. --cov-report=html

# Formatage du code
black .

# Linting
ruff check --fix .

# Sécurité
bandit -r .

# Vérification des dépendances
safety check  # ou pip-audit si safety échoue

# Pre-commit (tous les hooks)
pre-commit run --all-files
```

#### 🧪 Tests du système d'activation SMS

```bash
# Tests spécifiques au système d'activation
pytest users/tests/test_activation.py -v

# Tests des services d'activation
pytest users/tests/test_services.py::TestActivationService -v

# Tests des gateways SMS
pytest users/tests/test_services.py::TestSmsGateway -v

# Tests complets d'authentification
pytest users/tests/ -v
```

#### 📱 Test des endpoints d'activation

```bash
# 1. Inscription (compte inactif)
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "675799743",
    "first_name": "John",
    "last_name": "Doe",
    "password": "password123",
    "password_confirm": "password123",
    "email": "john@example.com"
  }'

# 2. Vérifier le code SMS dans les logs (mode dev)
./scripts/dev.sh logs | grep "Code d'activation"

# 3. Activation du compte
curl -X POST http://localhost:8000/api/auth/activate/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "675799743",
    "code": "123456"
  }'

# 4. Renvoi de code (si nécessaire)
curl -X POST http://localhost:8000/api/auth/resend-code/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "675799743"
  }'

# 5. Connexion (compte maintenant actif)
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "675799743",
    "password": "password123"
  }'

# 6. Profil utilisateur (avec JWT)
curl -X GET http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 🔍 Test du système SMS en développement

En mode développement, les codes SMS sont affichés dans les logs :

```bash
# Lancer en mode développement
./scripts/dev.sh up

# Surveiller les logs pour les codes SMS
./scripts/dev.sh logs | grep "SMS"

# Exemple de sortie dans les logs :
# [INFO] Code d'activation envoyé à +675799743: 123456
# [INFO] SMS envoyé via DummySmsGateway: +675799743 -> "Votre code d'activation: 123456"
```

### 📊 Base de données

```bash
# Accéder à PostgreSQL (Docker)
docker-compose exec db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}

# Sauvegarder la base
docker-compose exec db pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > backup.sql

# Restaurer la base
docker-compose exec -T db psql -U ${POSTGRES_USER} ${POSTGRES_DB} < backup.sql

# Accéder à pgAdmin
# http://localhost:5050
```

#### 🗄️ Configuration pgAdmin

**Accès à l'interface web :**

- **URL** : http://localhost:5050
- **Email** : `{PGADMIN_EMAIL}` (vérifiez dans votre fichier `.env`)
- **Mot de passe** : `{PGADMIN_PASSWORD}` (vérifiez dans votre fichier `.env`)

**Création du serveur PostgreSQL :**

| Paramètre    | Valeur                                             |
| ------------ | -------------------------------------------------- |
| **Name**     | `WaterBill Local`                                  |
| **Host**     | `waterbill-db`                                     |
| **Port**     | `5432`                                             |
| **Database** | `{POSTGRES_DB}`                                    |
| **Username** | `{POSTGRES_USER}`                                  |
| **Password** | `{POSTGRES_PASSWORD}` (vérifiez dans votre `.env`) |

**Étapes de connexion :**

1. Ouvrir http://localhost:5050
2. Se connecter avec les identifiants pgAdmin
3. Cliquer sur "Add New Server"
4. Remplir les informations ci-dessus
5. Sauvegarder la connexion

> **Note** : Le mot de passe PostgreSQL est généré automatiquement par Docker et visible dans les logs du conteneur `waterbill-db`. Consultez votre fichier `.env` pour les valeurs exactes de `{POSTGRES_PASSWORD}` et `{PGADMIN_PASSWORD}`.

### 🔧 Maintenance

```bash
# Nettoyer les conteneurs Docker
docker-compose down
docker system prune -a

# Vérifier l'espace disque
docker system df

# Logs de tous les services
docker-compose logs

# Redémarrer un service spécifique
docker-compose restart web
```

## 📚 Documentation complémentaire

### **📖 Documentation technique**

- **[📱 Documentation API Users](../users/USERS_API_DOCUMENTATION.md)** : Documentation complète de l'application d'authentification
- **[💧 Documentation Fonctionnelle](../WATERBILL_FUNCTIONAL_DOCUMENTATION.md)** : Spécifications fonctionnelles et métier
- **[🔧 Opérations Atomiques](../users/docs/ATOMIC_OPERATIONS.md)** : Documentation des opérations transactionnelles

### **🌐 Documentation en ligne**

- **Swagger UI** : http://localhost:8000/api/docs/
- **Redoc** : http://localhost:8000/api/redoc/
- **Admin Django** : http://localhost:8000/admin/

### **📚 Ressources externes**

- **Django REST Framework** : https://www.django-rest-framework.org/
- **JWT Authentication** : https://django-rest-framework-simplejwt.readthedocs.io/
- **Twilio SMS** : https://www.twilio.com/docs/sms
- **PostgreSQL** : https://www.postgresql.org/docs/

---

**📱 WaterBill API - Documentation v1.0**
_Dernière mise à jour : Septembre 2025_
