from tools.db import get_config_sync
from ..state import AgentState


def ssh_node(state: AgentState) -> AgentState:
    session_id = state.get("session_id", "unknown")
    ecs_ip = state.get("ecs_ip", "")
    logs = state.get("logs", [])

    logs.append({
        "agent_type": "ssh",
        "level": "INFO",
        "message": f"Iniciando conexion SSH a {ecs_ip}",
        "session_id": session_id,
    })

    if not ecs_ip:
        state["error"] = "No ECS IP disponible para conectar via SSH"
        logs.append({
            "agent_type": "ssh",
            "level": "ERROR",
            "message": state["error"],
            "session_id": session_id,
        })
        state["logs"] = logs
        return state

    import os
    ssh_username = get_config_sync("ssh_username") or os.getenv("SSH_USERNAME", "root")
    ssh_key_pem = get_config_sync("ssh_private_key") or os.getenv("SSH_PRIVATE_KEY", "")
    ssh_password = get_config_sync("ssh_password") or os.getenv("SSH_PASSWORD", "")

    auth_method = "key" if ssh_key_pem else "password" if ssh_password else None

    if not auth_method:
        logs.append({
            "agent_type": "ssh",
            "level": "WARN",
            "message": "Sin credenciales SSH (key ni password). Modo simulado.",
            "session_id": session_id,
        })
        state["ssh_result"] = {
            "simulated": True,
            "message": f"SSH simulado - comandos listos para ejecutar en {ecs_ip}",
            "ecs_ip": ecs_ip,
        }
        logs.append({
            "agent_type": "ssh",
            "level": "INFO",
            "message": f"SSH simulado OK para {ecs_ip}",
            "session_id": session_id,
        })
        state["logs"] = logs
        return state

    state["ssh_auth_method"] = auth_method

    try:
        from tools.ssh_client import SSHClientManager

        with SSHClientManager(
            host=ecs_ip,
            username=ssh_username,
            password=ssh_password if ssh_password else None,
            key_pem=ssh_key_pem if ssh_key_pem else None,
        ) as ssh:
            result = ssh.execute("whoami && hostname && uname -a")
            logs.append({
                "agent_type": "ssh",
                "level": "INFO",
                "message": f"SSH conectado ({auth_method}): {result['stdout'][:200]}",
                "session_id": session_id,
            })

            docker_result = ssh.execute(
                "curl -fsSL https://get.docker.com | bash 2>&1",
                timeout=120,
            )
            logs.append({
                "agent_type": "ssh",
                "level": "INFO",
                "message": f"Instalacion Docker: exit_code={docker_result['exit_code']}",
                "session_id": session_id,
            })

            state["ssh_result"] = {
                "hostname_check": result["stdout"].strip(),
                "docker_install_exit_code": docker_result["exit_code"],
                "docker_install_output": docker_result["stdout"][:500],
                "auth_method": auth_method,
            }
    except Exception as e:
        state["error"] = f"Error SSH: {str(e)}"
        logs.append({
            "agent_type": "ssh",
            "level": "ERROR",
            "message": state["error"],
            "session_id": session_id,
        })

    state["logs"] = logs
    return state
