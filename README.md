# device_battery

A small desktop app showing the battery level of every device I own, instead of checking
each one separately.

Python reads the hardware, React draws it, Electron holds the window.

## Running it

```bash
pnpm install     # first time only
pnpm dev
```

A window opens and refreshes every 30 seconds. Close it like any window.

There is also a terminal frontend with no JavaScript involved, useful for debugging:

```bash
python3 battery.py            # a table
python3 battery.py --json     # what the Electron app consumes
python3 battery.py --no-color # plain text
```

## How it fits together

```
battery.py  →  electron/main.ts  →  electron/preload.ts  →  src/App.tsx
(reads Mac)    (spawns python)      (bridge)                (draws it)
```

Electron runs two processes. The **main** process (`electron/`) is Node with full system
access, so it is the only part allowed to run `battery.py`. The **renderer** (`src/`) is
Chromium drawing React, and it deliberately cannot touch the system at all. `preload.ts`
is the entire bridge between them, exposing exactly two functions: `onReading` and
`refresh`.

That is why `App.tsx` calls `window.battery.onReading(...)` rather than importing
`child_process`. It literally cannot.

`src/types.ts` mirrors the JSON that `battery.py` emits. Change one, change the other.

## Where the numbers come from

| Row | Source | Setup needed |
|---|---|---|
| Mac | `pmset -g batt` | none |
| AirPods, and any Bluetooth device reporting a battery | `system_profiler SPBluetoothDataType -json` | none |
| iPhone | a JSON file in iCloud Drive, written by an iOS Shortcut | see `SHORTCUT_SETUP.md` |

Each source is read independently. If one fails, that row shows the reason and everything
else still renders.

Anything that pushes a `*.json` file into `iCloud Drive/device-battery/` shows up
automatically, so an iPad or Apple Watch is just another copy of the same Shortcut.
Readings older than 2 hours get flagged `stale` so a number that stopped updating never
looks current.

Only connected Bluetooth devices report. One AirPod in the case means one row, not two.

### Two things that look like bugs and are not

**System commands are called by absolute path** (`/usr/bin/pmset`,
`/usr/sbin/system_profiler`). Anything launching this without a login shell, Electron
from Finder included, gets a minimal PATH, and `/usr/sbin` is missing from bash's
fallback. Using a bare `system_profiler` silently breaks the Bluetooth read.

**`electron/main.ts` searches for a python3** rather than trusting PATH, for the same
reason. Set the `PYTHON` env var to override it.

## What it cannot do

**AirPods battery while they are connected to the iPhone.** The Mac only sees AirPods
when they are paired to the Mac. Apple exposes no API for this on either platform, and
iOS Shortcuts has no action to read it. There is no workaround, this is a hard limit.

**Charging status for anything but the Mac.** `system_profiler` returns twelve fields for
a connected AirPod (address, battery levels, firmware, serials, RSSI, services, vendor)
and not one of them is a charging flag. So `plugged_in` is `true`/`false` for the Mac and
`null` everywhere else.

`null` means unknown, and the UI shows nothing for it. Do not "improve" this by rendering
null as unplugged, that would state a fact nobody has. A bud sitting in the case charging
does not report at all, it simply vanishes from the list.

The AirPods case level only appears while the case is open and connected.

## Config

`config.json` controls naming and visibility. Anything not listed still shows up, so a
new Bluetooth device appears without touching this file.

```json
{
  "hide": ["Magic Keyboard"],
  "rename": {
    "Evan’s AirPods L": "AirPods L"
  }
}
```

The names on the left are the raw ones macOS reports. Run `python3 battery.py --json` to
see them exactly as detected, including the curly apostrophe Apple uses.

If the file is missing or malformed, everything shows with its raw name.

## Files

| File | What it is |
|---|---|
| `battery.py` | all reading logic, plus the terminal frontend |
| `electron/main.ts` | creates the window, polls `battery.py`, pushes results |
| `electron/preload.ts` | the only bridge between Node and the UI |
| `src/App.tsx` | layout and refresh state |
| `src/DeviceRow.tsx` | one device: icon, name, percent, bar |
| `src/DeviceIcon.tsx` | inline SVG icons, picked by device name |
| `src/types.ts` | `Device` and `Reading`, mirrors the Python JSON |
| `config.json` | device naming and visibility |
| `SHORTCUT_SETUP.md` | the iPhone half, iOS Shortcut instructions |

## Possible next steps

- Real artwork instead of the inline SVGs in `DeviceIcon.tsx`
- Apple Watch row, using the same Shortcut recipe as the iPhone
- History over time, which would need storage since nothing is currently persisted
