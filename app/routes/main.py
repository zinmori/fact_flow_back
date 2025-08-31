from fastapi import APIRouter
from app.models import AnalyzeRequest, AnalyzeResponse, VoteRequest, ArticleResponse
from app.services import db, analyzer
import hashlib
import uuid

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_article(request: AnalyzeRequest):
    """
    Analyze an article for fact-checking
    Returns existing analysis with community data if available, 
    otherwise performs new analysis
    """
    # Générer un ID unique pour l'article basé sur le contenu
    article_id = hashlib.md5(request.text.encode()).hexdigest()

    # Vérifier si l'analyse existe déjà
    existing_analysis = analyzer.get_article_with_community_data(article_id)

    if existing_analysis:
        # Si l'analyse existe déjà, on la renvoie avec toutes les données communautaires
        print(f"✅ Article existant trouvé: {article_id}")
        return AnalyzeResponse(**existing_analysis)

    # Sinon, on effectue une nouvelle analyse
    print(f"🆕 Nouvelle analyse pour: {article_id}")
    result = await analyzer.analyze_text(request.text)

    # Sauvegarder l'analyse en base
    db.save_article_analysis(article_id, request.text, result)

    # Retourner les résultats avec les champs communautaires initialisés
    return AnalyzeResponse(
        article_id=article_id,
        score=result['score'],
        label=result['label'],
        explanation=result['explanation'],
        community_score=None,  # Pas encore de votes
        positive_votes=0,
        negative_votes=0,
        total_votes=0
    )


@router.post("/vote")
async def vote_article(request: VoteRequest):
    """
    Submit a vote for an article and reward the user with points
    """
    try:
        # Save the vote
        db.save_vote(request.article_id, request.user_id, request.vote)
        
        # Reward user with points for voting
        points_awarded = 10  # Base points for voting
        db.add_points_to_user(
            request.user_id, 
            points_awarded, 
            f"Vote on article {request.article_id}"
        )
        
        # Update user reputation based on their voting history
        db.update_user_reputation(request.user_id)
        
        return {
            "status": "vote saved",
            "points_awarded": points_awarded,
            "message": f"Vote saved and {points_awarded} points awarded!"
        }
        
    except Exception as e:
        print(f"❌ Error processing vote: {e}")
        return {"status": "error", "message": "Failed to process vote"}


@router.get("/article/{article_id}/votes")
async def get_article_votes(article_id: str):
    """Récupérer les votes d'un article"""
    votes = db.get_article_votes(article_id)
    return votes


@router.get("/article/{article_id}", response_model=ArticleResponse)
async def get_article_with_combined_score(article_id: str):
    """Get article with AI, community and combined scores"""

    # Get AI analysis
    ai_analysis = db.get_article_analysis(article_id)
    if not ai_analysis:
        return {"error": "Article not found"}

    # Get community votes
    votes_data = db.get_article_votes(article_id)

    # Calculate scores
    ai_score = ai_analysis['score']
    community_score = analyzer.calculate_community_score(votes_data)
    combined_data = analyzer.calculate_combined_score(
        ai_score,
        community_score,
        votes_data['total']
    )

    return ArticleResponse(
        ai_score=ai_score,
        ai_label=ai_analysis['label'],
        community_score=community_score,
        combined_score=combined_data['combined_score'],
        combined_label=combined_data['combined_label'],
        vote_count=votes_data['total'],
        explanation=ai_analysis['explanation']
    )
