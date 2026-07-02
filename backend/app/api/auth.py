from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import UserCreate, UserLogin, UserOut, Token
from app.utils.jwt_helper import get_password_hash, verify_password, create_access_token
from app.database.connection import get_db_cursor
from app.api.deps import get_current_user
from app.utils.logging import logger
import psycopg2

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate):
    """Register a new recruiter."""
    hashed_pwd = get_password_hash(user_in.password)
    
    try:
        with get_db_cursor() as cursor:
            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE email = %s", (user_in.email,))
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
                
            # Insert new user
            cursor.execute(
                "INSERT INTO users (email, password_hash, full_name) VALUES (%s, %s, %s) RETURNING id, email, full_name, created_at",
                (user_in.email, hashed_pwd, user_in.full_name)
            )
            new_user = cursor.fetchone()
            
        logger.info(f"Registered new user: {user_in.email}")
        return dict(new_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user"
        )

@router.post("/login", response_model=Token)
def login(credentials: UserLogin):
    """Log in an existing recruiter and return a JWT access token."""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id, email, password_hash FROM users WHERE email = %s", (credentials.email,))
            user = cursor.fetchone()
            
        if not user or not verify_password(credentials.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Create token
        access_token = create_access_token(data={"sub": str(user["id"]), "email": user["email"]})
        logger.info(f"User logged in: {credentials.email}")
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )

@router.get("/me", response_model=UserOut)
def read_users_me(current_user: dict = Depends(get_current_user)):
    """Get details of the currently logged in recruiter."""
    return current_user
