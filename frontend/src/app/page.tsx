"use client";

import { useState } from "react";
import LogViewer from "@/components/LogViewer";
import Console from "@/components/Console";
import SecretsPanel from "@/components/SecretsPanel";

type Panel = "logs" | "console" | "secrets";

export default function Dashboard() {
  const [activePanel, setActivePanel] = useState<Panel>("console");
  const [logs, setLogs] = useState<string[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const addLog = (message: string) => {
    setLogs((prev) => [...prev, `[${new Date().toISOString()}] ${message}`]);
  };

  const handleCommandResult = (result: {
    session_id: string;
    status: string;
    intent?: string;
    result?: string;
    error?: string;
    details?: Record<string, unknown>;
  }) => {
    setSessionId(result.session_id);
    addLog(`SESSION: ${result.session_id}`);
    addLog(`INTENT: ${result.intent || "unknown"}`);
    addLog(`STATUS: ${result.status}`);
    if (result.result) addLog(`RESULT: ${result.result}`);
    if (result.error) addLog(`ERROR: ${result.error}`);
    if (result.details?.ecs_ip)
      addLog(`ECS_IP: ${result.details.ecs_ip}`);
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
          {(["console", "logs", "secrets"] as Panel[]).map((p) => (
            <button
              key={p}
              onClick={() => setActivePanel(p)}
              className={`terminal-btn ${
                activePanel === p
                  ? "bg-terminal-green text-terminal-bg"
                  : "text-terminal-muted hover:text-terminal-white"
              }`}
            >
              {p === "console" ? "Console" : p === "logs" ? "Logs" : "Secrets"}
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
        {activePanel === "secrets" && <SecretsPanel onLog={addLog} />}
      </main>

      <footer className="border-t border-terminal-border bg-terminal-panel px-6 py-1.5 flex items-center justify-between text-xs text-terminal-muted">
        <span>Huawei Cloud Provider: huaweicloud/huaweicloud ~<strong>1.60</strong></span>
        <span>Agents: Terraform | SSH | Kubernetes (CCE)</span>
        <span>v1.0.0</span>
      </footer>
    </div>
  );
}
