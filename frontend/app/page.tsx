"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AppLayout from "@/components/app-layout";
import { api } from "@/lib/api";

interface HealthResponse {
  status: string;
}

interface StatsCard {
  label: string;
  value: string | number;
  color: string;
  href: string;
}

export default function Dashboard() {
  const [status, setStatus] = useState<string>("checking");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<HealthResponse>("/health")
      .then((r) => setStatus(r.status))
      .catch(() => setStatus("error"))
      .finally(() => setLoading(false));
  }, []);

  const cards: StatsCard[] = [
    { label: "API Status", value: loading ? "..." : status, color: status === "ok" ? "var(--success)" : "var(--danger)", href: "/settings" },
    { label: "Drafts", value: "0", color: "var(--primary)", href: "/drafts" },
    { label: "Scheduled", value: "0", color: "var(--warning)", href: "/calendar" },
    { label: "Published", value: "0", color: "var(--success)", href: "/drafts" },
  ];

  return (
    <AppLayout>
      <div className="mx-auto max-w-5xl">
        <div className="mb-8">
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-[var(--muted-foreground)]">Autonomous Research & Copywriting Agent v1.5</p>
        </div>

        <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {cards.map((card) => (
            <Link
              key={card.label}
              href={card.href}
              className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-5 transition-shadow hover:shadow-md"
            >
              <p className="text-sm text-[var(--muted-foreground)]">{card.label}</p>
              <p className="mt-1 text-2xl font-bold" style={{ color: card.color }}>
                {card.value}
              </p>
            </Link>
          ))}
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-6">
            <h2 className="mb-4 text-lg font-semibold">Quick Actions</h2>
            <div className="flex flex-col gap-2">
              <Link href="/create" className="rounded-md bg-[var(--primary)] px-4 py-2 text-center text-sm font-medium text-[var(--primary-foreground)] transition-opacity hover:opacity-90">
                Generate Content
              </Link>
              <Link href="/calendar" className="rounded-md border border-[var(--border)] px-4 py-2 text-center text-sm font-medium transition-colors hover:bg-[var(--muted)]">
                View Calendar
              </Link>
              <Link href="/trends" className="rounded-md border border-[var(--border)] px-4 py-2 text-center text-sm font-medium transition-colors hover:bg-[var(--muted)]">
                Explore Trends
              </Link>
            </div>
          </div>

          <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-6">
            <h2 className="mb-4 text-lg font-semibold">Recent Activity</h2>
            <p className="text-sm text-[var(--muted-foreground)]">No activity yet. Start by generating your first content.</p>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
