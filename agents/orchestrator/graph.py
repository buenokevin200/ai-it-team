from typing import Literal

from langgraph.graph import StateGraph, END

from .nodes.terraform_agent import terraform_node
from .nodes.ssh_agent import ssh_node
from .nodes.kubernetes_agent import kubernetes_node
from .state import AgentState

SYSTEM_PROMPT = """
Eres un equipo de agentes autónomos especializados en gestionar infraestructura en 
Huawei Cloud (HWC). Operas bajo las siguientes reglas y conocimiento:

## IDENTIDAD
Eres un equipo compuesto por tres agentes especializados que colaboran:
- Agente Terraform: Experto en HWC Terraform Provider (huaweicloud/huaweicloud ~> 1.60)
- Agente SSH: Experto en administración Linux (Ubuntu/CentOS/Huawei EulerOS) vía SSH
- Agente Kubernetes: Experto en CCE (Cloud Container Engine), Helm, kubectl

## REGLAS DE SEGURIDAD (OBLIGATORIAS)
1. NUNCA muestres, loguees o expongas Access Keys, Secret Keys o claves privadas.
2. Siempre usa variables sensibles (sensitive = true) en Terraform.
3. Las conexiones SSH deben usar key-based auth con claves de 2048+ bits RSA.
4. Verifica que los Security Groups de HWC tengan reglas de minimo privilegio.
5. Por defecto, solicita confirmación humana antes de ejecutar terraform apply 
   o comandos destructivos (rm -rf, kubectl delete, etc.).
6. Registra TODAS las acciones en los logs del sistema con timestamp.

## FLUJO DE OPERACION
1. Analiza el objetivo del usuario.
2. Determina que agente(s) necesitas ejecutar y en que orden.
3. Ejecuta el plan, pasando outputs relevantes entre agentes.
4. Reporta resultados claros: que se hizo, IPs generadas, estados.

## CONOCIMIENTO TECNICO DE HUAWEI CLOUD
- Provider: huaweicloud/huaweicloud ~> 1.60
- ECS: Usa huaweicloud_compute_instance con flavors como s6.small.1, c6.large.2
- CCE: Usa huaweicloud_cce_cluster con tipo "VirtualMachine" o "BareMetal"
- VPC: Usa huaweicloud_vpc, huaweicloud_vpc_subnet, huaweicloud_networking_secgroup
- EIP: Usa huaweicloud_vpc_eip para IPs publicas
- Autenticacion: Usa environment vars TF_VAR_access_key, TF_VAR_secret_key

## FORMATO DE RESPUESTA
Siempre responde en el siguiente formato estructurado:

[intento: <terraform|ssh|kubernetes|multi_step>]
[plan: <descripcion de los pasos a ejecutar>]
[resultado: <output del comando/sistema>]
[error: <si aplica, descripcion del error y resolucion>]
"""


def parse_intent(state: AgentState) -> AgentState:
    user_input = state["user_input"].lower()

    if any(kw in user_input for kw in ["terraform", "ecs", "vpc", "eip", "security group", "infra", "crear servidor", "create server", "provision"]):
        state["intent"] = "terraform"
    elif any(kw in user_input for kw in ["ssh", "conectar", "connect", "install docker", "instalar", "configurar servidor", "configure"]):
        state["intent"] = "ssh"
    elif any(kw in user_input for kw in ["kubernetes", "k8s", "cce", "helm", "deploy", "desplegar", "pod", "cluster"]):
        state["intent"] = "kubernetes"
    elif any(kw in user_input for kw in ["multi", "full", "completo", "everything", "all", "full stack", "stack completo"]):
        state["intent"] = "multi_step"
    else:
        state["intent"] = "terraform"

    state["logs"] = state.get("logs", []) + [
        {
            "agent_type": "orchestrator",
            "level": "INFO",
            "message": f"Intencion clasificada: {state['intent']}",
            "session_id": state["session_id"],
        }
    ]
    return state


def router(state: AgentState) -> Literal["terraform", "ssh", "kubernetes", END]:
    intent = state.get("intent", "terraform")

    if intent == "multi_step":
        if not state.get("ecs_ip"):
            return "terraform"
        if not state.get("ssh_result"):
            return "ssh"
        if not state.get("kube_result"):
            return "kubernetes"
        return END

    return intent


def build_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("parse", parse_intent)
    workflow.add_node("terraform", terraform_node)  # type: ignore[arg-type]
    workflow.add_node("ssh", ssh_node)  # type: ignore[arg-type]
    workflow.add_node("kubernetes", kubernetes_node)  # type: ignore[arg-type]

    workflow.set_entry_point("parse")

    workflow.add_conditional_edges("parse", router)
    workflow.add_edge("terraform", router)  # type: ignore[arg-type]
    workflow.add_edge("ssh", router)  # type: ignore[arg-type]
    workflow.add_edge("kubernetes", router)  # type: ignore[arg-type]

    return workflow.compile()


graph = build_graph()
