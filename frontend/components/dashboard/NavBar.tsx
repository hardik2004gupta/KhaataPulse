"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

const NAV_ITEMS = [
  { href: "/", label: "Overview" },
  { href: "/dashboard", label: "Command Center" },
  { href: "/cases", label: "Risk Queue" },
  { href: "/evaluation", label: "Evaluations" },
] as const;

function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function NavBar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  // Collapse the mobile sheet whenever the route changes.
  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  return (
    <header
      className="sticky top-0 z-nav border-b border-border/60 backdrop-blur-xl"
      style={{ backgroundColor: "rgba(7,9,13,0.85)" }}
    >
      <div className="mx-auto flex h-16 max-w-shell items-center gap-6 px-5 sm:px-8 lg:gap-10">
        {/* ── Brand ─────────────────────────────────────────────────────── */}
        <Link href="/" className="group flex shrink-0 items-baseline gap-3">
          <span className="text-[15px] font-semibold tracking-tightest text-text-primary">
            KhaataPulse
          </span>
          <span className="mono hidden text-[10px] uppercase tracking-eyebrow text-text-muted transition-colors duration-base group-hover:text-text-secondary lg:inline">
            Revenue Intelligence
          </span>
        </Link>

        {/* ── Desktop nav ───────────────────────────────────────────────── */}
        <nav className="hidden items-center gap-1 md:flex" aria-label="Primary">
          {NAV_ITEMS.map(({ href, label }) => {
            const active = isActive(pathname, href);
            return (
              <Link
                key={href}
                href={href}
                aria-current={active ? "page" : undefined}
                className={`rounded px-3 py-1.5 text-[13px] font-medium transition-colors duration-base ${
                  active
                    ? "text-text-primary"
                    : "text-text-muted hover:text-text-primary"
                }`}
              >
                {label}
              </Link>
            );
          })}
        </nav>

        {/* ── Desktop CTA ───────────────────────────────────────────────── */}
        <div className="ml-auto hidden items-center lg:flex">
          <Link
            href="/dashboard"
            className="mono rounded border border-ai/40 px-3.5 py-1.5 text-[10px] uppercase tracking-eyebrow text-ai-text transition-colors duration-base hover:border-ai hover:bg-ai/10 hover:text-text-primary"
          >
            Open Command Center →
          </Link>
        </div>

        {/* ── Mobile toggle ─────────────────────────────────────────────── */}
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          aria-controls="mobile-nav"
          aria-label={open ? "Close navigation" : "Open navigation"}
          className="ml-auto flex h-9 w-9 items-center justify-center rounded border border-border text-text-secondary transition-colors duration-base hover:text-text-primary md:hidden"
        >
          <span className="relative block h-3 w-4">
            <span
              className={`absolute left-0 block h-px w-4 bg-current transition-transform duration-base ${
                open ? "top-1.5 rotate-45" : "top-0"
              }`}
            />
            <span
              className={`absolute left-0 top-1.5 block h-px w-4 bg-current transition-opacity duration-fast ${
                open ? "opacity-0" : "opacity-100"
              }`}
            />
            <span
              className={`absolute left-0 block h-px w-4 bg-current transition-transform duration-base ${
                open ? "top-1.5 -rotate-45" : "top-3"
              }`}
            />
          </span>
        </button>
      </div>

      {/* ── Mobile sheet ────────────────────────────────────────────────── */}
      <div
        id="mobile-nav"
        hidden={!open}
        className="border-t border-border/60 bg-bg-secondary/95 md:hidden"
      >
        <nav className="mx-auto flex max-w-shell flex-col px-5 py-3 sm:px-8" aria-label="Mobile">
          {NAV_ITEMS.map(({ href, label }) => {
            const active = isActive(pathname, href);
            return (
              <Link
                key={href}
                href={href}
                aria-current={active ? "page" : undefined}
                className={`border-b border-border-subtle py-3 text-sm transition-colors duration-base last:border-b-0 ${
                  active ? "text-text-primary" : "text-text-secondary"
                }`}
              >
                {label}
              </Link>
            );
          })}
          <Link
            href="/dashboard"
            className="mono mt-3 rounded border border-ai/40 px-3 py-2 text-center text-[10px] uppercase tracking-eyebrow text-ai-text"
          >
            Open Command Center →
          </Link>
        </nav>
      </div>
    </header>
  );
}
