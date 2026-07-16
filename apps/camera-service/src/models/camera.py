import uuid
from datetime import datetime, timezone
from sqlalchemy import CheckConstraint, Column, DateTime, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Camera(Base):  # type: ignore[misc,valid-type]
    """SQLAlchemy model representing a physical/network camera stream."""
    __tablename__ = "cameras"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_cameras_name_not_blank"),
        CheckConstraint("rtsp_url ~* '^rtsps?://[^[:space:]]+$'", name="ck_cameras_rtsp_scheme"),
        CheckConstraint("fps BETWEEN 1 AND 120", name="ck_cameras_fps_range"),
        CheckConstraint("status IN ('CONNECTED', 'DISCONNECTED')", name="ck_cameras_status_known"),
        Index("idx_cameras_status", "status"),
        Index("idx_cameras_created_at_id", "created_at", "id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    rtsp_url = Column(String(255), unique=True, nullable=False)
    location = Column(String(255))
    status = Column(String(50), nullable=False, default="DISCONNECTED")
    fps = Column(Integer, default=30)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
