from typing import List, Optional, TypedDict


class AgentState(TypedDict, total=False):
    user_input: str
    session_id: str
    intent: Optional[str]
    tf_plan_path: Optional[str]
    ecs_ip: Optional[str]
    ecs_ips: List[str]
    ssh_result: Optional[dict]
    kubeconfig_ref: Optional[str]
    kube_result: Optional[dict]
    error: Optional[str]
    logs: List[dict]
    stack_name: str
