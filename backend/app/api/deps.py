from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.jwt_helper import decode_access_token
from app.database.connection import get_db_cursor
from app.utils.logging import logger

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Dependency to retrieve the currently logged in recruiter from the database using JWT."""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    email = payload.get("email")
    
    # Query database to confirm user exists
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id, email, full_name, created_at FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Convert datetime to string or keep as dict
        return dict(user)
    except Exception as e:
        logger.error(f"Error fetching current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during user validation"
        )
