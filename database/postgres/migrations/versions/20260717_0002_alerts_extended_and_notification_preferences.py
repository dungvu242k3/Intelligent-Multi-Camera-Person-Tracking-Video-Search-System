"""alerts extended indexes and notification preferences

Revision ID: 20260717_0002
Revises: 20260716_0001
Create Date: 2026-07-17
"""

from alembic import op


revision = "20260717_0002"
down_revision = "20260716_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---- notification_preferences table ----
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS notification_preferences (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL,
            alert_type VARCHAR(100) NOT NULL,
            enabled BOOLEAN NOT NULL DEFAULT TRUE,
            min_severity VARCHAR(50) NOT NULL DEFAULT 'info',
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_notif_prefs_user_id_users
                FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,
            CONSTRAINT uq_notif_prefs_user_alert_type
                UNIQUE (user_id, alert_type),
            CONSTRAINT ck_notif_prefs_severity_known
                CHECK (min_severity IN ('info', 'warning', 'critical', 'emergency'))
        )
        """
    )

    # ---- Additional performance indexes ----
    with op.get_context().autocommit_block():
        # Cover query: "all unread alerts for a specific severity"
        op.execute(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_severity_unread "
            "ON alerts (severity, timestamp DESC) WHERE is_read = FALSE"
        )

        # Cover query: "all tracking events in last N minutes"
        op.execute(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tracking_events_recent "
            "ON tracking_events (timestamp DESC) WHERE timestamp > NOW() - INTERVAL '24 hours'"
        )

        # Cover query: "persons seen in a camera range"
        op.execute(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tracking_events_camera_person "
            "ON tracking_events (camera_id, person_id, timestamp DESC) WHERE person_id IS NOT NULL"
        )

        # Partial index: active users only
        op.execute(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_active_role "
            "ON users (role_id, email) WHERE is_active = TRUE"
        )

        # notification_preferences lookup index
        op.execute(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_notif_prefs_user_id "
            "ON notification_preferences (user_id)"
        )

    # ---- updated_at trigger function (shared) ----
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    # Apply trigger to all tables with updated_at
    for table in ("users", "cameras", "notification_preferences"):
        op.execute(
            f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_trigger
                    WHERE tgname = 'trg_{table}_updated_at'
                ) THEN
                    CREATE TRIGGER trg_{table}_updated_at
                    BEFORE UPDATE ON {table}
                    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
                END IF;
            END $$;
            """
        )


def downgrade() -> None:
    # Drop triggers
    for table in ("users", "cameras", "notification_preferences"):
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_updated_at ON {table}")

    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

    # Drop indexes
    with op.get_context().autocommit_block():
        for idx in (
            "idx_notif_prefs_user_id",
            "idx_users_active_role",
            "idx_tracking_events_camera_person",
            "idx_tracking_events_recent",
            "idx_alerts_severity_unread",
        ):
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {idx}")

    op.execute("DROP TABLE IF EXISTS notification_preferences CASCADE")
