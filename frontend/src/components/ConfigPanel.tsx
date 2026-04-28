"use client";

import { useState, useEffect, useCallback } from "react";

interface Props {
  onLog: (message: string) => void;
}

interface ConfigField {
  name: string;
  label: string;
  description: string;
  category: string;
  value: string;
  configured: boolean;
  sensitive: boolean;
}

const DEFAULT_FIELDS: ConfigField[] = [
  {
    name: "hwc_access_key",
    label: "Access Key (AK)",
    description: "Huawei Cloud Access Key",
    category: "hwc_access_key",
    value: "",
    configured: false,
    sensitive: true,
  },
  {
    name: "hwc_secret_key",
    label: "Secret Key (SK)",
    description: "Huawei Cloud Secret Key",
    category: "hwc_secret_key",
    value: "",
    configured: false,
    sensitive: true,
  },
  {
    name: "hwc_region",
    label: "Region",
    description: "Huawei Cloud Region (e.g. la-north-2)",
    category: "hwc_region",
    value: "",
    configured: false,
    sensitive: false,
  },
  {
    name: "hwc_project_id",
    label: "Project ID",
    description: "Huawei Cloud Project ID",
    category: "hwc_project_id",
    value: "",
    configured: false,
    sensitive: false,
  },
  {
    name: "ssh_private_key",
    label: "SSH Private Key",
    description: "RSA private key PEM for ECS access",
    category: "ssh_private_key",
    value: "",
    configured: false,
    sensitive: true,
  },
  {
    name: "ssh_username",
    label: "SSH Username",
    description: "Default username for SSH connections",
    category: "ssh_username",
    value: "",
    configured: false,
    sensitive: false,
  },
  {
    name: "ssh_password",
    label: "SSH Password",
    description: "Alternative auth: password-based SSH login",
    category: "ssh_password",
    value: "",
    configured: false,
    sensitive: true,
  },
  {
    name: "kubeconfig",
    label: "Kubeconfig",
    description: "Kubernetes config YAML for CCE cluster",
    category: "kubeconfig",
    value: "",
    configured: false,
    sensitive: true,
  },
  {
    name: "helm_release",
    label: "Helm Release Name",
    description: "Default Helm release name for deployments",
    category: "helm_release",
    value: "",
    configured: false,
    sensitive: false,
  },
  {
    name: "helm_chart",
    label: "Helm Chart",
    description: "Default Helm chart (e.g. stable/nginx-ingress)",
    category: "helm_chart",
    value: "",
    configured: false,
    sensitive: false,
  },
  {
    name: "ai_deepseek_api_key",
    label: "Deepseek API Key",
    description: "API key for AI agent reasoning engine",
    category: "ai_deepseek_api_key",
    value: "",
    configured: false,
    sensitive: true,
  },
  {
    name: "ai_deepseek_base_url",
    label: "Deepseek Base URL",
    description: "Custom API endpoint (default: https://api.deepseek.com)",
    category: "ai_deepseek_base_url",
    value: "",
    configured: false,
    sensitive: false,
  },
  {
    name: "ai_deepseek_model",
    label: "Deepseek Model",
    description: "Model name (default: deepseek-chat)",
    category: "ai_deepseek_model",
    value: "",
    configured: false,
    sensitive: false,
  },
];

