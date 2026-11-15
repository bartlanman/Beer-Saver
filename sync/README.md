# Tap sync: Beer Saver → Untappd + printed menu

Staff change kegs in **Beer Saver → ON TAP** only. Every few minutes `tap_sync.py`:

1. reads the tap list from the Beer Saver API (`/1392/Inventory`),
2. spots taps whose beer or keg-change time changed,
3. updates the Untappd **Beer on Tap!** menu for Taproom taps (Foundry taps aren't on Untappd),
4. writes `~/Desktop/Tap Menu/tap-menu.pdf` and sends it to the bar printer,
5. lists manual to-dos for brand-new beers: add to `beer-map.json`, add Toast buttons, link them in Beer Saver.

Toast can't be automated: as far as we know, Toast doesn't let outside tools create menu buttons for a regular restaurant account. New beers get a to-do instead.

## Status

- Beer Saver API read: **working** (tested Nov 12, 2026).
- Menu PDF and change detection: tested offline with sample data.
- Untappd writes and printing: **not yet tested live**. The script runs in dry-run mode until started with `--live`.

## Install (on a Mac that stays on near the printer)

➡️ **Step-by-step for the Mac mini: [INSTALL-Mac-mini.md](INSTALL-Mac-mini.md)**. The short version follows.


1. Store the credentials in the Keychain (not in this repo):
   ```bash
   security add-generic-password -s beersaver-api-user -a "$USER" -w   # paste <ClientID>-<username>
   security add-generic-password -s beersaver-api-pass -a "$USER" -w
   security add-generic-password -s untappd-email      -a "$USER" -w
   security add-generic-password -s untappd-token      -a "$USER" -w   # Untappd for Business > Account > API token
   ```
2. Find the printer name: `lpstat -p`.
3. Dry run: `python3 tap_sync.py --force`. Check the list and open the PDF.
4. Go live: `MENU_PRINTER=<printer> python3 tap_sync.py --live`.
5. Schedule it every 5 minutes with a LaunchAgent (template to come once the printer is picked).

## Files

- `beer-map.json`: Beer Saver beer name → Untappd beer, menu name, brewery, ABV, prices.
- `tap_sync.py`: the sync (Python 3, standard library only).
