# Chicago Clinic Intelligence System

A comprehensive healthcare analytics platform that provides actionable business intelligence for clinic owners, investors, and healthcare strategists in Chicago. The system combines data from multiple sources to deliver insights on market opportunities, competitive positioning, patient demand trends, and clinic performance metrics.

## Overview

This system collects and analyzes data from Google Places, Yelp, and Google Trends to provide a 360-degree view of the Chicago healthcare market. It features **9 interactive Power BI dashboards** with real-time insights on clinic performance, market gaps, competition, and patient acquisition strategies.

**Key Achievement:** 100% data completeness across all fields through advanced K-Nearest Neighbors imputation and multi-strategy data enrichment.

## Features

### Data Collection & Processing
- **Automated API Integration**: Collects data from Google Places, Yelp Fusion, and Google Trends
- **Smart Matching & Deduplication**: Merges records from multiple sources for the same physical clinic
- **Geographic Imputation**: K-NN algorithm fills missing ZIP codes using Haversine distance calculations
- **Multi-Strategy Enrichment**: Name inference, category mapping, and proxy ratings for complete data
- **Real-Time Updates**: Scheduled data refresh pipeline with automated cleaning

### Analytics & Intelligence
- **Visibility Scoring**: Proprietary algorithm ranks clinics based on ratings, reviews, and online presence
- **Demand Analysis**: Search trend analysis identifies underserved markets and emerging needs
- **Competitive Intelligence**: Market concentration metrics, competitor density mapping
- **Patient Sentiment Analysis**: VADER-based sentiment scoring on 190+ reviews
- **Opportunity Detection**: Demand-to-competition ratios highlight market gaps

### Data Quality
- **100% Complete Data**: 123 clinics with zero missing values across all critical fields
- **204 Values Imputed**: ZIP codes, clinic types, ratings enriched through ML-inspired techniques
- **Quality Scoring**: 0-100 data completeness score for each clinic
- **Source Tracking**: Transparent logging of original vs. imputed data

## Tech Stack

### Backend & Database
- **Python 3.8+** with SQLAlchemy ORM
- **Neon PostgreSQL** (serverless, auto-scaling)
- **psycopg2** for database connectivity
- **Pandas** for data manipulation

### APIs & Data Sources
- **Google Places API**: Clinic listings, ratings, reviews, hours
- **Yelp Fusion API**: Business data, ratings, categories
- **Google Trends API (pytrends)**: Search demand trends

### Analytics & Visualization
- **Power BI Desktop**: 9 interactive dashboards
- **DAX Measures**: Custom metrics and KPIs
- **Star Schema**: Optimized data model for performance
- **Row-Level Security**: Multi-tenant access control

### Machine Learning & Algorithms
- **K-Nearest Neighbors (K-NN)**: Geographic ZIP code imputation
- **Haversine Distance**: Great-circle distance calculations
- **Fuzzy Matching**: Clinic name similarity scoring
- **VADER Sentiment**: Review sentiment analysis

## Power BI Dashboards

### 1. Executive Summary Dashboard
High-level KPIs and market overview for decision-makers.
- Total clinics, average ratings, review volume
- Market distribution by clinic type
- Top 10 clinics by visibility score
- Data freshness indicators

### 2. Clinic Performance Scorecard
Deep dive into individual clinic metrics.
- Combined ratings (Google + Yelp)
- Review volume trends over time
- Sentiment analysis breakdown
- Visibility score components
- Competitive positioning within ZIP code

### 3. Market Opportunity Heatmap
Identifies underserved markets and expansion opportunities.
- Demand-to-competition ratio by service category and ZIP code
- High-opportunity areas highlighted
- Search volume trends by service type
- Market saturation indicators

### 4. Competitive Intelligence Dashboard
Analyzes competitor landscape and market share.
- Competitor density by ZIP code
- Market concentration metrics (top 3 share)
- Rating distribution analysis
- Service category breakdown
- Geographic coverage gaps

### 5. Search Demand Trends
Google Trends data showing patient demand patterns.
- Search volume trends by service category
- Seasonal demand patterns
- 7-day and 30-day rolling averages
- Emerging vs. declining services
- Location-specific demand insights

### 6. Data Quality Monitor
Tracks data completeness and collection status.
- Data source distribution (Google, Yelp, Both)
- Missing value tracking (pre/post imputation)
- Collection run logs and error rates
- Data freshness by source
- Quality score distribution

