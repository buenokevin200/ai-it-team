import os
import sqlite3
import uuid
from datetime import datetime
from typing import Optional

import aiosqlite


DB_PATH = os.getenv("DATABASE_PATH", "shared/db/agents.db")


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    db = await get_db()
    schema_path = os.path.join(os.path.dirname(DB_PATH), "schema.sql")
    if os.path.exists(schema_path):
        with open(schema_path) as f:
            await db.executescript(f.read())
    await db.commit()
    await db.close()


async def store_secret(name: str, category: str, encrypted_value: str) -> str:
    db = await get_db()
    secret_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO secrets (id, name, category, encrypted_value) VALUES (?, ?, ?, ?)"
        " ON CONFLICT(name) DO UPDATE SET encrypted_value = excluded.encrypted_value, updated_at = datetime('now')",
        (secret_id, name, category, encrypted_value),
    )
    await db.commit()
    await db.close()
    return secret_id


async def get_secret_encrypted(name: str) -> Optional[str]:
    db = await get_db()
    cursor = await db.execute("SELECT encrypted_value FROM secrets WHERE name = ?", (name,))
    row = await cursor.fetchone()
    await db.close()
    return row[0] if row else None


async def get_all_secrets():
    db = await get_db()
    cursor = await db.execute("SELECT id, name, category, created_at, updated_at FROM secrets ORDER BY name")
    rows = await cursor.fetchall()
    await db.close()
    return [dict(row) for row in rows]


async def delete_secret(name: str) -> bool:
    db = await get_db()
    cursor = await db.execute("DELETE FROM secrets WHERE name = ?", (name,))
    await db.commit()
    await db.close()
    return cursor.rowcount > 0


async def store_log(log: dict) -> str:
    db = await get_db()
    log_id = log.get("id") or str(uuid.uuid4())
    await db.execute(
        "INSERT INTO agent_logs (id, session_id, agent_type, level, message, metadata, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            log_id,
            log["session_id"],
            log["agent_type"],
            log.get("level", "INFO"),
            log["message"],
            log.get("metadata"),
            log.get("created_at", datetime.utcnow().isoformat()),
        ),
    )
    await db.commit()
    await db.close()
    return log_id


async def get_session_logs(session_id: str):
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM agent_logs WHERE session_id = ? ORDER BY created_at ASC",
        (session_id,),
    )
    rows = await cursor.fetchall()
    await db.close()
    return [dict(row) for row in rows]


async def store_deployment(deployment: dict) -> str:
    db = await get_db()
    dep_id = deployment.get("id") or str(uuid.uuid4())
    await db.execute(
        "INSERT INTO deployments (id, session_id, stack_name, status, tf_plan_path, ecs_ips, kubeconfig_ref, output, error) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            dep_id,
            deployment["session_id"],
            deployment["stack_name"],
            deployment.get("status", "pending"),
            deployment.get("tf_plan_path"),
            deployment.get("ecs_ips"),
            deployment.get("kubeconfig_ref"),
            deployment.get("output"),
            deployment.get("error"),
        ),
    )
    await db.commit()
    await db.close()
    return dep_id


async def get_config(name: str) -> Optional[dict]:
    db = await get_db()
    cursor = await db.execute("SELECT name, category FROM secrets WHERE name = ?", (name,))
    row = await cursor.fetchone()
    await db.close()
    return dict(row) if row else None


async def get_all_config():
    db = await get_db()
    cursor = await db.execute("SELECT id, name, category, created_at, updated_at FROM secrets ORDER BY category, name")
    rows = await cursor.fetchall()
    await db.close()
    results = []
    for row in rows:
        results.append({
            "name": row[1],
            "category": row[2],
            "configured": True,
            "value": "••••••••",
            "created_at": row[3],
            "updated_at": row[4],
        })
    return results


def get_config_sync(name: str) -> Optional[str]:
    db_path = os.getenv("DATABASE_PATH", "shared/db/agents.db")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT encrypted_value FROM secrets WHERE name = ?", (name,))
        row = cursor.fetchone()
        conn.close()
        if row:
            from tools.crypto import SecretCrypto
            crypto = SecretCrypto()
            return crypto.decrypt(row[0])
        return None
    except Exception:
        return None


def store_log_sync(log: dict) -> str:
    db_path = os.getenv("DATABASE_PATH", "shared/db/agents.db")
    log_id = log.get("id") or str(uuid.uuid4())
    try:
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO agent_logs (id, session_id, agent_type, level, message, metadata, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                log_id,
                log["session_id"],
                log["agent_type"],
                log.get("level", "INFO"),
                log["message"],
                log.get("metadata"),
                log.get("created_at", datetime.utcnow().isoformat()),
            ),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass
    return log_id


def update_deployment_sync(session_id: str, status: str, output: Optional[str] = None, error: Optional[str] = None):
    db_path = os.getenv("DATABASE_PATH", "shared/db/agents.db")
    try:
        conn = sqlite3.connect(db_path)
        conn.execute(
            "UPDATE deployments SET status = ?, output = ?, error = ?, updated_at = datetime('now') WHERE session_id = ?",
            (status, output, error, session_id),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass
