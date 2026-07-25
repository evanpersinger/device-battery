
"""Show battery levels for the Mac and every connected device in one view.

Reads three sources, each independently:
  - the Mac's own battery, via `pmset`
  - Bluetooth devices reporting a battery level, via `system_profiler`
  - devices that push their level into iCloud Drive (the iPhone, via a Shortcut)

Any source failing degrades to a single error row rather than killing the view.
"""

from __future__ import annotations # newer type-hint syntax
import argparse # parsing command-line flags
import json # converting python objects and JSON text
import re # regular expressions module
import subprocess # 
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent / "config.json"
CACHE_PATH = Path(__file__).resolve().parent / ".battery_cache.json"
PUSHED_FOLDER_NAME = "device-battery"
STALE_AFTER = timedelta(hours=2)
COMMAND_TIMEOUT = 15

# Absolute paths, because launchers like Ubersicht run commands without a login
# shell's PATH. /usr/sbin in particular is missing from bash's fallback PATH,
# which silently breaks the system_profiler call.
# Unlike electron/main.ts's resolvePython(), this isn't a search across
# candidates, it's a plain constant: Apple ships both binaries at these exact
# paths on every Mac, there is nothing to search for.
PMSET = "/usr/bin/pmset"
SYSTEM_PROFILER = "/usr/sbin/system_profiler"

# Bluetooth battery fields, mapped to the suffix shown after the device name.
BT_BATTERY_FIELDS = {
    "device_batteryLevelMain": "",
    "device_batteryLevelLeft": "L",
    "device_batteryLevelRight": "R",
    "device_batteryLevelCase": "Case",
    "device_batteryLevel": "",
}

GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
DIM = "\033[2m"
RESET = "\033[0m"


class CommandError(Exception):
    """A shell command failed or was unavailable."""

@dataclass
class Device:
    """One battery reading, or one failed attempt at getting a reading."""
    name: str
    percent: int | None = None
    status: str = ""
    source: str = ""
    updated_at: datetime | None = None
    error: str | None = None
    # True or False only when the source actually reports it. None means
    # unknown, which is the honest answer for every Bluetooth device: macOS
    # exposes no charging field for them at all.
    plugged_in: bool | None = None


@dataclass
class Config:
    """User preferences for which devices appear and what they're called."""
    hide: list[str] = field(default_factory=list)
    rename: dict[str, str] = field(default_factory=dict)
    # Devices that should always have a row, named as they appear after rename.
    # A source that stops reporting drops the device entirely, so without this
    # there is nothing left to gray out, the name goes too.
    expect: list[str] = field(default_factory=list)
    # Overrides icloud_root() when set, so a Shortcut can push into Google
    # Drive/Dropbox/etc. instead. Still joined with PUSHED_FOLDER_NAME, same as
    # the iCloud path.
    pushed_folder: str | None = None


def run_command(args: list[str]) -> str:
    """Run a command and return stdout, raising CommandError on any failure."""
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT,
            check=True,
        )
    except FileNotFoundError as exc:
        raise CommandError(f"{Path(args[0]).name} not found") from exc
    except subprocess.TimeoutExpired as exc:
        raise CommandError(f"{Path(args[0]).name} timed out") from exc
    except subprocess.CalledProcessError as exc:
        raise CommandError(f"{Path(args[0]).name} exited {exc.returncode}") from exc
    return result.stdout


def parse_percent(raw: str | int | float | None) -> int | None:
    """Turn a value like '70%', 70, or 0.7 into an int percent, else None.

    A float strictly between 0 and 1 is treated as a fraction and scaled up,
    because Shortcuts' "Get Battery Level" returns one on some iOS versions.
    Integers are never scaled: 1 means one percent, not one hundred.
    """
    if raw is None or isinstance(raw, bool):
        return None

    if isinstance(raw, float):
        value = raw * 100 if 0 < raw < 1 else raw
    elif isinstance(raw, int):
        value = float(raw)
    elif isinstance(raw, str):
        match = re.search(r"\d+(?:\.\d+)?", raw)
        if match is None:
            return None
        value = float(match.group(0))
    else:
        return None

    return max(0, min(100, round(value)))


