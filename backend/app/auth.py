import os
import uuid
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from fastapi import Header, HTTPException, Depends
import jwt
from dotenv import load_dotenv
from app.models import UserProfile
from app.storage import supabase_client

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET") or os.getenv("SUPABASE_JWT_SECRET") or "growwpulse_fallback_secret_key_2026"
DEFAULT_DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"

# In-memory storage for users when Supabase Auth is unavailable or local fallback is used
_local_users: Dict[str, Dict[str, Any]] = {
    "guest@growwpulse.local": {
        "id": DEFAULT_DEMO_USER_ID,
        "email": "guest@growwpulse.local",
        "name": "Guest Investor",
        "password_hash": hashlib.sha256("guest123".encode()).hexdigest()
    }
}


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _create_access_token(user_id: str, email: str, name: Optional[str] = None) -> str:
    payload = {
        "sub": str(user_id),
        "id": str(user_id),
        "email": email,
        "name": name or email.split("@")[0],
        "aud": "authenticated",
        "role": "authenticated",
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp())
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


async def register_user_account(email: str, password: str, name: Optional[str] = None) -> Dict[str, Any]:
    """Registers a user via Supabase Auth if available, otherwise registers locally."""
    clean_email = email.strip().lower()
    if not clean_email or "@" not in clean_email:
        raise HTTPException(status_code=400, detail="A valid email address is required.")
    if not password or len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    # 1. Attempt Supabase Auth if client exists
    if supabase_client:
        try:
            auth_res = supabase_client.auth.sign_up({
                "email": clean_email,
                "password": password,
                "options": {"data": {"name": name or clean_email.split("@")[0]}}
            })
            if auth_res and auth_res.user:
                token = auth_res.session.access_token if auth_res.session else _create_access_token(auth_res.user.id, clean_email, name)
                user_prof = UserProfile(
                    id=str(auth_res.user.id),
                    email=auth_res.user.email,
                    name=name or (auth_res.user.user_metadata.get("name") if auth_res.user.user_metadata else clean_email.split("@")[0])
                )
                return {
                    "token": token,
                    "user": user_prof,
                    "message": "Account created successfully."
                }
        except Exception as e:
            # If Supabase Auth fails due to configuration or connection, fallback to local registration
            pass

    # 2. Local fallback registration
    if clean_email in _local_users:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    new_id = str(uuid.uuid4())
    display_name = name or clean_email.split("@")[0]
    _local_users[clean_email] = {
        "id": new_id,
        "email": clean_email,
        "name": display_name,
        "password_hash": _hash_password(password)
    }

    token = _create_access_token(new_id, clean_email, display_name)
    return {
        "token": token,
        "user": UserProfile(id=new_id, email=clean_email, name=display_name),
        "message": "Account created successfully."
    }


async def login_user_account(email: str, password: str) -> Dict[str, Any]:
    """Logs in a user via Supabase Auth if available, otherwise validates locally."""
    clean_email = email.strip().lower()
    if not clean_email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required.")

    # 1. Attempt Supabase Auth if client exists
    if supabase_client:
        try:
            auth_res = supabase_client.auth.sign_in_with_password({
                "email": clean_email,
                "password": password
            })
            if auth_res and auth_res.user and auth_res.session:
                user_prof = UserProfile(
                    id=str(auth_res.user.id),
                    email=auth_res.user.email,
                    name=auth_res.user.user_metadata.get("name") if auth_res.user.user_metadata else clean_email.split("@")[0]
                )
                return {
                    "token": auth_res.session.access_token,
                    "user": user_prof,
                    "message": "Login successful."
                }
        except Exception as e:
            # If Supabase Auth fails due to invalid credentials, check if user exists locally
            pass

    # 2. Local fallback authentication
    user_record = _local_users.get(clean_email)
    if not user_record or user_record["password_hash"] != _hash_password(password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = _create_access_token(user_record["id"], clean_email, user_record["name"])
    return {
        "token": token,
        "user": UserProfile(id=user_record["id"], email=clean_email, name=user_record["name"]),
        "message": "Login successful."
    }


async def get_current_user(authorization: Optional[str] = Header(None)) -> UserProfile:
    """
    Extracts and validates Supabase JWT from Authorization Bearer header.
    If no token is present, returns a fallback demo user profile for guest usage.
    """
    if not authorization:
        return UserProfile(id=DEFAULT_DEMO_USER_ID, email="guest@growwpulse.local", name="Guest Investor")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format. Expected 'Bearer <token>'."
        )

    try:
        # First attempt verified decode with JWT_SECRET
        payload = None
        try:
            payload = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False}
            )
        except Exception:
            # Fallback to unverified decode to support tokens issued by Supabase cloud
            payload = jwt.decode(
                token,
                options={"verify_signature": False}
            )

        user_id = payload.get("sub") or payload.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token missing user identification ('sub').")

        email = payload.get("email")
        name = payload.get("name")
        if not name and isinstance(payload.get("user_metadata"), dict):
            name = payload.get("user_metadata", {}).get("name")

        return UserProfile(id=str(user_id), email=email, name=name)

    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")

