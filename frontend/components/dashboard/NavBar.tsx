"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/",           label: "Command Center" },
  { href: "/evaluation", label: "Evaluation" },
  { href: "/cases",      label: "Risk Queue"    },
];

export function NavBar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-30 border-b border-border bg-bg-secondary/90 backdrop-blur-md">
      <div className="max-w-screen-2xl mx-auto px-6 h-14 flex items-center gap-8">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-2.5 shrink-0">
          <span className="w-6 h-6 rounded bg-ai flex items-center justify-center text-white text-xs font-bold">
            KP
          </span>
          <span className="font-semibold text-text-primary tracking-tight">KhaataPulse</span>
          <span className="text-xs text-text-muted font-mono border border-border px-1 rounded">
            v1.0
          </span>
        </Link>

        {/* Nav */}
        <nav className="flex items-center gap-1">
          {NAV_ITEMS.map(({ href, label }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={`
                  px-3 py-1.5 rounded text-sm font-medium transition-colors
                  ${active
                    ? "bg-surface text-text-primary"
                    : "text-text-muted hover:text-text-secondary hover:bg-surface/50"
                  }
                `}
              >
                {label}
              </Link>
            );
          })}
        </nav>

        {/* Status pill */}
        <div className="ml-auto flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-recovery animate-pulse-glow" />
          <span className="text-xs text-text-muted mono">LIVE</span>
        </div>
      </div>
    </header>
  );
}
