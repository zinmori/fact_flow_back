from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    text: str


class AnalyzeResponse(BaseModel):
    score: float
    label: str
    explanation: str


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
    text: str
    vote: int  # 1 = credible, -1 = fake
