import firebase_admin
from firebase_admin import credentials, firestore
import os
import hashlib
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

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


def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return hash_password(password) == hashed_password


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
                'score': analysis_result['score'],
                'label': analysis_result['label'],
                'explanation': analysis_result['explanation'],
                'created_at': firestore.SERVER_TIMESTAMP
            }
            db.collection('articles').document(article_id).set(article_data)
            print(f"✅ Article analysé sauvegardé: {article_id}")
        else:
            print(f"🔄 Article analysé (mock): {article_id}")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde de l'analyse: {e}")


def get_article_analysis(article_id: str) -> Optional[Dict[str, Any]]:
    """Récupérer l'analyse d'un article"""
    try:
        if db:
            article_ref = db.collection('articles').document(article_id)
            article = article_ref.get()
            if article.exists:
                article_dict = article.to_dict()
                return {
                    "article_id": article_id,
                    "score": article_dict.get("score"),
                    "label": article_dict.get("label"),
                    "explanation": article_dict.get("explanation"),
                }
            else:
                print(f"⚠️  Article non trouvé: {article_id}")
                return None
    except Exception as e:
        print(f"❌ Erreur lors de la récupération de l'analyse: {e}")
        return None


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


def get_user_vote_count(user_id: str) -> int:
    """Get total number of votes made by a user"""
    try:
        if db:
            votes_ref = db.collection('votes').where('user_id', '==', user_id)
            votes = votes_ref.stream()
            return len(list(votes))
        else:
            return 0
    except Exception as e:
        print(f"❌ Error getting user vote count: {e}")
        return 0


# === USER FUNCTIONS ===

def create_user(username: str, email: str, password: str, profile_photo: Optional[str] = None) -> Optional[str]:
    """Create a new user and return user_id"""
    try:
        if db:
            # Check if email already exists
            existing_user = db.collection('users').where(
                'email', '==', email).limit(1).stream()
            if len(list(existing_user)) > 0:
                print(f"❌ Email already exists: {email}")
                return None

            # Check if username already exists
            existing_username = db.collection('users').where(
                'username', '==', username).limit(1).stream()
            if len(list(existing_username)) > 0:
                print(f"❌ Username already exists: {username}")
                return None

            user_id = str(uuid.uuid4())
            user_data = {
                'user_id': user_id,
                'username': username,
                'email': email,
                'password_hash': hash_password(password),
                'profile_photo': profile_photo,
                'level': 1,
                'points': 0,
                'badges': [],
                'streak': 0,
                'is_verified': False,
                'reputation': 0.0,
                'created_at': firestore.SERVER_TIMESTAMP,
                'last_login': firestore.SERVER_TIMESTAMP
            }

            db.collection('users').document(user_id).set(user_data)
            print(f"✅ User created: {username} ({user_id})")
            return user_id
        else:
            print(f"🔄 User created (mock): {username}")
            return str(uuid.uuid4())
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return None


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate user and return user data"""
    try:
        if db:
            users_ref = db.collection('users').where(
                'email', '==', email).limit(1)
            users = list(users_ref.stream())

            if len(users) == 0:
                print(f"❌ User not found: {email}")
                return None

            user_doc = users[0]
            user_data = user_doc.to_dict()

            if verify_password(password, user_data['password_hash']):
                # Update last login
                db.collection('users').document(user_data['user_id']).update({
                    'last_login': firestore.SERVER_TIMESTAMP
                })

                # Remove password hash from returned data
                user_data.pop('password_hash', None)
                print(f"✅ User authenticated: {email}")
                return user_data
            else:
                print(f"❌ Invalid password for: {email}")
                return None
        else:
            print(f"🔄 User authenticated (mock): {email}")
            return {
                'user_id': str(uuid.uuid4()),
                'username': 'mock_user',
                'email': email,
                'level': 1,
                'points': 0,
                'badges': [],
                'streak': 0,
                'is_verified': False,
                'reputation': 0.0
            }
    except Exception as e:
        print(f"❌ Error authenticating user: {e}")
        return None


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by ID"""
    try:
        if db:
            user_ref = db.collection('users').document(user_id)
            user_doc = user_ref.get()

            if user_doc.exists:
                user_data = user_doc.to_dict()
                # Remove password hash
                user_data.pop('password_hash', None)
                return user_data
            else:
                print(f"❌ User not found: {user_id}")
                return None
        else:
            print(f"🔄 Get user (mock): {user_id}")
            return {
                'user_id': user_id,
                'username': 'mock_user',
                'email': 'mock@example.com',
                'level': 1,
                'points': 0,
                'badges': [],
                'streak': 0,
                'is_verified': False,
                'reputation': 0.0
            }
    except Exception as e:
        print(f"❌ Error getting user: {e}")
        return None


