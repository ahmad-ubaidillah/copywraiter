"use client";

import { useState } from "react";
import AppLayout from "@/components/app-layout";
import { api } from "@/lib/api";

interface TrendResult {
  keyword: string;
  score: number;
  sources: Array<{ source: string; posts_count: number; volume: number }>;
}

export default function TrendsPage() {
  const [keyword, setKeyword] = useState("AI");
  const [result, setResult] = useState<TrendResult | null>(null);
  const [loading, setLoading] = useState(false);

  const search = async () => {
    setLoading(true);
    try {
      const r = await api.post<TrendResult>("/api/research/trends", { keyword });
      setResult(r);
    } catch {
      setResult(null);
    }
    setLoading(false);
  };

  return (
    <AppLayout>
      <div className="mx-auto max-w-4xl">
        <h1 className="mb-6 text-2xl font-bold">Trends</h1>

        <div className="mb-6 flex gap-2">
          <input
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && search()}
            placeholder="Search keyword..."
            className="flex-1 rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm"
          />
          <button
            onClick={search}
            disabled={loading}
            className="rounded-md bg-[var(--primary)] px-4 py-2 text-sm font-medium text-[var(--primary-foreground)] hover:opacity-90 disabled:opacity-50"
          >
            {loading ? "Searching..." : "Search"}
          </button>
        </div>

        {result && (
          <div className="space-y-4">
            <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-6">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">{result.keyword}</h2>
                <span className="rounded bg-[var(--primary)] px-3 py-1 text-sm font-medium text-[var(--primary-foreground)]">
                  Score: {result.score}
                </span>
              </div>
              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                {result.sources.map((s) => (
                  <div key={s.source} className="rounded-md bg-[var(--muted)] p-3">
                    <p className="text-sm font-medium capitalize">{s.source.replace("_", " ")}</p>
                    <p className="text-xs text-[var(--muted-foreground)]">
                      {s.posts_count} posts · vol: {s.volume}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
