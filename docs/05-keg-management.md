# 5. Keg management (ON TAP)

The tap list in BeerSAVER is what turns a meter reading into a beer name. If tap 7 says "Mayor of Munich" but you hooked up a different beer, every ounce gets charged to the wrong beer. **Keep ON TAP in sync with the cooler, every keg change, every time.**

## Current Keg Status (`CurrentKegStatus.aspx`)

One row per tap:

| Column | Meaning |
|--------|---------|
| **Tap Order** | `Bar - Tap#` |
| **Beverage** | What BeerSAVER thinks is on the tap. Click the name to edit beer-menu info (eBeerMenu). |
| **Last Changed** | When the current keg or beer was recorded |
| **Undo / Update** | **UPDATE** = change the beer on this tap. **Undo** = reverse the last change. |
| **Keg rem.** | % remaining (estimated from start size − poured) |
| **Retap** | Record a fresh keg of the same beer |
| **Amt rem.** | Gallons remaining |
| **Keg size** | Current container size; **Keg** button edits it |

Notes:
- **Kegs Rollover: N** on a row means more beer has gone through than one keg holds since the last change. A keg change was missed. Record the retap(s) at the right time(s).
- Use the **\*EMPTY** beverage for taps that are off. Don't leave an old beer assigned.
- Buttons on this screen include **Check Mapping** (see which PLUs are linked to the selected beverage), **New Beverage**, **Undo Last Change** and **Update eBeerMenu**.

### Change the beer on a tap (new keg of a *different* beer)

1. **ON TAP** → find the tap → **UPDATE**.
2. Choose the **Beverage** (or **New Beverage** if it doesn't exist yet. Set its price in Settings → Beverages afterwards).
3. Set **Date/Time** to when the keg was **actually** hooked up. Back-dating is fine and important: pours after that time move to the new beer.
4. Set **Keg size** and **Full Keg / Partial Keg**. For a partial keg, enter the remaining amount (% or oz).
5. Save. Then use **Check Mapping** to confirm the beer's POS buttons are linked. If not → [LINKING](06-pos-linking.md).

### Retap (fresh keg of the *same* beer)

- From **ON TAP → Retap** on the row, or
- **Retap Same Beer Keg** (`InventoryRetapKeg.aspx`): set the **retap time** per tap and **Save**. You can do several taps at once. Use **Edit** to change the last change's time.

Retaps reset % remaining and keg yield tracking. They don't change variance (the beer's the same), but they keep inventory honest.

### Undo a mistake

**Undo** on the row (or **Undo Last Change**) shows the change it will reverse: beverage, re-tap time, keg size, keg detail, re-tapped by. Confirm with **Yes**.

### Edit keg size / remaining

**Keg** button → **Update Keg**: date, keg size (13.2 / 15.5 / 5.16 gal or custom), **Full** or **Partial**, keg remaining. Use it after a manual keg weigh, or when a sixtel was recorded as a half-barrel.

## Keg Change History (`KegHistory.aspx`)

Every change per tap: **Beverage · Change Date · Changed By · Keg Size · Start Size · Yield**.

- **Yield** = how much of that keg was sold vs poured. Low yield on a finished keg means that keg lost a lot of beer. Compare yields across beers and bars.
- *Changed By* shows who made the change. "BeerSAVER Administrator" means support made it.
- **Expand All / Collapse All**.

## eBeerMenu

eBeerMenu is a digital tap list driven by ON TAP. When you change a beer, the menu changes.

- **Edit a beer's menu card**: click the beer name on ON TAP. Fields: **Display Name**, **Description line 1–3**, **External Logo Url**, **Display Icons** (up to 3), **Beverage Logo** (**Set Logo**), **Unavailable**.
- **Update eBeerMenu** button pushes changes.
- **Settings → Beer Menu Settings** (`BeerMenuSettings.aspx`): choose the page/layout, **Preview**, **Print Beer Menu** (PDF), and get the **Mobile Menu URL** and **QR code** to put on tables.
- TV screens: open the menu URL on a Firestick, Chromecast or tablet browser.
