# 8. Troubleshooting variance

Start with **setup** problems. They cause the biggest, most dramatic numbers. Real loss tends to be a steady few percent.

## Symptom → cause → fix

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Beer shows **poured, 0 sold, −100%** | (a) Its POS buttons aren't linked (b) a different beer is actually on that tap (c) line cleaning or flush (d) truly unrung | (a) LINKING → find the button → link (b) ON TAP → UPDATE with the real change time (c) move pours to Line Cleaning (d) talk to the shift |
| Beer shows **0 poured, sold > 0, +100%** | Its button is linked to it, but the beer isn't on any tap in ON TAP, or the button is linked to the wrong beer | ON TAP: put it on the right tap. LINKING: fix the button. |
| **Two beers mirror each other** (+X / −X) | Taps or buttons swapped between them | Check ON TAP assignments and LINKING for both |
| Pours on **\*EMPTY** | Tap was used but not assigned | ON TAP → UPDATE that tap to the real beer at the right time |
| Variance **% below −100%** | Some sales exist, but pours far exceed them | Usually setup: wrong beer on tap or a partial link. Check both. |
| **Kegs Rollover: N** on ON TAP | Keg changes not recorded | Record retaps (Retap Same Beer Keg) at the right times |
| Steady **−8% to −15%** across most beers | Over-pouring, foam, unrung tasters | Average Pours report; temperature; staff training; ring tasters |
| One beer always worst | Foaming line (temp, pressure, line length), or one bartender's habit | Check that beer's Temperature Exceptions and line; see the pour pattern in Pours Report |
| Lots of **tiny pours** (1–3 oz) on a tap | Foam dumping, sampling, top-offs | Fix foam (temp/gas); ring samples |
| **Off-hours pours** | Line cleaning, prep, or after-close drinking | Check Hours of Operation are right; classify cleaning; if neither, follow up |
| **Big positive variance** on a size | Serving size value set too high (e.g. a 24 oz mug that really pours 21.5) | Average Pours → adjust the size value or train |
| **Today looks terrible** | Sales haven't synced yet | Check "Sales Data last updated"; review yesterday instead |
| **Sales data last updated** is hours old | POS integration down | Contact support. Pours keep recording, and sales usually backfill. |
| Temperature reading **stuck** or missing | Sensor or box offline | Check the control box has network/PoE; contact support |
| A **new POS item** doesn't appear in LINKING | Sync delay | Wait up to 90 minutes, then check the **New PLU** tab |
| Slippage $ looks wrong | Wrong beverage price | Settings → Beverages → Edit / Set Price |
| Line-cleaning pours **still in variance** | Not auto-detected | Tick them on the timeline → Move to Line Cleaning (Water/Beer) |

## A 3-question test for any bad number

1. **Was the right beer on that tap at that time?** → ON TAP / Keg Change History
2. **Is every button that sold this beer linked to it, at the right size?** → Check Mapping / LINKING
3. **Are the leftover pours explainable** (cleaning, blown keg, foam, event)? → classify them

Whatever survives all three is real unaccounted beer.

## Reading the timeline for loss patterns

- **Pour with no sale within a few minutes** = the classic unrung drink.
- **Sales cluster at close, pours spread out** = drinks rung late (end-of-night tab entry). Not loss, but it makes shift reports noisy.
- **Pours right after close** = after-hours drinking, or cleaning. Check which tap.
- **Same server, repeated gaps** = coaching conversation.