def update_user(user_id: str, updates: Dict[str, Any]) -> bool:
    """Update user data"""
    try:
        if db:
            # Remove sensitive fields that shouldn't be updated directly
            safe_updates = {k: v for k, v in updates.items()
                            if k not in ['user_id', 'email', 'password_hash', 'created_at']}

            if safe_updates:
                db.collection('users').document(user_id).update(safe_updates)
                print(f"✅ User updated: {user_id}")
                return True
            else:
                print(f"⚠️ No valid updates for user: {user_id}")
                return False
        else:
            print(f"🔄 User updated (mock): {user_id}")
            return True
    except Exception as e:
        print(f"❌ Error updating user: {e}")
        return False


def add_points_to_user(user_id: str, points: int, reason: str = "") -> bool:
    """Add points to user and update level if necessary"""
    try:
        if db:
            user_ref = db.collection('users').document(user_id)
            user_doc = user_ref.get()

            if user_doc.exists:
                user_data = user_doc.to_dict()
                current_points = user_data.get('points', 0)
                current_level = user_data.get('level', 1)

                new_points = current_points + points
                new_level = calculate_level(new_points)

                updates = {
                    'points': new_points,
                    'level': new_level
                }

                # If level increased, add level-up badge
                if new_level > current_level:
                    current_badges = user_data.get('badges', [])
                    level_badge = f"level_{new_level}"
                    if level_badge not in current_badges:
                        current_badges.append(level_badge)
                        updates['badges'] = current_badges

                user_ref.update(updates)
                print(
                    f"✅ Points added to user {user_id}: +{points} ({reason})")
                return True
            else:
                print(f"❌ User not found for points update: {user_id}")
                return False
        else:
            print(f"🔄 Points added (mock): {user_id} +{points}")
            return True
    except Exception as e:
        print(f"❌ Error adding points: {e}")
        return False


def calculate_level(points: int) -> int:
    """Calculate user level based on points"""
    # Simple level calculation: every 100 points = 1 level
    return max(1, points // 100 + 1)


def update_user_reputation(user_id: str) -> bool:
    """Update user reputation based on vote accuracy"""
    try:
        if db:
            # Get all votes by the user
            votes_ref = db.collection('votes').where('user_id', '==', user_id)
            votes = list(votes_ref.stream())

            if len(votes) == 0:
                return True  # No votes yet, keep default reputation

            total_votes = len(votes)
            accurate_votes = 0

            # Calculate accuracy (simplified: assume community consensus is correct)
            for vote_doc in votes:
                vote_data = vote_doc.to_dict()
                article_id = vote_data['article_id']
                user_vote = vote_data['vote']

                # Get article votes to determine community consensus
                article_votes = get_article_votes(article_id)
                # Only consider articles with enough votes
                if article_votes['total'] >= 5:
                    community_consensus = 1 if article_votes['positive'] > article_votes['negative'] else -1
                    if user_vote == community_consensus:
                        accurate_votes += 1

            # Calculate reputation (0.0 to 1.0)
            if total_votes > 0:
                reputation = accurate_votes / total_votes

                # Update user reputation
                db.collection('users').document(user_id).update({
                    'reputation': reputation
                })

                print(
                    f"✅ User reputation updated: {user_id} -> {reputation:.2f}")
                return True

        return True
    except Exception as e:
        print(f"❌ Error updating user reputation: {e}")
        return False


def get_user_stats(user_id: str) -> Dict[str, Any]:
    """Get detailed user statistics"""
    try:
        user_data = get_user_by_id(user_id)
        if not user_data:
            return {}

        vote_count = get_user_vote_count(user_id)

        return {
            'total_votes': vote_count,
            'level': user_data.get('level', 1),
            'points': user_data.get('points', 0),
            'reputation': user_data.get('reputation', 0.0),
            'badges_count': len(user_data.get('badges', [])),
            'streak': user_data.get('streak', 0),
            'is_verified': user_data.get('is_verified', False)
        }
    except Exception as e:
        print(f"❌ Error getting user stats: {e}")
        return {}
