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
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

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
      onResult(data);

      if (data.intent_explanation) {
        setHistory((prev) => [...prev, `[AI Brain] ${data.intent_explanation}`]);
      }
      if (data.needs_confirmation) {
        setHistory((prev) => [...prev, "⚠ ACCION DESTRUCTIVA DETECTADA - Confirmacion requerida"]);
      }
      if (data.error) {
        setHistory((prev) => [...prev, `ERROR: ${data.error}`]);
      }
    } catch (err) {
      const msg = `Error: ${err instanceof Error ? err.message : "unknown"}`;
      onLog(msg);
      setHistory((prev) => [...prev, msg]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
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
              else if (line.startsWith("[AI Brain]")) color = "text-purple-400";
              else if (line.startsWith("ERROR")) color = "text-red-400";
              else if (line.includes("⚠")) color = "text-yellow-400";

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
          {loading ? "AI pensando..." : "Run"}
        </button>
      </div>
    </div>
  );
}
