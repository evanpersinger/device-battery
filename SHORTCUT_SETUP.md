# Getting your iPhone battery onto the Mac

Your Mac cannot read your iPhone's battery. Nothing can, there's no API for it. The
workaround is to have the iPhone write its own level into iCloud Drive on a schedule,
and have `battery.py` read that file.

Roughly 5 minutes of setup, all on the phone except step 1.

## 1. Enable iCloud Drive on the Mac (required first)

With iCloud Drive off there is nowhere for the file to land, so this comes first.

System Settings > Apple Account > iCloud > **See All** under "Saved to iCloud", then enable
iCloud Drive. The list is collapsed by default, so it isn't visible until you click See All.

Leave **Desktop & Documents Folders** off, it syncs your entire Desktop and isn't needed here.

Verify it worked, this should print a path ending in `com~apple~CloudDocs`:

```bash
python3 -c "import battery; print(battery.icloud_root())"
```

If it still prints a path ending in something like `(2024-10-12 11:17 AM)`, iCloud Drive
hasn't finished setting up. That folder is a leftover archive from when iCloud Drive was
last switched off, not a live sync folder. Wait a minute and check again.

### Create the device-battery folder

iCloud Drive is now syncing on your Mac, but the `device-battery` folder doesn't exist yet.
Create it so Shortcuts can save files there:

```bash
mkdir -p ~/Library/Mobile\ Documents/com~apple~CloudDocs/device-battery
```

Verify it was created:

```bash
ls -la ~/Library/Mobile\ Documents/com~apple~CloudDocs/device-battery
```

### Enable iCloud on your iPhone/Watch

On each device that will report battery:

**iPhone/iPad**: Settings > [Your Name] > iCloud > iCloud Drive > Turn **On**

**Apple Watch**: Settings > [Your Name] > iCloud > iCloud Drive > Turn **On**

The Shortcuts app needs access to iCloud Drive. It will ask for permission the first
time it tries to save a file—approve it.

## 2. Create the Shortcut

Shortcuts app > Shortcuts tab > `+` to create a new shortcut. Name it something like "Device Battery" or "iPhone Battery".

**Actions**, in order:

1. **Get Battery Level** (for percent)
2. **Get Battery Level** (mode: is charging status)
3. **Text** with the JSON structure below. Use the **"Select Variable" button** to insert the actual variable outputs (not literal text):

   ```
   {"name": "iPhone", "percent": Battery Level, "plugged_in": "Is Charging", "updated_at": "Formatted Date"}
   ```

   **Important formatting rules:**
   - `"percent": Battery Level` — NO quotes around the variable (outputs a number)
   - `"plugged_in": "Is Charging"` — quotes around ONLY this variable (outputs a string like "Yes" or "No")
   - `"updated_at": "Formatted Date"` — the outer quotes are literal text, the variable goes inside them

   The variables must be inserted as tokens/pills (colored elements), not typed as literal text. Tap "Select Variable" next to each bracketed item and choose the corresponding action output.

   The `updated_at` timestamp is used to show how long ago the reading was taken (e.g. "4 min ago") and to flag readings older than 2 hours as `stale`.

4. **Format Date** (required for the timestamp)
   - Date: Current Date
   - Format: Custom, ISO 8601
   - **Enable "Include ISO 8601 time"**

5. **Save Text** to iCloud Drive
   - Destination: iCloud Drive, folder `device-battery`, filename `iphone.json`
   - Turn **off** "Ask Where to Save"
   - Turn **on** "Overwrite If File Exists"

## 3. Create the Automation

Shortcuts app > Automation tab > `+` > Time of Day.

**Trigger**: Hourly. Use a time trigger, not the Battery Level trigger. Battery Level
only fires when crossing a threshold, so it can leave the reading hours stale.

**Action**: Run the Shortcut you just created.

Finally, turn **off** "Ask Before Running" so it runs silently.

### For Apple Watch

If you're setting up the Shortcut on your Apple Watch:

1. Open Shortcuts app on the Watch itself
2. Go to **Automation** tab
3. Tap `+` and select **Time of Day**
4. Set it to hourly at your preferred times (every 30 min like the iPhone)
5. Choose the Watch Shortcut to run
6. Turn **off** "Ask Before Running"

**Important:** The automation must be created on the Watch, not synced from iPhone. watchOS Shortcuts only reads the Watch's own battery when the Shortcut runs on the Watch device itself.

## 4. Check it

Run the automation once by hand from the Shortcuts app, then on the Mac:

```bash
python3 battery.py
```

You should get an iPhone row with a relative timestamp. Any reading older than 2 hours
gets flagged as `stale`, so a number that stopped updating never looks current.

## Gotchas

- **Percent must be a whole number.** If your iPhone row reads `1%` when the phone is
  actually full, Shortcuts sent `1.0` instead of `100`. Add a **Calculate** action
  multiplying Battery Level by 100.
- **Hourly is the floor.** iOS won't run personal automations more often than that
  reliably, and it may skip runs in Low Power Mode.
- **Adding more devices is free.** The script reads every `*.json` in the
  `device-battery` folder, so the same recipe on an iPad or Apple Watch (saving to
  `ipad.json`, `watch.json`) just works. The `name` field in the JSON is what gets
  displayed.

## What this still won't fix

AirPods battery while they're connected to your iPhone. The Mac only sees AirPods when
they're paired to the Mac, and iOS Shortcuts has no action to read AirPods battery.
There is no workaround for this one.
