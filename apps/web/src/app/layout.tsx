import type { Metadata } from "next";
import { Analytics } from "@vercel/analytics/react";
import { Geist, JetBrains_Mono } from "next/font/google";

import { ServiceWorkerRegister } from "@/components/pwa/sw-register";
import { SITE_URL } from "@/lib/site";

import "./globals.css";

const geist = Geist({ subsets: ["latin"], variable: "--font-sans" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

const TITLE = "Code Tribunal — Did the code build what the ticket asked for?";
const DESCRIPTION =
  "An intent-conformance court for AI-generated code. Seven agents reconcile the ticket against the diff and return a merge verdict with a 0–100 trust score. CLI · MCP · Web.";

export const metadata: Metadata = {
  // Absolute base for OG/twitter image URLs — see SITE_URL in lib/site.ts.
  metadataBase: new URL(SITE_URL),
  title: {
    default: TITLE,
    template: "%s · Code Tribunal",
  },
  description: DESCRIPTION,
  openGraph: {
    type: "website",
    siteName: "Code Tribunal",
    title: TITLE,
    description: DESCRIPTION,
  },
  twitter: {
    card: "summary_large_image",
    title: TITLE,
    description: DESCRIPTION,
  },
  applicationName: "Code Tribunal",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "Tribunal",
  },
  icons: {
    icon: "/icon-192.png",
    apple: "/apple-touch-icon.png",
  },
};

export const viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  themeColor: "#0f9d63",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${geist.variable} ${mono.variable}`}>
        {children}
        <ServiceWorkerRegister />
        <Analytics />
      </body>
    </html>
  );
}
