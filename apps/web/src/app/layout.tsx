import type { Metadata } from "next";
import { Geist, JetBrains_Mono } from "next/font/google";

import { AppShell } from "@/components/shell/app-shell";
import { ServiceWorkerRegister } from "@/components/pwa/sw-register";

import "./globals.css";

const geist = Geist({ subsets: ["latin"], variable: "--font-sans" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "Code Council",
  description: "See how frontier models reason about your code.",
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
        <AppShell>{children}</AppShell>
        <ServiceWorkerRegister />
      </body>
    </html>
  );
}
