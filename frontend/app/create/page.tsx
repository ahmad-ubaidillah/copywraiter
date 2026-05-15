"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/app-layout";
import { api } from "@/lib/api";

const FRAMEWORKS = ["Auto", "AIDA", "PAS", "BAB", "FAB", "THE_4_CS"];
const HOOKS = ["Auto", "Negative", "Statistical", "Curiosity", "Authority", "Question-Based"];
const LANGUAGES = [
  { value: "en", label: "English" },
  { value: "id_formal", label: "Indonesian (Formal)" },
  { value: "id_casual", label: "Indonesian (Casual/Gaul)" },
];

interface PlatformPreset {
  id: string;
  name: string;
  max_chars: number;
  hashtags: boolean;
  emoji_policy: string;
  recommended_length: string;
}

interface Variation {
  variation: string;
  content: string;
  chars: number;
  framework: string;
  hook_type: string;
}

export default function CreatePage() {
  const [topic, setTopic] = useState("");
  const [platform, setPlatform] = useState("linkedin");
  const [framework, setFramework] = useState("Auto");
  const [hook, setHook] = useState("Auto");
  const [language, setLanguage] = useState("en");
  const [platforms, setPlatforms] = useState<PlatformPreset[]>([]);
  const [loading, setLoading] = useState(false);
  const [variations, setVariations] = useState<Variation[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<{ platforms: PlatformPreset[] }>("/api/platforms/")
      .then((r) => setPlatforms(r.platforms))
      .catch(() => {});
  }, []);

  const selectedPlatform = platforms.find((p) => p.id === platform);

  const generate = async () => {
    if (!topic.trim()) return;
    setLoading(true);
    setError(null);
    setVariations([]);
    try {
      const fw = framework === "Auto" ? undefined : framework;
      const hk = hook === "Auto" ? undefined : hook;
      const result = await api.post<{
        strategy: { framework: string; hook_type: string };
        generation: { content: string; chars: number };
        variations?: Variation[];
      }>("/api/workflow/run", {
        topic,
        platform,
        language,
        user_id: "default",
      });
      setVariations([
        {
          variation: "A",
          content: result.generation.content,
          chars: result.generation.chars,
          framework: result.strategy.framework,
          hook_type: result.strategy.hook_type,
        },
      ]);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Generation failed");
    }
    setLoading(false);
  };

  return (
    <AppLayout>
      <div className="mx-auto max-w-4xl">
        <h1 className="mb-6 text-2xl font-bold">Create Content</h1>

        <div className="mb-6 grid gap-4 rounded-lg border border-[var(--border)] bg-[var(--card)] p-6 sm:grid-cols-2 lg:grid-cols-5">
          <div>
            <label className="mb-1 block text-sm font-medium">Platform</label>
            <select value={platform} onChange={(e) => setPlatform(e.target.value)} className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm">
              {platforms.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Topic</label>
            <input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Enter topic..."
              className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Framework</label>
            <select value={framework} onChange={(e) => setFramework(e.target.value)} className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm">
              {FRAMEWORKS.map((f) => <option key={f} value={f}>{f}</option>)}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Hook</label>
            <select value={hook} onChange={(e) => setHook(e.target.value)} className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm">
              {HOOKS.map((h) => <option key={h} value={h}>{h}</option>)}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Language</label>
            <select value={language} onChange={(e) => setLanguage(e.target.value)} className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm">
              {LANGUAGES.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}
            </select>
          </div>
        </div>

        {selectedPlatform && (
          <div className="mb-4 flex gap-4 text-xs text-[var(--muted-foreground)]">
            <span>Max: {selectedPlatform.max_chars.toLocaleString()} chars</span>
            <span>{selectedPlatform.hashtags ? "Hashtags OK" : "No hashtags"}</span>
            <span>Emoji: {selectedPlatform.emoji_policy}</span>
            <span>Recommended: {selectedPlatform.recommended_length}</span>
          </div>
        )}

        <button
          onClick={generate}
          disabled={loading || !topic.trim()}
          className="mb-6 rounded-md bg-[var(--primary)] px-6 py-2 text-sm font-medium text-[var(--primary-foreground)] transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {loading ? "Generating..." : "Generate"}
        </button>

        {error && (
          <div className="mb-6 rounded-md border border-[var(--danger)] bg-red-50 p-4 text-sm text-[var(--danger)]">
            {error}
          </div>
        )}

        {variations.length > 0 && (
          <div className="space-y-4">
            {variations.map((v) => (
              <div key={v.variation} className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-6">
                <div className="mb-3 flex items-center justify-between">
                  <span className="rounded bg-[var(--primary)] px-2 py-0.5 text-xs font-medium text-[var(--primary-foreground)]">
                    Variation {v.variation}
                  </span>
                  <span className="text-xs text-[var(--muted-foreground)]">
                    {v.framework} + {v.hook_type} · {v.chars} chars
                  </span>
                </div>
                <textarea
                  defaultValue={v.content}
                  rows={8}
                  className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm"
                />
              </div>
            ))}
          </div>
        )}
      </div>
    </AppLayout>
  );
}
