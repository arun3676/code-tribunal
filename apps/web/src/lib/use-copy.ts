"use client";

import { useState } from "react";

/** Copy-to-clipboard with a transient "copied" flag — one implementation for
 *  every copy button so timing/fallback behavior can't drift between them. */
export function useCopyToClipboard(resetMs = 1200) {
  const [copied, setCopied] = useState(false);

  async function copy(text: string) {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), resetMs);
    } catch {
      /* clipboard unavailable (e.g. insecure context) — no-op */
    }
  }

  return { copied, copy };
}