export default function ConfigPanel({ onLog }: Props) {
  const [fields, setFields] = useState<ConfigField[]>(DEFAULT_FIELDS);
  const [editedValues, setEditedValues] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: "success" | "error" | "info" } | null>(null);

  const showMessage = (text: string, type: "success" | "error" | "info" = "info") => {
    setMessage({ text, type });
    setTimeout(() => setMessage(null), 4000);
  };

  const fetchConfig = useCallback(async () => {
    try {
      const res = await fetch("/api/config");
      const data = await res.json();
      const updatedFields = DEFAULT_FIELDS.map((field) => {
        const stored = data.config?.find(
          (s: { name: string; category: string }) =>
            s.name === field.name || s.category === field.category
        );
        return {
          ...field,
          configured: stored?.configured || false,
          value: stored?.value || "",
        };
      });
      setFields(updatedFields);
      const initValues: Record<string, string> = {};
      updatedFields.forEach((f) => {
        if (!f.configured) initValues[f.name] = "";
      });
      setEditedValues(initValues);
    } catch {
      showMessage("No se pudo cargar la configuracion. Verifica que el backend este corriendo.", "error");
    }
  }, []);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  const handleChange = (name: string, value: string) => {
    setEditedValues((prev) => ({ ...prev, [name]: value }));
  };

  const saveField = async (field: ConfigField) => {
    const newValue = editedValues[field.name];
    if (newValue === undefined || newValue === field.value) return;

    try {
      const url = `/api/config?name=${encodeURIComponent(field.name)}&category=${encodeURIComponent(field.category)}&value=${encodeURIComponent(newValue)}`;
      const res = await fetch(url, { method: "POST" });
      const data = await res.json();
      if (data.status === "stored") {
        onLog(`Config saved: ${field.label}`);
        showMessage(`${field.label} guardado`, "success");
        fetchConfig();
      } else {
        showMessage(`Error al guardar ${field.label}`, "error");
      }
    } catch (err) {
      showMessage(`Error: ${err instanceof Error ? err.message : "unknown"}`, "error");
    }
  };

  const saveAll = async () => {
    setSaving(true);
    let count = 0;
    for (const field of fields) {
      const newValue = editedValues[field.name];
      if (newValue !== undefined && newValue && newValue !== field.value) {
        try {
          const url = `/api/config?name=${encodeURIComponent(field.name)}&category=${encodeURIComponent(field.category)}&value=${encodeURIComponent(newValue)}`;
          const res = await fetch(url, { method: "POST" });
          const data = await res.json();
          if (data.status === "stored") count++;
        } catch {
          // skip
        }
      }
    }
    onLog(`Config bulk save: ${count} fields updated`);
    showMessage(`${count} campos guardados`, "success");
    setSaving(false);
    fetchConfig();
  };

  const deleteField = async (field: ConfigField) => {
    try {
      await fetch(`/api/secrets/${encodeURIComponent(field.name)}`, { method: "DELETE" });
      onLog(`Config deleted: ${field.label}`);
      showMessage(`${field.label} eliminado`, "info");
      fetchConfig();
    } catch {
      showMessage(`Error al eliminar ${field.label}`, "error");
    }
  };

  const allConfigured = fields.every((f) => f.configured);
  const hasEdits = Object.values(editedValues).some((v) => v);

  return (
    <div className="h-full p-4">
      {message && (
        <div
          className={`mb-3 px-4 py-2 rounded text-xs ${
            message.type === "success"
              ? "bg-terminal-green/10 text-terminal-green border border-terminal-green/30"
              : message.type === "error"
              ? "bg-red-900/30 text-red-400 border border-red-500/30"
              : "bg-terminal-cyan/10 text-terminal-cyan border border-terminal-cyan/30"
          }`}
        >
          {message.text}
        </div>
      )}

      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <h2 className="text-terminal-cyan text-sm font-bold">
            Configuracion del Sistema
          </h2>
          <span
            className={`text-xs px-2 py-0.5 rounded ${
              allConfigured
                ? "bg-terminal-green/10 text-terminal-green"
                : "bg-yellow-500/10 text-yellow-400"
            }`}
          >
            {fields.filter((f) => f.configured).length}/{fields.length} configurados
          </span>
        </div>
        <div className="flex gap-2">
          <button
            onClick={fetchConfig}
            className="terminal-btn text-terminal-muted hover:text-terminal-white text-xs"
          >
            Recargar
          </button>
          {hasEdits && (
            <button
              onClick={saveAll}
              disabled={saving}
              className="terminal-btn-primary text-xs"
            >
              {saving ? "Guardando..." : "Guardar Todo"}
            </button>
          )}
        </div>
      </div>

      <div className="space-y-3 overflow-y-auto" style={{ maxHeight: "calc(100vh - 180px)" }}>
        <Section title="Inteligencia Artificial (Deepseek)" color="text-purple-400">
          {fields
            .filter((f) => f.category.startsWith("ai_"))
            .map((field) => (
              <ConfigRow
                key={field.name}
                field={field}
                editedValue={editedValues[field.name]}
                onChange={handleChange}
                onSave={saveField}
                onDelete={deleteField}
              />
            ))}
        </Section>

        <Section title="Huawei Cloud Credentials" color="text-terminal-green">
          {fields
            .filter((f) => f.category.startsWith("hwc_"))
            .map((field) => (
              <ConfigRow
                key={field.name}
                field={field}
                editedValue={editedValues[field.name]}
                onChange={handleChange}
                onSave={saveField}
                onDelete={deleteField}
              />
            ))}
        </Section>

        <Section title="SSH Configuration" color="text-terminal-cyan">
          {fields
            .filter((f) => f.category.startsWith("ssh_"))
            .map((field) => (
              <ConfigRow
                key={field.name}
                field={field}
                editedValue={editedValues[field.name]}
                onChange={handleChange}
                onSave={saveField}
                onDelete={deleteField}
              />
            ))}
        </Section>

        <Section title="Kubernetes / CCE Configuration" color="text-terminal-muted">
          {fields
            .filter((f) => f.category.startsWith("kube") || f.category.startsWith("helm"))
            .map((field) => (
              <ConfigRow
                key={field.name}
                field={field}
                editedValue={editedValues[field.name]}
                onChange={handleChange}
                onSave={saveField}
                onDelete={deleteField}
              />
            ))}
        </Section>
      </div>
    </div>
  );
}

