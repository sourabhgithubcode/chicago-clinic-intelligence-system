# Database Schema and Relationships

## Overview

The Clinic Intelligence System uses a **relational database** with 7 tables designed to store, analyze, and track clinic data from multiple sources (Google Places, Yelp, Google Trends).

---

## Entity Relationship Diagram (ERD)

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CLINIC INTELLIGENCE DATABASE                     │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────────┐
│    DATA COLLECTION       │
│         LOGS            │
│  (Standalone)           │
├──────────────────────────┤
│ PK: id                  │
│ collection_type         │
│ start_time              │
│ end_time                │
│ status                  │
│ records_collected       │
│ error_message           │
└──────────────────────────┘
        (No relationships - monitoring only)


┌──────────────────────────┐
│    SEARCH TRENDS        │
│  (Standalone)           │
├──────────────────────────┤
│ PK: id                  │
│ keyword                 │
│ service_category        │
│ date                    │
│ interest_score          │
│ interest_7day_avg       │
│ interest_30day_avg      │
└──────────────────────────┘
        (No relationships - Google Trends data)


┌──────────────────────────┐          ┌──────────────────────────┐
│       CLINICS           │          │       REVIEWS           │
│   (Master Table)        │◄─────────┤  (Child of Clinics)     │
├──────────────────────────┤  1:Many  ├──────────────────────────┤
│ PK: id                  │          │ PK: id                  │
│ google_place_id (UQ)    │          │ FK: clinic_id           │
│ yelp_business_id (UQ)   │          │ source (google/yelp)    │
│ name                    │          │ review_id               │
│ address                 │          │ author_name             │
│ city, state, zip_code   │          │ rating                  │
│ phone, website          │          │ text                    │
│ latitude, longitude     │          │ review_date             │
│ clinic_type             │          │ sentiment_score         │
│ google_rating           │          │ sentiment_label         │
│ google_review_count     │          └──────────────────────────┘
│ yelp_rating             │
│ yelp_review_count       │
│ hours_json              │          ┌──────────────────────────┐
│ is_open_now             │          │  VISIBILITY SCORES      │
│ is_active               │◄─────────┤  (Child of Clinics)     │
│ last_updated            │  1:Many  ├──────────────────────────┤
│ created_at              │          │ PK: id                  │
└──────────────────────────┘          │ FK: clinic_id           │
                                      │ calculation_date        │
                                      │ rating_score            │
                                      │ review_volume_score     │
                                      │ recency_score           │
                                      │ geographic_score        │
                                      │ overall_visibility_score│
                                      │ local_rank              │
                                      │ city_rank               │
                                      └──────────────────────────┘


┌──────────────────────────┐          ┌──────────────────────────┐
│   DEMAND METRICS        │          │  COMPETITOR ANALYSIS    │
│  (Standalone Aggregate) │          │  (Standalone Aggregate) │
├──────────────────────────┤          ├──────────────────────────┤
│ PK: id                  │          │ PK: id                  │
│ service_category        │          │ zip_code                │
│ zip_code                │          │ calculation_date        │
│ calculation_date        │          │ total_clinics           │
│ search_demand_index     │          │ by_type (JSON)          │
│ clinic_count            │          │ avg_rating              │
│ avg_rating              │          │ avg_review_count        │
│ demand_to_comp_ratio    │          │ top_3_market_share      │
│ opportunity_score       │          │ high_rated_count        │
└──────────────────────────┘          │ clinic_density_per_sqkm │
                                      └──────────────────────────┘
    (Aggregated from Clinics           (Aggregated from Clinics
     and SearchTrends data)             data by geographic area)
