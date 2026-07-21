# Shortcut Settings Reference

Template documentation for Shortcut configuration. Copy and customize for your device names and schedule.

## Device Shortcut Template

Create one Shortcut per device (e.g., "iPhone Battery", "Apple Watch Battery", "iPad Battery").

**Shortcut Actions** (in order):
1. Get Battery Level
2. Get Battery Level (mode: is charging status)
3. Format Date
   - Date: Current Date
   - Format: Custom, ISO 8601
   - Enable "Include ISO 8601 time"
4. Text:
   ```
   {"name": "Device Name", "percent": Battery Level, "plugged_in": "Is Charging", "updated_at": "Formatted Date"}
   ```
   Replace `"Device Name"` with your device name (must match the name in `config.json`)
   
   **Formatting rules (critical):**
   - `"percent": Battery Level` — NO quotes around the variable (must output a number)
   - `"plugged_in": "Is Charging"` — quotes around ONLY this variable (outputs a string like "Yes" or "No")
   - `"updated_at": "Formatted Date"` — the outer quotes are literal text in the JSON, insert the variable inside them
   
   Use the "Select Variable" button to insert the actual variables as tokens/pills (colored elements). They must be inserted, not typed as text.

5. Save Text
   - **Destination: iCloud Drive** (not "Shortcuts" — tap the dropdown to change it)
   - Subpath: `device-battery`
   - Filename: `device-name.json` (e.g., `iphone.json`, `watch.json`, `ipad.json`)
   - Ask Where to Save: OFF
   - Overwrite If File Exists: ON

**Automations**: Create Time of Day automations

Set up as many automations as desired within your preferred time window, spaced 30 minutes apart. Each automation:
- Trigger: Time of Day, Hourly at a specific time
- Action: Run Shortcut [Your Device Shortcut]
- Ask Before Running: OFF

**Example schedule** (8 AM - 10 PM, every 30 min): 28 automations total at 8:00, 8:30, 9:00, 9:30, etc.

## iCloud Setup

Required before Shortcuts can write files:
- iCloud Drive: Enabled on Mac
- Desktop & Documents Folders: OFF
- device-battery folder: Created at `~/Library/Mobile Documents/com~apple~CloudDocs/device-battery/`

Verify with:
```bash
python3 -c "import battery; print(battery.icloud_root())"
```

Should print a path ending in `com~apple~CloudDocs`.
