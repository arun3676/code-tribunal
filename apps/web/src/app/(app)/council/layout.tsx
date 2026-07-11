import type { Metadata } from "next";
import type { ReactNode } from "react";

// The council page is a client component, so its metadata lives here.
export const metadata: Metadata = {
  title: "Council",
  description:
    "Stream several model opinions over the same code in parallel and see where they agree, disagree, or miss things.",
};

export default function CouncilLayout({ children }: { children: ReactNode }) {
  return children;
}
