# Shortcut Settings Reference

Template documentation for Shortcut configuration. Copy and customize for your device names and schedule.

Bracketed items in the Text action below (`[Battery Level]`, `[is Charging]`,
`[Formatted Date]`) are Shortcuts variables, not literal text. Insert them by tapping
"Select Variable" in the Text action and picking the matching action's output, typing
the brackets by hand will not work.

`is Charging` isn't a separate action, it's one of the Detail options inside the same
`Get Battery Level` action. Step 2 below is the same action as step 1, just with
`is Charging` picked from that dropdown instead of `Battery Level`.

The times you pick for the **Automations** below are arbitrary, set whatever schedule
fits. Since a Time of Day automation only fires once at its set time, more automations
means more frequent battery updates, fewer means less frequent.

## Device Shortcut Template

Create one Shortcut per device (e.g., "iPhone Battery", "Apple Watch Battery", "iPad Battery").

**Shortcut Actions** (in order):
1. Get Battery Level
2. Get Battery Level (mode: is Charging)
3. Format Date
   - Date: Current Date
   - Format: Custom, ISO 8601
   - Enable "Include ISO 8601 time"
4. Text:
   ```
   {"name": "Device Name", "percent": [Battery Level], "plugged_in": "[Get Battery Level]", "updated_at": "[Formatted Date]"}
   ```
   Replace `"Device Name"` with your device name (must match the name in `config.json`)

   **Formatting rules (critical):**
   - `"percent": [Battery Level]` — NO quotes around the variable (must output a number)
   - `"plugged_in": "[Get Battery Level]"` — quotes around this one, the variable outputs a
     bare word like `Yes` or `No`, which is not valid JSON unquoted
   - `"updated_at": "[Formatted Date]"` — the outer quotes are literal text in the JSON, insert the variable inside them

5. Save Text
   - **Destination: iCloud Drive** (not "Shortcuts" — tap the dropdown to change it)
   - Subpath: `device-battery`
   - Filename: `device-name.txt` (e.g., `iphone.txt`, `watch.txt`, `ipad.txt`)
     Both `.json` and `.txt` are read; Shortcuts' Save action tends to produce `.txt`
   - Ask Where to Save: OFF
   - Overwrite If File Exists: ON

**Automations**: Time of Day trigger, one automation per desired update time (see note above)

Each automation: Run Shortcut [Your Device Shortcut], Ask Before Running: OFF

## iCloud Setup

Required before Shortcuts can write files:
- iCloud Drive: Enabled on Mac
- Desktop & Documents Folders: OFF
- device-battery folder: Created at `~/Library/Mobile Documents/com~apple~CloudDocs/device-battery/`

Verify with:
```bash
python3 -c "import battery; print(battery.icloud_root())"
```

Should print a path ending in `com~apple~CloudDocs`. `None` means iCloud Drive is not
syncing.
