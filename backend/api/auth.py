import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

from backend.database.mongodb import get_database
from backend.repositories.user import UserRepository
from backend.models.models import User
from backend.utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)

logger = logging.getLogger("RepoMindAI.api.auth")
router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer()

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """
    Dependency to fetch and validate the current authenticated user from JWT token
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing user identification subject",
        )
    
    db = get_database()
    user_repo = UserRepository(db)
    user = await user_repo.find_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Registered user not found in database",
        )
    return user

@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: UserRegister, db = Depends(get_database)):
    """
    Register a new user account and return an access token
    """
    user_repo = UserRepository(db)
    existing_user = await user_repo.find_by_email(payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists"
        )
    
    pwd_hash = hash_password(payload.password)
    new_user = User(
        email=payload.email.strip().lower(),
        password_hash=pwd_hash,
        full_name=payload.full_name,
        is_active=True
    )
    
    try:
        created_user = await user_repo.create(new_user)
        token = create_access_token(created_user.id)
        
        return TokenResponse(
            access_token=token,
            user=UserResponse(
                id=str(created_user.id),
                email=created_user.email,
                full_name=created_user.full_name
            )
        )
    except Exception as e:
        logger.error(f"Error during signup: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user. Please try again later."
        )

@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db = Depends(get_database)):
    """
    Authenticate user credentials and return an access token
    """
    user_repo = UserRepository(db)
    user = await user_repo.find_by_email(payload.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
        
    token = create_access_token(str(user.id))
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name
        )
    )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Return current authenticated user profile
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name
    )
