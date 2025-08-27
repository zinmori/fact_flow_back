from fastapi import APIRouter
from app.models import AnalyzeRequest, AnalyzeResponse, VoteRequest
from app.services import db, analyzer
import hashlib
import uuid

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_article(request: AnalyzeRequest):
    # Jour 2 : appel de l'analyzer amélioré
    result = await analyzer.analyze_text(request.text)

    # Générer un ID unique pour l'article basé sur le contenu
    article_id = hashlib.md5(request.text.encode()).hexdigest()

    # Sauvegarder l'analyse en base
    db.save_article_analysis(article_id, request.text, result)

    return result


@router.post("/vote")
async def vote_article(request: VoteRequest):
    db.save_vote(request.article_id, request.user_id, request.vote)
    return {"status": "vote saved"}


@router.get("/article/{article_id}/votes")
async def get_article_votes(article_id: str):
    """Récupérer les votes d'un article"""
    votes = db.get_article_votes(article_id)
    return votes
