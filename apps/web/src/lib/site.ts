/** Single source of truth for external site links and the canonical origin. */
export const GITHUB_URL = "https://github.com/arun3676/code-tribunal";
export const PYPI_URL = "https://pypi.org/project/code-tribunal/";

/**
 * Canonical site origin for metadata, sitemap, robots, and JSON-LD. Defaults to
 * the Vercel production domain so previews work with no env var; override with
 * NEXT_PUBLIC_SITE_URL once a custom domain is attached.
 */
export const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://code-council.vercel.app";
