import { app, BrowserWindow } from "electron";
import { execFile } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const currentDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.join(currentDir, "..");
const scriptPath = path.join(projectRoot, "battery.py");

const POLL_INTERVAL_MS = 30_000;
const POLL_TIMEOUT_MS = 20_000;

let window: BrowserWindow | null = null;
let timer: NodeJS.Timeout | null = null;

/**
 * Find a usable python3.
 *
 * Electron launched from Finder gets a minimal PATH with no pyenv shims, so a
 * bare "python3" is not safe to assume. Set the PYTHON env var to override.
 */
function resolvePython(): string {
  const candidates = [
    process.env.PYTHON,
    path.join(app.getPath("home"), ".pyenv/shims/python3"),
    "/opt/homebrew/bin/python3",
    "/usr/local/bin/python3",
    "/usr/bin/python3",
  ].filter((candidate): candidate is string => Boolean(candidate));

  return candidates.find((candidate) => existsSync(candidate)) ?? "python3";
}

/** Run battery.py once and push the result to the renderer. */
function poll(): void {
  execFile(
    resolvePython(),
    [scriptPath, "--json"],
    { timeout: POLL_TIMEOUT_MS },
    (error, stdout) => {
      if (!window || window.isDestroyed()) return;

      if (error) {
        window.webContents.send("reading", {
          devices: [],
          error: error.message,
          at: Date.now(),
        });
        return;
      }

      try {
        window.webContents.send("reading", {
          devices: JSON.parse(stdout),
          error: null,
          at: Date.now(),
        });
      } catch {
        window.webContents.send("reading", {
          devices: [],
          error: "battery.py returned output that is not valid JSON",
          at: Date.now(),
        });
      }
    },
  );
}

function createWindow(): void {
  window = new BrowserWindow({
    width: 320,
    height: 460,
    title: "Devices",
    backgroundColor: "#161618",
    titleBarStyle: "hiddenInset",
    resizable: true,
    webPreferences: {
      preload: path.join(currentDir, "preload.mjs"),
    },
  });

  const devServer = process.env.VITE_DEV_SERVER_URL;
  if (devServer) {
    void window.loadURL(devServer);
  } else {
    void window.loadFile(path.join(projectRoot, "dist/index.html"));
  }

  // First poll once the page can actually receive it.
  window.webContents.on("did-finish-load", poll);

  timer = setInterval(poll, POLL_INTERVAL_MS);

  window.on("closed", () => {
    if (timer) clearInterval(timer);
    timer = null;
    window = null;
  });
}

void app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  app.quit();
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
