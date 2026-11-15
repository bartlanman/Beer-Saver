# BeerSAVER Knowledge Base

How to use and manage **BeerSAVER**, the draft beer flow-metering and variance system from US BeerSAVER Systems. This guide covers the admin portal at `admin.usbeersaver.com`, the mobile apps, and the habits that turn the numbers into less lost beer.

> **Sources.** The portal sections were mapped from a live operator account in November 2026: menus, report names, buttons, dropdown options and settings pages. Hardware, pricing and integration details come from BeerSAVER's public website. Anything that could not be confirmed on screen is marked **(confirm with support)**.

---

## The 60-second version

BeerSAVER puts a flow meter on every draft line in the cooler. Each meter counts the ounces that leave the keg. The system pulls your POS sales and turns each sale into ounces using the serving size of the button that was rung. It then compares the two:

```
Variance (oz) = oz Sold (POS) − oz Poured (meters)
```

- **Negative variance**: more beer left the keg than was sold. That's loss: over-pours, unrung drinks, comps, samples, foam, spills.
- **Positive variance**: more was sold than poured. That is almost always a **setup problem** (a POS button linked to the wrong beer, or a tap showing the wrong beer). It is not "found" beer.
- **Slippage ($)**: variance in ounces × the beer's price per ounce. It can be shown at **Retail**, **Cost**, or **Profit**.

The job is to get negative variance as close to zero as possible. Then keep the setup clean enough that the number can be trusted.

---

## Contents

| # | Guide | What's in it |
|---|-------|--------------|
| 1 | [How BeerSAVER works](docs/01-how-it-works.md) | Hardware, data flow, key terms, the apps |
| 2 | [Portal map](docs/02-portal-map.md) | Every menu, page and URL in the admin portal |
| 3 | [Daily variance workflow](docs/03-daily-variance-workflow.md) | The 10-minute daily routine: read, drill down, classify, annotate |
| 4 | [Reports reference](docs/04-reports-reference.md) | Every report: what it shows, filters, drill-downs, exports |
| 5 | [Keg management (On Tap)](docs/05-keg-management.md) | Changing beers, retapping, keg edits, keg history, eBeerMenu |
| 6 | [POS linking (PLUs)](docs/06-pos-linking.md) | Linking POS buttons to beers and serving sizes |
| 7 | [Settings & administration](docs/07-settings-admin.md) | Users, alerts, locations, hours, beverages, sizes, calibration |
| 8 | [Troubleshooting variance](docs/08-troubleshooting.md) | Symptom → likely cause → fix |
| 9 | [Support, hardware & accounts](docs/09-support-hardware.md) | Getting help, login recovery, hardware facts, integrations |
| 11 | [Tap sync install (Mac mini)](sync/INSTALL-Mac-mini.md) | Beer Saver → Untappd + auto-printed menu: step-by-step setup |
| 10 | [BeerSAVER API](docs/10-api.md) | REST API: auth, endpoints, what to build with it |

---

## Quick start for a new manager

1. **Log in** at <https://admin.usbeersaver.com/BeerSAVER/Logon_new.aspx> with your Client ID, User ID and password, or with Google once your account is linked.
2. Check the **header bar** on every page. It shows cooler temperatures, today's off-hours pours, and today's slippage.
3. Open **VARIANCE**. This is the daily variance report. Look at **yesterday** (pick it on the calendar), not today, because today's sales are still coming in.
4. Sort by **oz Variance** and click into the worst beers. See [Daily workflow](docs/03-daily-variance-workflow.md).
5. Whenever a keg is changed or a new beer goes on, update **ON TAP** right away. Stale tap assignments are the #1 cause of bad numbers. See [Keg management](docs/05-keg-management.md).
6. Whenever a new draft button is added to the POS, link it in **LINKING**. See [POS linking](docs/06-pos-linking.md).

## Golden rules

1. **The tap list must match reality.** Every keg change → update ON TAP at the actual time of the change.
2. **Every draft button must be linked.** That means linked to the right beer and the right serving size.
3. **Every pour gets rung.** That includes comps, staff drinks and tasters. Use comp/taster buttons in the POS and don't pour "off the books".
4. **Classify, don't ignore.** Line cleaning, blown kegs and foam get moved to Line Cleaning or Adjustment with a reason. What's left is true unaccounted beer.
5. **Hours of Operation must be right.** They define what counts as "off-hours" pouring.
