from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    TERRAFORM = "terraform"
    SSH = "ssh"
    KUBERNETES = "kubernetes"
    ORCHESTRATOR = "orchestrator"
    AI_BRAIN = "ai_brain"


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


class LogLevel(str, Enum):
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    DEBUG = "DEBUG"


class SecretCategory(str, Enum):
    HWC_ACCESS_KEY = "hwc_access_key"
    HWC_SECRET_KEY = "hwc_secret_key"
    HWC_REGION = "hwc_region"
    HWC_PROJECT_ID = "hwc_project_id"
    SSH_PRIVATE_KEY = "ssh_private_key"
    SSH_USERNAME = "ssh_username"
    SSH_PASSWORD = "ssh_password"
    KUBECONFIG = "kubeconfig"
    HELM_RELEASE = "helm_release"
    HELM_CHART = "helm_chart"
    DEEPSEEK_API_KEY = "ai_deepseek_api_key"
    DEEPSEEK_BASE_URL = "ai_deepseek_base_url"
    DEEPSEEK_MODEL = "ai_deepseek_model"


class SecretCreate(BaseModel):
    name: str
    category: SecretCategory
    value: str


class SecretResponse(BaseModel):
    id: str
    name: str
    category: SecretCategory
    created_at: str
    updated_at: str


class AgentLog(BaseModel):
    id: str = Field(default_factory=lambda: f"log_{datetime.utcnow().timestamp()}")
    session_id: str
    agent_type: AgentType
    level: LogLevel = LogLevel.INFO
    message: str
    metadata: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AgentCommand(BaseModel):
    session_id: str = Field(default_factory=lambda: f"session_{datetime.utcnow().timestamp()}")
    command: str
    intent: Optional[str] = None


class AgentResponse(BaseModel):
    session_id: str
    status: str
    intent: Optional[str] = None
    intent_explanation: Optional[str] = None
    needs_confirmation: bool = False
    result: Optional[str] = None
    error: Optional[str] = None
    details: Optional[dict] = None


class AgentStatusInfo(BaseModel):
    id: str
    name: str
    status: AgentStatus = AgentStatus.IDLE
    last_run: Optional[str] = None
    metrics: dict = Field(default_factory=lambda: {"runs": 0, "success": 0, "errors": 0})


class DeploymentResponse(BaseModel):
    id: str
    session_id: str
    stack_name: str
    status: str
    ecs_ips: Optional[str] = None
    output: Optional[str] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str