```

---

## Table Details

### 1. **CLINICS** (Master Table)
**Purpose**: Central table storing all clinic information from Google Places and Yelp

**Key Fields**:
- `id` (PK) - Unique clinic identifier
- `google_place_id` (Unique) - Google's identifier
- `yelp_business_id` (Unique) - Yelp's identifier
- `name`, `address`, `city`, `state`, `zip_code` - Location info
- `latitude`, `longitude` - GPS coordinates
- `google_rating`, `google_review_count` - Google metrics
- `yelp_rating`, `yelp_review_count` - Yelp metrics
- `clinic_type` - Category (urgent_care, primary_care, etc.)
- `hours_json` - Operating hours (JSON format)
- `is_active` - Active status
- `last_updated`, `created_at` - Timestamps

**Indexes**:
- `google_place_id` (Unique)
- `yelp_business_id` (Unique)
- `zip_code`, `city`, `clinic_type`

**Relationships**:
- **1:Many** → Reviews (One clinic has many reviews)
- **1:Many** → VisibilityScores (One clinic has many daily scores)

---

### 2. **REVIEWS** (Child of Clinics)
**Purpose**: Store individual reviews from Google Places and Yelp

**Key Fields**:
- `id` (PK) - Unique review identifier
- `clinic_id` (FK) - Links to parent clinic
- `source` - 'google' or 'yelp'
- `review_id` - External review identifier
- `author_name` - Reviewer name
- `rating` - Star rating (1-5)
- `text` - Review content
- `review_date` - When review was posted
- `sentiment_score` - Computed sentiment (-1 to 1)
- `sentiment_label` - positive/neutral/negative

**Indexes**:
- `clinic_id` (Foreign Key)
- Composite: (`clinic_id`, `source`)
- `review_date`

**Relationship**:
- **Many:1** → Clinics (Many reviews belong to one clinic)

**Cascade Behavior**:
- If a clinic is deleted, all its reviews are also deleted (`cascade='all, delete-orphan'`)

---

### 3. **SEARCH_TRENDS** (Standalone)
**Purpose**: Store Google Trends data for service keywords

**Key Fields**:
- `id` (PK) - Unique trend record
- `keyword` - Search term (e.g., "urgent care")
- `service_category` - Category classification
- `location` - "Chicago, IL"
- `date` - Trend date
- `interest_score` - Google Trends score (0-100)
- `interest_7day_avg` - Rolling 7-day average
- `interest_30day_avg` - Rolling 30-day average

**Indexes**:
- `keyword`
- Composite: (`keyword`, `date`)
- Composite: (`service_category`, `date`)

**Relationships**:
- **None** - Standalone table (no foreign keys)
- Data is used to calculate DemandMetrics

---

### 4. **VISIBILITY_SCORES** (Child of Clinics)
**Purpose**: Daily calculated visibility metrics for each clinic

**Key Fields**:
- `id` (PK) - Unique score record
- `clinic_id` (FK) - Links to parent clinic
- `calculation_date` - Date of calculation
- `rating_score` - Score based on ratings (0-100)
- `review_volume_score` - Score based on review count (0-100)
- `recency_score` - Score based on recent activity (0-100)
- `geographic_score` - Score based on location density (0-100)
- `overall_visibility_score` - Composite score (0-100)
- `local_rank` - Rank within ZIP code
- `city_rank` - Rank across entire city

**Indexes**:
- `clinic_id` (Foreign Key)
- Composite: (`clinic_id`, `calculation_date`)
- `overall_visibility_score`

**Relationship**:
- **Many:1** → Clinics (Many daily scores belong to one clinic)

**Cascade Behavior**:
- If a clinic is deleted, all visibility scores are deleted

---

### 5. **DEMAND_METRICS** (Standalone Aggregate)
**Purpose**: Aggregate demand analysis by service category and location

**Key Fields**:
- `id` (PK) - Unique metric record
- `service_category` - Service type
- `zip_code` - Geographic area
- `calculation_date` - Date of calculation
- `search_demand_index` - Normalized demand score
- `search_volume_trend` - 'increasing'/'stable'/'decreasing'
- `clinic_count` - Number of clinics in area
- `avg_rating` - Average rating in area
- `total_review_count` - Total reviews in area
- `demand_to_competition_ratio` - Demand ÷ Supply
- `opportunity_score` - Composite opportunity metric

**Indexes**:
- `service_category`, `zip_code`
- Composite: (`service_category`, `zip_code`, `calculation_date`)
- `demand_to_competition_ratio`, `opportunity_score`

**Relationships**:
- **None** - Calculated from Clinics + SearchTrends data

**Data Source**:
- Aggregates data from `clinics` and `search_trends` tables

---

### 6. **COMPETITOR_ANALYSIS** (Standalone Aggregate)
**Purpose**: Market analysis by geographic area

**Key Fields**:
- `id` (PK) - Unique analysis record
- `zip_code` - Geographic area
- `calculation_date` - Date of analysis
- `total_clinics` - Number of clinics in ZIP
- `by_type` - JSON breakdown by clinic type
- `avg_rating` - Average rating in area
- `avg_review_count` - Average reviews per clinic
- `top_3_market_share` - % of reviews from top 3 clinics
- `high_rated_count` - Clinics with 4+ rating
- `low_review_count` - Clinics with <10 reviews
- `clinic_density_per_sqkm` - Clinics per square kilometer

**Indexes**:
- `zip_code`
- Composite: (`zip_code`, `calculation_date`)

**Relationships**:
- **None** - Calculated from Clinics data

**Data Source**:
- Aggregates data from `clinics` table

---

### 7. **DATA_COLLECTION_LOGS** (Standalone Monitoring)
**Purpose**: Track data collection runs for monitoring and debugging

**Key Fields**:
- `id` (PK) - Unique log entry
- `collection_type` - 'google_places', 'yelp', 'trends'
- `start_time` - Collection start timestamp
- `end_time` - Collection end timestamp
- `status` - 'success', 'failed', 'partial'
- `records_collected` - Number of new records
- `records_updated` - Number of updated records
- `records_failed` - Number of failures
- `error_message` - Error description
- `error_details` - JSON with error details

**Relationships**:
- **None** - Standalone monitoring table

---

## Relationship Summary

### Parent-Child Relationships (Foreign Keys)

```
CLINICS (1) ──→ (Many) REVIEWS
  └─ clinic_id foreign key
  └─ CASCADE DELETE: Deleting clinic deletes all reviews

