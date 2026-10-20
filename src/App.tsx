import { useEffect, useState } from "react";
import { DeviceRow } from "./DeviceRow";
import type { Reading } from "./types";

export function App() {
  const [reading, setReading] = useState<Reading | null>(null);

  useEffect(
    () =>
      window.battery.onReading((next) =>
        // A failed poll keeps the last good rows and only swaps in the error.
        setReading((prev) =>
          next.error !== null && prev
            ? { devices: prev.devices, error: next.error }
            : next,
        ),
      ),
    [],
  );

  return (
    <main className="app">
      <header className="app-header" />

      {reading === null ? (
        <p className="message">Reading...</p>
      ) : (
        <>
          {reading.error !== null ? (
            <p className="message message-error">{reading.error}</p>
          ) : reading.devices.length === 0 ? (
            <p className="message">No devices found</p>
          ) : null}
          {reading.devices.map((device, index) => (
            <DeviceRow key={`${device.name}-${index}`} device={device} />
          ))}
        </>
      )}
    </main>
  );
}
