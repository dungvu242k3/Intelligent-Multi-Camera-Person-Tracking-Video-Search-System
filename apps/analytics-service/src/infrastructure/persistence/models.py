import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Float, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class UserModel(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("length(trim(email)) > 0", name="ck_users_email_not_blank"),
        CheckConstraint("length(trim(hashed_password)) > 0", name="ck_users_hashed_password_not_blank"),
        Index("idx_users_active_email", "email", postgresql_where=text("is_active = TRUE")),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="VIEWER")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class CameraModel(Base):  # type: ignore[misc,valid-type]
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

    tracking_events = relationship("TrackingEventModel", back_populates="camera", cascade="all, delete-orphan")


class PersonModel(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "persons"
    __table_args__ = (
        CheckConstraint("total_appearances >= 1", name="ck_persons_total_appearances_positive"),
        CheckConstraint("last_seen >= first_seen", name="ck_persons_seen_order"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_name = Column(String(100))
    first_seen = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_seen = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    total_appearances = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    tracking_events = relationship("TrackingEventModel", back_populates="person")


class TrackingEventModel(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "tracking_events"
    __table_args__ = (
        CheckConstraint("camera_id IS NOT NULL", name="ck_tracking_events_camera_required"),
        CheckConstraint("bbox_width > 0 AND bbox_height > 0", name="ck_tracking_events_bbox_positive"),
        CheckConstraint("bbox_left >= 0 AND bbox_top >= 0", name="ck_tracking_events_bbox_origin"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_tracking_events_confidence_range"),
        Index("idx_tracking_events_timestamp", "timestamp"),
        Index("idx_tracking_events_timestamp_id", "timestamp", "id"),
        Index("idx_tracking_events_person", "person_id"),
        Index("idx_tracking_events_person_timestamp", "person_id", "timestamp", postgresql_where=text("person_id IS NOT NULL")),
        Index("idx_tracking_events_camera", "camera_id"),
        Index("idx_tracking_events_camera_timestamp", "camera_id", "timestamp"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id", ondelete="SET NULL", name="fk_tracking_events_person_id_persons"))
    camera_id = Column(UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="CASCADE", name="fk_tracking_events_camera_id_cameras"), nullable=False)
    bbox_left = Column(Float, nullable=False)
    bbox_top = Column(Float, nullable=False)
    bbox_width = Column(Float, nullable=False)
    bbox_height = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    crop_path = Column(String(555))
    timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    camera = relationship("CameraModel", back_populates="tracking_events")
    person = relationship("PersonModel", back_populates="tracking_events")


class FireEventModel(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "fire_events"
    __table_args__ = (
        CheckConstraint("camera_id IS NOT NULL", name="ck_fire_events_camera_required"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_fire_events_confidence_range"),
        Index("idx_fire_events_timestamp", "timestamp"),
        Index("idx_fire_events_camera_timestamp", "camera_id", "timestamp"),
        Index("idx_fire_events_unresolved_timestamp", "timestamp", postgresql_where=text("resolved = FALSE")),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camera_id = Column(UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="CASCADE", name="fk_fire_events_camera_id_cameras"), nullable=False)
    confidence = Column(Float, nullable=False)
    crop_path = Column(String(555))
    resolved = Column(Boolean, nullable=False, default=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class AlertModel(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "alerts"
    __table_args__ = (
        CheckConstraint("length(trim(type)) > 0", name="ck_alerts_type_not_blank"),
        CheckConstraint("length(trim(title)) > 0", name="ck_alerts_title_not_blank"),
        CheckConstraint("severity IN ('info', 'warning', 'critical', 'emergency')", name="ck_alerts_severity_known"),
        Index("idx_alerts_timestamp", "timestamp"),
        Index("idx_alerts_is_read", "is_read"),
        Index("idx_alerts_unread_timestamp", "timestamp", postgresql_where=text("is_read = FALSE")),
        Index("idx_alerts_camera_timestamp", "camera_id", "timestamp", postgresql_where=text("camera_id IS NOT NULL")),
        Index("idx_alerts_person_timestamp", "person_id", "timestamp", postgresql_where=text("person_id IS NOT NULL")),
        Index("idx_alerts_severity_timestamp", "severity", "timestamp"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String)
    camera_id = Column(UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="SET NULL", name="fk_alerts_camera_id_cameras"))
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id", ondelete="SET NULL", name="fk_alerts_person_id_persons"))
    is_read = Column(Boolean, nullable=False, default=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
