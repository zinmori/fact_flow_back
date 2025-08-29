from fastapi import APIRouter
from app.models import AnalyzeRequest, AnalyzeResponse, VoteRequest, ArticleResponse
from app.services import db, analyzer
import hashlib
import uuid

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_article(request: AnalyzeRequest):

    # Générer un ID unique pour l'article basé sur le contenu
    article_id = hashlib.md5(request.text.encode()).hexdigest()
    result = db.get_article_analysis(article_id)
    if result:
        # Si l'analyse existe déjà, on la renvoie
        return result

    result = await analyzer.analyze_text(request.text)

    # Sauvegarder l'analyse en base
    db.save_article_analysis(article_id, request.text, result)

    return result


@router.post("/vote")
async def vote_article(request: VoteRequest):
    article_id = hashlib.md5(request.text.encode()).hexdigest()
    db.save_vote(article_id, request.user_id, request.vote)
    return {"status": "vote saved"}


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
