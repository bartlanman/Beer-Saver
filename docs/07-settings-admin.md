# 7. Settings & administration

Open with the **person icon** in the top menu. The left menu is grouped: **Users · Locations · Beverages · POS · Support · BeerSAVER Admin**.

## Users

### User Accounts (`UserDetail.aspx`)

Users are listed per location: **Login Name · Name · Access Level · Last Login · # of Logins (last 7 days)**.

Access levels seen: **Admin**, **Employee**, **Developer - Admin** (BeerSAVER / integration staff).

Per-user actions:
| Action | Does |
|--------|------|
| **Alert** | Set that user's alert subscriptions |
| **Location** | Which locations the user can see |
| **Customize** | Per-user view/profile options |
| **Edit** | Name, login, access level |
| **Delete** | Remove the user |

**Add New User** sits at the bottom of each location. Give managers their own login. Shared logins make "Changed By" in Keg History useless. Remove people who leave.

### Change Password (`ChangePassword.aspx`)

### Alerts

- **System Messages** (`NotificationPage.aspx`): messages from BeerSAVER (outages, updates).
- **My Alerts Settings** (`AlertSetup.aspx`):
  - **Notification Time**: the window when you want alerts (start–end time) and your **Time Zone**.
  - **Off Hours Poured Alert**: notifies you when beer is poured outside Hours of Operation. **Set Beverages** / **Set Parameters**.
  - **Full Variance Report**: the daily emailed variance report. **Set Beverages** / **Set Parameters**.
  - **Variance and slippage alerts (theft)**.
  - **Cooler Room Temp. Alert**: **Set Parameters** (thresholds).
  - **System malfunction alerts**: e.g. a meter or box goes offline.

Recommended: owner/GM gets the Full Variance Report daily plus Off-Hours and Temp alerts. Bar managers get Off-Hours and Variance alerts.

## Locations

### Locations (`BranchMain.aspx`)

Each location (with phone, fax, email) and its **bars** (pouring stations). **Edit** a bar to rename it. Bar names appear on every report.

### Hours of Operation (`OperatingHourMain.aspx`)

Open/close time for each day of the week, per bar and for the location. You can define **Shifts**. The AM/PM checkbox switches the display.

This setting defines **off-hours**. Pours outside these hours are flagged in the header, in alerts, and in the timeline's Pre-Opening and After-Hours totals. Keep it current: holiday hours, events and seasonal changes. Wrong hours create false off-hours alerts, or hide real ones.

## Beverages

### Beverages (`BeverageMain.aspx`)

Every beverage by **Location** and **Type** (Draft…), grouped by category. Each shows its **Retail Price** (e.g. `$5.60/16`, meaning $5.60 per 16 oz).

- **Edit** sets the name, category, and **price** (retail, plus cost if used). Price drives **Slippage $**. A wrong price means a wrong dollar figure.
- **Add New Beverage**, **Sort the Beverages**, **Reset Sort**, **Set Price** (bulk).
- Watch for **duplicates** (two beverages with the same name). Pours and sales can land on different copies. Merge by relinking PLUs and taps to one copy **(ask support to delete the duplicate)**.

### Beer Menu Settings (`BeerMenuSettings.aspx`)

eBeerMenu layout, **Preview**, **Print Beer Menu**, **Mobile Menu URL** and **QR code**. See [Keg management → eBeerMenu](05-keg-management.md#ebeermenu).

### Serving Sizes

`PLUSizeMain.aspx`: the size list used for linking: **Size (name) · Size Value · Unit · Cocktail**. **Add New Retail Size**, **Edit**, **Update**.

- The *name* is a label. The *value* is what counts. A taster named "4" can be valued at 5.00 oz if your taster glass really pours 5.
- Use **Average Pours** to set values that match reality. If 24 oz mugs average 21.5 oz with a proper head, decide whether to train toward 24 or set the value to what you actually serve.

## POS

- **PLU List** (`PLUMain.aspx`) and **PLU Linking** (`PLUBeverageMain.aspx`). See [POS linking](06-pos-linking.md).

## Support

### Container Sizes (`BeverageSizeMain.aspx`)

Keg sizes: **Size · Value · Unit · Keg · Desc 1–3**. The defaults:

| Size | oz | Typical |
|------|----|---------|
| 15.5 gal | 1,984 | ½ bbl (domestic, craft) |
| 13.2 gal | 1,690 | 50 L import (e.g. Guinness, Heineken, Stella) |
| 5.16 gal | 661 | 20 L / sixtel |

**Add New Container Size** for ¼ bbl (7.75 gal), 30 L, etc.

### Line Calibration (`CalibrationMain.aspx`)

Choose **Location**, **Control Box** (*All Boxes / Primary-01 / Primary-02 / Secondary*), and a **Start/End time**, then **GO** to see the metered total. With the calibration controls (**Accept / Refresh / Save**) you can correct a meter's factor.

Typical calibration check:
1. Pour into a calibrated container (e.g. exactly 64 oz) on one tap, and note the time.
2. Pull that time window here and compare the metered ounces.
3. A consistent difference of a few % or more → recalibrate.

> Calibration changes affect every future reading. **Do this with BeerSAVER support**, or only if they have trained you on it.

## BeerSAVER Admin

### Server Detail (`ServerDetail.aspx`)

The list of servers (employees) that came from the POS: **ID · Name**, plus **Add New Server** and **Edit**. Server names appear on sales lines in the variance details. Some entries are system users (online ordering, kiosk, generic POS user) and are marked "DO NOT DELETE".
