"use client";

import { useState, useEffect } from "react";

interface Props {
  onLog: (message: string) => void;
}

const PRESET_CATEGORIES = [
  { value: "hwc_access_key", label: "Access Key (AK)" },
  { value: "hwc_secret_key", label: "Secret Key (SK)" },
  { value: "hwc_region", label: "Region" },
  { value: "hwc_project_id", label: "Project ID" },
  { value: "ssh_private_key", label: "SSH Private Key" },
  { value: "ssh_username", label: "SSH Username" },
];

export default function SecretsPanel({ onLog }: Props) {
  const [secrets, setSecrets] = useState<
    { id: string; name: string; category: string; created_at: string }[]
  >([]);
  const [name, setName] = useState("");
  const [category, setCategory] = useState(PRESET_CATEGORIES[0].value);
  const [value, setValue] = useState("");
  const [loading, setLoading] = useState(false);

  const fetchSecrets = async () => {
    try {
      const res = await fetch("/api/secrets");
      const data = await res.json();
      setSecrets(data.secrets || []);
    } catch {
      onLog("Error fetching secrets");
    }
  };

  useEffect(() => {
    fetchSecrets();
  }, []);

  const saveSecret = async () => {
    if (!name.trim() || !value.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(
        `/api/secrets?name=${encodeURIComponent(name)}&category=${encodeURIComponent(category)}&value=${encodeURIComponent(value)}`,
        { method: "POST" }
      );
      const data = await res.json();
      onLog(`Secret stored: ${data.name} (${data.category})`);
      setName("");
      setValue("");
      fetchSecrets();
    } catch (err) {
      onLog(`Error: ${err instanceof Error ? err.message : "unknown"}`);
    } finally {
      setLoading(false);
    }
  };

  const deleteSecret = async (secretName: string) => {
    try {
      await fetch(`/api/secrets/${encodeURIComponent(secretName)}`, {
        method: "DELETE",
      });
      onLog(`Secret deleted: ${secretName}`);
      fetchSecrets();
    } catch (err) {
      onLog(`Error: ${err instanceof Error ? err.message : "unknown"}`);
    }
  };

  return (
    <div className="h-full p-4 flex gap-4">
      <div className="flex-1 terminal-panel">
        <h2 className="text-terminal-cyan text-sm font-bold mb-3 pb-2 border-b border-terminal-border">
          Stored Secrets (Encrypted)
        </h2>
        {secrets.length === 0 ? (
          <p className="text-terminal-muted text-sm italic py-8 text-center">
            No secrets stored yet.
          </p>
        ) : (
          <div className="space-y-2">
            {secrets.map((s) => (
              <div
                key={s.id}
                className="flex items-center justify-between py-2 px-3 bg-terminal-bg rounded border border-terminal-border text-xs"
              >
                <div className="flex items-center gap-3">
                  <span className="text-terminal-white font-bold">
                    {s.name}
                  </span>
                  <span className="text-terminal-muted">
                    {s.category}
                  </span>
                  <span className="text-terminal-muted text-opacity-50">
                    {new Date(s.created_at).toLocaleDateString()}
                  </span>
                </div>
                <button
                  onClick={() => deleteSecret(s.name)}
                  className="terminal-btn-danger text-xs px-2 py-1"
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="w-80 terminal-panel">
        <h2 className="text-terminal-cyan text-sm font-bold mb-3 pb-2 border-b border-terminal-border">
          Add Secret
        </h2>
        <div className="space-y-3">
          <div>
            <label className="text-terminal-muted text-xs block mb-1">
              Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="my-hwc-key"
              className="terminal-input w-full"
            />
          </div>
          <div>
            <label className="text-terminal-muted text-xs block mb-1">
              Category
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="terminal-input w-full"
            >
              {PRESET_CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-terminal-muted text-xs block mb-1">
              Value
            </label>
            <input
              type="password"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder="••••••••"
              className="terminal-input w-full"
            />
          </div>
          <button
            onClick={saveSecret}
            disabled={loading || !name.trim() || !value.trim()}
            className="terminal-btn-primary w-full"
          >
            {loading ? "Encrypting..." : "Store (Encrypted)"}
          </button>
        </div>
        <p className="text-terminal-muted text-xs mt-4 leading-relaxed">
          Values are encrypted with Fernet (AES-128) before storage. The
          encryption key is kept in environment variables.
        </p>
      </div>
    </div>
  );
}
