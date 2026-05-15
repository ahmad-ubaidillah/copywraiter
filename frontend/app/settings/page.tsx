"use client";

import { useState } from "react";
import AppLayout from "@/components/app-layout";
import { api } from "@/lib/api";

export default function SettingsPage() {
  const [provider, setProvider] = useState("openai");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("gpt-4o");
  const [replizKey, setReplizKey] = useState("");
  const [tgUrl, setTgUrl] = useState("");
  const [tgChatId, setTgChatId] = useState("");
  const [discordUrl, setDiscordUrl] = useState("");
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const save = async () => {
    setError(null);
    setSaved(false);
    try {
      await api.post("/api/config/ai?user_id=default", { provider, api_key: apiKey, model });
      await api.post("/api/config/distribution?user_id=default", { repliz_api_key: replizKey });
      await api.post("/api/config/notifications?user_id=default", {
        telegram_url: tgUrl || undefined,
        telegram_chat_id: tgChatId || undefined,
        discord_url: discordUrl || undefined,
      });
      setSaved(true);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Save failed");
    }
  };

  const testAi = async () => {
    try {
      await api.post("/api/config/ai/test", { provider, api_key: apiKey, model });
      setSaved(true);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Test failed");
    }
  };

  return (
    <AppLayout>
      <div className="mx-auto max-w-3xl">
        <h1 className="mb-6 text-2xl font-bold">Settings</h1>

        {saved && (
          <div className="mb-4 rounded-md border border-[var(--success)] bg-green-50 p-3 text-sm text-[var(--success)]">
            Settings saved successfully.
          </div>
        )}
        {error && (
          <div className="mb-4 rounded-md border border-[var(--danger)] bg-red-50 p-3 text-sm text-[var(--danger)]">
            {error}
          </div>
        )}

        <div className="space-y-6">
          <section className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-6">
            <h2 className="mb-4 text-lg font-semibold">AI Provider</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium">Provider</label>
                <select value={provider} onChange={(e) => setProvider(e.target.value)} className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm">
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Model</label>
                <input value={model} onChange={(e) => setModel(e.target.value)} className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm" />
              </div>
              <div className="sm:col-span-2">
                <label className="mb-1 block text-sm font-medium">API Key</label>
                <input type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder="sk-..." className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm" />
              </div>
            </div>
            <button onClick={testAi} className="mt-4 rounded-md border border-[var(--border)] px-4 py-2 text-sm font-medium hover:bg-[var(--muted)]">
              Test Connection
            </button>
          </section>

          <section className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-6">
            <h2 className="mb-4 text-lg font-semibold">Distribution (Repliz)</h2>
            <div>
              <label className="mb-1 block text-sm font-medium">Repliz API Key</label>
              <input type="password" value={replizKey} onChange={(e) => setReplizKey(e.target.value)} placeholder="repliz_..." className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm" />
            </div>
          </section>

          <section className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-6">
            <h2 className="mb-4 text-lg font-semibold">Notifications</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium">Telegram Bot URL</label>
                <input value={tgUrl} onChange={(e) => setTgUrl(e.target.value)} placeholder="https://api.telegram.org/bot..." className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Telegram Chat ID</label>
                <input value={tgChatId} onChange={(e) => setTgChatId(e.target.value)} className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm" />
              </div>
              <div className="sm:col-span-2">
                <label className="mb-1 block text-sm font-medium">Discord Webhook URL</label>
                <input value={discordUrl} onChange={(e) => setDiscordUrl(e.target.value)} placeholder="https://discord.com/api/webhooks/..." className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm" />
              </div>
            </div>
          </section>

          <button onClick={save} className="rounded-md bg-[var(--primary)] px-6 py-2 text-sm font-medium text-[var(--primary-foreground)] hover:opacity-90">
            Save All Settings
          </button>
        </div>
      </div>
    </AppLayout>
  );
}
