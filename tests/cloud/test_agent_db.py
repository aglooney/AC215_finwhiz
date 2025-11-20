import os
import uuid

from sqlalchemy import delete
from sqlalchemy.exc import OperationalError

from agentic_user_data_processing import models
from agentic_user_data_processing.db import SessionLocal, session_scope


def test_session_message_crud_against_cloud_db():
    external_id = f"cloud-pytest-{uuid.uuid4()}"

    with session_scope() as db:
        try:
            user = models.User.get_or_create(db, external_id=external_id)
            agent_session = models.Session.create(db, user_id=user.id)
            models.Message.create(db, session_id=str(agent_session.id), role="user", content="cloud-integration-test")
        except OperationalError as exc:
            raise AssertionError(
                f"Cloud SQL unreachable using DB_HOST={os.getenv('DB_HOST')} "
                f"DB_NAME={os.getenv('DB_NAME')} DB_USER={os.getenv('DB_USER')}: {exc}"
            ) from exc

    with session_scope() as db:
        messages = models.Message.latest_for_session(db, session_id=str(agent_session.id), limit=1)
        assert messages, "Expected at least one message retrieved from Cloud SQL"
        assert messages[0].content == "cloud-integration-test"

    with SessionLocal() as db:
        db.execute(delete(models.Message).where(models.Message.session_id == agent_session.id))
        db.execute(delete(models.Document).where(models.Document.session_id == agent_session.id))
        db.execute(delete(models.Session).where(models.Session.id == agent_session.id))
        db.execute(delete(models.User).where(models.User.id == user.id))
        db.commit()
