# 1. How BeerSAVER works

## The data flow

```
 Keg ──► Flow meter (one per line, in the cooler)
             │  ounces poured, time-stamped
             ▼
       Control box (PoE-powered, in/near cooler) ──► BeerSAVER cloud
                                                         ▲
 POS (Toast, Aloha, Micros, Square, etc.) ── sales by button (PLU) ──┘
                                                         │
                                       Portal + mobile apps: variance, kegs, alerts
```

- **Flow meters**: Swiss-made, NSF-approved, installed on each line in the cooler room, with a lifetime warranty (per BeerSAVER).
- **Control box**: collects the meter readings. It runs on **PoE** (Power over Ethernet), so the cooler doesn't need an outlet. Larger sites have several boxes. The calibration screen lists them as *Primary-01*, *Primary-02*, *Secondary*, etc.
- **Temperature sensors**: each cooler or control-box area reports a liquid temperature. It shows in the portal header (e.g. "Tap Room 41.7°F").
- **Cloud**: pour data goes straight to BeerSAVER's cloud servers. Nothing is stored on your POS.
- **POS integration**: the POS sends every sale to BeerSAVER. Each sold item is a **PLU** (a POS button or menu item). BeerSAVER needs to know which **beverage** and which **serving size** each PLU represents. That is the job of **Linking**.

## Key terms

| Term | Meaning |
|------|---------|
| **Location / Branch** | A venue or account (e.g. one city location). Has its own taps, hours, beverages and PLUs. |
| **Bar / Pouring station** | A sub-area of a location with its own taps, e.g. "1 Taproom", "2 Foundry", "3 Draft Box". Reports can be filtered by bar. |
| **Tap order** | The tap's identifier, shown as `Bar - Tap#` (e.g. `1 Taproom - 07`, `1 Taproom - DB 2`). |
| **Beverage** | A beer (or wine or cocktail) defined in BeerSAVER. Taps get assigned beverages; PLUs get linked to beverages. |
| **\*EMPTY** | A placeholder beverage for a tap with nothing on it. Pours on an *EMPTY tap can't be matched to sales. |
| **PLU** | A POS item/button (name + PLU number or ID). Linked to a beverage + serving size. |
| **Serving size** | The ounces a PLU represents, e.g. size name "16" = 16.00 oz. A size *name* can differ from its *value*. For example, a "4" taster may be set to count as 5.00 oz. |
| **Container (keg) size** | 15.5 gal (½ bbl, 1,984 oz), 13.2 gal (50 L, 1,690 oz), 5.16 gal (20 L sixtel, 661 oz) by default. More can be added. |
| **oz Poured** | Measured by the meters. |
| **oz Sold** | Number of PLUs sold × each one's linked serving size. |
| **oz Variance** | Sold − Poured. Negative = loss. |
| **%** | Variance ÷ Sold. It can exceed −100% when little was sold. |
| **Slippage** | Variance converted to dollars. Toggle **Retail \| Cost \| Profit**. Pints = oz ÷ 16. |
| **Off-hours poured** | Ounces poured outside your **Hours of Operation**. Often line cleaning, sometimes a red flag. |
| **Line cleaning** | Pours flagged as water or beer used during line cleaning. BeerSAVER's AI auto-detects many cleaning cycles. You can also move pours there by hand. |
| **Adjustment** | Pours you move out of variance with a reason (Spillage, Foam, Blown Keg, Sample, etc.). |
| **Retap** | Recording that a tap got a fresh keg. It resets "keg remaining". |
| **Keg yield** | Of a finished keg, the share that was sold, shown in Keg Change History. |

## How "sold ounces" are calculated

For each sale BeerSAVER multiplies **number sold × linked serving size value**. Two consequences:

- If a PLU is linked to the **wrong beer**, that beer gets ounces it never poured (positive variance). The real beer looks like pure loss.
- If a PLU is linked to the **wrong size**, every sale is off by the difference. Example: a 24 oz button linked as 16 oz under-counts 8 oz per sale.

## The apps

- **BeerSAVER App** (iOS/iPad; also runs on Apple-silicon Macs): daily summary, inventory (poured/sold/variance per beer), current temperature, keg levels, alerts, and remote retap.
- **Keg Management App**: % remaining per keg, custom keg sizes and colors, retap scheduling by beer and time, and beer changes via date/time/new-beer dropdowns.
- **eBeerMenu** (add-on): a digital tap list for TVs (Firestick, Chromecast, tablet), a mobile page with a QR code, and a printable PDF. Keg levels are live. It's fed from the On Tap screen. See [Keg management](05-keg-management.md#ebeermenu).

## Data freshness

Every variance report footer shows **Pour Data last updated** and **Sales Data last updated**. Pour data is near-real-time. Sales data arrives from the POS on a short delay of a few minutes to longer, depending on the integration. **Judge a day only after it's closed.** Today's report will always look worse than it really is until the last sales sync.
