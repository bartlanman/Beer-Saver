# 2. Portal map

Base URL: `https://admin.usbeersaver.com/BeerSAVER/html/`

The portal is an ASP.NET web app. On a narrow window the top menu collapses into a **☰** button (top-left).

## Header bar (every page)

- **Cooler temperatures**: one reading per cooler / control box (e.g. *Draft Box 40.6°F · Foundry 43.9°F · Tap Room 41.7°F*). Click a reading to open **Temperature History**.
- **Alert: X oz poured during today's off hours**.
- **Today's Slippage: −X oz**.
- **Pure Chat bubble** (bottom-right): live chat / message to BeerSAVER support.
- **"Email or Phone# / Message" box**: a quick contact form to support, on every page.

## Main menu

| Menu | Page | Purpose |
|------|------|---------|
| **OVERVIEW** | `Home.aspx` | Dashboard: sold vs poured chart, variance by day, popular beverages |
| **VARIANCE** | `Report_Sales.aspx?g=D` | Daily Variance Report. This is the hub for all reports. |
| **ON TAP** | `CurrentKegStatus.aspx` | Current Keg Status: what's on each tap, % remaining, change beer, retap |
| **LINKING** | `BeverageMapping.aspx` | Link POS buttons (PLUs) to beverages and sizes |
| **👤 (person icon)** | `UserDetail.aspx` | Settings & admin area |
| **LOGOUT** | `Logout.aspx` | |

## Overview (`Home.aspx`)

- **Location** selector and **Date Range** (Today, Yesterday, Last 7/14 Days, This/Last Month, This/Last Year).
- **Variance Performance** chart and table: Sold / Poured / Variance per day.
- **Popular Beverages**: top 5/10/20 beers poured. Filters: date range, country, state/province. The country and state filters suggest this panel benchmarks the wider BeerSAVER network, not just your own taps **(confirm with support)**.

## Variance reports (left sub-menu under VARIANCE)

| Report | Page |
|--------|------|
| Variance Report: Daily / Monthly / Yearly / Custom | `Report_Sales.aspx` (`?g=D`, `?g=M`, `?g=Y`), Custom = `ReconcileReport.aspx` |
| Variance Log | `VarianceLogReport.aspx` |
| Average Pours | `ReportAvgPours.aspx` |
| Adjustment Report | `PourAdjustment.aspx` |
| Enterprise Report | `Report_Enterprise.aspx` |
| Line Cleaning Reports: Daily / Monthly / Yearly | `LineCleaningReport.aspx` (`?g=D`, none = monthly, `?g=Y`) |

Drill-downs from a variance row:

| Click on… | Opens |
|-----------|-------|
| **oz Poured** | `Report_SalesDetail.aspx`: Pours Report (every pour by time & meter) |
| **oz Sold** | `Report_SalesPLU.aspx`: Sales Report (every PLU sale by time, revenue center) |
| **oz Variance** (daily) | `Report_SalesVariance.aspx`: Unaccounted Variance Details (pours and sales interleaved) |
| **oz Variance** (monthly/yearly) | `Report_SalesVarDetail.aspx`: variance by month for that beer |

## Keg management (sub-menu under ON TAP)

| Page | URL |
|------|-----|
| Current Keg Status | `CurrentKegStatus.aspx` |
| Retap Same Beer Keg | `InventoryRetapKeg.aspx` |
| Keg Change History | `KegHistory.aspx` |
| Pre-link POS Buttons | `BeverageMapping.aspx` (same as LINKING) |

## Temperature

| Page | URL |
|------|-----|
| Temperature History | `TemperatureInfo.aspx?BoxID=…` |
| Temperature Exceptions | `TemperatureException.aspx` |

## Settings & admin (person icon)

| Group | Page | URL |
|-------|------|-----|
| Users | User Accounts | `UserDetail.aspx` |
| | Change Password | `ChangePassword.aspx` |
| | Alerts (System Messages / My Alerts Settings) | `NotificationPage.aspx`, `AlertSetup.aspx` |
| Locations | Locations | `BranchMain.aspx` |
| | Hours of Operation | `OperatingHourMain.aspx` |
| Beverages | Beverages | `BeverageMain.aspx` |
| | Beer Menu Settings (eBeerMenu) | `BeerMenuSettings.aspx` |
| | Serving Sizes | `PLUSizeMain.aspx` |
| POS | PLU List | `PLUMain.aspx` |
| | PLU Linking | `PLUBeverageMain.aspx` |
| Support | Container Sizes | `BeverageSizeMain.aspx` |
| | Line Calibration | `CalibrationMain.aspx` |
| BeerSAVER Admin | Server Detail | `ServerDetail.aspx` |
