"use client";

import Link from "next/link";
import { useEffect } from "react";
import { usePathname } from "next/navigation";

interface NavItem {
  href: string;
  label: string;
  /** Accent used for the active indicator — communicates the surface's domain. */
  tone: "recovery" | "warning" | "ai" | "neutral";
}

interface NavSection {
  label: string;
  items: NavItem[];
}

const SECTIONS: NavSection[] = [
  {
    label: "Command",
    items: [{ href: "/", label: "Overview", tone: "neutral" }],
  },
  {
    label: "Operations",
    items: [
      { href: "/dashboard", label: "Command Center", tone: "recovery" },
      { href: "/cases", label: "Risk Queue", tone: "warning" },
      { href: "/dashboard/time-machine", label: "Revenue Time Machine", tone: "ai" },
    ],
  },
  {
    label: "Evaluation",
    items: [
      { href: "/dashboard#policy", label: "Policy Comparison", tone: "recovery" },
      { href: "/evaluation", label: "Stress Test", tone: "ai" },
    ],
  },
  {
    label: "Governance",
    items: [{ href: "/dashboard#audit", label: "Audit Trail", tone: "neutral" }],
  },
];

const TONE_BAR: Record<NavItem["tone"], string> = {
  recovery: "bg-recovery",
  warning: "bg-warning",
  ai: "bg-ai",
  neutral: "bg-text-muted",
};

function isActive(pathname: string, href: string): boolean {
  // Hash links target a section of a page, never a route of their own.
  if (href.includes("#")) return false;
  if (href === "/") return pathname === "/";
  if (href === "/dashboard") return pathname === "/dashboard";
  return pathname === href || pathname.startsWith(`${href}/`);
}

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();

  return (
    <nav className="flex flex-col gap-6 py-5" aria-label="Command navigation">
      {SECTIONS.map((section) => (
        <div key={section.label}>
          <p className="mono px-4 pb-2 text-[9px] uppercase tracking-eyebrow text-text-faint">
            {section.label}
          </p>
          <ul className="flex flex-col">
            {section.items.map((item) => {
              const active = isActive(pathname, item.href);
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    onClick={onNavigate}
                    aria-current={active ? "page" : undefined}
                    className={`relative flex items-center py-2 pl-4 pr-3 text-[13px] transition-colors duration-base ${
                      active
                        ? "bg-surface/70 text-text-primary"
                        : "text-text-secondary hover:bg-surface/40 hover:text-text-primary"
                    }`}
                  >
                    <span
                      className={`absolute left-0 top-0 h-full w-0.5 transition-opacity duration-base ${
                        TONE_BAR[item.tone]
                      } ${active ? "opacity-100" : "opacity-0"}`}
                    />
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </nav>
  );
}

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

export function Sidebar({ open, onClose }: SidebarProps) {
  // Escape dismisses the mobile navigation sheet.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  return (
    <>
      {/* ── Desktop rail ──────────────────────────────────────────────────── */}
      <aside className="sticky top-12 hidden h-[calc(100vh-3rem)] w-[220px] shrink-0 flex-col justify-between border-r border-border/60 bg-bg-secondary/40 lg:flex">
        <NavLinks />
        <div className="mono border-t border-border-subtle px-4 py-3 text-[9px] uppercase tracking-eyebrow text-text-faint">
          v1.0 · MVP
        </div>
      </aside>

      {/* ── Mobile / tablet sheet ─────────────────────────────────────────── */}
      {open && (
        <div
          className="fixed inset-0 z-overlay bg-bg-primary/70 backdrop-blur-sm lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}
      {/* `invisible` while closed keeps the off-screen links out of the tab
         order — an aria-hidden container must never hold focusable children. */}
      <aside
        className={`fixed left-0 top-12 z-drawer flex h-[calc(100vh-3rem)] w-[220px] flex-col justify-between border-r border-border bg-bg-secondary transition-transform duration-base ease-out lg:hidden ${
          open ? "visible translate-x-0" : "invisible -translate-x-full"
        }`}
        aria-hidden={!open}
      >
        <NavLinks onNavigate={onClose} />
        <div className="mono border-t border-border-subtle px-4 py-3 text-[9px] uppercase tracking-eyebrow text-text-faint">
          v1.0 · MVP
        </div>
      </aside>
    </>
  );
}
