-- =====================================================
-- Intelligent Multi-Camera Person Tracking & Search
-- PostgreSQL Production Schema
-- =====================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table: roles (Auth service RBAC)
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    CONSTRAINT ck_roles_name_not_blank CHECK (length(trim(name)) > 0)
);

INSERT INTO roles (id, name, description)
VALUES
    (1, 'admin', 'Full administrative access'),
    (2, 'operator', 'Camera and tracking operations access'),
    (3, 'viewer', 'Read-only monitoring access')
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description;

-- Table: users (Auth service)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    role_id INTEGER NOT NULL DEFAULT 3,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_users_role_id_roles
        FOREIGN KEY (role_id)
        REFERENCES roles(id)
        ON DELETE RESTRICT
        DEFERRABLE INITIALLY IMMEDIATE,
    CONSTRAINT ck_users_email_not_blank CHECK (length(trim(email)) > 0),
    CONSTRAINT ck_users_hashed_password_not_blank CHECK (length(trim(hashed_password)) > 0)
);

-- Table: cameras (Camera service)
CREATE TABLE IF NOT EXISTS cameras (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    rtsp_url VARCHAR(255) UNIQUE NOT NULL,
    location VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'DISCONNECTED',
    fps INTEGER NOT NULL DEFAULT 30,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_cameras_name_not_blank CHECK (length(trim(name)) > 0),
    CONSTRAINT ck_cameras_rtsp_scheme CHECK (rtsp_url ~* '^rtsps?://[^[:space:]]+$'),
    CONSTRAINT ck_cameras_fps_range CHECK (fps BETWEEN 1 AND 120),
    CONSTRAINT ck_cameras_status_known CHECK (status IN ('CONNECTED', 'DISCONNECTED'))
);

-- Table: persons (Analytics / Search service metadata)
CREATE TABLE IF NOT EXISTS persons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    display_name VARCHAR(100),
    first_seen TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_appearances INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_persons_total_appearances_positive CHECK (total_appearances >= 1),
    CONSTRAINT ck_persons_seen_order CHECK (last_seen >= first_seen)
);

-- Table: tracking_events (Analytics service - relational tracking records)
CREATE TABLE IF NOT EXISTS tracking_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID,
    camera_id UUID NOT NULL,
    bbox_left REAL NOT NULL,
    bbox_top REAL NOT NULL,
    bbox_width REAL NOT NULL,
    bbox_height REAL NOT NULL,
    confidence REAL NOT NULL,
    crop_path VARCHAR(555),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_tracking_events_person_id_persons
        FOREIGN KEY (person_id)
        REFERENCES persons(id)
        ON DELETE SET NULL,
    CONSTRAINT fk_tracking_events_camera_id_cameras
        FOREIGN KEY (camera_id)
        REFERENCES cameras(id)
        ON DELETE CASCADE,
    CONSTRAINT ck_tracking_events_bbox_positive CHECK (bbox_width > 0 AND bbox_height > 0),
    CONSTRAINT ck_tracking_events_bbox_origin CHECK (bbox_left >= 0 AND bbox_top >= 0),
    CONSTRAINT ck_tracking_events_confidence_range CHECK (confidence >= 0 AND confidence <= 1)
);

-- Table: fire_events (Analytics / Alert service)
CREATE TABLE IF NOT EXISTS fire_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    camera_id UUID NOT NULL,
    confidence REAL NOT NULL,
    crop_path VARCHAR(555),
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_fire_events_camera_id_cameras
        FOREIGN KEY (camera_id)
        REFERENCES cameras(id)
        ON DELETE CASCADE,
    CONSTRAINT ck_fire_events_confidence_range CHECK (confidence >= 0 AND confidence <= 1)
);

-- Table: alerts (Notification / Alert service)
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    camera_id UUID,
    person_id UUID,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_alerts_camera_id_cameras
        FOREIGN KEY (camera_id)
        REFERENCES cameras(id)
        ON DELETE SET NULL,
    CONSTRAINT fk_alerts_person_id_persons
        FOREIGN KEY (person_id)
        REFERENCES persons(id)
        ON DELETE SET NULL,
    CONSTRAINT ck_alerts_type_not_blank CHECK (length(trim(type)) > 0),
    CONSTRAINT ck_alerts_title_not_blank CHECK (length(trim(title)) > 0),
    CONSTRAINT ck_alerts_severity_known CHECK (severity IN ('info', 'warning', 'critical', 'emergency'))
);

-- Unique and lookup indexes
CREATE UNIQUE INDEX IF NOT EXISTS uq_roles_name_lower ON roles (lower(name));
CREATE INDEX IF NOT EXISTS idx_users_active_email ON users (email) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_users_role_id ON users (role_id);

-- Camera query indexes
CREATE INDEX IF NOT EXISTS idx_cameras_status ON cameras (status);
CREATE INDEX IF NOT EXISTS idx_cameras_created_at_id ON cameras (created_at DESC, id);

-- Tracking query indexes
CREATE INDEX IF NOT EXISTS idx_tracking_events_timestamp ON tracking_events (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_tracking_events_timestamp_id ON tracking_events (timestamp DESC, id);
CREATE INDEX IF NOT EXISTS idx_tracking_events_person ON tracking_events (person_id);
CREATE INDEX IF NOT EXISTS idx_tracking_events_person_timestamp ON tracking_events (person_id, timestamp ASC) WHERE person_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tracking_events_camera ON tracking_events (camera_id);
CREATE INDEX IF NOT EXISTS idx_tracking_events_camera_timestamp ON tracking_events (camera_id, timestamp DESC);

-- Fire event indexes
CREATE INDEX IF NOT EXISTS idx_fire_events_timestamp ON fire_events (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_fire_events_camera_timestamp ON fire_events (camera_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_fire_events_unresolved_timestamp ON fire_events (timestamp DESC) WHERE resolved = FALSE;

-- Alert query indexes
CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_is_read ON alerts (is_read);
CREATE INDEX IF NOT EXISTS idx_alerts_unread_timestamp ON alerts (timestamp DESC) WHERE is_read = FALSE;
CREATE INDEX IF NOT EXISTS idx_alerts_camera_timestamp ON alerts (camera_id, timestamp DESC) WHERE camera_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_alerts_person_timestamp ON alerts (person_id, timestamp DESC) WHERE person_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_alerts_severity_timestamp ON alerts (severity, timestamp DESC);
