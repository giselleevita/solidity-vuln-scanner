"""Database models and helpers for persistent storage."""

from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any, Iterator, Optional

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text, create_engine
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

from app_config import get_config
from logger_config import get_logger

logger = get_logger(__name__)
config = get_config()

Base = declarative_base()
_engine = None
_SessionLocal = None
_metadata_initialized = False


def utc_now() -> datetime:
    return datetime.now(UTC)


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    api_key = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    analyses = relationship("Analysis", back_populates="user")


class Analysis(Base):
    """Analysis result storage"""
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    contract_name = Column(String, nullable=False, index=True)
    contract_code_hash = Column(String, index=True)  # SHA-256 hash
    risk_score = Column(Float, nullable=False)
    severity = Column(String, nullable=False, index=True)
    vulnerability_count = Column(Integer, default=0)
    lines_of_code = Column(Integer, default=0)
    analysis_time_ms = Column(Integer, default=0)
    analysis_result = Column(JSON)  # Full result as JSON
    llm_audit_result = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True)
    
    # Relationships
    user = relationship("User", back_populates="analyses")
    vulnerabilities = relationship("Vulnerability", back_populates="analysis")


class Vulnerability(Base):
    """Individual vulnerability storage"""
    __tablename__ = "vulnerabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    vuln_type = Column(String, nullable=False, index=True)
    severity = Column(String, nullable=False, index=True)
    line_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    code_snippet = Column(Text)
    remediation = Column(Text)
    confidence = Column(Float, default=0.8)
    unique_id = Column(String, index=True)
    
    # Relationships
    analysis = relationship("Analysis", back_populates="vulnerabilities")


class Webhook(Base):
    """Webhook configuration storage"""
    __tablename__ = "webhooks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    url = Column(String, nullable=False)
    events = Column(JSON)  # List of event names
    secret = Column(String, nullable=True)
    headers = Column(JSON, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)


class AuditLog(Base):
    """Audit log for security and compliance"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False, index=True)
    resource_type = Column(String, nullable=True)
    resource_id = Column(Integer, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True)


def get_database_url() -> str:
    """Get database URL from config"""
    config = get_config()
    if config.database_type == "postgresql":
        return f"postgresql://{config.database_user}:{config.database_password}@{config.database_host}:{config.database_port}/{config.database_name}"
    else:
        # SQLite (default)
        return f"sqlite:///{config.database_path}"


def get_engine(reset: bool = False):
    """Return a cached SQLAlchemy engine."""
    global _engine, _SessionLocal, _metadata_initialized

    if reset and _engine is not None:
        _engine.dispose()
        _engine = None
        _SessionLocal = None
        _metadata_initialized = False

    if _engine is None:
        database_url = get_database_url()
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        _engine = create_engine(database_url, echo=get_config().debug, connect_args=connect_args)

    return _engine


def get_session_local(reset: bool = False):
    """Return a cached session factory."""
    global _SessionLocal

    engine = get_engine(reset=reset)
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            bind=engine,
        )
    return _SessionLocal


def init_database(reset: bool = False):
    """Initialize database connection and create tables."""
    global _metadata_initialized

    try:
        engine = get_engine(reset=reset)
        if not _metadata_initialized:
            Base.metadata.create_all(bind=engine)
            _metadata_initialized = True
        logger.info("Database initialized: %s", get_database_url())
        return get_session_local(reset=reset)
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        return None


def reset_database_state() -> None:
    """Reset cached engine/session state for tests or config changes."""
    get_engine(reset=True)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide a transactional session scope."""
    SessionLocal = init_database()
    if SessionLocal is None:
        raise RuntimeError("Database session factory is unavailable")

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def serialize_webhook(webhook: Webhook, include_sensitive: bool = False) -> dict[str, Any]:
    payload = {
        "id": str(webhook.id),
        "url": webhook.url,
        "events": webhook.events or [],
        "active": webhook.active,
        "created_at": webhook.created_at.isoformat() if webhook.created_at else None,
    }

    if include_sensitive:
        payload.update(
            {
                "secret": webhook.secret,
                "headers": webhook.headers or {},
                "user_id": webhook.user_id,
            }
        )

    return payload


def find_active_user_by_api_key(api_key: str) -> Optional[User]:
    with session_scope() as session:
        return (
            session.query(User)
            .filter(User.api_key == api_key, User.is_active.is_(True))
            .first()
        )


def find_active_user_by_id(user_id: int) -> Optional[User]:
    with session_scope() as session:
        return (
            session.query(User)
            .filter(User.id == user_id, User.is_active.is_(True))
            .first()
        )


def create_webhook_record(
    user_id: Optional[int],
    url: str,
    events: Optional[list[str]] = None,
    secret: Optional[str] = None,
    headers: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    with session_scope() as session:
        webhook = Webhook(
            user_id=user_id,
            url=url,
            events=events or ["analysis.completed", "analysis.failed"],
            secret=secret,
            headers=headers or {},
            active=True,
        )
        session.add(webhook)
        session.flush()
        session.refresh(webhook)
        return serialize_webhook(webhook)


def list_webhook_records(
    user_id: Optional[int] = None,
    active_only: bool = False,
    include_sensitive: bool = False,
) -> list[dict[str, Any]]:
    with session_scope() as session:
        query = session.query(Webhook)
        if user_id is not None:
            query = query.filter(Webhook.user_id == user_id)
        if active_only:
            query = query.filter(Webhook.active.is_(True))
        webhooks = query.order_by(Webhook.created_at.desc()).all()
        return [serialize_webhook(webhook, include_sensitive=include_sensitive) for webhook in webhooks]


def delete_webhook_record(webhook_id: str, user_id: Optional[int] = None) -> bool:
    with session_scope() as session:
        query = session.query(Webhook).filter(Webhook.id == int(webhook_id))
        if user_id is not None:
            query = query.filter(Webhook.user_id == user_id)
        webhook = query.first()
        if webhook is None:
            return False
        session.delete(webhook)
        return True


def create_audit_log(
    action: str,
    user_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> None:
    with session_scope() as session:
        session.add(
            AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                details=details,
            )
        )


def store_analysis_result(
    user_id: Optional[int],
    contract_name: str,
    contract_code_hash: str,
    result: dict[str, Any],
) -> Optional[int]:
    with session_scope() as session:
        analysis = Analysis(
            user_id=user_id,
            contract_name=contract_name,
            contract_code_hash=contract_code_hash,
            risk_score=float(result.get("risk_score", 0)),
            severity=result.get("severity", "UNKNOWN"),
            vulnerability_count=len(result.get("vulnerabilities", [])),
            lines_of_code=int(result.get("lines_of_code", 0)),
            analysis_time_ms=int(result.get("analysis_time_ms", 0)),
            analysis_result=result,
            llm_audit_result=result.get("llm_audit"),
        )
        session.add(analysis)
        session.flush()
        return analysis.id


def get_db():
    """Dependency for FastAPI to get database session"""
    SessionLocal = init_database()
    if SessionLocal is None:
        return None

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
