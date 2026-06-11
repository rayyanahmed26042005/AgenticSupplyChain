"""
Authentication router providing credentials signup/login and mock OAuth.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field, EmailStr
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from app.core.mongodb import mongodb
from app.core.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from app.models.schemas import APIResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============= Pydantic Request Models =============
class UserSignup(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=2)
    role: str = Field(default="admin", description="customer or admin")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class OAuthLogin(BaseModel):
    email: EmailStr
    name: str
    provider: str = Field(..., description="google or microsoft")
    uid: str = Field(..., description="OAuth unique identifier")


# ============= Endpoints =============
@router.post("/signup")
async def signup(request: UserSignup):
    """Register a new user in MongoDB."""
    if mongodb.db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection is inactive",
        )

    # Check if user already exists
    existing_user = await mongodb.db["users"].find_one({"email": request.email.lower()})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists",
        )

    # Validate role
    role = request.role.lower()
    if role not in ["customer", "admin"]:
        role = "admin"

    # Hash the password
    hashed_pwd = hash_password(request.password)

    new_user = {
        "_id": str(uuid.uuid4()),
        "email": request.email.lower(),
        "hashed_password": hashed_pwd,
        "name": request.name,
        "role": role,
        "oauth_provider": None,
        "created_at": datetime.utcnow().isoformat(),
    }

    # Save to MongoDB
    await mongodb.db["users"].insert_one(new_user)

    # Generate token
    token_data = {
        "user_id": new_user["_id"],
        "email": new_user["email"],
        "role": new_user["role"],
        "name": new_user["name"],
    }
    token = create_access_token(token_data)

    user_info = {
        "id": new_user["_id"],
        "email": new_user["email"],
        "name": new_user["name"],
        "role": new_user["role"],
        "oauth_provider": None,
    }

    return APIResponse(
        data={"token": token, "user": user_info},
        message="User account registered successfully",
    )


@router.post("/login")
async def login(request: UserLogin):
    """Authenticate via email/password and return JWT."""
    if mongodb.db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection is inactive",
        )

    user = await mongodb.db["users"].find_one({"email": request.email.lower()})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or password",
        )

    # If user registered via OAuth, they might not have a password
    if not user.get("hashed_password"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please sign in using your OAuth provider",
        )

    # Verify password
    if not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or password",
        )

    # Generate token
    token_data = {
        "user_id": user["_id"],
        "email": user["email"],
        "role": user["role"],
        "name": user["name"],
    }
    token = create_access_token(token_data)

    user_info = {
        "id": user["_id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "oauth_provider": user.get("oauth_provider"),
    }

    return APIResponse(
        data={"token": token, "user": user_info},
        message="Logged in successfully",
    )


@router.post("/oauth")
async def oauth_login(request: OAuthLogin):
    """Simulate OAuth signup/login using Google/Microsoft credentials."""
    if mongodb.db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection is inactive",
        )

    # Find or create user
    user = await mongodb.db["users"].find_one({"email": request.email.lower()})

    if not user:
        # Sign up user
        user = {
            "_id": str(uuid.uuid4()),
            "email": request.email.lower(),
            "hashed_password": None,  # No password for OAuth
            "name": request.name,
            "role": "admin",  # Default to admin role for OAuth signups
            "oauth_provider": request.provider.lower(),
            "oauth_uid": request.uid,
            "created_at": datetime.utcnow().isoformat(),
        }
        await mongodb.db["users"].insert_one(user)
    else:
        # Update oauth credentials if not set
        if not user.get("oauth_provider"):
            await mongodb.db["users"].update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "oauth_provider": request.provider.lower(),
                        "oauth_uid": request.uid,
                    }
                },
            )
            user["oauth_provider"] = request.provider.lower()

    # Generate token
    token_data = {
        "user_id": user["_id"],
        "email": user["email"],
        "role": user["role"],
        "name": user["name"],
    }
    token = create_access_token(token_data)

    user_info = {
        "id": user["_id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "oauth_provider": user["oauth_provider"],
    }

    return APIResponse(
        data={"token": token, "user": user_info},
        message=f"Authenticated via {request.provider.capitalize()} successfully",
    )


@router.get("/me")
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieve details of the currently logged-in user."""
    user_info = {
        "id": current_user["_id"],
        "email": current_user["email"],
        "name": current_user["name"],
        "role": current_user["role"],
        "oauth_provider": current_user.get("oauth_provider"),
    }
    return APIResponse(data=user_info)
