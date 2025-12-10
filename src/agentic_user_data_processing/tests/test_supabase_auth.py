import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException


def test_sign_up_success():
    with patch("agentic_user_data_processing.supabase_auth.supabase") as mock_supabase:
        mock_response = MagicMock()
        mock_response.user = MagicMock(id="user-123", email="test@example.com")
        mock_response.session = MagicMock(access_token="token123", refresh_token="refresh123", expires_in=3600, expires_at=1234567890)
        mock_supabase.auth.sign_up.return_value = mock_response

        from agentic_user_data_processing import supabase_auth

        result = supabase_auth.sign_up("test@example.com", "password123")

        assert result["user"]["id"] == "user-123"
        assert result["session"]["access_token"] == "token123"


def test_sign_up_failure():
    with patch("agentic_user_data_processing.supabase_auth.supabase") as mock_supabase:
        mock_response = MagicMock()
        mock_response.user = None
        mock_supabase.auth.sign_up.return_value = mock_response

        from agentic_user_data_processing import supabase_auth

        with pytest.raises(HTTPException) as exc_info:
            supabase_auth.sign_up("test@example.com", "password123")
        assert exc_info.value.status_code == 400


def test_sign_in_success():
    with patch("agentic_user_data_processing.supabase_auth.supabase") as mock_supabase:
        mock_response = MagicMock()
        mock_response.user = MagicMock(id="user-123", email="test@example.com")
        mock_response.session = MagicMock(access_token="token123", refresh_token="refresh123", expires_in=3600, expires_at=1234567890)
        mock_supabase.auth.sign_in_with_password.return_value = mock_response

        from agentic_user_data_processing import supabase_auth

        result = supabase_auth.sign_in("test@example.com", "password123")

        assert result["user"]["id"] == "user-123"


def test_sign_in_invalid_credentials():
    with patch("agentic_user_data_processing.supabase_auth.supabase") as mock_supabase:
        mock_response = MagicMock()
        mock_response.user = None
        mock_supabase.auth.sign_in_with_password.return_value = mock_response

        from agentic_user_data_processing import supabase_auth

        with pytest.raises(HTTPException) as exc_info:
            supabase_auth.sign_in("test@example.com", "wrongpassword")
        assert exc_info.value.status_code == 401


def test_sign_out():
    with patch("agentic_user_data_processing.supabase_auth.supabase") as _:
        from agentic_user_data_processing import supabase_auth

        result = supabase_auth.sign_out("token123")
        assert result["message"] == "Successfully signed out"


def test_get_current_user_success():
    with patch("agentic_user_data_processing.supabase_auth.supabase") as mock_supabase:
        mock_response = MagicMock()
        mock_response.user = MagicMock(id="user-123", email="test@example.com")
        mock_supabase.auth.get_user.return_value = mock_response

        from agentic_user_data_processing import supabase_auth

        mock_credentials = MagicMock()
        mock_credentials.credentials = "valid-token"

        result = supabase_auth.get_current_user(mock_credentials)
        assert result["id"] == "user-123"


def test_refresh_session_success():
    with patch("agentic_user_data_processing.supabase_auth.supabase") as mock_supabase:
        mock_response = MagicMock()
        mock_response.session = MagicMock(access_token="new-token", refresh_token="new-refresh")
        mock_supabase.auth.refresh_session.return_value = mock_response

        from agentic_user_data_processing import supabase_auth

        result = supabase_auth.refresh_session("old-refresh-token")
        assert result["access_token"] == "new-token"