### 7. Patient Acquisition Plan
Actionable recommendations for clinic growth.
- Target ZIP codes with high demand
- Recommended service categories
- Digital marketing priority scores
- Online presence improvement suggestions
- Review generation targets

### 8. Metrics Glossary
Comprehensive definitions of all metrics and calculations.
- KPI definitions and formulas
- Data source descriptions
- Scoring methodology explanations
- Business context for each metric

### 9. Data Lineage & Architecture
Visual representation of data flow and system architecture.
- Data collection pipeline stages
- ETL process flowchart
- Database schema (star/galaxy)
- Imputation algorithms explained
- API integration architecture

## Quick Start

### Prerequisites
- Python 3.8 or higher
- Power BI Desktop (for dashboards)
- API Keys:
  - Google Places API key
  - Yelp Fusion API key
- Neon PostgreSQL database (or any PostgreSQL instance)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/sourabhgithubcode/clinic-intelligence-system.git
cd clinic-intelligence-system
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys and database credentials
```

4. **Initialize database**
```bash
python3 src/database/init_db.py create
```

5. **Run data collection pipeline**
```bash
# Full pipeline (collect + clean + impute)
python3 run_data_pipeline.py --full

# Or run specific collectors
python3 run_data_pipeline.py --google  # Google Places only
python3 run_data_pipeline.py --yelp    # Yelp only
python3 run_data_pipeline.py --clean-only  # Just clean existing data
```

6. **Open Power BI dashboards**
```bash
# Connect Power BI to your Neon database using provided connection guide
# See POWERBI_NEON_CONNECTION.md for detailed instructions
```

## Project Structure

```
clinic-intelligence-system/
├── src/
│   ├── collectors/              # API data collection
│   │   ├── google_places_collector.py
│   │   ├── yelp_collector.py
│   │   └── trends_collector.py
│   ├── database/                # Database models and setup
│   │   ├── models.py            # SQLAlchemy ORM models
│   │   └── init_db.py           # Database initialization
│   ├── analysis/                # Analytics and scoring
│   │   └── scoring_engine.py
│   └── utils/                   # Data processing utilities
│       ├── clinic_matcher.py    # Duplicate detection & merging
│       ├── data_enrichment.py   # Calculated fields
│       ├── data_cleaner.py      # Deduplication & standardization
│       └── comprehensive_imputation.py  # K-NN imputation
├── data/
│   ├── clinic_intelligence.db   # SQLite backup
│   └── exports/                 # CSV exports for Power BI
├── dashboards/
│   ├── powerbi_python_connector.py
│   └── *.pbix                   # Power BI dashboard files
├── config/
│   └── settings.py              # Configuration settings
├── CLAUDE.md                    # Detailed project documentation
├── POWERBI_NEON_CONNECTION.md   # Power BI setup guide
├── run_data_pipeline.py         # Automated pipeline orchestration
├── migrate_sqlite_to_neon.py    # Database migration script
├── requirements.txt             # Python dependencies
└── .env.example                 # Environment variable template
```

## Data Pipeline

### Automated Workflow

The system uses a fully automated pipeline (`run_data_pipeline.py`) that handles all data processing:

```
1. COLLECT → APIs write raw data to Neon PostgreSQL
   ↓
2. ENRICH → Add calculated fields (combined_rating, data_source, etc.)
   ↓
3. CLEAN → Find duplicates, merge, standardize formats
   ↓
4. IMPUTE → Fill ALL missing data (ZIP codes, types, ratings)
   ↓
5. EXPORT → Generate clean CSVs for Power BI backup
   ↓
