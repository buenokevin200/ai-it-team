import os
import json
import uuid
import tempfile
import subprocess
from datetime import datetime

from ..state import AgentState

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "tools", "huawei_tf")


def generate_provider_tf(work_dir: str):
    content = '''terraform {
  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = "~> 1.60"
    }
  }
}

provider "huaweicloud" {
  region      = var.region
  access_key  = var.access_key
  secret_key  = var.secret_key
  project_id  = var.project_id
}

variable "region"     { type = string }
variable "access_key" { type = string; sensitive = true }
variable "secret_key" { type = string; sensitive = true }
variable "project_id" { type = string }
'''
    with open(os.path.join(work_dir, "providers.tf"), "w") as f:
        f.write(content)


def generate_ecs_tf(work_dir: str, stack_name: str):
    content = f'''resource "huaweicloud_vpc" "{stack_name}" {{
  name = "{stack_name}-vpc"
  cidr = "10.0.0.0/16"
}}

resource "huaweicloud_vpc_subnet" "{stack_name}" {{
  name       = "{stack_name}-subnet"
  vpc_id     = huaweicloud_vpc.{stack_name}.id
  cidr       = "10.0.1.0/24"
  gateway_ip = "10.0.1.1"
}}

resource "huaweicloud_networking_secgroup" "{stack_name}" {{
  name = "{stack_name}-sg"
}}

resource "huaweicloud_networking_secgroup_rule" "ssh_in" {{
  security_group_id = huaweicloud_networking_secgroup.{stack_name}.id
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 22
  port_range_max    = 22
  remote_ip_prefix  = "0.0.0.0/0"
}}

resource "huaweicloud_vpc_eip" "{stack_name}" {{
  publicip {{
    type = "5_bgp"
  }}
  bandwidth {{
    name        = "{stack_name}-eip-bandwidth"
    size        = 1
    share_type  = "PER"
    charge_mode = "traffic"
  }}
}}

resource "huaweicloud_compute_instance" "{stack_name}" {{
  name               = "{stack_name}-ecs"
  image_id           = "5dce21dc-b024-4f75-a3e5-e3a5b199b6a4"
  flavor_id          = "s6.small.1"
  security_group_ids = [huaweicloud_networking_secgroup.{stack_name}.id]

  network {{
    uuid = huaweicloud_vpc_subnet.{stack_name}.id
  }}

  system_disk_type = "SAS"
  system_disk_size = 40

  admin_pass = "T3mpP@ssw0rd!"
}}

resource "huaweicloud_vpc_eip_associate" "{stack_name}" {{
  public_ip  = huaweicloud_vpc_eip.{stack_name}.address
  port_id    = huaweicloud_compute_instance.{stack_name}.network[0].port
}}

output "ecs_public_ip" {{
  value = huaweicloud_vpc_eip.{stack_name}.address
}}

output "ecs_id" {{
  value = huaweicloud_compute_instance.{stack_name}.id
}}
'''
    with open(os.path.join(work_dir, "main.tf"), "w") as f:
        f.write(content)


def terraform_node(state: AgentState) -> AgentState:
    session_id = state.get("session_id", "unknown")
    stack_name = state.get("stack_name", f"stack-{uuid.uuid4().hex[:8]}")
    state["stack_name"] = stack_name

    logs = state.get("logs", [])
    logs.append({
        "agent_type": "terraform",
        "level": "INFO",
        "message": f"Iniciando Terraform plan para stack: {stack_name}",
        "session_id": session_id,
    })

    work_dir = tempfile.mkdtemp(prefix=f"tf-{stack_name}-")

    try:
        generate_provider_tf(work_dir)
        generate_ecs_tf(work_dir, stack_name)

        tf_env = os.environ.copy()
        tf_env["TF_VAR_region"] = os.getenv("TF_VAR_region", "la-north-2")
        tf_env["TF_VAR_access_key"] = os.getenv("TF_VAR_access_key", "")
        tf_env["TF_VAR_secret_key"] = os.getenv("TF_VAR_secret_key", "")
        tf_env["TF_VAR_project_id"] = os.getenv("TF_VAR_project_id", "")

        init_result = subprocess.run(
            ["terraform", "init"],
            capture_output=True, text=True, cwd=work_dir, timeout=60, env=tf_env
        )
        logs.append({
            "agent_type": "terraform",
            "level": "INFO",
            "message": f"Terraform init: {init_result.stdout[:500]}",
            "session_id": session_id,
        })
        if init_result.returncode != 0:
            logs.append({
                "agent_type": "terraform",
                "level": "ERROR",
                "message": f"Terraform init failed: {init_result.stderr}",
                "session_id": session_id,
            })
            state["error"] = init_result.stderr
            state["logs"] = logs
            return state

        plan_result = subprocess.run(
            ["terraform", "plan", "-out=tfplan"],
            capture_output=True, text=True, cwd=work_dir, timeout=120, env=tf_env
        )
        logs.append({
            "agent_type": "terraform",
            "level": "INFO",
            "message": f"Terraform plan: {plan_result.stdout[:1000]}",
            "session_id": session_id,
        })

        if plan_result.returncode == 0:
            apply_result = subprocess.run(
                ["terraform", "apply", "-auto-approve", "tfplan"],
                capture_output=True, text=True, cwd=work_dir, timeout=300, env=tf_env
            )
            logs.append({
                "agent_type": "terraform",
                "level": "INFO",
                "message": f"Terraform apply: {apply_result.stdout[:1000]}",
                "session_id": session_id,
            })

            if apply_result.returncode == 0:
                output_result = subprocess.run(
                    ["terraform", "output", "-json"],
                    capture_output=True, text=True, cwd=work_dir, timeout=30, env=tf_env
                )
                try:
                    outputs = json.loads(output_result.stdout)
                    state["ecs_ip"] = outputs.get("ecs_public_ip", {}).get("value", "")
                    state["ecs_ips"] = [state["ecs_ip"]]
                except json.JSONDecodeError:
                    state["ecs_ip"] = "unknown"
                    state["ecs_ips"] = []

                state["tf_plan_path"] = work_dir
                logs.append({
                    "agent_type": "terraform",
                    "level": "INFO",
                    "message": f"Infraestructura desplegada. ECS IP: {state['ecs_ip']}",
                    "session_id": session_id,
                })
            else:
                state["error"] = apply_result.stderr
                logs.append({
                    "agent_type": "terraform",
                    "level": "ERROR",
                    "message": f"Apply fallido: {apply_result.stderr}",
                    "session_id": session_id,
                })
        else:
            state["error"] = plan_result.stderr
            logs.append({
                "agent_type": "terraform",
                "level": "ERROR",
                "message": f"Plan fallido: {plan_result.stderr}",
                "session_id": session_id,
            })
    except Exception as e:
        state["error"] = str(e)
        logs.append({
            "agent_type": "terraform",
            "level": "ERROR",
            "message": f"Error: {str(e)}",
            "session_id": session_id,
        })

    state["logs"] = logs
    return state