CLINICS (1) ──→ (Many) VISIBILITY_SCORES
  └─ clinic_id foreign key
  └─ CASCADE DELETE: Deleting clinic deletes all scores
```

### Standalone Tables (No Foreign Keys)

```
SEARCH_TRENDS
  └─ Used to calculate DEMAND_METRICS

DEMAND_METRICS
  └─ Aggregated from: CLINICS + SEARCH_TRENDS

COMPETITOR_ANALYSIS
  └─ Aggregated from: CLINICS

DATA_COLLECTION_LOGS
  └─ Monitoring only - no relationships
```

---

## Data Flow

```
┌─────────────────┐
│  API SOURCES    │
│  - Google Places│
│  - Yelp         │
│  - Google Trends│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   COLLECTORS    │
│  (Data Ingestion)│
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│        RAW DATA TABLES              │
│  - CLINICS                          │
│  - REVIEWS                          │
│  - SEARCH_TRENDS                    │
│  - DATA_COLLECTION_LOGS (tracking) │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────┐
│ ANALYSIS ENGINE │
│ (scoring_engine)│
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│     CALCULATED/AGGREGATE TABLES     │
│  - VISIBILITY_SCORES                │
│  - DEMAND_METRICS                   │
│  - COMPETITOR_ANALYSIS              │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  POWER BI       │
│  DASHBOARD      │
└─────────────────┘
```

---

## Key Design Patterns

### 1. **Dual Source Integration**
- Clinics can have data from Google Places, Yelp, or both
- `google_place_id` and `yelp_business_id` are unique but nullable
- Allows matching/merging data from multiple sources

### 2. **Time-Series Data**
- `VISIBILITY_SCORES`: Daily snapshots (via `calculation_date`)
- `SEARCH_TRENDS`: Daily trends (via `date`)
- `DEMAND_METRICS`: Periodic calculations (via `calculation_date`)
- Enables trend analysis over time

### 3. **Aggregate Tables**
- Pre-calculated metrics stored in dedicated tables
- Improves dashboard query performance
- Reduces need for complex real-time calculations

### 4. **JSON Columns**
- `categories`, `hours_json`: Flexible structured data
- `by_type`, `error_details`: Complex nested data
- Allows schema flexibility without migrations

### 5. **Cascade Deletes**
- Reviews and VisibilityScores auto-delete with parent Clinic
- Maintains referential integrity
- Prevents orphaned records

---

## Example Queries

### Get Clinic with All Reviews
```sql
SELECT
    c.name,
    c.google_rating,
    r.rating,
    r.text,
    r.source
FROM clinics c
LEFT JOIN reviews r ON c.id = r.clinic_id
WHERE c.name LIKE '%Michigan Avenue%';
```

### Get Clinic with Latest Visibility Score
```sql
SELECT
    c.name,
    vs.overall_visibility_score,
    vs.local_rank,
    vs.city_rank
FROM clinics c
LEFT JOIN visibility_scores vs ON c.id = vs.clinic_id
WHERE vs.calculation_date = (
    SELECT MAX(calculation_date)
    FROM visibility_scores
    WHERE clinic_id = c.id
);
```

### Find High-Opportunity Markets
```sql
SELECT
    dm.zip_code,
    dm.service_category,
    dm.opportunity_score,
    ca.total_clinics,
    ca.avg_rating
FROM demand_metrics dm
JOIN competitor_analysis ca
    ON dm.zip_code = ca.zip_code
    AND dm.calculation_date = ca.calculation_date
WHERE dm.opportunity_score > 80
ORDER BY dm.opportunity_score DESC;
```

---

## Database Statistics (Current)

- **Total Tables**: 7
- **Tables with Foreign Keys**: 2 (Reviews, VisibilityScores)
- **Standalone Tables**: 5
- **Total Indexes**: 20+
- **JSON Columns**: 4
- **Cascade Relationships**: 2

---

Generated: 2025-12-26
Database Version: SQLite / PostgreSQL Compatible
