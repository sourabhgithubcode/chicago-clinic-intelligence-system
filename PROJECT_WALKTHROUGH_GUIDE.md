# Project Walkthrough Guide - How to Explain This Project

This guide shows you how to explain your entire project using only the GitHub repository. Perfect for interviews, presentations, or onboarding.

---

## 🎯 30-Second Elevator Pitch

> "I built an automated healthcare market intelligence platform that solves a $30,000 problem for clinic owners. It collects data from Google Places and Yelp APIs, cleans it using machine learning algorithms, and delivers insights through 9 Power BI dashboards. The key innovation was achieving 100% data completeness using K-Nearest Neighbors imputation when 57% of the data had missing values."

---

## 📋 5-Minute Project Walkthrough

Use this structure when someone asks: **"Walk me through your project"**

### 1. Start with the Business Problem (30 seconds)

**Show:** `README.md` - "Why It Mattered" section

**What to say:**
> "Healthcare clinic owners in Chicago were making blind business decisions—where to open locations, which services to offer—without market data. Traditional market research costs $10,000-50,000. I saw that public API data could answer these questions if properly collected, cleaned, and visualized. The challenge was that raw API data had 57% missing values, which would make any analysis useless."

**Key metrics to mention:**
- 40% of healthcare businesses fail due to poor location decisions
- $200K+ annual losses from underutilized services
- APIs had 70% missing Google ratings, 57% missing clinic types, 27% missing ZIP codes

---

### 2. Show the Solution Architecture (1 minute)

**Show:** `FILE_NAMING_GUIDE.md` - Pipeline Flow diagram

**What to say:**
> "I built a fully automated pipeline with 5 stages:
> 1. **Data Collection**: Python scripts call Google Places and Yelp APIs
> 2. **Data Enrichment**: Calculate combined metrics from both sources
> 3. **Deduplication**: Fuzzy matching finds same clinics across APIs
> 4. **Imputation**: K-Nearest Neighbors fills missing data using geography
> 5. **Storage**: Clean data goes to Neon PostgreSQL, Power BI connects directly"

**Point to specific files:**
```
run_automated_data_collection_pipeline.py  ← Orchestrates everything
  ↓
collect_google_places_api_data.py         ← Google API
collect_yelp_fusion_api_data.py           ← Yelp API
  ↓
calculate_combined_metrics.py             ← Enrichment
deduplicate_standardize_data.py           ← Cleaning
knn_missing_data_imputation.py            ← ML imputation
  ↓
Neon PostgreSQL → Power BI Dashboards
```

---

### 3. Deep Dive: The Technical Challenge (2 minutes)

**Show:** `src/utils/knn_missing_data_imputation.py`

**What to say:**
> "The hardest problem was 57% missing data. I couldn't delete records—that loses 70% of data. Simple averages would distort analysis. Manual entry doesn't scale.
>
> **My solution:** Multi-strategy hierarchical imputation using domain knowledge.
>
> For **ZIP codes**, I used K-Nearest Neighbors with Haversine distance:
> - Find 3 nearest clinics with valid ZIPs
> - Use voting: if 2/3 neighbors are ZIP 60611, clinic is likely 60611
> - Result: 27 ZIPs imputed, 100% accuracy
>
> For **clinic types**, I built 4-strategy hierarchy:
> - Name keywords first: 'Urgent Care' → urgent_care (61% success)
> - API categories second: ['Chiropractors'] → physical_therapy (21%)
> - K-NN same ZIP third: use most common nearby type (14%)
> - Conservative fallback: primary_care (4%)
>
> For **ratings**, I used cross-platform correlation:
> - Missing Google rating? Use Yelp + 0.1 (ratings correlate at r=0.8)
> - Missing Yelp? Use Google - 0.1
> - Fallback: ZIP average or K-NN from 5 nearest clinics"

**Show specific code snippet (lines 29-40):**
```python
def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points on Earth (in meters)."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return 6371000 * c  # Earth radius in meters
```

**Key achievement:**
> "Went from 43% complete data to 100% complete. Imputed 204 missing values across 123 clinics with 93%+ confidence."

---

### 4. Show the Database Design (1 minute)

**Show:** `src/database/sqlalchemy_database_models.py`

**What to say:**
> "I designed a star schema optimized for analytics:
> - **Clinics** table is the fact table with combined metrics
> - **Reviews**, **SearchTrends**, **VisibilityScores** are dimension tables
> - Pre-calculated aggregations for performance: combined_rating, total_review_count
> - Indexed foreign keys for sub-second Power BI queries"

