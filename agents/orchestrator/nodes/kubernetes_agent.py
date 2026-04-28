import os

from tools.db import get_config_sync
from ..state import AgentState


def kubernetes_node(state: AgentState) -> AgentState:
    session_id = state.get("session_id", "unknown")
    logs = state.get("logs", [])
    namespace = state.get("stack_name", "default")

    logs.append({
        "agent_type": "kubernetes",
        "level": "INFO",
        "message": f"Iniciando despliegue Kubernetes en namespace: {namespace}",
        "session_id": session_id,
    })

    kubeconfig_content = get_config_sync("kubeconfig") or os.getenv("KUBECONFIG_CONTENT", "")
    if not kubeconfig_content:
        logs.append({
            "agent_type": "kubernetes",
            "level": "WARN",
            "message": "No se encontro KUBECONFIG_CONTENT. Modo simulado.",
            "session_id": session_id,
        })
        state["kube_result"] = {
            "simulated": True,
            "message": f"Kubernetes simulado - despliegue listo en namespace {namespace}",
            "namespace": namespace,
        }
        state["logs"] = logs
        return state

    try:
        from tools.kube_client import KubeClient

        client = KubeClient(kubeconfig_content)

        ns_result = client.kubectl(f"create namespace {namespace} --dry-run=client -o yaml | kubectl apply -f -")
        logs.append({
            "agent_type": "kubernetes",
            "level": "INFO",
            "message": f"Namespace {namespace}: {ns_result['stdout'][:200]}",
            "session_id": session_id,
        })

        if get_config_sync("helm_release") or os.getenv("HELM_RELEASE"):
            release = get_config_sync("helm_release") or os.getenv("HELM_RELEASE", f"app-{namespace}")
            chart = get_config_sync("helm_chart") or os.getenv("HELM_CHART", "stable/nginx")
            helm_result = client.helm_install(release, chart, namespace)
            logs.append({
                "agent_type": "kubernetes",
                "level": "INFO",
                "message": f"Helm install {release}: exit_code={helm_result['exit_code']}",
                "session_id": session_id,
            })
            state["kube_result"] = {
                "namespace": namespace,
                "helm_release": release,
                "helm_chart": chart,
                "exit_code": helm_result["exit_code"],
                "output": helm_result["stdout"][:500],
            }
        else:
            state["kube_result"] = {
                "namespace": namespace,
                "namespace_created": True,
                "message": "Namespace creado exitosamente. Helm no configurado.",
            }
    except Exception as e:
        state["error"] = f"Error Kubernetes: {str(e)}"
        logs.append({
            "agent_type": "kubernetes",
            "level": "ERROR",
            "message": state["error"],
            "session_id": session_id,
        })

    state["logs"] = logs
    return state
