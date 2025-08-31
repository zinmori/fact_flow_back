from pydantic import BaseModel
from typing import Optional


class AnalyzeRequest(BaseModel):
    text: str


class AnalyzeResponse(BaseModel):
    article_id: str
    score: float
    label: str
    explanation: str
    community_score: Optional[float] = None
    positive_votes: int = 0
    negative_votes: int = 0
    total_votes: int = 0


class ArticleResponse(BaseModel):
    ai_score: float
    ai_label: str
    community_score: float
    combined_score: float
    combined_label: str
    vote_count: int
    explanation: str


class VoteRequest(BaseModel):
    user_id: str
    article_id: str
    vote: int  # 1 = credible, -1 = fake
