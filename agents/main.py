import os
import uuid
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from tools.db import init_db, store_secret, get_secret_encrypted, get_all_secrets, delete_secret, store_log, get_session_logs, store_deployment
from tools.crypto import SecretCrypto
from orchestrator.graph import graph
from orchestrator.state import AgentState

load_dotenv()

app = FastAPI(title="AI-First-IT-Team Agents", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

crypto = SecretCrypto()
active_connections: dict[str, WebSocket] = {}


@app.on_event("startup")
async def startup():
    await init_db()


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai-first-it-team-agents"}


@app.post("/api/secrets")
async def create_secret(name: str, category: str, value: str):
    encrypted = crypto.encrypt(value)
    secret_id = await store_secret(name, category, encrypted)
    return {"id": secret_id, "name": name, "category": category, "status": "stored"}


@app.get("/api/secrets")
async def list_secrets():
    secrets = await get_all_secrets()
    return {"secrets": secrets}


@app.delete("/api/secrets/{name}")
async def remove_secret(name: str):
    deleted = await delete_secret(name)
    return {"deleted": deleted, "name": name}


@app.post("/api/agents/run")
async def run_agent(command: str):
    session_id = f"session_{datetime.utcnow().timestamp()}"
    initial_state: AgentState = {
        "user_input": command,
        "session_id": session_id,
        "logs": [],
        "stack_name": f"stack-{uuid.uuid4().hex[:8]}",
    }

    try:
        result = graph.invoke(initial_state)
        await store_deployment({
            "session_id": session_id,
            "stack_name": result.get("stack_name", ""),
            "status": "error" if result.get("error") else "success",
            "tf_plan_path": result.get("tf_plan_path"),
            "ecs_ips": str(result.get("ecs_ips", [])),
            "output": str(result.get("ssh_result") or result.get("kube_result")),
            "error": result.get("error"),
        })
        for log in result.get("logs", []):
            await store_log(log)
        return {
            "session_id": result.get("session_id"),
            "status": "error" if result.get("error") else "success",
            "intent": result.get("intent"),
            "result": str(result.get("ssh_result") or result.get("kube_result") or "ok"),
            "error": result.get("error"),
            "details": {
                "ecs_ip": result.get("ecs_ip"),
                "stack_name": result.get("stack_name"),
            },
        }
    except Exception as e:
        return {
            "session_id": session_id,
            "status": "error",
            "intent": "unknown",
            "result": None,
            "error": str(e),
            "details": {},
        }


@app.get("/api/logs/{session_id}")
async def get_logs(session_id: str):
    logs = await get_session_logs(session_id)
    return {"session_id": session_id, "logs": logs}


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    connection_id = str(uuid.uuid4())
    active_connections[connection_id] = websocket
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"echo: {data}")
    except WebSocketDisconnect:
        active_connections.pop(connection_id, None)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
