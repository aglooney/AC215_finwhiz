"""
Supabase authentication module.

Handles user authentication using Supabase Auth.
"""

import os
from typing import Dict, Any
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Security scheme for extracting Bearer token
security = HTTPBearer()


def sign_up(email: str, password: str) -> Dict[str, Any]:
    """
    Create a new user in Supabase.

    Args:
        email: User's email address
        password: User's password

    Returns:
        Dict containing user and session information

    Raises:
        HTTPException: If signup fails
    """
    try:
        response = supabase.auth.sign_up(
            {
                "email": email,
                "password": password,
            }
        )

        if response.user is None:
            raise HTTPException(status_code=400, detail="Signup failed")

        return {
            "user": {
                "id": response.user.id,
                "email": response.user.email,
            },
            "session": (
                {
                    "access_token": response.session.access_token if response.session else None,
                    "refresh_token": response.session.refresh_token if response.session else None,
                    "expires_in": response.session.expires_in if response.session else None,
                    "expires_at": response.session.expires_at if response.session else None,
                }
                if response.session
                else None
            ),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Signup failed: {str(e)}")


def sign_in(email: str, password: str) -> Dict[str, Any]:
    """
    Sign in an existing user.

    Args:
        email: User's email address
        password: User's password

    Returns:
        Dict containing user and session information

    Raises:
        HTTPException: If sign in fails
    """
    try:
        response = supabase.auth.sign_in_with_password(
            {
                "email": email,
                "password": password,
            }
        )

        if response.user is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return {
            "user": {
                "id": response.user.id,
                "email": response.user.email,
            },
            "session": (
                {
                    "access_token": response.session.access_token if response.session else None,
                    "refresh_token": response.session.refresh_token if response.session else None,
                    "expires_in": response.session.expires_in if response.session else None,
                    "expires_at": response.session.expires_at if response.session else None,
                }
                if response.session
                else None
            ),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Sign in failed: {str(e)}")


def sign_out(access_token: str) -> Dict[str, str]:
    """
    Sign out a user.

    Args:
        access_token: User's access token

    Returns:
        Dict with success message

    Raises:
        HTTPException: If sign out fails
    """
    try:
        supabase.auth.sign_out()
        return {"message": "Successfully signed out"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Sign out failed: {str(e)}")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    FastAPI dependency to get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Authorization credentials (Bearer token)

    Returns:
        Dict containing user information

    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        token = credentials.credentials

        # Get user from Supabase using the JWT token
        response = supabase.auth.get_user(token)

        if response.user is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")

        return {
            "id": response.user.id,
            "email": response.user.email,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


def refresh_session(refresh_token: str) -> Dict[str, Any]:
    """
    Refresh an access token using a refresh token.

    Args:
        refresh_token: User's refresh token

    Returns:
        Dict containing new access and refresh tokens

    Raises:
        HTTPException: If refresh fails
    """
    try:
        response = supabase.auth.refresh_session(refresh_token)

        if response.session is None:
            raise HTTPException(status_code=401, detail="Token refresh failed")

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token refresh failed: {str(e)}")
