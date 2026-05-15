"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "Dashboard", icon: "📊" },
  { href: "/create", label: "Create", icon: "✏️" },
  { href: "/calendar", label: "Calendar", icon: "📅" },
  { href: "/drafts", label: "Drafts", icon: "📝" },
  { href: "/trends", label: "Trends", icon: "📈" },
  { href: "/log", label: "Agent Log", icon: "🤖" },
  { href: "/settings", label: "Settings", icon: "⚙️" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-full w-56 border-r border-[var(--border)] bg-[var(--card)] p-4">
      <Link href="/" className="mb-6 block text-xl font-bold text-[var(--primary)]">
        copywrAIter
      </Link>
      <nav className="flex flex-col gap-1">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors ${
              pathname === item.href
                ? "bg-[var(--primary)] text-[var(--primary-foreground)]"
                : "text-[var(--muted-foreground)] hover:bg-[var(--muted)]"
            }`}
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>
    </aside>
  );
}
