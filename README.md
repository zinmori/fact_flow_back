# FactFlow Backend

Backend FastAPI pour l'extension de détection de fake news FactFlow.

## Configuration

1. Copier `.env.example` vers `.env` et remplir les variables
2. Configurer Firebase :
    - Créer un projet Firebase
    - Activer Firestore
    - Télécharger le fichier de service account comme `firebase-credentials.json`

## Installation

```bash
# Activer l'environnement virtuel
.\env\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

## Lancement

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoints

### `/ping`

Test de connectivité

### `/analyze` (POST)

Analyse un texte pour détecter les fake news

```json
{
    "text": "Votre texte à analyser"
}
```

Retourne :

```json
{
    "score": 0.75,
    "label": "Green",
    "explanation": "Source fiable. Contient 2 indicateur(s) fiables"
}
```

### `/vote` (POST)

Vote sur la crédibilité d'un article

```json
{
    "article_id": "article_hash",
    "user_id": "user_123",
    "vote": 1
}
```

### `/article/{article_id}/votes` (GET)

Récupère les votes d'un article

## Architecture

-   `app/main.py` : Point d'entrée FastAPI
-   `app/routes.py` : Définition des endpoints
-   `app/models.py` : Modèles Pydantic
-   `app/services/analyzer.py` : Logique d'analyse NLP
-   `app/services/db.py` : Interface Firebase/Firestore

## Jour 1 ✅

-   [x] Squelette FastAPI
-   [x] Endpoints de base (/ping, /analyze, /vote)
-   [x] Connexion Firebase
-   [x] Models Pydantic

## Jour 2 ✅

-   [x] Intégration analyse de patterns textuels
-   [x] Support API HuggingFace (optionnel)
-   [x] Normalisation scores en 3 niveaux
-   [x] Explications détaillées
-   [x] Sauvegarde des analyses
