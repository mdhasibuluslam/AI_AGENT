CREATE TABLE IF NOT EXISTS roles (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS permissions (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id BIGINT NOT NULL
        REFERENCES roles(id) ON DELETE CASCADE,
    permission_id BIGINT NOT NULL
        REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id BIGINT NOT NULL
        REFERENCES users(id) ON DELETE CASCADE,
    role_id BIGINT NOT NULL
        REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, role_id)
);

-- Standard roles
INSERT INTO roles (name)
VALUES ('customer'), ('support_agent'), ('admin')
ON CONFLICT (name) DO NOTHING;

-- Permissions
INSERT INTO permissions (name, description)
VALUES
    ('chat:use', 'Use the AI chat'),
    ('support:manage', 'Perform approved support operations'),
    ('users:manage', 'Manage user accounts and roles')
ON CONFLICT (name) DO NOTHING;

-- Customer: normal chat only
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'customer'
  AND p.name = 'chat:use'
ON CONFLICT DO NOTHING;

-- Support agent: chat and approved support operations
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'support_agent'
  AND p.name IN ('chat:use', 'support:manage')
ON CONFLICT DO NOTHING;

-- Admin: all currently defined permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'admin'
ON CONFLICT DO NOTHING;