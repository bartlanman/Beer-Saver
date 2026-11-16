# Install the tap sync on the Mac mini

**What it does once installed:** every 5 minutes the Mac mini checks Beer Saver. When a tap gets a **different beer**, it updates the Untappd "Beer on Tap!" menu and prints **10 copies** of a fresh tap menu on the Kyocera. A retap of the same beer changes nothing on the menu, so it's ignored.

**Time:** about 30 minutes. **Where:** at the Mac mini (BARTs-Mini-2), logged in as you, on the office Wi-Fi (BCBC Private).

**Have ready, in your password manager (never in this repo or a chat):**
- Beer Saver API login: user `<ClientID>-<username>` and its password (the login the Beer Saver API answers to)
- Untappd for Business: your email and the **Read & Write** API token (Untappd → Account → API Access). Regenerating the token first is a good idea, since the old one was shown in a chat.

Every command below goes into **Terminal** (⌘ Space → type `Terminal` → Return). Paste one block at a time, then press Return.

---

## Step 1: Check the basics (2 min)

```bash
python3 --version
ls "/Applications/Google Chrome.app" >/dev/null && echo "Chrome OK"
lpstat -p
```

- **python3:** you should see `Python 3.x`. If macOS offers to install "command line developer tools", click **Install**, wait, then run it again.
- **Chrome OK:** Chrome turns the menu into a PDF. If it's missing, install Chrome from google.com/chrome.
- **lpstat -p:** lists your printers. Find the Kyocera line, e.g. `printer TaskAlfa_3552ci is idle`, and **write down the name** (here `TaskAlfa_3552ci`). It's used in Steps 4–5.
  - No Kyocera listed? Add it: System Settings → Printers & Scanners → Add Printer → **IP** tab → `192.168.2.126`, protocol **IPP** → Add. Then run `lpstat -p` again.
  - Listed but pointing at the old `192.168.2.51`? That address stopped working on 2026-11-15. Delete that printer and re-add it at `192.168.2.126`.

## Step 2: Download the sync (1 min)

```bash
mkdir -p ~/BeerSaver && cd ~/BeerSaver
curl -fsSLO https://raw.githubusercontent.com/bartlanman/Beer-Saver/main/sync/tap_sync.py
curl -fsSLO https://raw.githubusercontent.com/bartlanman/Beer-Saver/main/sync/beer-map.json
ls -l
```

You should see `tap_sync.py` and `beer-map.json`.

## Step 3: Store the four logins in the Keychain (3 min)

Each command asks for a value, and nothing shows as you type. Paste the command, press Return, type or paste the value, press Return. It asks you to retype it.

```bash
security add-generic-password -s beersaver-api-user -a "$USER" -w
```
→ the Beer Saver API **user name**, e.g. `ClientID-username`

```bash
security add-generic-password -s beersaver-api-pass -a "$USER" -w
```
→ the Beer Saver API **password**

```bash
security add-generic-password -s untappd-email -a "$USER" -w
```
→ your Untappd for Business **email**

```bash
security add-generic-password -s untappd-token -a "$USER" -w
```
→ the Untappd **Read & Write** token

Made a typo? Run the same command with `-U` added before `-w` to overwrite it.

## Step 4: Practice run, nothing changed anywhere (3 min)

```bash
cd ~/BeerSaver && python3 tap_sync.py --force
```

Check what it prints:

- `22 taps, 22 changed (DRY RUN)` and one line per tap. **Do the beers match what's really on tap?** If not, fix ON TAP in Beer Saver first.
- Any `Untappd replace …` / `Untappd add …` lines show what it *would* change on Untappd. With Beer Saver and Untappd in sync, there should be few or none. Read each one before going on.
- `TO DO (manual): …` lists beers missing from `beer-map.json` (tell Claude, or add them).
- Errors:
  - `HTTP Error 403` from api.usbeersaver.com → wrong Beer Saver API user or password (Step 3).
  - `HTTP Error 401` from business.untappd.com → wrong Untappd email or token (Step 3).
  - A popup "python3 wants to use your keychain" → enter your Mac password and click **Always Allow** (once per login).

Open the menu it made:
```bash
open ~/Desktop/"Tap Menu"/tap-menu.pdf
```
Check the names, breweries, ABV and prices.

