import { contextBridge, ipcRenderer } from "electron";
import type { Reading } from "../src/types";

/**
 * The only bridge between the renderer and Node. The renderer never touches
 * child_process directly, it just subscribes to readings the main process pushes.
 */
contextBridge.exposeInMainWorld("battery", {
  /** Subscribe to readings. Returns an unsubscribe function. */
  onReading(callback: (reading: Reading) => void): () => void {
    const listener = (_event: Electron.IpcRendererEvent, reading: Reading) =>
      callback(reading);
    ipcRenderer.on("reading", listener);
    return () => {
      ipcRenderer.off("reading", listener);
    };
  },
});
