"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/app-layout";
import { api } from "@/lib/api";

interface CalendarData {
  calendar: Record<string, Array<{
    id: string;
    title: string;
    content: string;
    status: string;
    scheduled_at: string | null;
    platform: string;
  }>>;
}

export default function CalendarPage() {
  const [calendar, setCalendar] = useState<CalendarData["calendar"]>({});
  const [loading, setLoading] = useState(true);
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());

  useEffect(() => {
    api.get<CalendarData>(`/api/calendar/?user_id=default&month=${month}&year=${year}`)
      .then((r) => setCalendar(r.calendar))
      .catch(() => setCalendar({}))
      .finally(() => setLoading(false));
  }, [month, year]);

  const daysInMonth = new Date(year, month, 0).getDate();
  const firstDay = new Date(year, month - 1, 1).getDay();
  const days = Array.from({ length: daysInMonth }, (_, i) => i + 1);
  const blanks = Array.from({ length: firstDay }, (_, i) => i);

  const statusColor = (s: string) => {
    switch (s) {
      case "published": return "var(--success)";
      case "scheduled": return "var(--warning)";
      case "draft": return "var(--muted-foreground)";
      default: return "var(--muted-foreground)";
    }
  };

  return (
    <AppLayout>
      <div className="mx-auto max-w-5xl">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold">Content Calendar</h1>
          <div className="flex gap-2">
            <button onClick={() => setMonth((m) => (m <= 1 ? 12 : m - 1))} className="rounded-md border border-[var(--border)] px-3 py-1 text-sm hover:bg-[var(--muted)]">←</button>
            <span className="flex items-center text-sm font-medium">{new Date(year, month - 1).toLocaleString("en", { month: "long", year: "numeric" })}</span>
            <button onClick={() => setMonth((m) => (m >= 12 ? 1 : m + 1))} className="rounded-md border border-[var(--border)] px-3 py-1 text-sm hover:bg-[var(--muted)]">→</button>
          </div>
        </div>

        {loading ? (
          <p className="text-sm text-[var(--muted-foreground)]">Loading...</p>
        ) : (
          <div className="grid grid-cols-7 gap-1">
            {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((d) => (
              <div key={d} className="py-2 text-center text-xs font-medium text-[var(--muted-foreground)]">{d}</div>
            ))}
            {blanks.map((b) => <div key={`b-${b}`} />)}
            {days.map((day) => {
              const key = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
              const posts = calendar[key] || [];
              return (
                <div key={day} className="min-h-20 rounded-md border border-[var(--border)] bg-[var(--card)] p-1">
                  <span className="text-xs font-medium">{day}</span>
                  {posts.map((p) => (
                    <div key={p.id} className="mt-1 truncate rounded bg-[var(--muted)] px-1 py-0.5 text-[10px]" style={{ borderLeft: `2px solid ${statusColor(p.status)}` }}>
                      {p.title || "Untitled"}
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </AppLayout>
  );
}
