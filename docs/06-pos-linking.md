# 6. POS linking (PLUs)

Every draft button in your POS must be linked to **one beverage** and **one serving size**. BeerSAVER can't know that "Golden Child 16oz" means 16 oz of *Golden Child Bask IPA* until you tell it.

There are two screens that do this.

## LINKING / Pre-link POS Buttons (`BeverageMapping.aspx`)

The main, day-to-day linking screen.

**Filters across the top**
- **Tap**: show PLUs for the beer on a given tap (e.g. `07 [Mayor of Munich]`).
- **Beverage**: All, or one beverage.
- **Select Category**: your POS menu groups (e.g. *Tap Room Beers*, *Foundry Beer*, *Showroom Beer*).
- **Search** box, plus **Clear**.
- **Page Size**: 20 / 40 / 60 / 80 / 100.

**Columns**: Link (checkbox) · **PLU** (POS item name, with its category in brackets) · **PLU Number** (POS ID) · **Beverage** (dropdown) · **Size Name** (dropdown) · **Updated Date**.

**Row colors / legend**: *Originally Linked · Modified · Removed/Incomplete · Not Linked · Linked to Other*.

**To link a button**
1. Find it (search for the item name, or filter by category).
2. Pick the **Beverage** from the dropdown.
3. Pick the **Size** (the size name maps to an oz value, e.g. `16 oz 16`, `24 oz 24`, `5 oz 4`).
4. **Save Changes**. If you leave the page with unsaved changes, you'll be asked to **SAVE & Continue**, **Discard & Continue**, or **Cancel**.

**+ New Beverage** creates a beverage from this screen. **Back to Inventory Page** returns to ON TAP.

> **New POS items take up to 90 minutes to appear here** after they are added to the POS.

## Settings → PLU Linking (`PLUBeverageMain.aspx`)

The same job in a different layout. Use it for bulk work.

- **PLU Type** = POS category. **Cocktail** checkbox shows cocktail PLUs.
- Header shows "*N PLU in use, N PLU linked*". If those two numbers differ, something sold that isn't linked.
- Tabs: **Changed PLU** / **New PLU**. Check these after any POS menu change.
- Each row: PLU name (item/modifier, e.g. `Baby Bask/16oz`, `Baby Bask/Mug 24oz`), PLU number, **Beverage**, **Size**.
- **Save** asks which locations to sync the changed PLUs to (multi-location accounts).

## Settings → PLU List (`PLUMain.aspx`)

A raw list of every item the POS has sent: **PLU · PLU Number · Cocktail · Use · Prev PLU · Date Add/Mod.**

- **Use** = whether BeerSAVER should consider this PLU. Untick cans, bottles and non-draft items so they don't clutter linking.
- **Cocktail** marks wine or cocktail items that use a different size set.
- **Changed PLU / New PLU** tabs show recent POS changes.

## Linking rules of thumb

1. **Only draft items** need linking. Cans, bottles, pitchers sold as packaged product, and food: leave them unlinked or set **Use** off.
2. **Pitchers poured from a tap** are draft. Link them with the correct size (add a 48 or 60 oz serving size if needed).
3. **Every size gets its own link.** 4 oz taster, 8 oz, 16 oz pint and 24 oz mug are separate PLUs (or modifiers), each linked to the same beer with its own size.
4. **Flights**: link each taster PLU or modifier. If the POS sells "Flight" as one item with no beer choice, BeerSAVER can't split it. Ask your POS admin to add beer modifiers, or ring tasters separately.
5. **When a beer rotates off**, relink or retire its buttons. A button still linked to an old beer sends sold ounces to a beer with no pours (+100% variance).
6. **Comps and staff beers** should still be rung on a $0 or comp button that is **linked**, so the ounces are accounted for.
7. After any POS menu change: **LINKING → New PLU / Changed PLU**, then link.

## Example of a linking problem

A day's report showed:
- *Untitled Art New Zealand Lager*: **0 poured, 16 sold (+100%)**
- The sale behind it was a "**Zealandia IPA 16oz**" button.

So the Zealandia button was linked to the wrong beverage. The fix: in LINKING, search "Zealandia", set the right beverage, and save. Also check ON TAP for which tap the poured beer is actually on.
