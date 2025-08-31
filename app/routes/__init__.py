"""
Routes package initialization
"""

from .main import router
from .users import router as users_router

__all__ = ["router", "users_router"]
