# 3. Daily variance workflow

About 10 minutes a day. Do it every day: patterns show up in days, and the timeline is easiest to explain while the shift is fresh.

## Step 1: Open yesterday's report

1. **VARIANCE** → it opens on **today**.
2. Click **yesterday's date** on the calendar (top-left). Today's numbers are incomplete until the POS finishes syncing; check **Sales Data last updated** at the bottom.
3. Leave **Shift: ALL** and **Bar: By Beverage**. Use **By Bar** or a single bar (e.g. *1 Taproom*) to see where loss happens.
4. Look at the totals line: `Beer Total: oz Poured · oz Sold · oz Variance · % · $ Slippage (pints)`.

## Step 2: Sort and triage

Click the **oz Variance** column header to sort. Sort the rows into four buckets:

| Pattern | Most likely | Go to |
|---------|-------------|-------|
| Poured > 0, Sold = 0, −100% | Beer not linked, wrong beer on tap in ON TAP, line cleaning, or truly unrung | Step 3 |
| Sold > 0, Poured = 0, +100% | PLU linked to this beer, but the beer is on a different tap (or not on any tap) | [POS linking](06-pos-linking.md), [ON TAP](05-keg-management.md) |
| Steady −5% to −15% | Over-pouring, foam, tasters not rung | Average Pours report, staff coaching |
| Big one-off spike | Blown keg, line cleaning, event, a large unrung pour | Step 3 |

Two beers with mirror-image variance (one +X, one −X) almost always means a **linking** or **tap-assignment** mix-up between them. Fix the setup; it isn't theft.

## Step 3: Drill into a beer

Click the beer's **oz Variance** number. This opens **Unaccounted Variance Details**, which interleaves every pour and every sale by time:

```
12:14 PM          16.00 sold   Hornig 16oz - <server>
12:16 PM  16.65 poured   -0.65  1 Taproom - 01
12:41 PM          16.00 sold   Hornig 16oz - <server>
12:41 PM  14.71 poured   +0.64  1 Taproom - 01
12:54 PM  14.71 poured  -14.07  1 Taproom - 01   ← pour with no sale
```

Read it like a ledger. A pour that never gets "paid off" by a nearby sale is unaccounted. The server name on the sale line tells you who was ringing. On a shared POS login, that may be a generic user.

Other useful views:
- **oz Poured** → every pour with time and meter (tap). Look for runs of tiny pours (foam, top-offs) or one big pour (pitcher, flush).
- **oz Sold** → every PLU sale: which button, how many, which revenue center.
- **View Timeline** (top of the daily report) shows the whole day across all taps. It is split into **Pre-Opening**, **Day** and **After-Hours** totals based on your Hours of Operation.

## Step 4: Classify what isn't loss

On the variance details page or the timeline, tick the pours, then use the icons:

| Icon (hover title) | Use for |
|--------------------|---------|
| **Move to Line Cleaning (Water)** | Water flushes during line cleaning |
| **Move to Line Cleaning (Beer)** | Beer pushed out during cleaning or re-priming |
| **Move to Adjustment (Beer)** | Anything else legitimate. Pick a reason (below). |

Adjustment reasons: **Spillage, Calibration, Foam, Kitchen, Blown Keg, Wrong Mapping, Sample, Event Pours, Canning, Employee Error, Other (Non-Beer), Other (Beer), Line Cleaning Water, Line Cleaning Beer.**

- Moved pours leave the variance and show up in the **Adjustment Report** or **Line Cleaning Reports**. Use **Move Back** there to undo.
- Be honest. Adjustments that just hide loss destroy the report's value. Only move pours you can explain.

## Step 5: Annotate

At the bottom of the daily report, **Remarks → Edit** lets you leave a note on the day ("Keg blew on tap 4 at 7pm", "Staff training pours"). Notes help whoever reviews later, and support when they audit.

## Step 6: Fix the cause

- Wrong beer on a tap → fix in **ON TAP** with the actual change time. See [Keg management](05-keg-management.md).
- Unlinked or mislinked PLU → **LINKING**. See [POS linking](06-pos-linking.md).
- Off-hours pours → check **Hours of Operation**, and ask who was in the building.
- Chronic over-pour → **Average Pours** report, then coach.

## Weekly and monthly

- **Weekly**: Overview → *Last 7 Days* chart. Look for a day that stands out. Check **Average Pours**. Check **Temperature Exceptions**.
- **Monthly**: VARIANCE → **Monthly**. Sort by **Retail Slippage $**. Export (CSV icons) for your P&L or bookkeeping. Look at **Keg Change History** yields.
- Track the **Beer Total %** over time. BeerSAVER says most customers get to the 1–3% range. Set a target and watch the trend.
