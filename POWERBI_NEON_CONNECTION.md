# Power BI Connection to Neon Database

## Connection Details

Your clinic intelligence data is now hosted on **Neon PostgreSQL** database.

### Database Credentials

**Connection Information:**
- **Server:** `ep-calm-recipe-a8tryfj4-pooler.eastus2.azure.neon.tech`
- **Port:** `5432`
- **Database:** `neondb`
- **Username:** `neondb_owner`
- **Password:** `npg_fcp6hyHUrPS7`

**Connection String:**
```
postgresql://neondb_owner:npg_fcp6hyHUrPS7@ep-calm-recipe-a8tryfj4-pooler.eastus2.azure.neon.tech:5432/neondb?sslmode=require
```

---

## Method 1: PostgreSQL Connector (Recommended)

### Step 1: Install PostgreSQL Driver

Power BI Desktop needs the Npgsql driver:
1. Download from: https://github.com/npgsql/npgsql/releases
2. Or install via Windows: https://www.postgresql.org/download/windows/

### Step 2: Connect in Power BI

1. Open **Power BI Desktop**
2. Click **Get Data** → **More...**
3. Search for **PostgreSQL database**
4. Click **Connect**

### Step 3: Enter Connection Details

In the PostgreSQL database window:

**Server:**
```
ep-calm-recipe-a8tryfj4-pooler.eastus2.azure.neon.tech
```

**Database:**
```
neondb
```

**Data Connectivity mode:**
- Select **Import** (recommended for best performance)
- Or **DirectQuery** (for real-time data)

Click **OK**

### Step 4: Authentication

1. Select **Database** authentication
2. Enter credentials:
   - **User name:** `neondb_owner`
   - **Password:** `npg_fcp6hyHUrPS7`
3. Click **Connect**

### Step 5: Select Tables

You'll see all 7 tables:
- ✅ **clinics** - Main clinic data (123 records)
- ✅ **reviews** - Customer reviews (191 records)
- ✅ **search_trends** - Google Trends data (1,512 records)
- ✅ **visibility_scores** - Calculated scores (114 records)
- ✅ **demand_metrics** - Market demand analysis (280 records)
- ✅ **competitor_analysis** - Competition metrics (9 records)
- ✅ **data_collection_logs** - Collection history (13 records)

**Select the tables you need** (typically start with `clinics`, `reviews`, and `demand_metrics`)

Click **Load** or **Transform Data** (to clean/shape data first)

---

## Method 2: ODBC Connection (Alternative)

### Step 1: Install PostgreSQL ODBC Driver

1. Download from: https://www.postgresql.org/ftp/odbc/versions/msi/
2. Install the driver (choose 64-bit for most systems)

### Step 2: Configure ODBC Data Source

**Windows:**
1. Open **ODBC Data Source Administrator** (64-bit)
2. Click **Add** → Select **PostgreSQL Unicode**
3. Configure:
   - **Data Source:** `NeonClinicDB`
   - **Server:** `ep-calm-recipe-a8tryfj4-pooler.eastus2.azure.neon.tech`
   - **Port:** `5432`
   - **Database:** `neondb`
   - **User Name:** `neondb_owner`
   - **Password:** `npg_fcp6hyHUrPS7`
   - **SSL Mode:** `require`
4. Click **Test** to verify
5. Click **Save**

### Step 3: Connect in Power BI

1. **Get Data** → **ODBC**
2. Select **NeonClinicDB** from dropdown
3. Click **OK**
4. Select tables and **Load**

---

## Method 3: Direct SQL Query (Advanced)

If you want to load custom queries:

1. **Get Data** → **PostgreSQL database**
2. Enter server and database details
3. Click **Advanced options**
4. Enter SQL query:

```sql
-- Example: Get clinics with combined ratings
SELECT
    id,
    name,
    address,
    city,
    zip_code,
    clinic_type,
    google_rating,
    yelp_rating,
    ROUND((COALESCE(google_rating, 0) + COALESCE(yelp_rating, 0)) / 2, 2) as combined_rating,
    (COALESCE(google_review_count, 0) + COALESCE(yelp_review_count, 0)) as total_reviews,
    latitude,
    longitude
FROM clinics
WHERE is_active = true
ORDER BY combined_rating DESC;
```

---

