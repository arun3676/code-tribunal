import { CourtRoster } from "@/components/landing/court-roster";
import { Hero } from "@/components/landing/hero";
import { InstallSection } from "@/components/landing/install-section";
import { LandingFooter } from "@/components/landing/landing-footer";
import { LandingHeader } from "@/components/landing/landing-header";
import { MotionRoot } from "@/components/landing/motion-primitives";
import { Problem } from "@/components/landing/problem";
import { TrialPipeline } from "@/components/landing/trial-pipeline";
import { VerdictDemo } from "@/components/landing/verdict-demo";

/*
 * Landing page — thin server component. MotionRoot (client) provides the
 * LazyMotion context; each section is a client component that animates itself
 * and carries its own max-w-6xl px-4 py-16 container, so the page adds no
 * extra gutters. overflow-x-clip contains the rotated/offset hero exhibits.
 */
export default function LandingPage() {
  return (
    <MotionRoot>
      <div className="overflow-x-clip">
        <LandingHeader />
        <main>
          <Hero />
          <Problem />
          <CourtRoster />
          <TrialPipeline />
          <VerdictDemo />
          <InstallSection />
        </main>
        <LandingFooter />
      </div>
    </MotionRoot>
  );
}
