import type { Reading } from "./types";

declare global {
  interface Window {
    battery: {
      onReading(callback: (reading: Reading) => void): () => void;
    };
  }
}

export {};
