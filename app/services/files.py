"""
File management service for local file storage
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException

# Configuration
UPLOAD_DIR = "uploads"
PROFILE_PHOTOS_DIR = os.path.join(UPLOAD_DIR, "profile_photos")
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def initialize_upload_directories():
    """Create upload directories if they don't exist"""
    os.makedirs(PROFILE_PHOTOS_DIR, exist_ok=True)
    print(f"✅ Upload directories initialized: {PROFILE_PHOTOS_DIR}")


def validate_image_file(file: UploadFile) -> bool:
    """Validate uploaded image file"""
    # Check file extension
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        return False

    # Check content type
    if not file.content_type.startswith("image/"):
        return False

    return True


def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename while preserving extension"""
    file_extension = Path(original_filename).suffix.lower()
    unique_name = f"{uuid.uuid4()}{file_extension}"
    return unique_name


async def save_profile_photo(user_id: str, file: UploadFile) -> Optional[str]:
    """
    Save profile photo and return the file path
    Returns None if save fails
    """
    try:
        # Initialize directories
        initialize_upload_directories()

        # Validate file
        if not validate_image_file(file):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
            )

        # Generate unique filename
        unique_filename = generate_unique_filename(file.filename)
        file_path = os.path.join(PROFILE_PHOTOS_DIR, unique_filename)

        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Return relative path for URL generation
        relative_path = f"uploads/profile_photos/{unique_filename}"
        print(f"✅ Profile photo saved: {relative_path} for user {user_id}")

        return relative_path

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error saving profile photo: {e}")
        return None


def delete_profile_photo(file_path: str) -> bool:
    """Delete a profile photo file"""
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            print(f"✅ Profile photo deleted: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"❌ Error deleting profile photo: {e}")
        return False


def get_file_url(file_path: str, base_url: str = "http://localhost:8000") -> str:
    """Generate full URL for a file path"""
    if not file_path:
        return ""

    # Ensure file_path uses forward slashes for URLs
    normalized_path = file_path.replace("\\", "/")
    return f"{base_url}/{normalized_path}"


def cleanup_old_user_photos(user_id: str, current_photo_path: str):
    """Remove old profile photos for a user (optional cleanup)"""
    try:
        # This is a simple implementation
        # In a more robust system, you might track all user photos in the database
        if current_photo_path and os.path.exists(current_photo_path):
            # For now, we just ensure the current photo exists
            pass
    except Exception as e:
        print(f"⚠️ Error during photo cleanup: {e}")


# Initialize directories on module import
initialize_upload_directories()
