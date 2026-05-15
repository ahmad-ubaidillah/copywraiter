"use client";

import { useEffect, useRef, useState } from "react";
import AppLayout from "@/components/app-layout";
import { api } from "@/lib/api";

interface LogEntry {
  timestamp: string;
  step: string;
  status: string;
  message: string;
}

export default function AgentLogPage() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [autoScroll, setAutoScroll] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetch = () => {
      api.get<{ log: LogEntry[] }>("/api/agent-log/?limit=200")
        .then((r) => setLogs(r.log))
        .catch(() => {});
    };
    fetch();
    const interval = setInterval(fetch, 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (autoScroll) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs, autoScroll]);

  const statusColor = (s: string) => {
    switch (s) {
      case "success": return "text-[var(--success)]";
      case "error": return "text-[var(--danger)]";
      default: return "text-[var(--muted-foreground)]";
    }
  };

  return (
    <AppLayout>
      <div className="mx-auto max-w-4xl">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold">Agent Thinking Log</h1>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={autoScroll} onChange={(e) => setAutoScroll(e.target.checked)} />
            Auto-scroll
          </label>
        </div>

        <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-4 font-mono text-xs">
          {logs.length === 0 ? (
            <p className="text-[var(--muted-foreground)]">Waiting for agent activity...</p>
          ) : (
            logs.map((entry, i) => (
              <div key={i} className="border-b border-[var(--border)] py-2 last:border-0">
                <span className="text-[var(--muted-foreground)]">{new Date(entry.timestamp).toLocaleTimeString()}</span>
                {" "}
                <span className={`font-semibold ${statusColor(entry.status)}`}>[{entry.step}]</span>
                {" "}
                <span>{entry.message}</span>
              </div>
            ))
          )}
          <div ref={bottomRef} />
        </div>
      </div>
    </AppLayout>
  );
}
