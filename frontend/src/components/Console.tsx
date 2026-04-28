"use client";

import { useState, useRef, useEffect } from "react";

interface Props {
  onLog: (message: string) => void;
  onResult: (result: {
    session_id: string;
    status: string;
    intent?: string;
    intent_explanation?: string;
    needs_confirmation?: boolean;
    result?: string;
    error?: string;
    details?: Record<string, unknown>;
  }) => void;
}

export default function Console({ onLog, onResult }: Props) {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<string[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const pollResult = async (sid: string) => {
    let attempts = 0;
    while (true) {
      await new Promise((r) => setTimeout(r, 2000));
      attempts++;

      if (attempts === 15) {
        setHistory((prev) => [...prev, "⚠ La operacion esta tomando mas de 30 segundos. Verifica los logs en la pestana Logs."]);
      }

      try {
        const res = await fetch(`/api/deployments/${encodeURIComponent(sid)}`);
        const data = await res.json();

        const logsRes = await fetch(`/api/logs/${encodeURIComponent(sid)}`);
        const logsData = await logsRes.json();
        if (logsData.logs) {
          logsData.logs.forEach((log: { message: string; agent_type: string; level: string }) => {
            const prefix = log.agent_type === "ai_brain" ? "[AI Brain]" : `[${log.agent_type}]`;
            const line = `${prefix} ${log.message}`;
            setHistory((prev) => {
              if (prev.includes(line)) return prev;
              return [...prev, line];
            });
          });
        }

        if (data.status === "processing" || data.status === "unknown") {
          continue;
        }

        onResult({
          session_id: sid,
          status: data.status,
          intent: data.intent,
          intent_explanation: data.intent_explanation,
          needs_confirmation: data.needs_confirmation,
          result: data.result,
          error: data.error,
          details: data.details,
        });

        if (data.intent_explanation) {
          setHistory((prev) => [...prev, `[AI Brain] ${data.intent_explanation}`]);
        }
        if (data.needs_confirmation) {
          setHistory((prev) => [...prev, "⚠ ACCION DESTRUCTIVA DETECTADA"]);
        }
        if (data.error) {
          setHistory((prev) => [...prev, `ERROR: ${data.error}`]);
        }
        setLoading(false);
        return;
      } catch {
        continue;
      }
    }
  };

  const executeCommand = async (command: string) => {
    if (!command.trim()) return;

    const trimmed = command.trim();
    setHistory((prev) => [...prev, `$ ${trimmed}`]);
    onLog(`> ${trimmed}`);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/agents/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: trimmed }),
      });
      const data = await res.json();

      if (data.status === "processing" && data.session_id) {
        setSessionId(data.session_id);
        setHistory((prev) => [...prev, "Procesando... (los logs apareceran en tiempo real)"]);
        onLog(`SESSION: ${data.session_id}`);
        pollResult(data.session_id);
      } else {
        onResult(data);
        setLoading(false);
      }
    } catch (err) {
      const msg = `Error: ${err instanceof Error ? err.message : "unknown"}`;
      onLog(msg);
      setHistory((prev) => [...prev, msg]);
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      executeCommand(input);
    }
  };

  return (
    <div className="h-full flex flex-col p-4">
      <div className="flex-1 terminal-panel overflow-y-auto mb-4">
        <pre className="text-terminal-muted text-sm whitespace-pre-wrap select-text">
          {`╔══════════════════════════════════════════════════════════╗
║  AI-First IT Team - Multi-Agent Console               ║
║  Agents with Deepseek AI Brain                        ║
╠══════════════════════════════════════════════════════════╣
║  Comandos disponibles:                                  ║
║                                                         ║
║  "crea un servidor ECS"     → Terraform + AI Brain     ║
║  "conectate por SSH"        → SSH Agent + AI Brain     ║
║  "despliega en kubernetes"  → K8s Agent + AI Brain     ║
║  "stack completo con docker" → Flujo multi-step + AI   ║
║                                                         ║
║  Agentes: Terraform | SSH | Kubernetes | AI (Deepseek) ║
╚══════════════════════════════════════════════════════════╝`}
        </pre>
        {history.length > 0 && (
          <div className="mt-4">
            {history.map((line, i) => {
              let color = "text-terminal-white";
              if (line.startsWith("$")) color = "text-terminal-cyan";
              else if (line.includes("[AI Brain]") || line.startsWith("[AI Brain]")) color = "text-purple-400";
              else if (line.startsWith("ERROR")) color = "text-red-400";
              else if (line.includes("⚠")) color = "text-yellow-400";
              else if (line.startsWith("[terraform]")) color = "text-terminal-green";
              else if (line.startsWith("[ssh]")) color = "text-terminal-cyan";
              else if (line.startsWith("[kubernetes]")) color = "text-terminal-muted";

              return (
                <div key={i} className={`text-sm py-0.5 ${color}`}>
                  {line}
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        <span className="text-terminal-green font-bold text-sm">$</span>
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="crea un servidor ECS..."
          disabled={loading}
          className="flex-1 terminal-input"
          autoComplete="off"
        />
        <button
          onClick={() => executeCommand(input)}
          disabled={loading || !input.trim()}
          className="terminal-btn-primary"
        >
          {loading ? "Ejecutando..." : "Run"}
        </button>
      </div>
    </div>
  );
}
