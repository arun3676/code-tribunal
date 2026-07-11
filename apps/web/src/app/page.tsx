import { CourtRoster } from "@/components/landing/court-roster";
import { Hero } from "@/components/landing/hero";
import { InstallSection } from "@/components/landing/install-section";
import { LandingFooter } from "@/components/landing/landing-footer";
import { LandingHeader } from "@/components/landing/landing-header";
import { MotionRoot } from "@/components/landing/motion-primitives";
import { Problem } from "@/components/landing/problem";
import { TrialPipeline } from "@/components/landing/trial-pipeline";
import { VerdictDemo } from "@/components/landing/verdict-demo";
import { Waitlist } from "@/components/landing/waitlist";
import { GITHUB_URL, PYPI_URL, SITE_URL } from "@/lib/site";

/*
 * Landing page — thin server component. MotionRoot (client) provides the
 * LazyMotion context; each section is a client component that animates itself
 * and carries its own max-w-6xl px-4 py-16 container, so the page adds no
 * extra gutters. overflow-x-clip contains the rotated/offset hero exhibits.
 */

const JSON_LD = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "Code Tribunal",
  description:
    "An intent-conformance court for AI-generated code. Seven agents reconcile the ticket against the diff and return a merge verdict with a 0–100 trust score.",
  url: SITE_URL,
  applicationCategory: "DeveloperApplication",
  operatingSystem: "Windows, macOS, Linux",
  offers: { "@type": "Offer", price: "0", priceCurrency: "USD" },
  sameAs: [GITHUB_URL, PYPI_URL],
};

export default function LandingPage() {
  return (
    <MotionRoot>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(JSON_LD) }}
      />
      <div className="overflow-x-clip">
        <LandingHeader />
        <main>
          <Hero />
          <Problem />
          <CourtRoster />
          <TrialPipeline />
          <VerdictDemo />
          <InstallSection />
          <Waitlist />
        </main>
        <LandingFooter />
      </div>
    </MotionRoot>
  );
}
