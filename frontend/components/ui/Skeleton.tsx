"use client";

export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div className={`animate-pulse bg-surface-elevated rounded ${className}`} />
  );
}

export function MetricSkeleton() {
  return (
    <div className="bg-surface border border-border rounded-lg p-5">
      <Skeleton className="h-3 w-24 mb-3" />
      <Skeleton className="h-9 w-32" />
      <Skeleton className="h-2 w-20 mt-2" />
    </div>
  );
}

export function RowSkeleton() {
  return (
    <div className="flex items-center gap-4 px-4 py-3 border-b border-border">
      <Skeleton className="h-4 w-32" />
      <Skeleton className="h-4 w-12" />
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-4 w-16 ml-auto" />
    </div>
  );
}
