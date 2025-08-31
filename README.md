# FactFlow Backend - Documentation API

## Vue d'ensemble

FactFlow Backend est une API de fact-checking alimentée par l'IA (Gemini) avec validation communautaire et gestion d'utilisateurs complète.

## Fonctionnalités principales

### 🤖 Analyse IA avec Gemini

- Analyse automatique du contenu avec Gemini AI
- Traitement du contenu HTML (extraction du contenu principal)
- Scores de fiabilité (0-1) et labels (Green/Yellow/Red)
- Contexte temporel et date du jour inclus dans l'analyse

### 👥 Système communautaire

- Votes utilisateurs sur la crédibilité des articles
- Calcul du score communautaire basé sur les votes
- Récompenses en points pour les votants
- Système de réputation basé sur la précision des votes

### 🏆 Gestion des utilisateurs

- Inscription/Connexion avec JWT
- Profils utilisateurs complets avec :
  - Username et photo de profil
  - Système de niveaux et points
  - Badges débloqués
  - Streak de connexion
  - Statut de vérification
  - Score de réputation
- CRUD complet des utilisateurs

## Endpoints API

### Analyse et votes

```
POST /analyze          - Analyser un texte/article
POST /vote             - Voter sur un article (avec récompenses)
GET /article/{id}      - Récupérer un article avec scores
GET /article/{id}/votes - Récupérer les votes d'un article
```

### Gestion utilisateurs

```
POST /users/register      - Inscription
POST /users/login         - Connexion
GET /users/me             - Profil utilisateur actuel
PUT /users/me             - Mettre à jour le profil
POST /users/me/upload-photo - Upload photo de profil
GET /users/{id}           - Profil public d'un utilisateur
GET /users/{id}/stats     - Statistiques d'un utilisateur
```

```
POST /users/register   - Inscription
POST /users/login      - Connexion
GET /users/me          - Profil utilisateur actuel
PUT /users/me          - Mettre à jour le profil
GET /users/{id}        - Profil public d'un utilisateur
GET /users/{id}/stats  - Statistiques d'un utilisateur
```

## Modèles de données

### AnalyzeResponse

```json
{
  "article_id": "string",
  "score": 0.75,
  "label": "Green",
  "explanation": "L'article provient d'une source fiable...",
  "community_score": 0.8,
  "positive_votes": 15,
  "negative_votes": 3,
  "total_votes": 18
}
```

### UserResponse

```json
{
  "user_id": "uuid",
  "username": "john_doe",
  "email": "john@example.com",
  "profile_photo": "https://...",
  "level": 5,
  "points": 450,
  "badges": ["level_5", "voter_pro"],
  "streak": 7,
  "is_verified": false,
  "reputation": 0.85
}
```

## Système de récompenses

### Points

- **Vote sur un article**: +10 points
- **Niveau**: +1 level tous les 100 points
- **Badges automatiques**: Badge de niveau débloqué

### Réputation

- Calculée basée sur la précision des votes
- Comparaison avec le consensus communautaire
- Mise à jour automatique après chaque vote

## Gestion des fichiers

### Upload de photos de profil

- **Endpoint**: `POST /users/me/upload-photo`
- **Type**: Multipart form-data
- **Fichier**: field name `file`
- **Formats supportés**: .jpg, .jpeg, .png, .gif, .webp
- **Taille max**: 5MB
- **Stockage**: Local sur le serveur
- **URL**: `http://localhost:8000/uploads/profile_photos/{filename}`

### Exemple d'upload

```javascript
const formData = new FormData();
formData.append("file", fileInput.files[0]);

fetch("/users/me/upload-photo", {
  method: "POST",
  headers: {
    Authorization: "Bearer " + token,
  },
  body: formData,
})
  .then((response) => response.json())
  .then((data) => {
    console.log("Photo uploadée:", data.profile_photo);
  });
```

## Sécurité

### Authentification JWT

- Tokens JWT avec expiration (24h \* 7 par défaut)
- Headers Authorization: `Bearer <token>`
- Hachage sécurisé des mots de passe (SHA-256)

### Variables d'environnement

```env
JWT_SECRET_KEY=your-secret-key-change-this-in-production
GOOGLE_API_KEY=your-gemini-api-key
```

## Base de données (Firebase)

### Collections

- `users`: Profils utilisateurs
- `articles`: Analyses d'articles
- `votes`: Votes utilisateurs

### Configuration Firebase

Placer le fichier `firebase.json` à la racine du projet avec les credentials Firebase.

## Installation et démarrage

```bash
# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos clés API

# Démarrer le serveur
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Structure du projet

```
app/
├── main.py              # Point d'entrée FastAPI
├── models.py            # Modèles Pydantic
├── routes/
│   ├── main.py          # Routes principales (analyze, vote)
│   └── users.py         # Routes utilisateurs
└── services/
    ├── analyzer.py      # Service d'analyse Gemini
    ├── auth.py          # Service d'authentification JWT
    └── db.py            # Interface base de données Firebase
```

## Améliorations futures possibles

1. **Système de badges avancé**

   - Badges pour différents types d'activités
   - Badges temporaires (événements spéciaux)

2. **Analyse avancée**

   - Historique des analyses
   - Catégorisation des articles
   - Détection de sources

3. **Gamification**

   - Classements (leaderboards)
   - Défis hebdomadaires
   - Récompenses spéciales

4. **API sociale**
   - Suivi d'autres utilisateurs
   - Commentaires sur les articles
   - Partage d'analyses
