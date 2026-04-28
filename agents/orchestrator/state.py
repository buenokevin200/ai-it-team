from typing import List, Optional, TypedDict


class AgentState(TypedDict, total=False):
    user_input: str
    session_id: str
    intent: Optional[str]
    intent_explanation: Optional[str]
    needs_confirmation: bool
    tf_plan_path: Optional[str]
    ecs_ip: Optional[str]
    ecs_ips: List[str]
    ssh_result: Optional[dict]
    ssh_auth_method: Optional[str]
    kubeconfig_ref: Optional[str]
    kube_result: Optional[dict]
    ai_suggestion: Optional[str]
    error: Optional[str]
    logs: List[dict]
    stack_name: str
