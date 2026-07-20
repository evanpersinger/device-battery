import AirPod from "./icons/airpod.svg?react";
import AirPodsCase from "./icons/airpods-case.svg?react";

/**
 * Device icons.
 *
 * Real SVG files live in src/icons/ and are imported with `?react`. To add one,
 * drop the file in, import it, and add a case below. Hardcoded fills are
 * rewritten to currentColor by the svgr config in vite.config.ts, so icons
 * inherit the surrounding text color. If a new icon renders in the wrong color,
 * its fill is missing from that map.
 *
 * Devices with no file yet fall back to hand-drawn strokes, which will not
 * perfectly match the weight of a downloaded set.
 */

type IconKind =
  | "laptop"
  | "airpod-left"
  | "airpod-right"
  | "airpods-case"
  | "phone"
  | "watch"
  | "generic";

/** Guess an icon from the device name. Falls back to a generic dot. */
function kindFor(name: string): IconKind {
  const lower = name.toLowerCase();

  // Order matters. "AirPods Case" contains "airpod", and "Left AirPod"
  // contains both "left" and "airpod", so the specific checks come first.
  if (lower.includes("case")) return "airpods-case";
  if (lower.includes("airpod") || lower.includes("headphone")) {
    return lower.includes("left") ? "airpod-left" : "airpod-right";
  }
  if (lower.includes("macbook") || lower.includes("mac") || lower.includes("laptop")) {
    return "laptop";
  }
  if (lower.includes("iphone") || lower.includes("phone")) return "phone";
  if (lower.includes("watch")) return "watch";
  return "generic";
}

/** Inline fallbacks, drawn on a 20x20 grid with strokes rather than fills. */
function StrokeIcon({ kind }: { kind: "laptop" | "phone" | "watch" | "generic" }) {
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
      {kind === "laptop" && (
        <>
          <rect x="3" y="4" width="14" height="9" rx="1.2" />
          <path d="M1 15.5h18" />
        </>
      )}
      {kind === "phone" && (
        <>
          <rect x="6" y="2.5" width="8" height="15" rx="1.6" />
          <path d="M9 15.2h2" />
        </>
      )}
      {kind === "watch" && (
        <>
          <rect x="6" y="5.5" width="8" height="9" rx="2" />
          <path d="M8 5.5V3h4v2.5M8 14.5V17h4v-2.5" />
        </>
      )}
      {kind === "generic" && <circle cx="10" cy="10" r="4" />}
    </svg>
  );
}

export function DeviceIcon({ name }: { name: string }) {
  const kind = kindFor(name);

  if (kind === "airpods-case") {
    return <AirPodsCase className="device-icon" aria-hidden="true" />;
  }

  // One artwork for both buds. A left AirPod is the mirror image of a right
  // one, not a rotation, rotating would put the stem above the bud.
  if (kind === "airpod-left" || kind === "airpod-right") {
    return (
      <AirPod
        className="device-icon"
        style={kind === "airpod-left" ? { transform: "scaleX(-1)" } : undefined}
        aria-hidden="true"
      />
    );
  }

  return <StrokeIcon kind={kind} />;
}
