"""
Database models and helper methods for the agent service.
"""
import uuid
from datetime import datetime
from typing import Iterable, Optional, List

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from .db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="user")

    @classmethod
    def get_or_create(
        cls,
        db: Session,
        *,
        user_id: Optional[uuid.UUID] = None,
        external_id: Optional[str] = None,
    ) -> "User":
        if external_id:
            instance = db.query(cls).filter_by(external_id=external_id).first()
            if instance:
                return instance
        if user_id and (existing := db.get(cls, user_id)):
            return existing
        instance = cls(id=user_id or uuid.uuid4(), external_id=external_id)
        db.add(instance)
        db.commit()
        db.refresh(instance)
        return instance


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user: Mapped[User] = relationship("User", back_populates="sessions")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="session", cascade="all, delete-orphan")

    @classmethod
    def create(cls, db: Session, *, user_id: uuid.UUID) -> "Session":
        instance = cls(user_id=user_id)
        db.add(instance)
        db.commit()
        db.refresh(instance)
        return instance

    @classmethod
    def get(cls, db: Session, session_id: str) -> Optional["Session"]:
        try:
            key = uuid.UUID(str(session_id))
        except (ValueError, TypeError):
            return None
        return db.get(cls, key)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # "user" or "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    session: Mapped[Session] = relationship("Session", back_populates="messages")

    @classmethod
    def create(cls, db: Session, *, session_id: str, role: str, content: str) -> "Message":
        instance = cls(session_id=uuid.UUID(str(session_id)), role=role, content=content)
        db.add(instance)
        db.commit()
        db.refresh(instance)
        return instance

    @classmethod
    def latest_for_session(cls, db: Session, *, session_id: str, limit: int = 20) -> Iterable["Message"]:
        return (
            db.query(cls)
            .filter(cls.session_id == uuid.UUID(str(session_id)))
            .order_by(cls.created_at.desc())
            .limit(limit)
            .all()
        )


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, index=True)
    document_type: Mapped[str] = mapped_column(String(32), nullable=False)
    gcs_uri: Mapped[str] = mapped_column(String(512), nullable=False)
    raw_metadata: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    session: Mapped[Session] = relationship("Session", back_populates="documents")

    @classmethod
    def create(
        cls,
        db: Session,
        *,
        session_id: str,
        document_type: str,
        gcs_uri: str,
        raw_metadata: Optional[str],
    ) -> "Document":
        instance = cls(
            session_id=uuid.UUID(str(session_id)),
            document_type=document_type,
            gcs_uri=gcs_uri,
            raw_metadata=raw_metadata,
        )
        db.add(instance)
        db.commit()
        db.refresh(instance)
        return instance

    @classmethod
    def latest_for_session(cls, db: Session, *, session_id: str) -> Optional["Document"]:
        return (
            db.query(cls)
            .filter(cls.session_id == uuid.UUID(session_id))
            .order_by(cls.created_at.desc())
            .first()
        )
