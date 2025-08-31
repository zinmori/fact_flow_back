"""
User management routes
"""

from fastapi import APIRouter, HTTPException, Depends, Header, UploadFile, File
from typing import Optional
from app.models import (
    UserRegistration, UserLogin, UserProfile, UserUpdate,
    UserResponse, AuthResponse
)
from app.services import db, auth, files

router = APIRouter(prefix="/users", tags=["users"])


def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Dependency to get current authenticated user"""
    if not authorization:
        raise HTTPException(
            status_code=401, detail="Authorization header required")

    try:
        # Extract token from "Bearer <token>"
        token = authorization.split(" ")[1] if authorization.startswith(
            "Bearer ") else authorization
        user_data = auth.verify_access_token(token)

        if not user_data:
            raise HTTPException(
                status_code=401, detail="Invalid or expired token")

        return user_data
    except (IndexError, AttributeError):
        raise HTTPException(
            status_code=401, detail="Invalid authorization header format")


@router.post("/register", response_model=AuthResponse)
async def register_user(user_data: UserRegistration):
    """Register a new user"""
    try:
        # Create user in database
        user_id = db.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            profile_photo=user_data.profile_photo
        )

        if not user_id:
            raise HTTPException(
                status_code=400, detail="Email or username already exists")

        # Get full user data
        full_user_data = db.get_user_by_id(user_id)
        if not full_user_data:
            raise HTTPException(
                status_code=500, detail="Error retrieving user data")

        # Create JWT token
        access_token = auth.create_access_token(full_user_data)

        # Prepare response
        user_response = UserResponse(
            user_id=full_user_data["user_id"],
            username=full_user_data["username"],
            email=full_user_data["email"],
            profile_photo=full_user_data.get("profile_photo"),
            level=full_user_data["level"],
            points=full_user_data["points"],
            badges=full_user_data["badges"],
            streak=full_user_data["streak"],
            is_verified=full_user_data["is_verified"],
            reputation=full_user_data["reputation"]
        )

        return AuthResponse(
            access_token=access_token,
            user=user_response
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Registration error: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error during registration")


@router.post("/login", response_model=AuthResponse)
async def login_user(credentials: UserLogin):
    """Login a user"""
    try:
        # Authenticate user
        user_data = db.authenticate_user(
            credentials.email, credentials.password)

        if not user_data:
            raise HTTPException(
                status_code=401, detail="Invalid email or password")

        # Create JWT token
        access_token = auth.create_access_token(user_data)

        # Prepare response
        user_response = UserResponse(
            user_id=user_data["user_id"],
            username=user_data["username"],
            email=user_data["email"],
            profile_photo=user_data.get("profile_photo"),
            level=user_data["level"],
            points=user_data["points"],
            badges=user_data["badges"],
            streak=user_data["streak"],
            is_verified=user_data["is_verified"],
            reputation=user_data["reputation"]
        )

        return AuthResponse(
            access_token=access_token,
            user=user_response
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login error: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error during login")


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    try:
        user_data = db.get_user_by_id(current_user["user_id"])

        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        return UserResponse(
            user_id=user_data["user_id"],
            username=user_data["username"],
            email=user_data["email"],
            profile_photo=user_data.get("profile_photo"),
            level=user_data["level"],
            points=user_data["points"],
            badges=user_data["badges"],
            streak=user_data["streak"],
            is_verified=user_data["is_verified"],
            reputation=user_data["reputation"]
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    updates: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update current user profile"""
    try:
        # Prepare updates (only non-None values)
        update_data = {k: v for k, v in updates.dict().items()
                       if v is not None}

        if not update_data:
            raise HTTPException(
                status_code=400, detail="No valid updates provided")

        # Update user
        success = db.update_user(current_user["user_id"], update_data)

        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to update user")

        # Get updated user data
        user_data = db.get_user_by_id(current_user["user_id"])

        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        return UserResponse(
            user_id=user_data["user_id"],
            username=user_data["username"],
            email=user_data["email"],
            profile_photo=user_data.get("profile_photo"),
            level=user_data["level"],
            points=user_data["points"],
            badges=user_data["badges"],
            streak=user_data["streak"],
            is_verified=user_data["is_verified"],
            reputation=user_data["reputation"]
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_profile(user_id: str):
    """Get public user profile by ID"""
    try:
        user_data = db.get_user_by_id(user_id)

        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        return UserResponse(
            user_id=user_data["user_id"],
            username=user_data["username"],
            email=user_data["email"],
            profile_photo=user_data.get("profile_photo"),
            level=user_data["level"],
            points=user_data["points"],
            badges=user_data["badges"],
            streak=user_data["streak"],
            is_verified=user_data["is_verified"],
            reputation=user_data["reputation"]
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{user_id}/stats")
async def get_user_stats(user_id: str):
    """Get user statistics"""
    try:
        stats = db.get_user_stats(user_id)

        if not stats:
            raise HTTPException(status_code=404, detail="User not found")

        return stats

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting user stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/me/upload-photo")
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload profile photo for current user"""
    try:
        # Save the uploaded file
        file_path = await files.save_profile_photo(current_user["user_id"], file)

        if not file_path:
            raise HTTPException(
                status_code=500, detail="Failed to save profile photo")

        # Generate the full URL for the photo
        photo_url = files.get_file_url(file_path)

        # Update user profile with new photo URL
        success = db.update_user(current_user["user_id"], {
            "profile_photo": photo_url
        })

        if not success:
            # Clean up the uploaded file if database update fails
            files.delete_profile_photo(file_path)
            raise HTTPException(
                status_code=500, detail="Failed to update user profile")

        # Return success response with the new photo URL
        return {
            "status": "success",
            "message": "Profile photo uploaded successfully",
            "profile_photo": photo_url
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error uploading profile photo: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error during photo upload")