## Step 5: Print one real menu (1 min)

Replace `TaskAlfa_3552ci` with the name from Step 1 if yours differs.

```bash
cd ~/BeerSaver && MENU_PRINTER=TaskAlfa_3552ci MENU_COPIES=1 python3 tap_sync.py --live --force --no-untappd
```

A tap menu should come out of the Kyocera (`MENU_COPIES=1` keeps the test to one sheet; the live sync prints 10). `--no-untappd` keeps Untappd untouched during this test.

## Step 6: Turn it on, every 5 minutes (3 min)

Again, swap in your printer name if it differs. Paste the **whole block**:

```bash
PRINTER=TaskAlfa_3552ci
mkdir -p ~/Library/LaunchAgents
cat > ~/Library/LaunchAgents/com.basiccity.tapsync.plist <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.basiccity.tapsync</string>
  <key>ProgramArguments</key><array>
    <string>/usr/bin/python3</string><string>$HOME/BeerSaver/tap_sync.py</string><string>--live</string>
  </array>
  <key>EnvironmentVariables</key><dict><key>MENU_PRINTER</key><string>$PRINTER</string></dict>
  <key>StartInterval</key><integer>300</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>$HOME/BeerSaver/tap-sync.log</string>
  <key>StandardErrorPath</key><string>$HOME/BeerSaver/tap-sync.log</string>
</dict></plist>
EOF
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.basiccity.tapsync.plist && echo "Tap sync is ON"
```

Check it ran:
```bash
sleep 5; tail -n 5 ~/BeerSaver/tap-sync.log
```
You should see a line like `… 22 taps, 0 changed`. If a keychain popup appears, click **Always Allow**.

## Step 7: Keep the Mac mini awake (1 min)

System Settings → **Energy** (or Energy Saver) → turn on **"Prevent automatic sleeping when the display is off"**. The display can sleep; the computer can't. Leave it logged in, since the sync runs in your login.

## Step 8: Real-world test

Next time a **different beer** goes on a Taproom tap, update **ON TAP** in Beer Saver as usual. Within about 5 minutes:
- Untappd shows the new beer on that tap, with prices from `beer-map.json`.
- 10 fresh menus print on the Kyocera.

A brand-new beer that isn't in `beer-map.json` still prints on the menu under its Beer Saver name, but Untappd skips it. The log then shows `TO DO`: add it to the map (ask Claude), add its Toast buttons, and link them in Beer Saver → LINKING.

---

## Everyday commands

| To… | Run |
|---|---|
| See what it's been doing | `tail -n 30 ~/BeerSaver/tap-sync.log` |
| Pause it | `launchctl bootout gui/$(id -u)/com.basiccity.tapsync` |
| Start it again | `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.basiccity.tapsync.plist` |
| Reprint the menu now (10 copies) | `cd ~/BeerSaver && MENU_PRINTER=TaskAlfa_3552ci python3 tap_sync.py --live --force --no-untappd` |
| Reprint just one | same, with `MENU_COPIES=1` before `python3` |
| Change how many print per changeover | in `~/Library/LaunchAgents/com.basiccity.tapsync.plist`, add `<key>MENU_COPIES</key><string>12</string>` inside `EnvironmentVariables`, then Pause and Start it again |
| Get the latest script and beer list | `cd ~/BeerSaver && curl -fsSLO https://raw.githubusercontent.com/bartlanman/Beer-Saver/main/sync/tap_sync.py && curl -fsSLO https://raw.githubusercontent.com/bartlanman/Beer-Saver/main/sync/beer-map.json` |
| Update a password or token | the Step 3 command with `-U` before `-w` |

## Good to know

- **Beer Saver is the master list.** Whatever ON TAP says goes onto Untappd and the printed menu, so keep ON TAP right.
- **Foundry taps** print on the menu but aren't on Untappd (no Foundry menu there yet).
- **The Beer Saver API login is shared** with the Profit Signals integration. If its password changes, update the Keychain (Step 3 with `-U`) or the sync stops. The log shows `403`.
- **The printer is wired** at `192.168.2.126` (fixed IP, since 2026-11-15). If it's ever unreachable, a missed print waits in the Mac's print queue and goes out when the printer is back.
