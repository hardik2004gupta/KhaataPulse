"use client";

import React, { useMemo, useState } from "react";

interface PayloadViewerProps {
  payload: Record<string, unknown>;
  /** Render expanded from the start (drawer contexts). */
  defaultOpen?: boolean;
  label?: string;
}

type Token = { text: string; kind: "key" | "string" | "number" | "bool" | "plain" };

/**
 * Tokenise pretty-printed JSON line-by-line for syntax colouring.
 * Deliberately simple - payloads are structured audit records, not arbitrary code.
 */
function tokenizeLine(line: string): Token[] {
  const tokens: Token[] = [];
  // Split on quoted strings while preserving them.
  const parts = line.split(/("(?:[^"\\]|\\.)*")/g);

  parts.forEach((part) => {
    if (!part) return;

    if (part.startsWith('"') && part.endsWith('"') && part.length > 1) {
      tokens.push({ text: part, kind: "string" });
      return;
    }

    // Non-string run: pull out numbers and literals.
    const sub = part.split(/(\b-?\d+\.?\d*(?:[eE][+-]?\d+)?\b|\btrue\b|\bfalse\b|\bnull\b)/g);
    sub.forEach((s) => {
      if (!s) return;
      if (/^-?\d+\.?\d*(?:[eE][+-]?\d+)?$/.test(s)) {
        tokens.push({ text: s, kind: "number" });
      } else if (s === "true" || s === "false" || s === "null") {
        tokens.push({ text: s, kind: "bool" });
      } else {
        tokens.push({ text: s, kind: "plain" });
      }
    });
  });

  // A quoted string immediately followed by a colon is an object key.
  for (let i = 0; i < tokens.length; i++) {
    if (tokens[i].kind !== "string") continue;
    const next = tokens[i + 1];
    if (next && next.kind === "plain" && next.text.trimStart().startsWith(":")) {
      tokens[i] = { ...tokens[i], kind: "key" };
    }
  }

  return tokens;
}

const TOKEN_CLASS: Record<Token["kind"], string> = {
  key: "text-text-secondary",
  string: "text-recovery-text",
  number: "text-warning-text",
  bool: "text-ai-text",
  plain: "text-text-faint",
};

export function PayloadViewer({ payload, defaultOpen = false, label }: PayloadViewerProps) {
  const [open, setOpen] = useState(defaultOpen);
  const [copied, setCopied] = useState(false);

  const json = useMemo(() => JSON.stringify(payload, null, 2), [payload]);
  const lines = useMemo(() => json.split("\n"), [json]);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(json);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1400);
    } catch {
      // Clipboard unavailable - silently ignore, the payload stays selectable.
    }
  };

  const isEmpty = !payload || Object.keys(payload).length === 0;

  return (
    <div className="mt-1.5">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          disabled={isEmpty}
          className="mono text-[10px] uppercase tracking-eyebrow text-text-faint transition-colors duration-base hover:text-text-secondary disabled:cursor-default disabled:opacity-50"
        >
          {isEmpty ? "no payload" : open ? "▾ hide payload" : "▸ show payload"}
          {label && !isEmpty ? ` · ${label}` : ""}
        </button>

        {open && !isEmpty && (
          <button
            type="button"
            onClick={copy}
            className="mono text-[10px] uppercase tracking-eyebrow text-text-faint transition-colors duration-base hover:text-recovery-text"
          >
            {copied ? "✓ copied" : "copy"}
          </button>
        )}
      </div>

      {open && !isEmpty && (
        <pre className="mono mt-2 max-h-48 overflow-auto rounded border border-border bg-bg-primary p-3 text-[11px] leading-relaxed">
          {lines.map((line, i) => (
            <div key={i} className="whitespace-pre">
              {tokenizeLine(line).map((t, j) => (
                <span key={j} className={TOKEN_CLASS[t.kind]}>
                  {t.text}
                </span>
              ))}
            </div>
          ))}
        </pre>
      )}
    </div>
  );
}
