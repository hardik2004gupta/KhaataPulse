"use client";
import { useState } from "react";
import type { RecoveryCase } from "@/lib/types";
import { NavBar } from "@/components/dashboard/NavBar";
import { RiskQueue } from "@/components/risk/RiskQueue";
import { CaseDetailDrawer } from "@/components/risk/CaseDetailDrawer";

export default function CasesPage() {
  const [selected, setSelected] = useState<RecoveryCase | null>(null);

  return (
    <div className="min-h-screen bg-bg-primary">
      <NavBar />

      <main className="max-w-screen-xl mx-auto px-6 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-text-primary">Risk Queue</h1>
          <p className="text-text-muted text-sm mt-1">
            Live recovery cases routed through the KhaataPulse pipeline
          </p>
        </div>

        <RiskQueue onSelect={setSelected} />
      </main>

      <CaseDetailDrawer case_={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
