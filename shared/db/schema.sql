-- SQLite schema for AI-First-IT-Team

CREATE TABLE IF NOT EXISTS secrets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    encrypted_value TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS agent_logs (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    level TEXT NOT NULL DEFAULT 'INFO',
    message TEXT NOT NULL,
    metadata TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_agent_logs_session ON agent_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_logs_created ON agent_logs(created_at);

CREATE TABLE IF NOT EXISTS deployments (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    stack_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    tf_plan_path TEXT,
    ecs_ips TEXT,
    kubeconfig_ref TEXT,
    output TEXT,
    error TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS agent_memory (
    id TEXT PRIMARY KEY,
    agent_type TEXT NOT NULL,
    memory_key TEXT NOT NULL,
    memory_value TEXT NOT NULL,
    ttl_seconds INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_agent_memory_key ON agent_memory(memory_key);
