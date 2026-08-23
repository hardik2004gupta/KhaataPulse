"use client";

import React from "react";

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: React.ReactNode;
  /** Glyph shown in the marker. Defaults to an idle-instrument ring. */
  glyph?: string;
}

export function EmptyState({ title, description, action, glyph = "◌" }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center px-4 py-16 text-center">
      <div
        aria-hidden="true"
        className="mb-4 flex h-12 w-12 items-center justify-center rounded-full border border-border bg-surface-elevated"
      >
        <span className="text-xl text-text-muted">{glyph}</span>
      </div>
      <p className="mono text-[10px] uppercase tracking-eyebrow text-text-secondary">{title}</p>
      {description && (
        <p className="mt-2 max-w-prose text-xs text-text-muted">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
