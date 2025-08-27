import firebase_admin
from firebase_admin import credentials, firestore
import os
from typing import Optional, Dict, Any

# Initialize Firebase


def initialize_firebase():
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate("firebase.json")
            firebase_admin.initialize_app(cred)
            print("✅ Firebase initialisé")
        except:
            print("⚠️  Firebase non configuré - utilisation du mode mock")
            return None

    return firestore.client()


# Instance globale
db = initialize_firebase()


def save_vote(article_id: str, user_id: str, vote: int):
    """Enregistrer un vote utilisateur"""
    try:
        if db:
            vote_data = {
                'article_id': article_id,
                'user_id': user_id,
                'vote': vote,
                'timestamp': firestore.SERVER_TIMESTAMP
            }
            db.collection('votes').add(vote_data)
            print(
                f"✅ Vote enregistré en Firebase: article={article_id}, user={user_id}, vote={vote}")
        else:
            # Mode mock si Firebase non disponible
            print(
                f"🔄 Vote enregistré (mock): article={article_id}, user={user_id}, vote={vote}")
    except Exception as e:
        print(f"❌ Erreur lors de l'enregistrement du vote: {e}")


def save_article_analysis(article_id: str, text: str, analysis_result: Dict[Any, Any]):
    """Sauvegarder une analyse d'article"""
    try:
        if db:
            article_data = {
                'article_id': article_id,
                'text': text,
                'ai_score': analysis_result['score'],
                'ai_label': analysis_result['label'],
                'ai_explanation': analysis_result['explanation'],
                'created_at': firestore.SERVER_TIMESTAMP
            }
            db.collection('articles').document(article_id).set(article_data)
            print(f"✅ Article analysé sauvegardé: {article_id}")
        else:
            print(f"🔄 Article analysé (mock): {article_id}")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde de l'analyse: {e}")


def get_article_votes(article_id: str) -> Dict[str, int]:
    """Récupérer les votes d'un article"""
    try:
        if db:
            votes_ref = db.collection('votes').where(
                'article_id', '==', article_id)
            votes = votes_ref.stream()

            positive_votes = 0
            negative_votes = 0

            for vote in votes:
                vote_data = vote.to_dict()
                if vote_data['vote'] == 1:
                    positive_votes += 1
                elif vote_data['vote'] == -1:
                    negative_votes += 1

            return {
                'positive': positive_votes,
                'negative': negative_votes,
                'total': positive_votes + negative_votes
            }
        else:
            # Mode mock
            return {'positive': 0, 'negative': 0, 'total': 0}
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des votes: {e}")
        return {'positive': 0, 'negative': 0, 'total': 0}
