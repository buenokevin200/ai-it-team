import { NextResponse } from "next/server";

const AGENT_URL = process.env.AGENT_SERVICE_URL || "http://localhost:8000";

export async function GET() {
  try {
    const res = await fetch(`${AGENT_URL}/api/agents/status`);
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({
      agents: [
        { id: "orchestrator", name: "Orchestrator", type: "orchestrator", status: "idle", metrics: { runs: 0, success: 0, errors: 0 }, description: "LangGraph workflow" },
        { id: "terraform", name: "Terraform Agent", type: "terraform", status: "idle", metrics: { runs: 0, success: 0, errors: 0 }, description: "HWC provisioning" },
        { id: "ssh", name: "SSH Agent", type: "ssh", status: "idle", metrics: { runs: 0, success: 0, errors: 0 }, description: "Remote admin" },
        { id: "kubernetes", name: "K8s Agent", type: "kubernetes", status: "idle", metrics: { runs: 0, success: 0, errors: 0 }, description: "CCE/Helm" },
        { id: "ai_brain", name: "AI Brain", type: "ai_brain", status: "disabled", metrics: { runs: 0, success: 0, errors: 0 }, description: "Deepseek disabled" },
      ],
      ai: { ready: false, provider: "none", model: "deepseek-chat" },
    });
  }
}
