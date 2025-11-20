import uuid

import pytest
from sqlalchemy import delete

from agentic_user_data_processing import models
from agentic_user_data_processing.db import SessionLocal, session_scope


def test_session_message_crud_against_cloud_db():
    external_id = f"cloud-pytest-{uuid.uuid4()}"

    with session_scope() as db:
        user = models.User.get_or_create(db, external_id=external_id)
        agent_session = models.Session.create(db, user_id=user.id)
        models.Message.create(db, session_id=str(agent_session.id), role="user", content="cloud-integration-test")

    with session_scope() as db:
        messages = models.Message.latest_for_session(db, session_id=str(agent_session.id), limit=1)
        assert messages
        assert messages[0].content == "cloud-integration-test"

    with SessionLocal() as db:
        db.execute(delete(models.Message).where(models.Message.session_id == agent_session.id))
        db.execute(delete(models.Document).where(models.Document.session_id == agent_session.id))
        db.execute(delete(models.Session).where(models.Session.id == agent_session.id))
        db.execute(delete(models.User).where(models.User.id == user.id))
        db.commit()