def read_mac_battery() -> Device:
    """Read the Mac's internal battery from pmset."""
    try:
        output = run_command([PMSET, "-g", "batt"])
    except CommandError as exc:
        return Device(name="Mac", source="pmset", error=str(exc))

    match = re.search(r"(\d+)%", output)
    if match is None:
        return Device(name="Mac", source="pmset", error="no internal battery")
    percent = int(match.group(1))

    return Device(
        name="Mac",
        percent=percent,
        source="pmset",
        updated_at=datetime.now(),
        plugged_in=mac_plugged_in(output),
    )


def mac_plugged_in(output: str) -> bool | None:
    """Read the power source from pmset, or None if it says something new.

    pmset opens with "Now drawing from 'AC Power'" or "'Battery Power'". Anything
    else (a UPS, say) is reported as unknown rather than guessed at.
    """
    match = re.search(r"Now drawing from '([^']+)'", output)
    if match is None:
        return None

    source = match.group(1)
    if source == "AC Power":
        return True
    if source == "Battery Power":
        return False
    return None


def read_bluetooth_batteries() -> list[Device]:
    """Read every connected Bluetooth device that reports a battery level."""
    try:
        raw = run_command([SYSTEM_PROFILER, "SPBluetoothDataType", "-json"])
    except CommandError as exc:
        return [Device(name="Bluetooth", source="bluetooth", error=str(exc))]

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return [Device(name="Bluetooth", source="bluetooth", error=f"bad JSON: {exc}")]

    devices: list[Device] = []
    for controller in data.get("SPBluetoothDataType", []):
        for entry in controller.get("device_connected", []):
            for name, info in entry.items():
                if isinstance(info, dict):
                    devices.extend(bluetooth_devices(name, info))
    return devices


def bluetooth_devices(name: str, info: dict) -> list[Device]:
    """Expand one Bluetooth device into a row per battery it reports.

    AirPods report left, right, and (only while the case is open) case levels.
    Devices with no battery field at all, like a paired iPhone or Watch, yield
    nothing, which is how they stay out of the view.
    """
    found: list[Device] = []
    for bt_field, label in BT_BATTERY_FIELDS.items():
        percent = parse_percent(info.get(bt_field))
        if percent is None:
            continue
        display = f"{name} {label}".strip()
        found.append(
            Device(name=display, percent=percent, source="bluetooth", updated_at=datetime.now())
        )
    return found


def icloud_root() -> Path | None:
    """Locate iCloud Drive, checking both the classic and CloudStorage paths.

    A dead archive left behind when Drive is switched off always carries a
    "(<timestamp>)" suffix in its folder name, unlike a live folder.
    read_pushed_devices() checks for that same suffix to tell "Drive is off"
    apart from "Drive is on but empty" instead of getting an empty result either way.
    """
    classic = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs"
    if classic.is_dir():
        return classic

    cloud_storage = Path.home() / "Library" / "CloudStorage"
    if not cloud_storage.is_dir():
        return None

    # macOS leaves timestamped copies like "iCloudDrive-iCloudDrive (2024-10-12
    # 11:17 AM)" behind when iCloud Drive is switched off. Those are archives,
    # not the live folder, so only fall back to one if nothing else exists.
    candidates = [path for path in cloud_storage.glob("iCloudDrive*") if path.is_dir()]
    live = [path for path in candidates if "(" not in path.name]
    for path in sorted(live) or sorted(candidates):
        return path
    return None


def read_pushed_devices(config: Config) -> list[Device]:
    """Read devices that push their level into a synced folder via a Shortcut."""
    if config.pushed_folder:
        root = Path(config.pushed_folder).expanduser()
    else:
        root = icloud_root()
        if root is None or "(" in root.name:
            return [Device(name="iCloud Drive", source="pushed", error="iCloud Drive is not syncing")]

    folder = root / PUSHED_FOLDER_NAME
    if not folder.is_dir():
        return []

    devices: list[Device] = []
    for path in sorted(list(folder.glob("*.json")) + list(folder.glob("*.txt"))):
        devices.append(pushed_device(path))
    return devices


def pushed_device(path: Path) -> Device:
    """Parse one pushed JSON file into a Device."""
    fallback = path.stem
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return Device(name=fallback, source="pushed", error=f"unreadable: {exc}")

    if not isinstance(data, dict):
        return Device(name=fallback, source="pushed", error="expected a JSON object")

    percent = parse_percent(data.get("percent"))
    if percent is None:
        return Device(name=fallback, source="pushed", error="no percent field")

    return Device(
        name=data.get("name") or fallback,
        percent=percent,
        source="pushed",
        updated_at=parse_timestamp(data.get("updated_at")),
        plugged_in=parse_bool(data.get("plugged_in")),
    )


