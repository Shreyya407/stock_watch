import os
from typing import Optional
from fastapi import Header, HTTPException, Depends
import jwt
from dotenv import load_dotenv
from app.models import UserProfile

load_dotenv()

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
DEFAULT_DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"


async def get_current_user(authorization: Optional[str] = Header(None)) -> UserProfile:
    """
    Extracts and validates Supabase JWT from Authorization Bearer header.
    If no token is present, returns a fallback demo user profile for guest usage.
    """
    if not authorization:
        # Default demo guest user for exploration
        return UserProfile(id=DEFAULT_DEMO_USER_ID, email="guest@growwpulse.local")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format. Expected 'Bearer <token>'."
        )

    try:
        # If JWT Secret is provided, verify signature
        if SUPABASE_JWT_SECRET:
            payload = jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False}
            )
        else:
            # Decode unverified to extract claims (sub, email) when backend secret isn't configured
            payload = jwt.decode(
                token,
                options={"verify_signature": False}
            )

        user_id = payload.get("sub") or payload.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token missing user identification ('sub').")

        email = payload.get("email")
        return UserProfile(id=str(user_id), email=email)

    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")
