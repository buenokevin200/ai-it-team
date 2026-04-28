"use client";

import { useEffect, useRef } from "react";

interface Props {
  logs: string[];
}

export default function LogViewer({ logs }: Props) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  return (
    <div className="h-full p-4">
      <div className="terminal-panel h-full overflow-y-auto">
        <div className="flex items-center justify-between mb-3 pb-2 border-b border-terminal-border">
          <span className="text-terminal-cyan text-sm font-bold">
            Real-Time Agent Logs
          </span>
          <span className="text-terminal-muted text-xs">
            {logs.length} entries
          </span>
        </div>
        {logs.length === 0 ? (
          <div className="text-terminal-muted text-sm italic py-8 text-center">
            No logs yet. Run a command from the Console tab.
          </div>
        ) : (
          <div className="space-y-0.5">
            {logs.map((log, i) => {
              const isError = log.includes("ERROR");
              const isWarn = log.includes("WARN");
              const color = isError
                ? "text-red-400"
                : isWarn
                ? "text-yellow-400"
                : "text-terminal-white";
              return (
                <div
                  key={i}
                  className={`text-xs ${color} whitespace-pre-wrap break-all py-0.5`}
                >
                  {log}
                </div>
              );
            })}
            <div ref={endRef} />
          </div>
        )}
      </div>
    </div>
  );
}
