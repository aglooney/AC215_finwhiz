import pytest
from datetime import datetime
from unittest.mock import MagicMock

# Mock the database session
import sys
sys.modules['agentic_user_data_processing.db'] = MagicMock()

from agentic_user_data_processing import models


def test_session_model_creation():
    session = models.Session(
        id="test-session-id",
        user_id="test-user-id"
    )
    assert session.id == "test-session-id"
    assert session.user_id == "test-user-id"


def test_message_model_creation():
    msg = models.Message(
        id="msg-id",
        session_id="session-id",
        role="user",
        content="Hello"
    )
    assert msg.role == "user"
    assert msg.content == "Hello"


def test_document_model_creation():
    doc = models.Document(
        id="doc-id",
        session_id="session-id",
        document_type="w2",
        gcs_uri="gs://bucket/file.pdf"
    )
    assert doc.document_type == "w2"
    assert doc.gcs_uri == "gs://bucket/file.pdf"


def test_user_profile_model():
    profile = models.UserProfile(
        id="profile-id",
        user_id="user-id",
        age=30,
        retirement_age=65,
        risk_tolerance="moderate",
        investment_goal="retirement"
    )
    assert profile.age == 30
    assert profile.risk_tolerance == "moderate"
