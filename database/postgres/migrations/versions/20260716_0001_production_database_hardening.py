"""production database hardening

Revision ID: 20260716_0001
Revises:
Create Date: 2026-07-16
"""

from alembic import op


revision = "20260716_0001"
down_revision = None
branch_labels = None
depends_on = None


def _add_check_constraint_if_missing(table: str, name: str, condition: str) -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = '{name}'
                  AND conrelid = '{table}'::regclass
            ) THEN
                ALTER TABLE {table}
                ADD CONSTRAINT {name} CHECK ({condition}) NOT VALID;
            END IF;
        END $$;
        """
    )


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            description TEXT
        )
        """
    )
    op.execute(
        """
        INSERT INTO roles (id, name, description)
        VALUES
            (1, 'admin', 'Full administrative access'),
            (2, 'operator', 'Camera and tracking operations access'),
            (3, 'viewer', 'Read-only monitoring access')
        ON CONFLICT (id) DO UPDATE
        SET name = EXCLUDED.name,
            description = EXCLUDED.description
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            email VARCHAR(255) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            full_name VARCHAR(100),
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            role_id INTEGER NOT NULL DEFAULT 3,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS cameras (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(100) NOT NULL,
            rtsp_url VARCHAR(255) UNIQUE NOT NULL,
            location VARCHAR(255),
            status VARCHAR(50) NOT NULL DEFAULT 'DISCONNECTED',
            fps INTEGER NOT NULL DEFAULT 30,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS persons (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            display_name VARCHAR(100),
            first_seen TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            total_appearances INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS tracking_events (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            person_id UUID REFERENCES persons(id) ON DELETE SET NULL,
            camera_id UUID REFERENCES cameras(id) ON DELETE CASCADE,
            bbox_left REAL NOT NULL,
            bbox_top REAL NOT NULL,
            bbox_width REAL NOT NULL,
            bbox_height REAL NOT NULL,
            confidence REAL NOT NULL,
            crop_path VARCHAR(555),
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS fire_events (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            camera_id UUID REFERENCES cameras(id) ON DELETE CASCADE,
            confidence REAL NOT NULL,
            crop_path VARCHAR(555),
            resolved BOOLEAN NOT NULL DEFAULT FALSE,
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            type VARCHAR(100) NOT NULL,
            severity VARCHAR(50) NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            camera_id UUID REFERENCES cameras(id) ON DELETE SET NULL,
            person_id UUID REFERENCES persons(id) ON DELETE SET NULL,
            is_read BOOLEAN NOT NULL DEFAULT FALSE,
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(100)")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role_id INTEGER")
    op.execute("ALTER TABLE users ALTER COLUMN role_id SET DEFAULT 3")
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'users'
                  AND column_name = 'role'
            ) THEN
                UPDATE users
                SET role_id = CASE upper(role)
                    WHEN 'ADMIN' THEN 1
                    WHEN 'OPERATOR' THEN 2
                    WHEN 'USER' THEN 2
                    WHEN 'VIEWER' THEN 3
                    ELSE 3
                END
                WHERE role_id IS NULL;
            END IF;

            UPDATE users
            SET role_id = 3
            WHERE role_id IS NULL;
        END $$;
        """
    )
    op.execute("ALTER TABLE users ALTER COLUMN role_id SET NOT NULL")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_users_role_id_roles'
                  AND conrelid = 'users'::regclass
            ) THEN
                ALTER TABLE users
                ADD CONSTRAINT fk_users_role_id_roles
                FOREIGN KEY (role_id)
                REFERENCES roles(id)
                ON DELETE RESTRICT
                DEFERRABLE INITIALLY IMMEDIATE;
            END IF;
        END $$;
        """
    )

    _add_check_constraint_if_missing("users", "ck_users_email_not_blank", "length(trim(email)) > 0")
    _add_check_constraint_if_missing("users", "ck_users_hashed_password_not_blank", "length(trim(hashed_password)) > 0")
    _add_check_constraint_if_missing("roles", "ck_roles_name_not_blank", "length(trim(name)) > 0")
    _add_check_constraint_if_missing("cameras", "ck_cameras_name_not_blank", "length(trim(name)) > 0")
    _add_check_constraint_if_missing("cameras", "ck_cameras_rtsp_scheme", "rtsp_url ~* '^rtsps?://[^[:space:]]+$'")
    _add_check_constraint_if_missing("cameras", "ck_cameras_fps_range", "fps BETWEEN 1 AND 120")
    _add_check_constraint_if_missing("cameras", "ck_cameras_status_known", "status IN ('CONNECTED', 'DISCONNECTED')")
    _add_check_constraint_if_missing("persons", "ck_persons_total_appearances_positive", "total_appearances >= 1")
    _add_check_constraint_if_missing("persons", "ck_persons_seen_order", "last_seen >= first_seen")
    _add_check_constraint_if_missing("tracking_events", "ck_tracking_events_camera_required", "camera_id IS NOT NULL")
    _add_check_constraint_if_missing("tracking_events", "ck_tracking_events_bbox_positive", "bbox_width > 0 AND bbox_height > 0")
    _add_check_constraint_if_missing("tracking_events", "ck_tracking_events_bbox_origin", "bbox_left >= 0 AND bbox_top >= 0")
    _add_check_constraint_if_missing("tracking_events", "ck_tracking_events_confidence_range", "confidence >= 0 AND confidence <= 1")
    _add_check_constraint_if_missing("fire_events", "ck_fire_events_camera_required", "camera_id IS NOT NULL")
    _add_check_constraint_if_missing("fire_events", "ck_fire_events_confidence_range", "confidence >= 0 AND confidence <= 1")
    _add_check_constraint_if_missing("alerts", "ck_alerts_type_not_blank", "length(trim(type)) > 0")
    _add_check_constraint_if_missing("alerts", "ck_alerts_title_not_blank", "length(trim(title)) > 0")
    _add_check_constraint_if_missing("alerts", "ck_alerts_severity_known", "severity IN ('info', 'warning', 'critical', 'emergency')")

    with op.get_context().autocommit_block():
        op.execute("CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS uq_roles_name_lower ON roles (lower(name))")
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_active_email ON users (email) WHERE is_active = TRUE")
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_role_id ON users (role_id)")
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cameras_status ON cameras (status)")
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cameras_created_at_id ON cameras (created_at DESC, id)")
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tracking_events_timestamp_id ON tracking_events (timestamp DESC, id)")
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tracking_events_person_timestamp ON tracking_events (person_id, timestamp ASC) WHERE person_id IS NOT NULL")
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tracking_events_camera_timestamp ON tracking_events (camera_id, timestamp DESC)")
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fire_events_camera_timestamp ON fire_events (camera_id, timestamp DESC)")
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fire_events_unresolved_timestamp ON fire_events (timestamp DESC) WHERE resolved = FALSE")
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_unread_timestamp ON alerts (timestamp DESC) WHERE is_read = FALSE")
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_camera_timestamp ON alerts (camera_id, timestamp DESC) WHERE camera_id IS NOT NULL")
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_person_timestamp ON alerts (person_id, timestamp DESC) WHERE person_id IS NOT NULL")
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_severity_timestamp ON alerts (severity, timestamp DESC)")


def downgrade() -> None:
    with op.get_context().autocommit_block():
        for index_name in (
            "idx_alerts_severity_timestamp",
            "idx_alerts_person_timestamp",
            "idx_alerts_camera_timestamp",
            "idx_alerts_unread_timestamp",
            "idx_fire_events_unresolved_timestamp",
            "idx_fire_events_camera_timestamp",
            "idx_tracking_events_camera_timestamp",
            "idx_tracking_events_person_timestamp",
            "idx_tracking_events_timestamp_id",
            "idx_cameras_created_at_id",
            "idx_cameras_status",
            "idx_users_role_id",
            "idx_users_active_email",
            "uq_roles_name_lower",
        ):
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {index_name}")

    for table, constraint in (
        ("alerts", "ck_alerts_severity_known"),
        ("alerts", "ck_alerts_title_not_blank"),
        ("alerts", "ck_alerts_type_not_blank"),
        ("fire_events", "ck_fire_events_confidence_range"),
        ("fire_events", "ck_fire_events_camera_required"),
        ("tracking_events", "ck_tracking_events_confidence_range"),
        ("tracking_events", "ck_tracking_events_bbox_origin"),
        ("tracking_events", "ck_tracking_events_bbox_positive"),
        ("tracking_events", "ck_tracking_events_camera_required"),
        ("persons", "ck_persons_seen_order"),
        ("persons", "ck_persons_total_appearances_positive"),
        ("cameras", "ck_cameras_status_known"),
        ("cameras", "ck_cameras_fps_range"),
        ("cameras", "ck_cameras_rtsp_scheme"),
        ("cameras", "ck_cameras_name_not_blank"),
        ("roles", "ck_roles_name_not_blank"),
        ("users", "ck_users_hashed_password_not_blank"),
        ("users", "ck_users_email_not_blank"),
    ):
        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {constraint}")

    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS fk_users_role_id_roles")
