# Getting your iPhone battery onto the Mac

Your Mac cannot read your iPhone's battery. Nothing can, there's no API for it. The
workaround is to have the iPhone write its own level into iCloud Drive on a schedule,
and have `battery.py` read that file.

Roughly 5 minutes of setup, all on the phone except step 1.

## 1. Enable iCloud Drive on the Mac (required first)

iCloud Drive is currently **off** on this Mac, so there's nowhere for the file to land.

System Settings > Apple Account > iCloud > iCloud Drive > turn on.

Verify it worked, this should print a path with no error:

```bash
python3 -c "import battery; print(battery.icloud_root())"
```

If the path it prints still ends in something like `(2024-10-12 11:17 AM)`, iCloud Drive
hasn't finished setting up. That folder is a leftover archive from when iCloud Drive was
last switched off, not a live sync folder. Wait a minute and check again.

## 2. Build the automation on the iPhone

Shortcuts app > Automation tab > `+` > Time of Day.

**Trigger**: Hourly. Use a time trigger, not the Battery Level trigger. Battery Level
only fires when crossing a threshold, so it can leave the reading hours stale.

**Actions**, in order:

1. **Get Battery Level**
2. **Format Date**
   - Date: Current Date
   - Format: Custom, ISO 8601
3. **Text**, containing exactly this (the two bracketed bits are variable tokens you
   insert, not literal text):

   ```
   {"name": "iPhone", "percent": [Battery Level], "updated_at": "[Formatted Date]"}
   ```

   An optional `"plugged_in": true` or `false` is read if you can produce it. Shortcuts
   has no direct "is charging" action, so leave it out unless you find a way. Omitting
   it means unknown, which displays as nothing. That is correct, and better than
   claiming the phone is unplugged when nobody actually knows.

4. **Save File**
   - Destination: iCloud Drive, folder `device-battery`, filename `iphone.json`
   - Turn **off** "Ask Where to Save"
   - Turn **on** "Overwrite If File Exists"

Finally, turn **off** "Ask Before Running" so it runs silently.

## 3. Check it

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