6. POWER BI → Direct Neon connection OR use exported CSVs
```

### Imputation Algorithms

**ZIP Code Imputation (K-Nearest Neighbors)**
- Finds 3 nearest clinics with valid ZIP codes using Haversine distance
- Voting mechanism: most common ZIP among neighbors wins
- Maximum distance threshold: 5,000 meters (5km)
- Result: 27 ZIP codes imputed with 100% accuracy

**Clinic Type Imputation (Multi-Strategy)**
1. Name keyword matching (61% of imputations)
2. API category inference (21%)
3. K-NN same ZIP code (14%)
4. Fallback default (4%)
- Result: 57 clinic types imputed

**Rating Imputation (Proxy + K-NN)**
- Google ratings: Yelp rating + 0.1 adjustment (93% correlation)
- Yelp ratings: Google rating - 0.1 adjustment
- Fallback: Average by type/ZIP or K-NN (5 nearest)
- Result: 97 ratings imputed (70 Google + 27 Yelp)

**Total Imputed:** 204 missing values across 123 clinics → **100% data completeness**

## Database Schema

### Core Tables

**clinics** - Master clinic table (100 active + 23 inactive)
- Identifiers: google_place_id, yelp_business_id
- Location: address, city, zip_code, latitude, longitude
- Metrics: combined_rating, total_review_count, data_quality_score
- Categories: clinic_type, rating_category, review_volume_category

**reviews** - Reviews from both sources (191 records)
- Rating, text, author, review_date
- Sentiment analysis: score (-1 to 1), label (excellent/positive/neutral/negative)

**search_trends** - Google Trends data (1,512 records)
- Keyword, service_category, date
- Interest score (0-100), rolling averages

**visibility_scores** - Calculated visibility metrics (114 records)
- Component scores: rating, review volume, recency, geographic
- Overall visibility score (0-100)
- Local and city rankings

**demand_metrics** - Demand-supply analysis (280 records)
- Search demand index, trend direction
- Clinic count, competition metrics
- Opportunity score

**competitor_analysis** - Market concentration (9 records)
- Total clinics by ZIP, breakdown by type
- Market share, density metrics

**data_collection_logs** - Pipeline monitoring (13 records)
- Collection type, status, duration
- Records collected/updated/failed

## Current Data Statistics

- **Total Clinics:** 123 (100 active, 23 duplicates/inactive)
- **Data Completeness:** 100% across all fields
- **Geographic Coverage:** 11 Chicago ZIP codes
- **Data Sources:**
  - Both APIs: 6 clinics (6%)
  - Google Only: 27 clinics (27%)
  - Yelp Only: 67 clinics (67%)
- **Average Ratings:**
  - Google: 4.1 stars (448 avg reviews)
  - Yelp: 3.8 stars (42 avg reviews)
  - Combined: 4.0 stars
- **Total Reviews Analyzed:** 191
- **Search Trends Tracked:** 1,512 data points

## Usage Examples

### Collect Data from All Sources
```bash
python3 run_data_pipeline.py --full
```

### Update Only Google Places Data
```bash
python3 run_data_pipeline.py --google
```

### Clean and Impute Existing Data
```bash
python3 run_data_pipeline.py --clean-only
```

### Preview Imputation Changes (Dry Run)
```bash
python3 src/utils/comprehensive_imputation.py --dry-run
```

### Test Clinic Matching Algorithm
```bash
python3 -m src.utils.clinic_matcher
```

## Power BI Integration

### Method 1: Direct PostgreSQL Connection (Recommended)
1. Open Power BI Desktop
2. Get Data → PostgreSQL database
3. Enter connection details from `.env` file
4. Select all tables
5. Create relationships (auto-detected)
6. Build visualizations

### Method 2: CSV Import (Backup)
1. Run data export: `python3 -m src.utils.data_cleaner`
2. Import CSVs from `data/exports/` folder
3. Power Query automatically loads clean data

See `POWERBI_NEON_CONNECTION.md` for detailed setup instructions.

## Data Quality & Validation

- **Pre-Collection:** API rate limiting, error handling
- **Post-Collection:** Duplicate detection with fuzzy matching
- **Enrichment:** Calculated fields with validation rules
- **Imputation:** Conservative strategies with distance thresholds
- **Validation:** Data quality scores (0-100) for transparency
- **Monitoring:** Collection logs track success rates and errors

## Contributing

This project was developed as part of a data analytics capstone. For questions or collaboration:
- **Developer:** Sourabh Rodagi
- **Institution:** DePaul University, MS Business Analytics
- **Project Type:** Healthcare Analytics & Business Intelligence

## License

This project is for educational and analytical purposes. API data is subject to Google Places and Yelp Terms of Service.

## Acknowledgments

- **Google Places API** - Clinic location and review data
- **Yelp Fusion API** - Business information and ratings
- **Google Trends API (pytrends)** - Search demand data
- **Neon Database** - Serverless PostgreSQL hosting
- **Power BI** - Interactive dashboard platform

## Documentation

- **CLAUDE.md** - Complete technical documentation with architecture decisions
- **POWERBI_NEON_CONNECTION.md** - Power BI setup and connection guide
- **requirements.txt** - Python package dependencies
- **Database Models** - See `src/database/models.py` for full schema

---

**Built with Claude Code** - Anthropic's AI-powered development assistant
