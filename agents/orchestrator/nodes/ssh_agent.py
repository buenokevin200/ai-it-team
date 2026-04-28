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

    ssh_username = "root"
    ssh_key_pem = ""

    import os
    env_key = os.getenv("SSH_PRIVATE_KEY", "")

    if env_key:
        ssh_key_pem = env_key
    else:
        logs.append({
            "agent_type": "ssh",
            "level": "WARN",
            "message": "No se encontro SSH_PRIVATE_KEY en variables de entorno. Modo simulado.",
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

    try:
        from tools.ssh_client import SSHClientManager

        with SSHClientManager(
            host=ecs_ip,
            username=ssh_username,
            key_pem=ssh_key_pem,
        ) as ssh:
            result = ssh.execute("whoami && hostname && uname -a")
            logs.append({
                "agent_type": "ssh",
                "level": "INFO",
                "message": f"SSH conectado: {result['stdout'][:200]}",
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
