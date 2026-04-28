import os
import uuid
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from tools.db import init_db, store_secret, get_secret_encrypted, get_all_secrets, delete_secret, store_log, get_session_logs, store_deployment, get_all_config, get_config_sync
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

_agent_metrics = {
    "orchestrator": {"runs": 0, "success": 0, "errors": 0},
    "terraform": {"runs": 0, "success": 0, "errors": 0},
    "ssh": {"runs": 0, "success": 0, "errors": 0},
    "kubernetes": {"runs": 0, "success": 0, "errors": 0},
    "ai_brain": {"runs": 0, "success": 0, "errors": 0},
}


def get_ai_status() -> dict:
    deepseek_key = get_config_sync("ai_deepseek_api_key")
    return {
        "ready": bool(deepseek_key),
        "provider": "deepseek" if deepseek_key else "none",
        "model": get_config_sync("ai_deepseek_model") or "deepseek-chat",
    }


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


@app.get("/api/config")
async def get_config():
    config = await get_all_config()
    return {"config": config}


@app.post("/api/config")
async def save_config(name: str, category: str, value: str):
    encrypted = crypto.encrypt(value)
    secret_id = await store_secret(name, category, encrypted)
    return {"id": secret_id, "name": name, "category": category, "status": "stored"}


@app.get("/api/agents/status")
async def agent_status():
    ai_info = get_ai_status()
    return {
        "agents": [
            {
                "id": "orchestrator",
                "name": "Orchestrator",
                "type": "orchestrator",
                "status": "idle" if _agent_metrics["orchestrator"]["runs"] == 0 else "success",
                "metrics": _agent_metrics["orchestrator"],
                "description": "LangGraph workflow orchestration",
            },
            {
                "id": "terraform",
                "name": "Terraform Agent",
                "type": "terraform",
                "status": "idle",
                "metrics": _agent_metrics["terraform"],
                "description": "Huawei Cloud infrastructure provisioning",
            },
            {
                "id": "ssh",
                "name": "SSH Agent",
                "type": "ssh",
                "status": "idle",
                "metrics": _agent_metrics["ssh"],
                "description": "Remote server administration",
            },
            {
                "id": "kubernetes",
                "name": "Kubernetes Agent",
                "type": "kubernetes",
                "status": "idle",
                "metrics": _agent_metrics["kubernetes"],
                "description": "CCE cluster management & Helm",
            },
            {
                "id": "ai_brain",
                "name": "AI Brain",
                "type": "ai_brain",
                "status": "ready" if ai_info["ready"] else "disabled",
                "provider": ai_info["provider"],
                "model": ai_info["model"],
                "metrics": _agent_metrics["ai_brain"],
                "description": f"Deepseek reasoning engine ({ai_info['model']})",
            },
        ],
        "ai": ai_info,
    }


@app.post("/api/agents/run")
async def run_agent(command: str):
    session_id = f"session_{datetime.utcnow().timestamp()}"
    initial_state: AgentState = {
        "user_input": command,
        "session_id": session_id,
        "logs": [],
        "stack_name": f"stack-{uuid.uuid4().hex[:8]}",
        "needs_confirmation": False,
    }

    try:
        _agent_metrics["orchestrator"]["runs"] += 1
        _agent_metrics["ai_brain"]["runs"] += 1

        result = graph.invoke(initial_state)

        status = "success"
        if result.get("error"):
            status = "error"
            _agent_metrics["orchestrator"]["errors"] += 1
        else:
            _agent_metrics["orchestrator"]["success"] += 1
        _agent_metrics["ai_brain"]["success"] += 1

        await store_deployment({
            "session_id": session_id,
            "stack_name": result.get("stack_name", ""),
            "status": status,
            "tf_plan_path": result.get("tf_plan_path"),
            "ecs_ips": str(result.get("ecs_ips", [])),
            "output": str(result.get("ssh_result") or result.get("kube_result")),
            "error": result.get("error"),
        })
        for log in result.get("logs", []):
            await store_log(log)

        if result.get("intent") == "terraform":
            agent_key = "terraform"
        elif result.get("intent") == "ssh":
            agent_key = "ssh"
        elif result.get("intent") == "kubernetes":
            agent_key = "kubernetes"
        else:
            agent_key = None

        if agent_key:
            _agent_metrics[agent_key]["runs"] += 1
            if status == "success":
                _agent_metrics[agent_key]["success"] += 1
            else:
                _agent_metrics[agent_key]["errors"] += 1

        return {
            "session_id": result.get("session_id"),
            "status": status,
            "intent": result.get("intent"),
            "intent_explanation": result.get("intent_explanation"),
            "needs_confirmation": result.get("needs_confirmation", False),
            "result": str(result.get("ssh_result") or result.get("kube_result") or result.get("ai_suggestion") or "ok"),
            "error": result.get("error"),
            "details": {
                "ecs_ip": result.get("ecs_ip"),
                "stack_name": result.get("stack_name"),
            },
        }
    except Exception as e:
        _agent_metrics["orchestrator"]["errors"] += 1
        return {
            "session_id": session_id,
            "status": "error",
            "intent": "unknown",
            "result": None,
            "needs_confirmation": False,
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
