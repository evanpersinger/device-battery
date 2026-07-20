/**
 * Mirrors one entry of `battery.py --json`.
 *
 * Keep this in sync with `to_json` in battery.py. A null percent means that
 * source failed, and `error` says why.
 */
export interface Device {
  name: string;
  percent: number | null;
  status: string;
  source: string;
  updated_at: string | null;
  /** Relative age like "12m ago", already prefixed "stale," when old. Empty if unknown. */
  age: string;
  error: string | null;
}

/** What the main process sends to the renderer on every poll. */
export interface Reading {
  devices: Device[];
  /** Set when battery.py itself failed to run, rather than a single device failing. */
  error: string | null;
  /** ms since epoch, stamped when the poll completed. */
  at: number;
}
