# 4. Reports reference

All reports live under **VARIANCE**. Common controls:

- **Location** dropdown (multi-location accounts).
- **Calendar** (month/year pickers plus day grid; click a week number to select the week).
- **Slippage: Retail | Cost | Profit**: switches how $ is calculated. Retail uses the beverage's retail price per oz, set in Settings → Beverages.
- **Bar: By Beverage | By Bar | <each bar>**.
- **Shift**: ALL or a single shift (shifts come from Hours of Operation).
- **Column headers are sortable**. Click them.
- **Off hours poured: (X oz)**: clickable; shows the off-hours pours.

## Variance Report (Daily / Monthly / Yearly / Custom)

Columns: **Beverage · oz Poured · oz Sold · oz Variance · % · Retail Slippage**, grouped Draft → Beer, with **Beer Total**, **Draft Total** and **Slippage Total** (also shown in pints).

- **Daily**: one day. Includes **View Timeline** and **Remarks**.
- **Monthly**: pick a month. The variance drill-down shows variance by month for the year.
- **Yearly**: whole year.
- **Custom** (`ReconcileReport.aspx`): any start/end **date and time**. Good for a single event, a shift that crosses midnight, or a keg's life. Has **Expand All / Collapse All**.

**Exports** (icons at the bottom):
| Icon | Exports |
|------|---------|
| *detailed_to_csv* | Detail rows (pours) |
| *summary_to_csv* | The summary table |
| *mix_to_csv* | The sales mix (PLUs sold) |

Footer: **Pour Data last updated** / **Sales Data last updated**.

## Variance Log

A single chronological list of every pour and every sale for the day: **Time · Beverage · oz Poured · oz Sold · oz +/-**. Fastest way to see a shift as it happened. Opens in a stripped-down page; use your browser's back button.

## Average Pours

Average actual pour vs the target for each **serving size**:

```
Serving Size Name   Serving Size   Avg. Pour   Plus/Minus
16                  16.00 oz       15.93 oz    -0.07
24                  24.00 oz       21.50 oz    -2.50
```

How to read it:
- **Plus** means bartenders pour more than the size. Classic over-pour.
- **Minus on large sizes** (e.g. 24 oz mugs averaging 21.5) usually means the glass doesn't hold the nominal size with a proper head, or the size is set wrong. That gap still shows up as positive variance per sale, so set the serving-size *value* to what is really poured. See [Settings → Serving Sizes](07-settings-admin.md#serving-sizes).
- The averages come from matching pours to sales, so heavy unrung pouring skews them.

## Adjustment Report

Every pour you moved to **Adjustment**, with its reason. Tick pours and **Move Back** to return them to variance.

## Enterprise Report

A Custom-style variance report (start/end dates, Retail/Cost/Profit, Expand/Collapse) across **all locations** on the account. For multi-unit operators. It may also count only in-hours pours **(confirm with support)**: on the same day it showed less pour volume than the daily report, which seems to leave out pre-opening pours.

## Line Cleaning Reports (Daily / Monthly / Yearly)

**Tap · Beverage · Wasted (beer) · Water**, per period. "No wasted beverage for this day" means nothing was classified as cleaning. Use it to:
- Confirm cleaning actually happened on schedule (water volume per tap).
- Watch beer wasted during cleaning. Big numbers mean lines weren't drained before cleaning, or weren't primed carefully after.

## Drill-down pages

| Page | Shows |
|------|-------|
| **Pours Report** (click oz Poured) | Pouring station, meter, oz per pour, with time. Filter by station and shift. |
| **Sales Report** (click oz Sold) | PLU number, item sold, number sold, oz sold, revenue center, time. Filter by bar. |
| **Unaccounted Variance Details** (click oz Variance, daily) | Pours and sales interleaved, running variance, adjustment tools, **Show Graph**, export. |
| **Variance Details** (click oz Variance, monthly) | That beer's variance month by month for the year. Great for spotting when a problem started. |

## Temperature

- **Temperature History**: pick a cooler and a date; see the readings. **Refresh** reloads them.
- **Temperature Exceptions**: every period in the last 7/14 days or last month where a cooler went **below 30.0° or above 42.0°**, with time span and temperature range. Warm spikes cause foam, and foam shows up as variance.
