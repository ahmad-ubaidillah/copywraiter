import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "copywrAIter — Autonomous Research & Copywriting Agent",
  description: "AI-powered content lifecycle automation",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
        {children}
      </body>
    </html>
  );
}
