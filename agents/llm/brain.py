from typing import Optional

from .provider import get_provider


_SYSTEM_INTENT_PROMPT = """
Eres un arquitecto cloud experto en Huawei Cloud. Tu tarea es clasificar la intencion
del usuario en una de estas categorias:

- "terraform": El usuario quiere crear/modificar/eliminar infraestructura (ECS, VPC, EIP, Security Groups)
- "ssh": El usuario quiere conectarse a un servidor, ejecutar comandos, instalar software
- "kubernetes": El usuario quiere desplegar en CCE, usar kubectl/helm
- "multi_step": El usuario pide un flujo completo que involucra multiples pasos (infra + ssh + k8s)
- "unknown": No se puede determinar

Responde SOLO con la palabra de la categoria, nada mas.
"""

_SYSTEM_EXPLAIN_PROMPT = """
Eres un arquitecto cloud senior. Dado el objetivo del usuario, explica en 2-3 lineas
que acciones vas a ejecutar y por que. Se claro y tecnico.
"""


class AgentBrain:
    def intent(self, user_input: str, fallback: str = "terraform") -> str:
        try:
            llm = get_provider().get_chat_llm()
            messages = [
                {"role": "system", "content": _SYSTEM_INTENT_PROMPT},
                {"role": "user", "content": user_input},
            ]
            response = llm.invoke(messages)
            intent = response.content.strip().lower()
            if intent in ("terraform", "ssh", "kubernetes", "multi_step", "unknown"):
                return intent
            return fallback
        except (RuntimeError, Exception):
            from orchestrator.graph import _fallback_intent
            return _fallback_intent(user_input)

    def explain_plan(self, user_input: str, intent: str) -> str:
        try:
            llm = get_provider().get_chat_llm()
            messages = [
                {"role": "system", "content": _SYSTEM_EXPLAIN_PROMPT},
                {
                    "role": "user",
                    "content": f"Usuario: {user_input}\nIntencion: {intent}\n\nExplica el plan:",
                },
            ]
            response = llm.invoke(messages)
            return response.content.strip()
        except Exception:
            return f"Ejecutando {intent} segun solicitud del usuario."

    def needs_confirmation(self, intent: str, user_input: str) -> bool:
        destructive_keywords = ["delete", "eliminar", "destroy", "remove", "rm", "terminate", "kill"]
        input_lower = user_input.lower()
        return any(kw in input_lower for kw in destructive_keywords)


class TerraformBrain(AgentBrain):
    def suggest_resources(self, goal: str) -> str:
        try:
            llm = get_provider().get_chat_llm(temperature=0.2)
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Eres un experto en Terraform para Huawei Cloud. "
                        "Dado el objetivo del usuario, recomienda que recursos HWC crear "
                        "(ECS, VPC, subnets, EIP, security groups). Responde en texto plano."
                    ),
                },
                {"role": "user", "content": goal},
            ]
            response = llm.invoke(messages)
            return response.content.strip()
        except Exception:
            return "No se pudo generar sugerencia automatica."


class SSHBrain(AgentBrain):
    def suggest_commands(self, goal: str) -> str:
        try:
            llm = get_provider().get_chat_llm(temperature=0.2)
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Eres un administrador de sistemas Linux experto. "
                        "Dado el objetivo del usuario, sugiere comandos bash seguros "
                        "para ejecutar en un servidor remoto."
                    ),
                },
                {"role": "user", "content": goal},
            ]
            response = llm.invoke(messages)
            return response.content.strip()
        except Exception:
            return "No se pudo generar sugerencia."


class K8sBrain(AgentBrain):
    def recommend_deployment(self, goal: str) -> str:
        try:
            llm = get_provider().get_chat_llm(temperature=0.2)
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Eres un experto en Kubernetes y CCE de Huawei Cloud. "
                        "Dado el objetivo del usuario, recomienda el despliegue optimo "
                        "(namespace, deployment, service, ingress, Helm chart)."
                    ),
                },
                {"role": "user", "content": goal},
            ]
            response = llm.invoke(messages)
            return response.content.strip()
        except Exception:
            return "No se pudo generar recomendacion."