function Section({ title, color, children }: { title: string; color: string; children: React.ReactNode }) {
  return (
    <div className="terminal-panel">
      <h3 className={`text-terminal-white text-xs font-bold mb-3 pb-2 border-b border-terminal-border flex items-center gap-2`}>
        <span className={color}>{">"}</span>
        {title}
      </h3>
      {children}
    </div>
  );
}

function ConfigRow({
  field,
  editedValue,
  onChange,
  onSave,
  onDelete,
}: {
  field: ConfigField;
  editedValue: string | undefined;
  onChange: (name: string, value: string) => void;
  onSave: (field: ConfigField) => void;
  onDelete: (field: ConfigField) => void;
}) {
  const currentValue = editedValue !== undefined ? editedValue : (field.configured ? "••••••••" : "");
  const hasEdit = editedValue !== undefined && editedValue !== field.value && editedValue !== "";

  return (
    <div className="flex items-center gap-3 py-2 border-b border-terminal-border/50 last:border-b-0">
      <div className="w-48 shrink-0">
        <div className="text-terminal-white text-xs font-bold">{field.label}</div>
        <div className="text-terminal-muted text-xs">{field.description}</div>
      </div>
      <div className="flex-1">
        <input
          type={field.sensitive ? "password" : "text"}
          value={currentValue}
          onChange={(e) => onChange(field.name, e.target.value)}
          placeholder={field.configured ? "••••••••" : `Ingrese ${field.label}...`}
          className="terminal-input w-full"
        />
      </div>
      <div className="flex items-center gap-2 shrink-0">
        {field.configured && (
          <span className="text-terminal-green text-xs w-5 text-center" title="Configurado">
            ✓
          </span>
        )}
        {!field.configured && <span className="text-terminal-muted text-xs w-5 text-center">-</span>}
        {hasEdit && (
          <button
            onClick={() => onSave(field)}
            className="terminal-btn-primary text-xs px-3 py-1"
          >
            Guardar
          </button>
        )}
        {field.configured && (
          <button
            onClick={() => onDelete(field)}
            className="terminal-btn-danger text-xs px-3 py-1"
          >
            Limpiar
          </button>
        )}
      </div>
    </div>
  );
}
