# File Naming Guide - Descriptive File Names

This project uses descriptive file names so anyone can understand what each file does without opening it.

## Naming Convention

**Format:** `action_what_purpose.py`

**Examples:**
- `collect_google_places_api_data.py` (not `google_places_collector.py`)
- `knn_missing_data_imputation.py` (not `comprehensive_imputation.py`)
- `deduplicate_standardize_data.py` (not `data_cleaner.py`)

## Core Pipeline: APIs → Collect → Clean → Neon → Power BI

The project follows a streamlined pipeline with only essential files.

## File Inventory

### Root Level Scripts

| File Name | What It Does |
|-----------|--------------|
| `run_automated_data_collection_pipeline.py` | **Master orchestration script** - Runs complete data collection, cleaning, and imputation pipeline |

### Data Collectors (`src/collectors/`)

| File Name | What It Does |
|-----------|--------------|
| `collect_google_places_api_data.py` | Collects clinic data from Google Places API → writes to Neon database |
| `collect_yelp_fusion_api_data.py` | Collects clinic data from Yelp Fusion API → writes to Neon database |

### Data Processing (`src/utils/`)

| File Name | What It Does |
|-----------|--------------|
| `calculate_combined_metrics.py` | Calculates combined ratings (Google + Yelp), data sources, quality scores |
| `deduplicate_standardize_data.py` | Finds duplicate clinics, merges them, standardizes formats |
| `duplicate_clinic_detector_merger.py` | Core fuzzy matching algorithm for duplicate detection (used by deduplicate script) |
| `knn_missing_data_imputation.py` | Fills ALL missing data: ZIP codes, clinic types, ratings using K-NN and multi-strategy imputation |

### Database (`src/database/`)

| File Name | What It Does |
|-----------|--------------|
| `sqlalchemy_database_models.py` | SQLAlchemy ORM models defining database schema (Clinic, Review, SearchTrend, etc.) |
| `initialize_create_database_tables.py` | Creates database tables, manages connections to Neon PostgreSQL |

## Documentation Files

| File Name | Purpose |
|-----------|---------|
| `README.md` | Complete project overview with business context, technical details, pipeline flow |
| `CLAUDE.md` | Detailed technical documentation with architecture decisions and development log |
| `POWERBI_NEON_CONNECTION.md` | Step-by-step guide for connecting Power BI to Neon PostgreSQL |
| `FILE_NAMING_GUIDE.md` | This file - explains naming convention and file structure |

## Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  run_automated_data_collection_pipeline.py (Orchestrator)       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1-2: Data Collection                                      │
│  • collect_google_places_api_data.py → Neon Database            │
│  • collect_yelp_fusion_api_data.py → Neon Database              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: Data Enrichment                                        │
│  • calculate_combined_metrics.py                                │
│    - Combined ratings, data sources, quality scores             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: Data Cleaning & Deduplication                          │
│  • deduplicate_standardize_data.py                              │
│    - Uses: duplicate_clinic_detector_merger.py                  │
│    - Merges duplicates, standardizes formats                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: Missing Data Imputation                                │
│  • knn_missing_data_imputation.py                               │
│    - ZIP codes (K-NN geographic)                                │
│    - Clinic types (name/category inference)                     │
│    - Ratings (cross-platform proxy)                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Neon PostgreSQL Database (100% Complete Data)                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Power BI Dashboards (Direct Connection)                        │
└─────────────────────────────────────────────────────────────────┘
```

## Why This Matters

**Before:** Files like `view_data.py`, `quickstart.py`, `models.py` required opening files to understand their purpose.

**After:** Files like `collect_google_places_api_data.py`, `knn_missing_data_imputation.py`, `sqlalchemy_database_models.py` are self-documenting.

## Benefits

✅ **Clarity:** File names describe exactly what each script does
✅ **Onboarding:** New developers understand structure immediately
✅ **Focused:** Only essential pipeline files, no clutter
✅ **Maintenance:** Easy to find and modify specific functionality
✅ **Searchability:** Descriptive names make finding files trivial

## Naming Patterns Used

### Action Verbs
- `collect_` - Fetches data from external APIs
- `calculate_` - Computes derived metrics
- `deduplicate_` - Removes duplicate records
- `knn_` - Uses K-Nearest Neighbors algorithm
- `run_` - Orchestrates multiple steps
- `initialize_` - Set up initial state

### What It Acts On
- `_google_places_api_data` - Google Places API source
- `_yelp_fusion_api_data` - Yelp Fusion API source
- `_database_` - Database operations
- `_combined_metrics` - Aggregated calculations
- `_missing_data_` - Null/empty values
- `_clinic_` - Clinic records

### Technology Indicators
- `_knn_` - K-Nearest Neighbors algorithm
- `_sqlalchemy_` - SQLAlchemy ORM
- `_neon_` or `_postgresql_` - Neon PostgreSQL

## Quick Reference

**Need to...**
- **Run the complete pipeline?** → `python3 run_automated_data_collection_pipeline.py --full`
- **Collect only Google data?** → `python3 run_automated_data_collection_pipeline.py --google`
- **Collect only Yelp data?** → `python3 run_automated_data_collection_pipeline.py --yelp`
- **Clean existing data?** → `python3 run_automated_data_collection_pipeline.py --clean-only`
- **Modify database schema?** → Edit `src/database/sqlalchemy_database_models.py`
- **Change imputation logic?** → Edit `src/utils/knn_missing_data_imputation.py`
- **Adjust duplicate detection?** → Edit `src/utils/duplicate_clinic_detector_merger.py`

## Project Structure

```
chicago-clinic-intelligence-system/
├── run_automated_data_collection_pipeline.py  ← START HERE
│
├── src/
│   ├── collectors/           ← Data collection from APIs
│   │   ├── collect_google_places_api_data.py
│   │   └── collect_yelp_fusion_api_data.py
│   │
│   ├── utils/                ← Data processing & cleaning
│   │   ├── calculate_combined_metrics.py
│   │   ├── deduplicate_standardize_data.py
│   │   ├── duplicate_clinic_detector_merger.py
│   │   └── knn_missing_data_imputation.py
│   │
│   └── database/             ← Database models & connections
│       ├── sqlalchemy_database_models.py
│       └── initialize_create_database_tables.py
│
├── data/                     ← Data storage (SQLite backup)
├── config/                   ← Configuration settings
├── docs/                     ← Additional documentation
│
└── Documentation Files
    ├── README.md
    ├── CLAUDE.md
    ├── POWERBI_NEON_CONNECTION.md
    └── FILE_NAMING_GUIDE.md (this file)
```

## Removed Files (Not Part of Core Pipeline)

The following files were deleted as they were not essential to the core pipeline flow:

**One-Time/Testing Scripts:**
- `migrate_database_sqlite_to_postgresql.py` - One-time migration (already completed)
- `test_database_connection.py` - Testing utility
- `demo_quick_data_collection.py` - Demo script

**Viewing/Export Tools:**
- `inspect_database_records.py` - Database viewing (not part of pipeline)
- `export_clean_data_for_powerbi.py` - CSV export (direct Neon connection used instead)

**Legacy/Replaced Scripts:**
- `zipcode_knn_geographic_imputation.py` - Replaced by comprehensive imputation
- `scheduler.py` - Not used in current pipeline

**Obsolete Connectors:**
- `powerbi_direct_database_connector_script.py` - SQLite connector (now using Neon)

**Redundant Documentation:**
- `PROJECT_README.md` - Superseded by README.md
- `IMPLEMENTATION_SUMMARY.md` - Info consolidated into README.md

---

**Last Updated:** 2026-01-26
**Maintained By:** Sourabh Rodagi
