# AI-First IT Team

Sistema Multi-Agente para gestion de infraestructura en Huawei Cloud con agentes de IA autonomas.

## Stack

| Capa | Tecnologia |
|------|-----------|
| Frontend | Next.js 14 + React + Tailwind CSS |
| Orquestacion | LangGraph (Python) |
| Agentes | Terraform (HWC Provider) / SSH (Paramiko) / Kubernetes (CCE) |
| Base de Datos | SQLite con secrets cifrados (Fernet) |
| Runtime | Docker Compose |

## Quick Start

```bash
cp agents/.env.example .env
docker compose up --build
```

- Dashboard: http://localhost:3000
- Agent API: http://localhost:8000/health

## Agents

| Agente | Proposito |
|--------|-----------|
| Terraform | Provisiona infraestructura HWC (ECS, VPC, EIP, Security Groups) |
| SSH | Conexion segura a ECS con Paramiko, administracion remota |
| Kubernetes | Despliegue en CCE (Cloud Container Engine), Helm charts |

## Secrets Management

Las credenciales (AK/SK, SSH keys) se cifran con Fernet (AES-128) antes de almacenarse en SQLite. La clave maestra se inyecta via `ENCRYPTION_KEY`.

## Architecture

```
User → Next.js Dashboard → API Routes → LangGraph Orchestrator
                                              ├── Terraform Agent
                                              ├── SSH Agent
                                              └── Kubernetes Agent
```
