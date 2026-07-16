-- =====================================================
-- Seed: Default Users
-- Multi-Camera Person Tracking System
-- =====================================================
-- Admin password: Admin@1234
-- Hash generated with: bcrypt(rounds=12)
-- IMPORTANT: Change this password immediately in production!
-- =====================================================

-- Ensure roles exist first (idempotent)
INSERT INTO roles (id, name, description)
VALUES
    (1, 'admin',    'Full administrative access'),
    (2, 'operator', 'Camera and tracking operations access'),
    (3, 'viewer',   'Read-only monitoring access')
ON CONFLICT (id) DO NOTHING;

-- Default admin user
-- Password: Admin@1234 (bcrypt hash, cost=12)
INSERT INTO users (id, email, hashed_password, full_name, is_active, role_id)
VALUES (
    uuid_generate_v4(),
    'admin@mcpt.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewYQk4xrgJABj15y',
    'System Administrator',
    TRUE,
    1
)
ON CONFLICT (email) DO NOTHING;

-- Default operator user (for testing)
-- Password: Operator@1234
INSERT INTO users (id, email, hashed_password, full_name, is_active, role_id)
VALUES (
    uuid_generate_v4(),
    'operator@mcpt.local',
    '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
    'Camera Operator',
    TRUE,
    2
)
ON CONFLICT (email) DO NOTHING;

-- Default viewer user (for testing)
-- Password: Viewer@1234
INSERT INTO users (id, email, hashed_password, full_name, is_active, role_id)
VALUES (
    uuid_generate_v4(),
    'viewer@mcpt.local',
    '$2b$12$wBx4YtPTkMy1oZVzIAlpC.8IJrnjBF9hTX8qUOuJDrAtSt5fSTXKy',
    'Dashboard Viewer',
    TRUE,
    3
)
ON CONFLICT (email) DO NOTHING;
