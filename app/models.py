from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


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


# === USER MODELS ===

class UserRegistration(BaseModel):
    username: str
    email: EmailStr
    password: str
    profile_photo: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserProfile(BaseModel):
    user_id: str
    username: str
    email: EmailStr
    profile_photo: Optional[str] = None
    level: int = 1
    points: int = 0
    badges: List[str] = []
    streak: int = 0
    is_verified: bool = False
    reputation: float = 0.0
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


class UserUpdate(BaseModel):
    username: Optional[str] = None
    profile_photo: Optional[str] = None


class UserResponse(BaseModel):
    user_id: str
    username: str
    email: EmailStr
    profile_photo: Optional[str] = None
    level: int
    points: int
    badges: List[str]
    streak: int
    is_verified: bool
    reputation: float


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
