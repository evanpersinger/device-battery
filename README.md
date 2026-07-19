# device_battery

One view of the battery level on every device I own, instead of checking each one
separately.

```
$ python3 battery.py
MacBook Pro  ███████░░░  68%  discharging, 3:16 left
AirPods L    ███████░░░  67%
AirPods R    ████████░░  79%
iPhone       █████████░  88%  12m ago
```

Bars are colored in a real terminal: green above 50, yellow from 20 to 50, red below 20.

## Usage

```bash
python3 battery.py            # the table above
python3 battery.py --json     # machine-readable, for piping elsewhere
python3 battery.py --no-color # plain text even on a terminal
```

No dependencies. macOS and Python 3.10 or newer, both of which you already have.

## Where the numbers come from

| Row | Source | Setup needed |
|---|---|---|
| Mac | `pmset -g batt` | none |
| AirPods, and any Bluetooth device reporting a battery | `system_profiler SPBluetoothDataType -json` | none |
| iPhone | a JSON file in iCloud Drive, written by an iOS Shortcut | see `SHORTCUT_SETUP.md` |

Each source is read independently. If one fails, its row shows a dim error and the rest
of the table still renders.

Anything that pushes a `*.json` file into `iCloud Drive/device-battery/` shows up
automatically, so an iPad or Apple Watch is just another copy of the same Shortcut.
Readings older than 2 hours get flagged `stale` so a number that stopped updating never
looks current.

## What it cannot do

**AirPods battery while they are connected to the iPhone.** The Mac only sees AirPods
when they are paired to the Mac. Apple exposes no API for this on either platform, and
iOS Shortcuts has no action to read it. There is no workaround, this is a hard limit.

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

## Possible next steps

- Menu bar display: `brew install --cask swiftbar`, then point it at this script. The
  `--json` flag exists for exactly this, no code changes needed.
- Apple Watch row, using the same Shortcut recipe as the iPhone.
