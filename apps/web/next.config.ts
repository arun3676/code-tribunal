import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  typedRoutes: true,
  // Monorepo tracing for local/docker only — breaks Vercel output paths when set on deploy.
  ...(process.env.VERCEL ? {} : { outputFileTracingRoot: path.join(process.cwd(), "../..") }),
};

export default nextConfig;
