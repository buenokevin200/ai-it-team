"use client";

import { useState } from "react";
import LogViewer from "@/components/LogViewer";
import Console from "@/components/Console";
import ConfigPanel from "@/components/ConfigPanel";
import AgentMesh from "@/components/AgentMesh";

type Panel = "console" | "logs" | "mesh" | "config";

export default function Dashboard() {
  const [activePanel, setActivePanel] = useState<Panel>("mesh");
  const [logs, setLogs] = useState<string[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const addLog = (message: string) => {
    setLogs((prev) => [...prev, `[${new Date().toISOString()}] ${message}`]);
  };

  const handleCommandResult = (result: {
    session_id: string;
    status: string;
    intent?: string;
    intent_explanation?: string;
    needs_confirmation?: boolean;
    result?: string;
    error?: string;
    details?: Record<string, unknown>;
  }) => {
    setSessionId(result.session_id);
    addLog(`SESSION: ${result.session_id}`);
    addLog(`INTENT: ${result.intent || "unknown"}`);
    if (result.intent_explanation)
      addLog(`AI PLAN: ${result.intent_explanation}`);
    addLog(`STATUS: ${result.status}`);
    if (result.needs_confirmation)
      addLog(`⚠ CONFIRMACION REQUERIDA: Accion destructiva detectada`);
    if (result.result) addLog(`RESULT: ${result.result}`);
    if (result.error) addLog(`ERROR: ${result.error}`);
    if (result.details?.ecs_ip)
      addLog(`ECS_IP: ${result.details.ecs_ip}`);
  };

  const tabLabel = (p: Panel) => {
    switch (p) {
      case "console": return "Console";
      case "logs": return "Logs";
      case "mesh": return "Agent Mesh";
      case "config": return "Configuracion";
    }
  };

  return (
    <div className="h-screen flex flex-col">
      <header className="border-b border-terminal-border bg-terminal-panel px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-terminal-cyan text-xl font-bold">AI-First IT Team</span>
          <span className="text-terminal-muted text-xs">
            Huawei Cloud Multi-Agent System
          </span>
        </div>
        <nav className="flex gap-1">
          {(["console", "logs", "mesh", "config"] as Panel[]).map((p) => (
            <button
              key={p}
              onClick={() => setActivePanel(p)}
              className={`terminal-btn ${
                activePanel === p
                  ? "bg-terminal-green text-terminal-bg"
                  : "text-terminal-muted hover:text-terminal-white"
              }`}
            >
              {tabLabel(p)}
            </button>
          ))}
        </nav>
        {sessionId && (
          <span className="text-terminal-muted text-xs">
            Session: {sessionId.slice(0, 16)}...
          </span>
        )}
      </header>

      <main className="flex-1 overflow-hidden">
        {activePanel === "console" && (
          <Console onLog={addLog} onResult={handleCommandResult} />
        )}
        {activePanel === "logs" && <LogViewer logs={logs} />}
        {activePanel === "mesh" && <AgentMesh />}
        {activePanel === "config" && <ConfigPanel onLog={addLog} />}
      </main>

      <footer className="border-t border-terminal-border bg-terminal-panel px-6 py-1.5 flex items-center justify-between text-xs text-terminal-muted">
        <span>Huawei Cloud Provider: huaweicloud/huaweicloud ~<strong>1.60</strong></span>
        <span>Agents: Terraform | SSH | Kubernetes (CCE) | AI Brain (Deepseek)</span>
        <span>v2.0.0</span>
      </footer>
    </div>
  );
}
