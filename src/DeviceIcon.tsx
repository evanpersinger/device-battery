/**
 * Device icons.
 *
 * Inline SVG for now so there are no asset imports to wire up. To use real
 * artwork instead, drop files in src/icons/ and swap the returned element here,
 * the rest of the app does not care what this renders.
 */

import type { ReactElement } from "react";

type IconKind = "laptop" | "headphones" | "phone" | "watch" | "generic";

/** Guess an icon from the device name. Falls back to a generic dot. */
function kindFor(name: string): IconKind {
  const lower = name.toLowerCase();
  if (lower.includes("macbook") || lower.includes("mac")) return "laptop";
  if (lower.includes("airpod") || lower.includes("headphone")) return "headphones";
  if (lower.includes("iphone") || lower.includes("phone")) return "phone";
  if (lower.includes("watch")) return "watch";
  return "generic";
}

const paths: Record<IconKind, ReactElement> = {
  laptop: (
    <>
      <rect x="3" y="4" width="14" height="9" rx="1.2" />
      <path d="M1 15.5h18" />
    </>
  ),
  headphones: (
    <>
      <path d="M4 12V9.5a6 6 0 0 1 12 0V12" />
      <rect x="2.5" y="11.5" width="3.5" height="5.5" rx="1.5" />
      <rect x="14" y="11.5" width="3.5" height="5.5" rx="1.5" />
    </>
  ),
  phone: (
    <>
      <rect x="6" y="2.5" width="8" height="15" rx="1.6" />
      <path d="M9 15.2h2" />
    </>
  ),
  watch: (
    <>
      <rect x="6" y="5.5" width="8" height="9" rx="2" />
      <path d="M8 5.5V3h4v2.5M8 14.5V17h4v-2.5" />
    </>
  ),
  generic: <circle cx="10" cy="10" r="4" />,
};

export function DeviceIcon({ name }: { name: string }) {
  return (
    <svg
      className="device-icon"
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.4"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[kindFor(name)]}
    </svg>
  );
}
