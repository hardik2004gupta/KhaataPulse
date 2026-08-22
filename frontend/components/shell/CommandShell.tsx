"use client";

import React, { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import type { EvaluationRunResult } from "@/lib/types";
import { TopBar } from "./TopBar";
import { Sidebar } from "./Sidebar";

interface CommandShellProps {
  children: React.ReactNode;
  /** Drives the run-context readout in the top bar. */
  evalResult?: EvaluationRunResult | null;
}

/**
 * Application frame for every operational surface.
 * Full-width telemetry bar above a fixed navigation rail and the content column.
 */
export function CommandShell({ children, evalResult = null }: CommandShellProps) {
  const [navOpen, setNavOpen] = useState(false);
  const pathname = usePathname();

  // Collapse the mobile rail whenever the route changes.
  useEffect(() => {
    setNavOpen(false);
  }, [pathname]);

  return (
    <div className="min-h-screen bg-bg-primary">
      <TopBar
        evalResult={evalResult}
        navOpen={navOpen}
        onToggleNav={() => setNavOpen((v) => !v)}
      />

      <div className="flex">
        <Sidebar open={navOpen} onClose={() => setNavOpen(false)} />
        <main className="min-w-0 flex-1">{children}</main>
      </div>
    </div>
  );
}
