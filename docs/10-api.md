# 10. BeerSAVER API

BeerSAVER has a read-mostly REST API for pulling pours, sales, variance, keg levels and temperatures into your own tools (spreadsheets, dashboards, accounting). This page is based on the *BEERSaver API* document BeerSAVER sent to Basic City in November 2026. The calls haven't been tested yet; anything that's an inference is marked **(untested)**.

> **Never commit credentials to this repo.** It is public. Keep the API password in a password manager or an environment variable.

## Basics

| Item | Value |
|------|-------|
| Base URL | `https://api.usbeersaver.com/api/` |
| URL pattern | `https://api.usbeersaver.com/api/{BranchID}/{Function}?{Params}` |
| Auth | HTTP **Basic** auth on **every** request |
| Basic-auth username | `{ClientID}-{UserName}` (client ID, a hyphen, then your portal user name) |
| Basic-auth password | Your BeerSAVER password |
| Basic City's BranchID | **1392** (Waynesboro VA, the "Location ID") |
| All branches you can see | Use BranchID **`-1`** |
| Permissions | Each user can use only certain functions at certain branches. Anything else returns *permission denied*. |

The **Client ID** is the same one you type on the portal login page. It is not the Location ID.

### Dates and "Day of Business"

- Most daily calls take `Year` (4 digits) plus `Day` (or `No`). The day is the **day of the year, 1–366**: Jan 1 = 1, Feb 1 = 32, Nov 8 2026 = 312.
- Calls that take a time range use `Start` / `End` in `yyyy-MM-dd HH:mm:ss tt` format (e.g. `2026-11-08 12:00:00 PM`). URL-encode the spaces (`%20`).
- `Type` = `Day`/`D`, `Week`/`W` or `Month`/`M`. With `Type=W`, `No` is a week number; with `Type=M`, a month number **(untested; inferred from the examples)**.

### Quick test (curl)

```bash
export BS_USER="<ClientID>-<UserName>"   # e.g. 12345-jsmith
export BS_PASS="<password>"
curl -u "$BS_USER:$BS_PASS" "https://api.usbeersaver.com/api/-1/User"
curl -u "$BS_USER:$BS_PASS" "https://api.usbeersaver.com/api/1392/Inventory"
curl -u "$BS_USER:$BS_PASS" "https://api.usbeersaver.com/api/1392/Variance?Year=2026&Day=312"
```

## Endpoints

| # | Endpoint | Method | What it returns |
|---|----------|--------|-----------------|
| 1 | `/-1/User` | GET | The logged-in user: UserID, **ClientID**, access level, name, dates, Locked/Active, default unit and temperature unit |
| 2 | `/{Branch}/branch` | GET | ClientID, ClientName, BranchID, BranchName. With `-1`, every branch you can access. |
| 3 | `/{Branch}/Inventory` | GET | One row per meter/tap: MeterID, MeterNumber, Description, BeverageID/Name, ConnectTime (last keg change), **CurrentKegPctRemaining**, **CurrentKegAmtRemaining**, size, KegCost, **ParPoint** |
| 4 | `/{Branch}/Sales?Year=&Day=` | GET | Every POS sale for the day: LogDate, PLU, Quantity, Size, BeverageID/Name, RevenueCenter, PLUID, **ServerID**, **IsOffHour**. Add `&CountOnly=true` to get only `TotalRecord`. |
| 5 | `/{Branch}/Variance?Year=&Day=` | GET | The daily variance report: one row per beverage with Poured, Sold, Variance, Percentage, ItemSold, Slippage, SlippageType, UnitCost, RetailPrice, category/type |
| 5b | `/{Branch}/Variance?Year=&Day=&Beverage=` | GET | The **Unaccounted Variance Details** for one beer: each pour/sale with LogDate, Poured, Sold, running sums, **Stolen** flag, PLUName, Shift, MeterID, **ServerName**, BarID, RevenueCenterID, PourException info |
| 6 | `/{Branch}/TopPour` | GET | Top N beers by oz poured. `Top=&Year=&No=&Type=` or `Top=&Start=&End=` |
| 7 | `/{Branch}/TopSale` | GET | Top N beers by oz sold. Same parameters as TopPour. |
| 8 | `/{Branch}/TopSalePLU` | GET | Top N POS buttons: BeverageID/Name, LocalPLUNumber, PLUName, Sold (oz), ItemCount. Same parameters plus `OrderBy=oz` or `count`. |
| 9 | `/{Branch}/KegRetap?MeterID=&Time=` | **POST** | Records a **retap** (fresh keg of the same beer) on that meter at that time. 200 = OK; 500 = error, with a message. |
| 10a | `/{Branch}/Temperature?date=` | GET | Every control box with CurrentTemp, TodayLowest, TodayHighest, EarliestUpdate, LastUpdate (°F) |
| 10b | `/{Branch}/Temperature?box=&start=&end=&interval=` | GET | Temperature readings for one box (Time `HH:mm`, Temp °F) every *interval* minutes |
| 10c | `/{Branch}/Temperature?box=&start=&end=` | GET | **Temperature exceptions**: StartTime, EndTime, TempMin, TempMax, Status (Above/Below), TotalMinutes |
| 11 | `/{Branch}/v2_BranchVariance?Year=&Day=` (`&Beverage=`) | GET | Newer ("v2") version of the daily variance summary; same fields as #5, more compact |
| 12 | Variance Timeline | GET | The **View Timeline** data: LogDate, Time, Amount, Unit, **IsPour** (true = pour, false = sale), BeverageName, Description, BeverageID, PourID. Optional `&Beverage=`. |

Notes:
- **Box IDs** for Basic City (from the portal): Draft Box = **2394**, Foundry = **2393**, Tap Room = **2392**. You can confirm them with 10a.
- **Temperature history is kept about 3 months.** For exceptions, keep the range between EarliestUpdate and LastUpdate.
- **MeterID** for KegRetap comes from `/Inventory`. It is not the tap number.
- In the PDF, the Variance Timeline examples are copied from Branch Variance (`v2_BranchVariance`), so the document doesn't give the real function name. **Ask support for it.** Likely `v2_VarianceTimeline` **(untested)**.
- The PDF shows the endpoint as `http://` in the pattern and `https://` in the examples. Use **https**.

## What to build with it

| Idea | Endpoints |
|------|-----------|
| Daily variance email or Slack post to managers | `Variance` (yesterday), then `Variance&Beverage=` for the worst 3 beers |
| A "who poured without ringing" view | `Variance&Beverage=` (rows with `Stolen=true`, plus ServerName nearby) or the Timeline |
| Tap list / low-keg alert (e.g. reorder when below ParPoint) | `Inventory` |
| Push keg levels to Untappd or a menu screen | `Inventory` |
| Monthly slippage into the P&L / bookkeeping | `Variance` for each day of the month, summed |
| Cooler temperature monitoring | `Temperature` (10a/10c) |
| Retap from a button on the bar tablet | `KegRetap` (POST) |

## Open questions for BeerSAVER support

1. What is the exact function name for the Variance Timeline (#12)?
2. With `Type=W` / `Type=M`, is `No` a week/month number or a day number?
3. Are there rate limits?
4. Can we get a read-only API user, separate from the owner's login? Then the POST endpoint can't be used by mistake, and a leaked key can't change keg data.
