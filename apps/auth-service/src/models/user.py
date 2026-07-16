import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):  # type: ignore[misc,valid-type]
    """SQLAlchemy model representing system authenticated users."""
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("length(trim(email)) > 0", name="ck_users_email_not_blank"),
        CheckConstraint("length(trim(hashed_password)) > 0", name="ck_users_hashed_password_not_blank"),
        Index("idx_users_active_email", "email", postgresql_where=text("is_active = TRUE")),
        Index("idx_users_role_id", "role_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="RESTRICT", name="fk_users_role_id_roles"), nullable=False, default=3)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
