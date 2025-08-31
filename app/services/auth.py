"""
Authentication service for JWT token management
"""

import jwt
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# JWT Configuration
JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 1 week


def create_access_token(user_data: Dict[str, Any]) -> str:
    """Create a JWT access token for a user"""
    try:
        # Prepare payload
        payload = {
            "user_id": user_data["user_id"],
            "username": user_data["username"],
            "email": user_data["email"],
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            "iat": datetime.utcnow(),
            "type": "access"
        }

        # Create token
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        print(f"✅ JWT token created for user: {user_data['username']}")
        return token

    except Exception as e:
        print(f"❌ Error creating JWT token: {e}")
        raise Exception("Could not create access token")


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a JWT access token"""
    try:
        # Decode token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        # Check token type
        if payload.get("type") != "access":
            print("❌ Invalid token type")
            return None

        # Return user data
        return {
            "user_id": payload.get("user_id"),
            "username": payload.get("username"),
            "email": payload.get("email")
        }

    except jwt.ExpiredSignatureError:
        print("❌ JWT token has expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"❌ Invalid JWT token: {e}")
        return None
    except Exception as e:
        print(f"❌ Error verifying JWT token: {e}")
        return None


def get_current_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """Get current user data from JWT token"""
    user_data = verify_access_token(token)
    if user_data:
        # You could fetch additional user data from database here if needed
        return user_data
    return None