## Sample Power BI Measures

Once connected, create these DAX measures:

### Combined Rating
```dax
Combined Rating =
    AVERAGEX(
        clinics,
        (clinics[google_rating] + clinics[yelp_rating]) / 2
    )
```

### Total Review Count
```dax
Total Reviews =
    SUM(clinics[google_review_count]) +
    SUM(clinics[yelp_review_count])
```

### Clinic Count by Type
```dax
Clinics by Type =
    CALCULATE(
        COUNTROWS(clinics),
        ALLEXCEPT(clinics, clinics[clinic_type])
    )
```

### Market Opportunity Score
```dax
Opportunity Score =
    AVERAGE(demand_metrics[opportunity_score])
```

---

## Recommended Visualizations

### 1. **Clinic Map**
- Visual: **Map** or **ArcGIS Map**
- Location: `clinics[latitude]`, `clinics[longitude]`
- Size: `Total Reviews`
- Color: `Combined Rating`

### 2. **Rating Distribution**
- Visual: **Clustered Column Chart**
- Axis: `clinics[clinic_type]`
- Values: `Average of google_rating`, `Average of yelp_rating`

### 3. **Geographic Performance**
- Visual: **Table** or **Matrix**
- Rows: `clinics[zip_code]`
- Values: `Count of clinics`, `Combined Rating`, `Total Reviews`

### 4. **Demand vs Supply**
- Visual: **Scatter Chart**
- X-axis: `demand_metrics[search_demand_index]`
- Y-axis: `demand_metrics[clinic_count]`
- Size: `demand_metrics[opportunity_score]`

### 5. **Review Timeline**
- Visual: **Line Chart**
- Axis: `reviews[review_date]`
- Values: `Count of reviews`, `Average of rating`

---

## Troubleshooting

### Error: "Couldn't authenticate"
- **Solution:** Double-check username and password
- Ensure SSL mode is enabled
- Verify firewall isn't blocking port 5432

### Error: "Can't connect to server"
- **Solution:** Check internet connection
- Verify server address is correct
- Try connecting from command line: `psql 'postgresql://neondb_owner:npg_fcp6hyHUrPS7@ep-calm-recipe-a8tryfj4-pooler.eastus2.azure.neon.tech:5432/neondb'`

### Slow Performance
- **Solution:** Use **Import** mode instead of DirectQuery
- Create aggregated tables in Power BI
- Add indexes to Neon database (already included)

### Tables Not Showing
- **Solution:** Ensure schema is `public` (default)
- Refresh metadata in Power BI
- Verify tables exist: Run query in Neon console

---

## Data Refresh Schedule

To keep Power BI dashboard updated:

1. **Power BI Desktop:**
   - Click **Refresh** button manually
   - Or set auto-refresh in dataset settings

2. **Power BI Service (Pro/Premium):**
   - Publish report to Power BI Service
   - Configure scheduled refresh:
     - Gateway: Not needed (cloud database)
     - Frequency: Daily at 3:00 AM (after data collection)
     - Credentials: Store Neon credentials securely

3. **Data Collection Schedule:**
   - Run collectors: `python3 -m src.collectors.google_places_collector`
   - Then `python3 -m src.collectors.yelp_collector`
   - Data updates in Neon automatically
   - Power BI refreshes on schedule

---

## Security Best Practices

1. **Don't share credentials publicly**
2. **Use Row-Level Security (RLS)** in Power BI if needed
3. **Rotate passwords** regularly in Neon console
4. **Monitor query performance** in Neon dashboard
5. **Set up read-only user** for Power BI:

```sql
-- Create read-only user for Power BI (optional)
CREATE USER powerbi_reader WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE neondb TO powerbi_reader;
GRANT USAGE ON SCHEMA public TO powerbi_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO powerbi_reader;
```

---

## Next Steps

1. ✅ Connect Power BI to Neon (follow method 1 above)
2. 📊 Create your first dashboard
3. 📈 Set up scheduled refresh
4. 🎨 Customize visuals and themes
5. 📤 Publish to Power BI Service (if available)

---

**Migration Date:** 2026-01-10
**Database:** Neon PostgreSQL
**Total Records:** 2,242 (123 clinics, 191 reviews, 1,512 trends, etc.)
**Status:** ✅ Active and Ready