def parse_bool(raw: object) -> bool | None:
    """Read a pushed boolean, tolerating the strings Shortcuts tends to send."""
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, str):
        lowered = raw.strip().lower()
        if lowered in {"true", "yes", "1"}:
            return True
        if lowered in {"false", "no", "0"}:
            return False
    return None


def parse_timestamp(raw: str | None) -> datetime | None:
    """Parse an ISO timestamp, tolerating a trailing Z, into local naive time."""
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)
    return parsed


def describe_age(moment: datetime | None) -> str:
    """Describe how long ago a reading was taken, flagging stale ones."""
    if moment is None:
        return ""

    delta = datetime.now() - moment
    if delta < timedelta(0):
        return "clock skew"

    minutes = int(delta.total_seconds() // 60)
    if minutes < 60:
        age = f"{minutes}m ago"
    elif minutes < 60 * 24:
        age = f"{minutes // 60}h ago"
    else:
        age = f"{minutes // (60 * 24)}d ago"

    return f"stale, {age}" if delta > STALE_AFTER else age


def load_config(path: Path) -> Config:
    """Load config, falling back to showing everything if it's missing or bad."""
    if not path.is_file():
        return Config()
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return Config()
    if not isinstance(data, dict):
        return Config()
    pushed_folder = data.get("pushed_folder")
    return Config(
        hide=list(data.get("hide", [])),
        rename=dict(data.get("rename", {})),
        expect=list(data.get("expect", [])),
        pushed_folder=pushed_folder if isinstance(pushed_folder, str) else None,
    )


def load_cache() -> dict[str, dict]:
    """Load the last-known reading for every device we've ever seen.

    Falls back to an empty cache if the file is missing or corrupt, same as
    load_config, a lost local cache is not worth crashing a poll over.
    """
    if not CACHE_PATH.is_file():
        return {}
    try:
        data = json.loads(CACHE_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_cache(cache: dict[str, dict]) -> None:
    """Persist the cache, best-effort. A failed write should not break a poll."""
    try:
        CACHE_PATH.write_text(json.dumps(cache, indent=2))
    except OSError:
        pass


def device_to_cache_entry(device: Device) -> dict:
    """Serialize a live reading for storage in the cache."""
    return {
        "percent": device.percent,
        "status": device.status,
        "source": device.source,
        "updated_at": (device.updated_at or datetime.now()).isoformat(),
        "plugged_in": device.plugged_in,
    }


def cache_entry_to_device(name: str, entry: dict) -> Device:
    """Rebuild a Device from a cached entry, for a source that has gone quiet.

    updated_at comes from the cache, not now, so describe_age() reports how
    long it has actually been since this device last reported.
    """
    return Device(
        name=name,
        percent=entry.get("percent"),
        status=entry.get("status") or "",
        source="cached",
        updated_at=parse_timestamp(entry.get("updated_at")),
        plugged_in=entry.get("plugged_in"),
    )


def default_display_name(raw_name: str) -> str | None:
    """Guess a friendly display name from words in a raw device name.

    Used only as a fallback when config.json's own `rename` has no entry, so
    a fresh install shows sensible names (iPhone, AirPods Case, ...) with no
    configuration at all. Checked most-specific first, so "AirPods Case"
    matches before the plainer "AirPods" family check would. The L/R/Case
    suffixes are reliable to match on because bluetooth_devices() is the one
    appending them (" L", " R", " Case"), not arbitrary vendor text.
    """
    lowered = raw_name.lower()

    if "airpods" in lowered:
        if lowered.endswith(" case"):
            return "AirPods Case"
        if lowered.endswith(" l"):
            return "Left AirPod"
        if lowered.endswith(" r"):
            return "Right AirPod"
        return "AirPods"

    if "iphone" in lowered:
        return "iPhone"
    if "ipad" in lowered:
        return "iPad"
    if "apple watch" in lowered:
        return "Apple Watch"

    return None


def apply_config(devices: list[Device], config: Config) -> list[Device]:
    """Rename devices and drop hidden ones. Unknown devices are kept.

    config.rename always wins when present. Otherwise default_display_name()
    is tried, so a fresh install still shows friendly names with no config at
    all. Failing both, the raw name is kept as-is.
    """
    kept: list[Device] = []
    for device in devices:
        if device.name in config.hide:
            continue
        device.name = (
            config.rename.get(device.name)
            or default_display_name(device.name)
            or device.name
        )
        kept.append(device)
    return kept


def fill_missing(
    devices: list[Device], config: Config, cache: dict[str, dict]
) -> list[Device]:
    """Fill in every expected device that did not report this run.

    Runs after apply_config, so the names compared here are the renamed ones a
    user actually sees. A device with a cached last-known reading falls back
    to that (existing staleness logic then labels it "stale, ...ago"). A
    device that has never once reported still gets a plain "not reporting"
    row, there is nothing to fall back to.
    """
    present = {device.name for device in devices}
    missing = [name for name in config.expect if name not in present]
    filled: list[Device] = []
    for name in missing:
        entry = cache.get(name)
        if entry and entry.get("percent") is not None:
            filled.append(cache_entry_to_device(name, entry))
        else:
            filled.append(Device(name=name, source="expected", error="not reporting"))
    return devices + filled


def order_devices(devices: list[Device], config: Config) -> list[Device]:
    """Give every device in `expect` a fixed position, live or not.

    Without this, a device's row jumps around as it starts and stops
    reporting, since a live reading lands wherever its source happened to put
    it while a placeholder from fill_missing() always lands at the end. Most
    visible with the AirPods Case, which used to hop position every time the
    lid opened or shut.

    Devices not in `expect` are unaffected: sorted() is stable, so they keep
    their original relative order, just placed after every expected device.
    """
    def rank(device: Device) -> tuple[int, int]:
        try:
            return (0, config.expect.index(device.name))
        except ValueError:
            return (1, 0)

    return sorted(devices, key=rank)


def collect_devices(config: Config) -> list[Device]:
    """Gather every reading from every source."""
    devices = [read_mac_battery()]
    devices.extend(read_bluetooth_batteries())
    devices.extend(read_pushed_devices(config))
    return devices


def level_color(percent: int) -> str:
    """Pick a color for a battery level."""
    if percent <= 20:
        return RED
    if percent <= 50:
        return YELLOW
    return GREEN


def render_bar(percent: int, width: int = 10) -> str:
    """Draw a proportional bar for a battery level."""
    filled = max(0, min(width, round(percent / 100 * width)))
    return "█" * filled + "░" * (width - filled)


def render(devices: list[Device], use_color: bool) -> str:
    """Format all readings as an aligned table."""
    if not devices:
        return "No devices found."

    def paint(text: str, color: str) -> str:
        return f"{color}{text}{RESET}" if use_color else text

    width = max(len(device.name) for device in devices)
    lines: list[str] = []

    for device in devices:
        name = device.name.ljust(width)

        if device.percent is None:
            reason = device.error or "no reading"
            lines.append(f"{name}  {paint('--     ' + reason, DIM)}")
            continue

        bar = paint(render_bar(device.percent), level_color(device.percent))
        level = f"{device.percent}%".rjust(4)

        notes = [note for note in (device.status, describe_age(device.updated_at)) if note]
        suffix = f"  {paint(', '.join(notes), DIM)}" if notes else ""
        lines.append(f"{name}  {bar} {level}{suffix}")

    return "\n".join(lines)


def to_json(devices: list[Device]) -> str:
    """Serialize readings for machine consumption, e.g. a menu bar frontend."""
    payload = [
        {
            "name": device.name,
            "percent": device.percent,
            "status": device.status,
            "source": device.source,
            "updated_at": device.updated_at.isoformat() if device.updated_at else None,
            "age": describe_age(device.updated_at),
            "plugged_in": device.plugged_in,
            "error": device.error,
        }
        for device in devices
    ]
    return json.dumps(payload, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON instead of a table",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="disable ANSI color even on a terminal",
    )
    args = parser.parse_args()

    config = load_config(CONFIG_PATH)
    cache = load_cache()
    devices = order_devices(
        fill_missing(apply_config(collect_devices(config), config), config, cache), config
    )

    for device in devices:
        if device.percent is not None and device.source != "cached":
            cache[device.name] = device_to_cache_entry(device)
    save_cache(cache)

    if args.json:
        print(to_json(devices))
        return 0

    use_color = sys.stdout.isatty() and not args.no_color
    print(render(devices, use_color))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
