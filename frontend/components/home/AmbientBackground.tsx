/**
 * Ambient background — five CSS-only layers rendered behind every surface.
 *
 * No canvas, no JS animation loop, no scroll listeners. Every layer is a
 * static paint plus a very slow CSS transform, so the compositor handles it
 * on its own thread. All motion is disabled under `prefers-reduced-motion`
 * (see globals.css), leaving the static atmospheric colour in place.
 */
export function AmbientBackground() {
  return (
    <div className="ambient-root" aria-hidden="true">
      {/* 1 — base wash */}
      <div className="ambient-base" />

      {/* 2 — structural grid */}
      <div className="ambient-grid" />

      {/* 3 — atmospheric light: AI, recovery, risk */}
      <div className="ambient-blob ambient-blob-ai" />
      <div className="ambient-blob ambient-blob-recovery" />
      <div className="ambient-blob ambient-blob-warning" />

      {/* 4 — horizon edge */}
      <div className="ambient-horizon" />

      {/* 5 — scan */}
      <div className="ambient-scan" />
    </div>
  );
}
