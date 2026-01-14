"""
Database Models and Setup
SQLAlchemy models for persistent storage
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from app_config import get_config
from logger_config import get_logger

logger = get_logger(__name__)
config = get_config()

Base = declarative_base()


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
    created_at = Column(DateTime, default=datetime.utcnow)
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
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
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
    created_at = Column(DateTime, default=datetime.utcnow)


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
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


def get_database_url() -> str:
    """Get database URL from config"""
    if config.database_type == "postgresql":
        return f"postgresql://{config.database_user}:{config.database_password}@{config.database_host}:{config.database_port}/{config.database_name}"
    else:
        # SQLite (default)
        return f"sqlite:///{config.database_path}"


def init_database():
    """Initialize database connection and create tables"""
    try:
        database_url = get_database_url()
        engine = create_engine(database_url, echo=config.debug)
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        logger.info(f"Database initialized: {database_url}")
        return SessionLocal
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        return None


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