**Show key fields (lines 16-62):**
```python
class Clinic(Base):
    # Identifiers from both APIs
    google_place_id = Column(String(255), unique=True, index=True)
    yelp_business_id = Column(String(255), unique=True, index=True)

    # Calculated fields (populated by data enrichment)
    combined_rating = Column(Float)  # Average of both sources
    combined_review_count = Column(Integer)  # Sum from both
    data_source = Column(String(20))  # 'Both', 'Google Only', 'Yelp Only'
    data_quality_score = Column(Integer)  # 0-100 completeness
```

**Business value:**
> "This design enables Power BI dashboards to load in <2 seconds even with 1,500+ records because all expensive joins are pre-calculated."

---

### 5. Demonstrate the End-to-End Pipeline (30 seconds)

**Show:** `run_automated_data_collection_pipeline.py` (lines 147-181)

**What to say:**
> "The entire pipeline runs with one command:
> ```bash
> python3 run_automated_data_collection_pipeline.py --full
> ```
>
> This executes all 5 stages automatically:
> - Collects data from APIs → writes to Neon database
> - Enriches with calculated fields
> - Finds and merges 16 duplicate clinics
> - Imputes 204 missing values using K-NN
> - Result: 100% complete data ready for Power BI
>
> Runtime: ~15 minutes for full refresh vs. 40 hours manual work."

---

### 6. Show the Business Impact (30 seconds)

**Show:** `README.md` - "What Happened → Clear Business Outcomes" section

**What to say:**
> "**Quantifiable results:**
> - 100% data completeness (from 43% original)
> - 9 interactive dashboards answering specific business questions
> - 15-minute automated refresh vs. 40 hours/week manual work
> - $0 ongoing cost vs. $30,000 traditional market research
> - Identified specific market opportunities: e.g., Chinatown (60605) has low competition + rising demand"

---

## 🗣️ Interview-Style Q&A

### Q: "What was the hardest technical challenge?"

**Answer:**
> "Handling 57% missing data without distorting analysis. I rejected simple solutions like deletion or overall averages. Instead, I built a hierarchical imputation strategy that tries the most accurate method first, then falls back gracefully.
>
> For example, for clinic types:
> 1. Name inference (most accurate, 61% success)
> 2. Category mapping (21%)
> 3. K-NN same ZIP (14%)
> 4. Conservative default (4%)
>
> This resilience thinking—building fallback strategies—is something I now apply to all my work."

**Show:** `src/utils/knn_missing_data_imputation.py` lines 200-350

---

### Q: "How did you handle duplicate data?"

**Answer:**
> "Same physical clinic appeared in both Google and Yelp with different names. Northwestern Medicine vs. Northwestern Immediate Care = same location.
>
> I built a fuzzy matching algorithm with weighted scoring:
> - Phone match: 40 points (most reliable)
> - Coordinate distance <50m: 35 points
> - Name similarity >75%: 15 points
> - Address match: 10 points
> - Threshold: 50+ = duplicate
>
> Found and merged 16 duplicates (13% reduction), preventing double-counting competitors in market saturation analysis."

**Show:** `src/utils/duplicate_clinic_detector_merger.py`

---

### Q: "How do you ensure data quality?"

**Answer:**
> "Three layers:
> 1. **Collection validation**: API error handling, rate limiting
> 2. **Quality scoring**: Every clinic gets 0-100 score based on completeness
> 3. **Transparency**: I preserved original data_quality_score even after imputation, so users can distinguish original vs. imputed data
>
> This builds trust—users see 'this rating is imputed from Yelp proxy' rather than thinking all data is original."

**Show:** `src/database/sqlalchemy_database_models.py` line 62

---

### Q: "Could this scale to other cities?"

**Answer:**
> "Yes, it's parameterized. The pipeline takes ZIP codes as input, so scaling to any city just requires:
> 1. Update config with new ZIP codes
> 2. Run pipeline command
> 3. Same cleaning/imputation logic applies
>
> The K-NN algorithm is geography-agnostic—works anywhere. Could easily add NYC, LA, etc."

**Show:** `config/settings.py` and `run_automated_data_collection_pipeline.py`

---

### Q: "What would you do differently?"

**Answer from README.md:**
> "Three things:
> 1. **User interviews first**: Spent 2 weeks building metrics no one asked for. Should've validated requirements upfront.
> 2. **Unit tests for imputation**: Currently manual validation. Need automated tests for edge cases.
> 3. **Incremental updates**: Currently full refresh. Could optimize to only update changed records, reducing API costs."

---

## 📊 File-by-File Explanation Map

When someone asks "What does this file do?", use this guide:

### **run_automated_data_collection_pipeline.py**
**Purpose:** Orchestration - master script that runs entire pipeline
**Key sections:**
- Lines 1-31: Pipeline documentation
- Lines 61-86: Collection methods
- Lines 147-181: Full pipeline execution flow
**Talking point:** "This is the entry point. One command runs everything: collect → clean → impute → store in Neon."

