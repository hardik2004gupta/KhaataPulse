"use client";

export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div className={`animate-pulse bg-surface-elevated rounded ${className}`} />
  );
}

/** Mirrors MetricCard: eyebrow label, metric value, sub-value. */
export function MetricSkeleton() {
  return (
    <div className="rounded-panel border border-border bg-surface p-5">
      <Skeleton className="mb-3 h-3 w-24" />
      <Skeleton className="h-8 w-32 sm:h-9" />
      <Skeleton className="mt-2 h-2 w-20" />
    </div>
  );
}

/** Mirrors one RiskQueue row: customer, risk, amount, diagnosis, timestamp. */
export function RowSkeleton() {
  return (
    <div className="flex h-10 items-center gap-4 border-b border-border-subtle px-4">
      <Skeleton className="h-4 w-32" />
      <Skeleton className="h-4 w-12" />
      <Skeleton className="h-4 w-24" />
      <Skeleton className="ml-auto h-4 w-16" />
    </div>
  );
}
