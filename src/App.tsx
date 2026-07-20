import { useEffect, useState } from "react";
import { DeviceRow } from "./DeviceRow";
import type { Reading } from "./types";

export function App() {
  const [reading, setReading] = useState<Reading | null>(null);

  useEffect(() => window.battery.onReading(setReading), []);

  return (
    <main className="app">
      <header className="app-header">
        <h1>Devices</h1>
      </header>

      {reading === null ? (
        <p className="message">Reading...</p>
      ) : reading.error !== null ? (
        <p className="message message-error">{reading.error}</p>
      ) : reading.devices.length === 0 ? (
        <p className="message">No devices found</p>
      ) : (
        reading.devices.map((device, index) => (
          <DeviceRow key={`${device.name}-${index}`} device={device} />
        ))
      )}
    </main>
  );
}
