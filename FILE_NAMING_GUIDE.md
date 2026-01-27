# File Naming Guide - Descriptive File Names

This project uses descriptive file names so anyone can understand what each file does without opening it.

## Naming Convention

**Format:** `action_what_purpose.py`

**Examples:**
- `collect_google_places_api_data.py` (not `google_places_collector.py`)
- `calculate_visibility_scores.py` (not `scoring_engine.py`)
- `knn_missing_data_imputation.py` (not `comprehensive_imputation.py`)

## File Inventory

### Root Level Scripts

| File Name | What It Does |
|-----------|--------------|
| `run_automated_data_collection_pipeline.py` | Master script that runs the complete data collection, cleaning, and imputation pipeline |
| `demo_quick_data_collection.py` | Quick demo/test script for trying out data collection from APIs |
| `inspect_database_records.py` | View and explore data stored in the PostgreSQL database |
| `export_clean_data_for_powerbi.py` | Export cleaned data as CSV files for Power BI import |
| `migrate_database_sqlite_to_postgresql.py` | One-time migration script to move data from SQLite to Neon PostgreSQL |
| `test_database_connection.py` | Test connection to PostgreSQL database |

### Data Collectors (`src/collectors/`)

| File Name | What It Does |
|-----------|--------------|
| `collect_google_places_api_data.py` | Collects clinic data from Google Places API (locations, ratings, reviews) |
| `collect_yelp_fusion_api_data.py` | Collects clinic data from Yelp Fusion API (business info, ratings, reviews) |
| `collect_google_trends_search_data.py` | Collects search demand trends from Google Trends API |

### Data Processing (`src/utils/`)

| File Name | What It Does |
|-----------|--------------|
| `calculate_combined_metrics.py` | Calculates combined ratings, data sources, quality scores for each clinic |
| `deduplicate_standardize_data.py` | Finds duplicate clinics, merges them, standardizes phone/name/ZIP formats |
| `duplicate_clinic_detector_merger.py` | Core algorithm for fuzzy matching and merging duplicate clinic records |
| `knn_missing_data_imputation.py` | Fills ALL missing data using K-Nearest Neighbors and multi-strategy imputation |
| `zipcode_knn_geographic_imputation.py` | Legacy script (replaced by comprehensive imputation) - fills missing ZIP codes |
| `scheduler.py` | Scheduling utilities for automated data refresh |

### Database (`src/database/`)

| File Name | What It Does |
|-----------|--------------|
| `sqlalchemy_database_models.py` | SQLAlchemy ORM models defining database tables (Clinic, Review, etc.) |
| `initialize_create_database_tables.py` | Creates database tables, manages database connections |

### Analysis (`src/analysis/`)

| File Name | What It Does |
|-----------|--------------|
| `calculate_visibility_scores.py` | Calculates visibility scores based on ratings, reviews, and online presence |

### Dashboards (`dashboards/`)

| File Name | What It Does |
|-----------|--------------|
| `powerbi_direct_database_connector_script.py` | Python script for direct Power BI connection to PostgreSQL database |

## Documentation Files

| File Name | Purpose |
|-----------|---------|
| `README.md` | Technical project overview, installation, usage |
| `BUSINESS_CASE_README.md` | Business-focused narrative: why, what, how, outcomes, learnings |
| `CLAUDE.md` | Complete technical documentation with architecture decisions and conversation log |
| `POWERBI_NEON_CONNECTION.md` | Step-by-step guide for connecting Power BI to Neon PostgreSQL |
| `IMPLEMENTATION_SUMMARY.md` | Summary of implementation details |
| `FILE_NAMING_GUIDE.md` | This file - explains the naming convention |

## Why This Matters

**Before:** Files like `view_data.py`, `quickstart.py`, `models.py` required opening files to understand their purpose.

**After:** Files like `inspect_database_records.py`, `demo_quick_data_collection.py`, `sqlalchemy_database_models.py` are self-documenting.

## Benefits

✅ **Onboarding:** New team members understand the codebase structure immediately
✅ **Maintenance:** Easy to find the right file when debugging or enhancing
✅ **Collaboration:** No ambiguity about what each script does
✅ **Documentation:** File names serve as inline documentation
✅ **Searchability:** Descriptive names make grep/search much more effective

## Naming Patterns Used

### Action Verbs
- `collect_` - Fetches data from external APIs
- `calculate_` - Computes derived metrics
- `deduplicate_` - Removes duplicate records
- `knn_` - Uses K-Nearest Neighbors algorithm
- `run_` - Orchestrates multiple steps
- `demo_` - Test/demonstration script
- `inspect_` - View/explore data
- `export_` - Save data to external format
- `migrate_` - Move data between systems
- `test_` - Verify functionality
- `initialize_` - Set up initial state

### What It Acts On
- `_google_places_api_data` - Google Places API
- `_yelp_fusion_api_data` - Yelp Fusion API
- `_database_records` - Database contents
- `_visibility_scores` - Visibility metrics
- `_combined_metrics` - Aggregated calculations
- `_missing_data_` - Null/empty values

### Technology Indicators
- `_knn_` - K-Nearest Neighbors algorithm
- `_sqlalchemy_` - SQLAlchemy ORM
- `_postgresql_` - PostgreSQL database
- `_powerbi_` - Power BI integration

## Future File Additions

When adding new files, follow this format:

```
[action]_[what]_[technology/method].py
```

**Examples:**
- `predict_clinic_success_ml_model.py` - Predictive modeling
- `scrape_competitor_websites_selenium.py` - Web scraping
- `analyze_patient_sentiment_vader.py` - Sentiment analysis
- `forecast_demand_time_series.py` - Time series forecasting

## Quick Reference

**Need to...**
- **Collect new data?** → `run_automated_data_collection_pipeline.py`
- **View database?** → `inspect_database_records.py`
- **Export for Power BI?** → `export_clean_data_for_powerbi.py`
- **Test API connection?** → `demo_quick_data_collection.py`
- **Fix missing data?** → `knn_missing_data_imputation.py`
- **Remove duplicates?** → `deduplicate_standardize_data.py`
- **Change database schema?** → `src/database/sqlalchemy_database_models.py`
- **Add new API?** → Create `collect_[source]_api_data.py` in `src/collectors/`

---

**Last Updated:** 2026-01-26
**Maintained By:** Sourabh Rodagi
