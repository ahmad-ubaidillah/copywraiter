"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/app-layout";
import { api } from "@/lib/api";

interface Draft {
  id: string;
  title: string;
  content: string;
  source: string;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export default function DraftsPage() {
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "archived">("all");

  useEffect(() => {
    api.get<Draft[]>(`/drafts/?user_id=default&is_archived=${filter === "archived"}`)
      .then((r) => setDrafts(r))
      .catch(() => setDrafts([]))
      .finally(() => setLoading(false));
  }, [filter]);

  return (
    <AppLayout>
      <div className="mx-auto max-w-5xl">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold">Drafts</h1>
          <div className="flex gap-2">
            <button onClick={() => setFilter("all")} className={`rounded-md px-3 py-1 text-sm ${filter === "all" ? "bg-[var(--primary)] text-[var(--primary-foreground)]" : "border border-[var(--border)] hover:bg-[var(--muted)]"}`}>Active</button>
            <button onClick={() => setFilter("archived")} className={`rounded-md px-3 py-1 text-sm ${filter === "archived" ? "bg-[var(--primary)] text-[var(--primary-foreground)]" : "border border-[var(--border)] hover:bg-[var(--muted)]"}`}>Archived</button>
          </div>
        </div>

        {loading ? (
          <p className="text-sm text-[var(--muted-foreground)]">Loading...</p>
        ) : drafts.length === 0 ? (
          <p className="text-sm text-[var(--muted-foreground)]">No drafts found.</p>
        ) : (
          <div className="space-y-3">
            {drafts.map((d) => (
              <div key={d.id} className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-4">
                <div className="mb-2 flex items-center justify-between">
                  <h3 className="font-medium">{d.title || "Untitled"}</h3>
                  <span className="text-xs text-[var(--muted-foreground)]">{new Date(d.updated_at).toLocaleDateString()}</span>
                </div>
                <p className="truncate text-sm text-[var(--muted-foreground)]">{d.content}</p>
                <div className="mt-2 flex gap-2">
                  <span className="rounded bg-[var(--muted)] px-2 py-0.5 text-[10px]">{d.source}</span>
                  {d.is_archived && <span className="rounded bg-[var(--muted)] px-2 py-0.5 text-[10px]">archived</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppLayout>
  );
}