---

### **src/collectors/collect_google_places_api_data.py**
**Purpose:** Fetches clinic data from Google Places API
**Key features:**
- API authentication and rate limiting
- Error handling for failed requests
- Writes directly to Neon PostgreSQL
**Talking point:** "Collects location, ratings, reviews, hours from Google. Handles API quotas gracefully with retries."

---

### **src/collectors/collect_yelp_fusion_api_data.py**
**Purpose:** Fetches clinic data from Yelp Fusion API
**Key features:**
- Business search by location
- Review collection with sentiment data
- Writes directly to Neon PostgreSQL
**Talking point:** "Complements Google data. Yelp has different clinics and more detailed categories."

---

### **src/utils/calculate_combined_metrics.py**
**Purpose:** Data enrichment - calculates derived fields
**What it calculates:**
- `combined_rating` = average(Google, Yelp)
- `combined_review_count` = sum(Google, Yelp)
- `data_source` = "Both", "Google Only", "Yelp Only"
- `rating_category` = "Excellent", "Good", "Medium", "Low"
- `data_quality_score` = 0-100 completeness
**Talking point:** "This moves data cleaning OUT of Power BI into the pipeline, so the database is always clean."

---

### **src/utils/deduplicate_standardize_data.py**
**Purpose:** Finds and merges duplicate clinics, standardizes formats
**What it does:**
- Uses fuzzy matching to find same clinic across APIs
- Merges duplicate records (keeps primary, deactivates duplicates)
- Standardizes phone: "+1-312-926-2000" → "(312) 926-2000"
- Cleans names: removes extra spaces, fixes caps
- Formats ZIPs: "60612-1234" → "60612"
**Talking point:** "Found 16 duplicates (13% reduction). Prevents double-counting competitors in market analysis."

---

### **src/utils/duplicate_clinic_detector_merger.py**
**Purpose:** Core algorithm for fuzzy matching duplicates
**Algorithm:**
- Phone match: +40 points
- Coordinate distance <50m: +35 points
- Name similarity >75%: +15 points
- Address match: +10 points
- Threshold ≥50 = duplicate
**Talking point:** "Weighted scoring prioritizes reliable signals like phone numbers over fuzzy name matches."

---

### **src/utils/knn_missing_data_imputation.py**
**Purpose:** THE KEY INNOVATION - fills all missing data using ML
**Strategies:**
1. **ZIP codes**: K-NN with Haversine distance (geographic proximity)
2. **Clinic types**: Name keywords → Categories → K-NN → Default
3. **Ratings**: Cross-platform proxy (Google ↔ Yelp) → ZIP avg → K-NN
**Result:** 204 missing values imputed, 100% completeness
**Talking point:** "This is where the magic happens. Went from 43% complete to 100% without distorting analysis."

---

### **src/database/sqlalchemy_database_models.py**
**Purpose:** Database schema - defines all tables
**Key tables:**
- `Clinic`: Master table with combined metrics
- `Review`: Patient reviews with sentiment analysis
- `SearchTrend`: Google Trends demand data
- `VisibilityScore`: Calculated ranking metrics
**Talking point:** "Star schema optimized for analytics. Pre-calculated fields enable sub-second Power BI queries."

---

### **src/database/initialize_create_database_tables.py**
**Purpose:** Database initialization and connection management
**What it does:**
- Creates all tables in Neon PostgreSQL
- Manages database sessions
- Logging configuration
**Talking point:** "Handles all database setup. One function creates entire schema from SQLAlchemy models."

---

## 🎨 Visual Aids to Show

### 1. Pipeline Flow Diagram
**File:** `FILE_NAMING_GUIDE.md` lines 60-98

### 2. Database Schema
**File:** `src/database/sqlalchemy_database_models.py`
**Show:** Lines 16-78 (Clinic model with all fields)

### 3. Haversine Distance Formula
**File:** `src/utils/knn_missing_data_imputation.py` lines 29-40
**Explain:** "Calculates great-circle distance on Earth's surface. More accurate than Euclidean distance for geolocation."

### 4. Before/After Data Completeness
**File:** `README.md` "What Happened" section
**Show table:**
```
BEFORE: 27% missing ZIPs, 57% missing types, 70% missing Google ratings
AFTER: 100% complete across ALL fields
```

---

## 💼 Tailored Explanations by Audience

### For Technical Interviewers (Data Engineers, ML Engineers):
**Focus on:**
- K-NN algorithm implementation
- Haversine distance calculation
- Hierarchical fallback strategies
- Star schema design choices
- SQLAlchemy ORM usage
- API rate limiting and error handling

**Show:** Code in imputation and collector files

