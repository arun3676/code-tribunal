import type { Metadata } from "next";
import type { ReactNode } from "react";

// The tribunal page is a client component, so its metadata lives here.
export const metadata: Metadata = {
  title: "War Room",
  description:
    "Watch seven AI agents cross-examine a diff against its ticket and stamp a merge verdict with a 0–100 trust score.",
};

export default function TribunalLayout({ children }: { children: ReactNode }) {
  return children;
}
