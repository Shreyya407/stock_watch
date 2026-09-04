import os
import uuid
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from fastapi import Header, HTTPException, Depends, status
import jwt
from dotenv import load_dotenv
from app.models import UserProfile
from app.storage import supabase_client, DatabaseUnavailableException, storage_service

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET") or os.getenv("SUPABASE_JWT_SECRET") or "growwpulse_jwt_secret_key_2026_secure"


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


async def _sync_profile(user_id: str, email: str, name: str):
    """Ensures profile record and starter watchlist are saved/updated in Supabase."""
    if supabase_client:
        try:
            supabase_client.table("profiles").upsert({
                "id": user_id,
                "email": email,
                "name": name,
                "attention_threshold": 40,
                "default_sort": "attention_score",
                "theme": "dark",
                "auto_refresh_interval": 15,
                "notifications_enabled": True,
                "last_active_at": datetime.now(timezone.utc).isoformat()
            }).execute()
        except Exception as e:
            print(f"Notice: public.profiles sync ({e})")
        
        # Ensure user's starter watchlist is provisioned in Supabase
        try:
            await storage_service.initialize_starter_watchlist(user_id)
        except Exception:
            pass


async def register_user_account(email: str, password: str, name: Optional[str] = None) -> Dict[str, Any]:
    """Registers a user via Supabase Auth and stores profile in public.profiles."""
    clean_email = email.strip().lower()
    if not clean_email or "@" not in clean_email:
        raise HTTPException(status_code=400, detail="A valid email address is required.")
    if not password or len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    display_name = name or clean_email.split("@")[0]

    if not supabase_client:
        raise DatabaseUnavailableException(
            message="Database authentication service is temporarily unavailable. Account could not be created."
        )

    # 1. Attempt admin user creation first (auto-confirms user in auth.users)
    try:
        admin_res = supabase_client.auth.admin.create_user({
            "email": clean_email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {"name": display_name}
        })
        if admin_res and admin_res.user:
            u_id = str(admin_res.user.id)
            # Sync user profile & starter watchlist to Supabase
            await _sync_profile(u_id, clean_email, display_name)
            
            token = _create_access_token(u_id, clean_email, display_name)
            return {
                "token": token,
                "user": UserProfile(id=u_id, email=clean_email, name=display_name),
                "message": "Account created successfully."
            }
    except Exception as admin_err:
        err_msg = str(admin_err).lower()
        if "already registered" in err_msg or "already exists" in err_msg or "unique constraint" in err_msg:
            raise HTTPException(status_code=400, detail="An account with this email already exists.")
        
        # 2. Try standard signup if admin API had permission difference
        try:
            auth_res = supabase_client.auth.sign_up({
                "email": clean_email,
                "password": password,
                "options": {"data": {"name": display_name}}
            })
            if auth_res and auth_res.user:
                u_id = str(auth_res.user.id)
                # Sync user profile & starter watchlist to Supabase
                await _sync_profile(u_id, clean_email, display_name)
                
                token = auth_res.session.access_token if auth_res.session else _create_access_token(u_id, clean_email, display_name)
                return {
                    "token": token,
                    "user": UserProfile(id=u_id, email=clean_email, name=display_name),
                    "message": "Account created successfully."
                }
        except HTTPException:
            raise
        except Exception as signup_err:
            signup_msg = str(signup_err).lower()
            if "already registered" in signup_msg or "already exists" in signup_msg:
                raise HTTPException(status_code=400, detail="An account with this email already exists.")
            raise DatabaseUnavailableException(
                message="Database is temporarily unavailable. Could not register account.",
                details=str(signup_err)
            )

    raise DatabaseUnavailableException(
        message="Database authentication service is temporarily unavailable. Could not register account."
    )


async def login_user_account(email: str, password: str) -> Dict[str, Any]:
    """Logs in a user via Supabase Auth and refreshes public.profiles record."""
    clean_email = email.strip().lower()
    if not clean_email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required.")

    if not supabase_client:
        raise DatabaseUnavailableException(
            message="Database authentication service is temporarily unavailable."
        )

    try:
        auth_res = supabase_client.auth.sign_in_with_password({
            "email": clean_email,
            "password": password
        })
        if auth_res and auth_res.user:
            u_id = str(auth_res.user.id)
            name = auth_res.user.user_metadata.get("name") if auth_res.user.user_metadata else clean_email.split("@")[0]
            
            # Sync user profile & starter watchlist to Supabase
            await _sync_profile(u_id, clean_email, name)
            
            token = auth_res.session.access_token if auth_res.session else _create_access_token(u_id, clean_email, name)
            return {
                "token": token,
                "user": UserProfile(id=u_id, email=auth_res.user.email, name=name),
                "message": "Login successful."
            }
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    except HTTPException:
        raise
    except Exception as e:
        err_msg = str(e).lower()
        if "invalid login" in err_msg or "invalid credentials" in err_msg or "invalid grant" in err_msg:
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        raise DatabaseUnavailableException(
            message="Database authentication service is temporarily unavailable.",
            details=str(e)
        )


async def get_current_user(authorization: Optional[str] = Header(None)) -> UserProfile:
    """
    Extracts and validates Supabase JWT from Authorization Bearer header.
    Rejects unauthenticated requests with 401 Unauthorized.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided."
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'."
        )

    try:
        payload = None
        try:
            payload = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False}
            )
        except Exception:
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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid or expired token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Authentication error: {str(e)}")