---

### For Data Analyst Interviewers:
**Focus on:**
- Problem-solving approach (why hierarchical strategies?)
- Business impact metrics (40% failure rate, $30K savings)
- Data quality improvements (43% → 100%)
- Power BI integration and performance
- How insights answer specific business questions

**Show:** README.md outcomes and FILE_NAMING_GUIDE.md pipeline

---

### For Business Stakeholders / Product Managers:
**Focus on:**
- Market research problem ($30K cost, 40% failure rate)
- Solution value (automated, $0 ongoing cost, 15-min refresh)
- Specific insights delivered (e.g., Chinatown expansion opportunity)
- Scalability to other cities
- ROI and business outcomes

**Show:** README.md business context sections

---

### For Fellow Students / Junior Developers:
**Focus on:**
- Project structure and file organization
- How to read and understand the codebase
- Learning journey (mistakes made, lessons learned)
- Git workflow and documentation practices
- How to explain technical projects clearly

**Show:** FILE_NAMING_GUIDE.md structure, README.md learnings section

---

## 🚀 Demo Flow for Live Walkthrough

If you can show the actual repository during an interview/presentation:

### **Step 1: Start with README.md** (1 min)
Navigate to repo → Open README.md → Scroll to business context

### **Step 2: Show FILE_NAMING_GUIDE.md** (1 min)
Show pipeline flow diagram → Explain 5 stages

### **Step 3: Open run_automated_data_collection_pipeline.py** (30 sec)
Show the orchestration logic (lines 147-181)

### **Step 4: Deep dive imputation** (2 min)
Open `src/utils/knn_missing_data_imputation.py`
→ Show Haversine function (lines 29-40)
→ Show ZIP imputation logic (lines 45-120)
→ Show hierarchical clinic type logic (lines 200-280)

### **Step 5: Show database models** (1 min)
Open `src/database/sqlalchemy_database_models.py`
→ Show Clinic model (lines 16-78)
→ Explain combined_rating, data_quality_score fields

### **Step 6: Return to README.md for outcomes** (30 sec)
Scroll to "What Happened" section → Show metrics

**Total time: 6 minutes**

---

## 📝 Quick Talking Points Cheat Sheet

**Keep these memorized for quick responses:**

1. **Problem:** Healthcare clinic owners making $200K mistakes without market data
2. **Solution:** Automated pipeline collecting Google + Yelp data → 9 Power BI dashboards
3. **Key challenge:** 57% missing data would destroy analysis
4. **Innovation:** K-NN imputation with hierarchical fallbacks → 100% completeness
5. **Technical stack:** Python, Neon PostgreSQL, Power BI, SQLAlchemy, K-NN algorithm
6. **Results:** 204 values imputed, 15-min refresh vs. 40 hrs manual, $0 vs. $30K cost
7. **Scale:** 123 clinics, 11 ZIP codes, 9 dashboards, 50+ KPIs
8. **Learnings:** Data quality is THE work (60% of time), automation creates compound value

---

## 🎯 Repository Files as Portfolio Evidence

**When asked for proof of specific skills:**

| Skill | Show This File | Line Numbers |
|-------|---------------|--------------|
| **Python programming** | Any collector or util file | All |
| **API integration** | `collect_google_places_api_data.py` | Full file |
| **Machine Learning (K-NN)** | `knn_missing_data_imputation.py` | 29-40, 45-120 |
| **Database design** | `sqlalchemy_database_models.py` | 16-78, 81-118 |
| **Data cleaning** | `deduplicate_standardize_data.py` | Full file |
| **Algorithm design** | `duplicate_clinic_detector_merger.py` | Scoring logic |
| **System architecture** | `run_automated_data_collection_pipeline.py` | 147-181 |
| **Documentation** | `README.md`, `FILE_NAMING_GUIDE.md` | All |
| **Git/Version control** | Commit history | GitHub |
| **Business acumen** | `README.md` "Why It Mattered" | Lines 12-30 |

---

## 🔑 Key Differentiators to Emphasize

What makes this project stand out:

1. **End-to-End Ownership**: "I built everything solo—collection, cleaning, database, documentation"
2. **Real Business Problem**: "$30K cost savings isn't hypothetical—that's actual market research pricing"
3. **ML Application**: "Not just K-NN theory—practical application solving real missing data"
4. **Production Quality**: "Not a school project—automated pipeline with error handling, logging, 100% data completeness"
5. **Scalable Design**: "Works for any city with just config changes"
6. **Clear Documentation**: "Anyone can understand the project from GitHub alone"

---

**Last Updated:** 2026-01-26
**Your Name:** Sourabh Rodagi
**Repository:** https://github.com/sourabhgithubcode/chicago-clinic-intelligence-system
