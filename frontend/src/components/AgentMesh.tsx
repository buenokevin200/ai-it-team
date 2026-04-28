"use client";

import { useEffect, useState, useCallback } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  useNodesState,
  useEdgesState,
  MarkerType,
} from "reactflow";
import "reactflow/dist/style.css";

interface AgentInfo {
  id: string;
  name: string;
  type: string;
  status: string;
  metrics?: { runs: number; success: number; errors: number };
  description?: string;
  provider?: string;
  model?: string;
}

const initialNodes: Node[] = [
  {
    id: "ai_brain",
    type: "default",
    position: { x: 250, y: 0 },
    data: {
      label: "AI Brain",
      status: "disabled",
      provider: "",
      type: "ai_brain",
    },
  },
  {
    id: "orchestrator",
    type: "default",
    position: { x: 250, y: 120 },
    data: {
      label: "Orchestrator",
      status: "idle",
      type: "orchestrator",
    },
  },
  {
    id: "terraform",
    type: "default",
    position: { x: 50, y: 280 },
    data: {
      label: "Terraform",
      status: "idle",
      type: "terraform",
    },
  },
  {
    id: "ssh",
    type: "default",
    position: { x: 250, y: 280 },
    data: {
      label: "SSH Agent",
      status: "idle",
      type: "ssh",
    },
  },
  {
    id: "kubernetes",
    type: "default",
    position: { x: 450, y: 280 },
    data: {
      label: "K8s Agent",
      status: "idle",
      type: "kubernetes",
    },
  },
];

const initialEdges: Edge[] = [
  {
    id: "e-ai-orch",
    source: "ai_brain",
    target: "orchestrator",
    animated: false,
    markerEnd: { type: MarkerType.ArrowClosed },
  },
  {
    id: "e-orch-tf",
    source: "orchestrator",
    target: "terraform",
    animated: false,
    markerEnd: { type: MarkerType.ArrowClosed },
  },
  {
    id: "e-orch-ssh",
    source: "orchestrator",
    target: "ssh",
    animated: false,
    markerEnd: { type: MarkerType.ArrowClosed },
  },
  {
    id: "e-orch-k8s",
    source: "orchestrator",
    target: "kubernetes",
    animated: false,
    markerEnd: { type: MarkerType.ArrowClosed },
  },
  {
    id: "e-tf-ssh",
    source: "terraform",
    target: "ssh",
    animated: false,
    markerEnd: { type: MarkerType.ArrowClosed },
  },
  {
    id: "e-ssh-k8s",
    source: "ssh",
    target: "kubernetes",
    animated: false,
    markerEnd: { type: MarkerType.ArrowClosed },
  },
];

const STATUS_COLORS: Record<string, string> = {
  idle: "#6c7086",
  running: "#00ddff",
  success: "#00ff88",
  error: "#ff4444",
  ready: "#00ff88",
  disabled: "#6c7086",
};

const AGENT_ICONS: Record<string, string> = {
  orchestrator: "⚙",
  terraform: "{}",
  ssh: ">_",
  kubernetes: "⎈",
  ai_brain: "🧠",
};

export default function AgentMesh() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [aiStatus, setAiStatus] = useState<{ ready: boolean; provider: string; model: string }>({
    ready: false,
    provider: "none",
    model: "deepseek-chat",
  });

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch("/api/agents/status");
      const data = await res.json();

      if (data.ai) {
        setAiStatus(data.ai);
      }

      if (data.agents) {
        const updatedNodes = nodes.map((node) => {
          const agent = data.agents.find((a: AgentInfo) => a.id === node.id);
          if (!agent) return node;
          return {
            ...node,
            data: {
              ...node.data,
              label: buildNodeLabel(agent),
              status: agent.status,
              provider: agent.provider || "",
              model: agent.model || "",
              metrics: agent.metrics,
            },
            style: buildNodeStyle(agent.status, agent.type),
          };
        });

        const updatedEdges = edges.map((edge) => {
          const sourceAgent = data.agents.find((a: AgentInfo) => a.id === edge.source);
          return {
            ...edge,
            animated: sourceAgent?.status === "running",
            style: {
              stroke: sourceAgent?.status === "running" ? "#00ddff" : "#1e1e2e",
              strokeWidth: sourceAgent?.status === "running" ? 2 : 1,
            },
          };
        });

        setNodes(updatedNodes);
        setEdges(updatedEdges);
      }
    } catch {
      // Silently handle - mesh will show default idle state
    }
  }, [nodes, edges, setNodes, setEdges]);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-full w-full relative">
      <div className="absolute top-4 left-4 z-10 flex items-center gap-3">
        <span className="text-terminal-white text-xs font-bold">
          Agent Service Mesh
        </span>
        <span
          className={`text-xs px-2 py-0.5 rounded ${
            aiStatus.ready
              ? "bg-terminal-green/10 text-terminal-green"
              : "bg-yellow-500/10 text-yellow-400"
          }`}
        >
          AI: {aiStatus.ready ? `${aiStatus.provider} (${aiStatus.model})` : "No configurado"}
        </span>
      </div>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        attributionPosition="bottom-left"
      >
        <Background color="#1e1e2e" gap={20} />
        <Controls className="!bg-[#12121a] !border-[#1e1e2e] !rounded-lg" />
        <MiniMap
          style={{
            background: "#12121a",
            border: "1px solid #1e1e2e",
            borderRadius: "8px",
          }}
          nodeColor={(node) => STATUS_COLORS[node.data?.status as string] || "#6c7086"}
          maskColor="rgba(10,10,15,0.7)"
        />
      </ReactFlow>
    </div>
  );
}

function buildNodeLabel(agent: AgentInfo): string {
  const icon = AGENT_ICONS[agent.type] || "◈";
  const metrics = agent.metrics
    ? `${icon} ${agent.name}\n${agent.metrics.runs} runs | ✓${agent.metrics.success} | ✗${agent.metrics.errors}`
    : `${icon} ${agent.name}`;
  return metrics;
}

function buildNodeStyle(status: string, type: string): React.CSSProperties {
  const color = STATUS_COLORS[status] || "#6c7086";
  const isAi = type === "ai_brain";

  return {
    background: `${color}15`,
    border: `2px solid ${color}`,
    borderRadius: "12px",
    padding: "12px 20px",
    color: color,
    fontWeight: "bold",
    fontSize: "13px",
    fontFamily: "'JetBrains Mono', monospace",
    boxShadow: status === "running" ? `0 0 20px ${color}40` : "none",
    minWidth: "180px",
    textAlign: "center",
    whiteSpace: "pre-line",
    lineHeight: "1.6",
  };
}
