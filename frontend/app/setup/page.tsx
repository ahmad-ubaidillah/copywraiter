"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

const steps = ["AI Provider", "Distribution", "Language", "Style", "Done"];

interface ProviderPreset {
  id: string;
  name: string;
  base_url: string;
  example_models: string[];
}

export default function SetupPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [providers, setProviders] = useState<ProviderPreset[]>([]);
  const [form, setForm] = useState({
    provider: "openai",
    apiKey: "",
    model: "gpt-4o",
    baseUrl: "",
    replizAccessKey: "",
    replizSecretKey: "",
    replizBaseUrl: "",
    language: "en",
    styleText: "",
  });

  useEffect(() => {
    api.get<{ providers: ProviderPreset[] }>("/api/config/ai/providers")
      .then((r) => setProviders(r.providers))
      .catch(() => {});
  }, []);

  const selectProvider = (id: string) => {
    const preset = providers.find((p) => p.id === id);
    setForm((f) => ({
      ...f,
      provider: id,
      baseUrl: preset?.base_url || "",
      model: preset?.example_models?.[0] || f.model,
    }));
  };

  const update = (field: string, value: string) => setForm((f) => ({ ...f, [field]: value }));

  const testConnection = async () => {
    setLoading(true);
    setResult(null);
    try {
      await api.post("/api/config/ai/test", {
        provider: form.provider,
        api_key: form.apiKey,
        model: form.model,
        base_url: form.baseUrl || undefined,
      });
      setResult("Connection successful!");
    } catch (e: unknown) {
      setResult(`Failed: ${e instanceof Error ? e.message : "Unknown error"}`);
    }
    setLoading(false);
  };

  const saveAiConfig = async () => {
    setLoading(true);
    try {
      await api.post("/api/config/ai?user_id=default", {
        provider: form.provider,
        api_key: form.apiKey,
        model: form.model,
        base_url: form.baseUrl,
      });
      setStep(1);
    } catch (e: unknown) {
      setResult(`Failed: ${e instanceof Error ? e.message : "Unknown error"}`);
    }
    setLoading(false);
  };

  const saveDistribution = async () => {
    setLoading(true);
    try {
      await api.post("/api/config/distribution?user_id=default", {
        repliz_access_key: form.replizAccessKey,
        repliz_secret_key: form.replizSecretKey,
        repliz_base_url: form.replizBaseUrl,
      });
      setStep(2);
    } catch (e: unknown) {
      setResult(`Failed: ${e instanceof Error ? e.message : "Unknown error"}`);
    }
    setLoading(false);
  };

  const saveLanguage = async () => {
    setStep(3);
  };

  const saveStyle = async () => {
    if (form.styleText.trim()) {
      try {
        await api.post("/api/style/save?user_id=default", { text: form.styleText });
      } catch {
      }
    }
    setStep(4);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--background)] p-6">
      <div className="w-full max-w-lg">
        <h1 className="mb-2 text-center text-2xl font-bold text-[var(--primary)]">copywrAIter</h1>
        <p className="mb-6 text-center text-sm text-[var(--muted-foreground)]">Setup Wizard — Step {step + 1} of {steps.length}</p>

        <div className="mb-6 flex gap-1">
          {steps.map((s, i) => (
            <div
              key={s}
              className={`h-1 flex-1 rounded ${i <= step ? "bg-[var(--primary)]" : "bg-[var(--border)]"}`}
            />
          ))}
        </div>

        <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-6">
          {step === 0 && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold">AI Provider Configuration</h2>
              <div>
                <label className="mb-1 block text-sm font-medium">Provider</label>
                <select
                  value={form.provider}
                  onChange={(e) => selectProvider(e.target.value)}
                  className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm"
                >
                  <optgroup label="Built-in">
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic</option>
                  </optgroup>
                  <optgroup label="Hermes-compatible (OpenAI-compatible API)">
                    {providers
                      .filter((p) => !["openai", "anthropic", "custom"].includes(p.id))
                      .map((p) => (
                        <option key={p.id} value={p.id}>{p.name}</option>
                      ))}
                  </optgroup>
                  <option value="custom">Custom Endpoint</option>
                </select>
              </div>
              {(form.provider === "custom" || (providers.find(p => p.id === form.provider)?.base_url === "")) && (
                <div>
                  <label className="mb-1 block text-sm font-medium">Base URL</label>
                  <input
                    type="text"
                    value={form.baseUrl}
                    onChange={(e) => update("baseUrl", e.target.value)}
                    placeholder="https://api.example.com/v1"
                    className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm"
                  />
                </div>
              )}
              <div>
                <label className="mb-1 block text-sm font-medium">API Key</label>
                <input
                  type="password"
                  value={form.apiKey}
                  onChange={(e) => update("apiKey", e.target.value)}
                  placeholder="sk-..."
                  className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Model</label>
                <input
                  type="text"
                  value={form.model}
                  onChange={(e) => update("model", e.target.value)}
                  className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Base URL (optional)</label>
                <input
                  type="text"
                  value={form.baseUrl}
                  onChange={(e) => update("baseUrl", e.target.value)}
                  placeholder="https://api.openai.com/v1"
                  className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={testConnection}
                  disabled={loading || !form.apiKey}
                  className="rounded-md border border-[var(--border)] px-4 py-2 text-sm font-medium transition-colors hover:bg-[var(--muted)] disabled:opacity-50"
                >
                  {loading ? "Testing..." : "Test Connection"}
                </button>
                <button
                  onClick={saveAiConfig}
                  disabled={loading || !form.apiKey}
                  className="flex-1 rounded-md bg-[var(--primary)] px-4 py-2 text-sm font-medium text-[var(--primary-foreground)] transition-opacity hover:opacity-90 disabled:opacity-50"
                >
                  Save & Continue
                </button>
              </div>
              {result && (
                <p className={`text-sm ${result.startsWith("Connection") ? "text-[var(--success)]" : "text-[var(--danger)]"}`}>
                  {result}
                </p>
              )}
            </div>
          )}

          {step === 1 && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold">Distribution (Repliz API)</h2>
              <div className="space-y-3">
                <div>
                  <label className="mb-1 block text-sm font-medium">Access Key</label>
                  <input
                    type="password"
                    value={form.replizAccessKey}
                    onChange={(e) => update("replizAccessKey", e.target.value)}
                    placeholder="9221167021"
                    className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium">Secret Key</label>
                  <input
                    type="password"
                    value={form.replizSecretKey}
                    onChange={(e) => update("replizSecretKey", e.target.value)}
                    placeholder="c1nNqv..."
                    className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium">Repliz Base URL (optional)</label>
                  <input
                    type="text"
                    value={form.replizBaseUrl}
                    onChange={(e) => update("replizBaseUrl", e.target.value)}
                    placeholder="https://api.repliz.com"
                    className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm"
                  />
                </div>
              </div>
              <button
                onClick={saveDistribution}
                disabled={loading}
                className="w-full rounded-md bg-[var(--primary)] px-4 py-2 text-sm font-medium text-[var(--primary-foreground)] transition-opacity hover:opacity-90 disabled:opacity-50"
              >
                {loading ? "Saving..." : "Save & Continue"}
              </button>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold">Language Selection</h2>
              <select
                value={form.language}
                onChange={(e) => update("language", e.target.value)}
                className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm"
              >
                <option value="en">English</option>
                <option value="id_formal">Indonesian (Formal)</option>
                <option value="id_casual">Indonesian (Casual/Gaul)</option>
                <option value="custom">Custom</option>
              </select>
              <button
                onClick={saveLanguage}
                className="w-full rounded-md bg-[var(--primary)] px-4 py-2 text-sm font-medium text-[var(--primary-foreground)] transition-opacity hover:opacity-90"
              >
                Continue
              </button>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold">Style Reference</h2>
              <p className="text-sm text-[var(--muted-foreground)]">
                Paste existing content to analyze your writing style.
              </p>
              <textarea
                value={form.styleText}
                onChange={(e) => update("styleText", e.target.value)}
                rows={6}
                placeholder="Paste your existing posts here..."
                className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm"
              />
              <button
                onClick={saveStyle}
                className="w-full rounded-md bg-[var(--primary)] px-4 py-2 text-sm font-medium text-[var(--primary-foreground)] transition-opacity hover:opacity-90"
              >
                Continue
              </button>
            </div>
          )}

          {step === 4 && (
            <div className="space-y-4 text-center">
              <h2 className="text-lg font-semibold text-[var(--success)]">Setup Complete!</h2>
              <p className="text-sm text-[var(--muted-foreground)]">
                Your copywrAIter instance is ready. Start creating content.
              </p>
              <button
                onClick={() => router.push("/")}
                className="w-full rounded-md bg-[var(--primary)] px-4 py-2 text-sm font-medium text-[var(--primary-foreground)] transition-opacity hover:opacity-90"
              >
                Go to Dashboard
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
