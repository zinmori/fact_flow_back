from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    text: str


class AnalyzeResponse(BaseModel):
    score: float
    label: str
    explanation: str


class VoteRequest(BaseModel):
    article_id: str
    user_id: str
    vote: int  # 1 = credible, -1 = fake
