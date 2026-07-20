import { DeviceIcon } from "./DeviceIcon";
import type { Device } from "./types";

/** Bar color by level, matching the terminal frontend's thresholds. */
function levelColor(percent: number): string {
  if (percent <= 20) return "var(--red)";
  if (percent <= 50) return "var(--yellow)";
  return "var(--green)";
}

/**
 * Shown only when plugged_in is exactly true.
 *
 * A null means the device never told us, which is every Bluetooth device.
 * Rendering anything for null would claim knowledge we do not have.
 */
function PluggedInBolt() {
  return (
    <svg
      className="bolt"
      viewBox="0 0 20 20"
      fill="currentColor"
      aria-label="plugged in"
    >
      <path d="M11.3 1.5 4.2 11.2h4.1l-.6 7.3 7.1-9.7h-4.1z" />
    </svg>
  );
}

export function DeviceRow({ device }: { device: Device }) {
  // A null percent means that source failed. Show why rather than a fake bar.
  if (device.percent === null) {
    return (
      <div className="row">
        <div className="row-head">
          <span className="row-name">
            <DeviceIcon name={device.name} />
            {device.name}
          </span>
          <span className="row-percent row-percent-missing">--</span>
        </div>
        <div className="row-note">{device.error ?? "no reading"}</div>
      </div>
    );
  }

  const color = levelColor(device.percent);
  const note = [device.status, device.age].filter(Boolean).join(", ");

  return (
    <div className="row">
      <div className="row-head">
        <span className="row-name">
          <DeviceIcon name={device.name} />
          {device.name}
        </span>
        <span className="row-percent" style={{ color }}>
          {device.plugged_in === true ? <PluggedInBolt /> : null}
          {device.percent}%
        </span>
      </div>
      <div className="row-track">
        <div
          className="row-fill"
          style={{ width: `${device.percent}%`, background: color }}
        />
      </div>
      {note ? <div className="row-note">{note}</div> : null}
    </div>
  );
}
