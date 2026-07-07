"use client";

/*
 * Shared motion vocabulary for the landing page. Every landing section imports
 * from here so easing, stagger rhythm, and reduced-motion behavior stay
 * consistent. Import motion values from "motion/react" ONLY via this file's
 * re-exports (LazyMotion + m.*) to keep the bundle on the domAnimation subset.
 */

import {
  LazyMotion,
  domAnimation,
  m,
  useReducedMotion,
  type Variants,
  type Transition,
} from "motion/react";
import { PropsWithChildren } from "react";

export { m, useReducedMotion };

/** Signature ease for reveals — fast start, long settle (same family as .btn-tactile). */
export const EASE_OUT_EXPO = [0.16, 1, 0.3, 1] as const;

/** Spring for stamp slams / pops. */
export const SPRING_SLAM: Transition = { type: "spring", stiffness: 340, damping: 22, mass: 0.9 };

/** Wrap the whole landing once; keeps motion features tree-shaken to domAnimation. */
export function MotionRoot({ children }: PropsWithChildren) {
  return <LazyMotion features={domAnimation}>{children}</LazyMotion>;
}

/**
 * Variants factory honoring prefers-reduced-motion: transforms collapse to
 * opacity-only fades, matching the existing globals.css reduced-motion policy.
 */
export function useRevealVariants(distance = 24): Variants {
  const reduced = useReducedMotion();
  return {
    hidden: { opacity: 0, y: reduced ? 0 : distance },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: reduced ? 0.3 : 0.7, ease: EASE_OUT_EXPO },
    },
  };
}

/** Parent variants that stagger children on scroll-into-view. */
export const STAGGER_PARENT: Variants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08, delayChildren: 0.05 } },
};

/**
 * Scroll-reveal wrapper: fades/slides content in once, when ~30% visible.
 * Use `stagger` to make direct m.* children animate in sequence via variants.
 */
export function Reveal({
  children,
  className,
  stagger = false,
  distance = 24,
  as: Tag = "div",
}: PropsWithChildren<{
  className?: string;
  stagger?: boolean;
  distance?: number;
  as?: "div" | "section" | "ul";
}>) {
  const item = useRevealVariants(distance);
  const MTag = m[Tag];
  return (
    <MTag
      className={className}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.3 }}
      variants={stagger ? STAGGER_PARENT : item}
    >
      {children}
    </MTag>
  );
}

/** Child item for use inside <Reveal stagger>. */
export function RevealItem({
  children,
  className,
  distance = 24,
}: PropsWithChildren<{ className?: string; distance?: number }>) {
  const item = useRevealVariants(distance);
  return (
    <m.div className={className} variants={item}>
      {children}
    </m.div>
  );
}
