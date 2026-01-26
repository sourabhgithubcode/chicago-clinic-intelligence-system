"""
CLEANED DATA SCRIPT FOR POWER BI
This script loads, cleans, and sanitizes all tables from the Clinic Intelligence database
Use this in Power BI's Python script connector for clean, analysis-ready data

HOW TO USE IN POWER BI:
1. Open Power BI Desktop
2. Get Data → Python script
3. Paste this entire script
4. Update db_path to your database location
5. Click OK - all tables will be available
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

# =============================================================================
# UPDATE THIS PATH TO YOUR DATABASE LOCATION
# =============================================================================
db_path = r'/Users/HP/clinic intelligent system/data/clinic_intelligence.db'
# Windows example: r'C:\Users\Sourabh\Downloads\clinic_intelligent_system\data\clinic_intelligence.db'

conn = sqlite3.connect(db_path)

# ============================================================================
# 1. CLINICS TABLE - Main clinic information
# ============================================================================
clinics = pd.read_sql_query("SELECT * FROM clinics", conn)

# Clean clinics data
clinics_clean = clinics.copy()

# Fill missing categorical values
clinics_clean['clinic_type'] = clinics_clean['clinic_type'].fillna('Unknown')
clinics_clean['categories'] = clinics_clean['categories'].fillna('[]')
clinics_clean['website'] = clinics_clean['website'].fillna('')
clinics_clean['phone'] = clinics_clean['phone'].fillna('')
clinics_clean['address'] = clinics_clean['address'].fillna('')

# Create combined rating (prefer Google, fallback to Yelp)
clinics_clean['combined_rating'] = clinics_clean['google_rating'].fillna(clinics_clean['yelp_rating'])
clinics_clean['combined_review_count'] = clinics_clean['google_review_count'].fillna(0) + clinics_clean['yelp_review_count'].fillna(0)

# Create data source indicator
clinics_clean['has_google_data'] = clinics_clean['google_place_id'].notna().astype(int)
clinics_clean['has_yelp_data'] = clinics_clean['yelp_business_id'].notna().astype(int)
clinics_clean['data_source'] = 'Both'
clinics_clean.loc[clinics_clean['has_google_data'] == 0, 'data_source'] = 'Yelp Only'
clinics_clean.loc[clinics_clean['has_yelp_data'] == 0, 'data_source'] = 'Google Only'

# Rating categories
clinics_clean['rating_category'] = pd.cut(
    clinics_clean['combined_rating'],
    bins=[0, 2.5, 3.5, 4.0, 5.0],
    labels=['Low (0-2.5)', 'Medium (2.5-3.5)', 'Good (3.5-4.0)', 'Excellent (4.0+)'],
    include_lowest=True
)

# Review volume categories
clinics_clean['review_volume_category'] = pd.cut(
    clinics_clean['combined_review_count'],
    bins=[-1, 10, 50, 100, 1000000],
    labels=['Low (0-10)', 'Medium (11-50)', 'High (51-100)', 'Very High (100+)']
)

# Convert dates
clinics_clean['last_updated'] = pd.to_datetime(clinics_clean['last_updated'])
clinics_clean['created_at'] = pd.to_datetime(clinics_clean['created_at'])

# Final clinics table
clinics = clinics_clean[[
    'id', 'name', 'address', 'city', 'state', 'zip_code', 'phone', 'website',
    'latitude', 'longitude', 'clinic_type', 'categories',
    'google_rating', 'google_review_count', 'yelp_rating', 'yelp_review_count',
    'combined_rating', 'combined_review_count', 'rating_category', 'review_volume_category',
    'data_source', 'has_google_data', 'has_yelp_data', 'is_active',
    'last_updated', 'created_at'
]]

# ============================================================================
# 2. REVIEWS TABLE - Customer reviews
# ============================================================================
reviews = pd.read_sql_query("SELECT * FROM reviews", conn)

# Clean reviews data
reviews_clean = reviews.copy()

# Fill missing text
reviews_clean['text'] = reviews_clean['text'].fillna('')
reviews_clean['author_name'] = reviews_clean['author_name'].fillna('Anonymous')

# Convert dates
reviews_clean['review_date'] = pd.to_datetime(reviews_clean['review_date'])
reviews_clean['created_at'] = pd.to_datetime(reviews_clean['created_at'])

# Create review length category
reviews_clean['text_length'] = reviews_clean['text'].str.len()
reviews_clean['review_length_category'] = pd.cut(
    reviews_clean['text_length'],
    bins=[-1, 50, 200, 500, 1000000],
    labels=['Short', 'Medium', 'Long', 'Very Long']
)

# Rating category
reviews_clean['rating_category'] = pd.cut(
    reviews_clean['rating'],
    bins=[0, 2, 3, 4, 5],
    labels=['Negative (1-2)', 'Neutral (3)', 'Positive (4)', 'Excellent (5)'],
    include_lowest=True
)

# Days since review
reviews_clean['days_since_review'] = (pd.Timestamp.now() - reviews_clean['review_date']).dt.days

# Final reviews table
reviews = reviews_clean[[
    'id', 'clinic_id', 'source', 'author_name', 'rating', 'rating_category',
    'text', 'text_length', 'review_length_category', 'review_date', 'days_since_review',
    'created_at'
]]

# ============================================================================
# 3. SEARCH TRENDS TABLE - Google Trends data
# ============================================================================
search_trends = pd.read_sql_query("SELECT * FROM search_trends", conn)

# Clean search trends
search_trends_clean = search_trends.copy()

# Convert dates
search_trends_clean['date'] = pd.to_datetime(search_trends_clean['date'])
search_trends_clean['created_at'] = pd.to_datetime(search_trends_clean['created_at'])

# Create trend categories
search_trends_clean['demand_level'] = pd.cut(
    search_trends_clean['interest_score'],
    bins=[-1, 25, 50, 75, 100],
    labels=['Low', 'Medium', 'High', 'Very High']
)

# Trend direction (comparing 7-day avg to 30-day avg)
search_trends_clean['trend_direction'] = 'Stable'
search_trends_clean.loc[
    search_trends_clean['interest_7day_avg'] > search_trends_clean['interest_30day_avg'] * 1.1,
    'trend_direction'
] = 'Increasing'
search_trends_clean.loc[
    search_trends_clean['interest_7day_avg'] < search_trends_clean['interest_30day_avg'] * 0.9,
    'trend_direction'
] = 'Decreasing'

# Extract year, month, week
search_trends_clean['year'] = search_trends_clean['date'].dt.year
search_trends_clean['month'] = search_trends_clean['date'].dt.month
search_trends_clean['month_name'] = search_trends_clean['date'].dt.strftime('%B')
search_trends_clean['week'] = search_trends_clean['date'].dt.isocalendar().week

# Final search trends table
search_trends = search_trends_clean[[
    'id', 'keyword', 'service_category', 'location', 'date', 'year', 'month', 'month_name', 'week',
    'interest_score', 'interest_7day_avg', 'interest_30day_avg',
    'demand_level', 'trend_direction', 'created_at'
]]

# ============================================================================
# 4. DEMAND METRICS TABLE - Market demand analysis
# ============================================================================
demand_metrics = pd.read_sql_query("SELECT * FROM demand_metrics", conn)

# Clean demand metrics
demand_metrics_clean = demand_metrics.copy()

# Convert dates
demand_metrics_clean['calculation_date'] = pd.to_datetime(demand_metrics_clean['calculation_date'])
demand_metrics_clean['created_at'] = pd.to_datetime(demand_metrics_clean['created_at'])

# Fill zeros with NaN for better filtering
demand_metrics_clean['avg_rating'] = demand_metrics_clean['avg_rating'].replace(0, np.nan)

# Create demand categories
demand_metrics_clean['demand_category'] = pd.cut(
    demand_metrics_clean['search_demand_index'],
    bins=[-1, 10, 25, 40, 1000],
    labels=['Low', 'Medium', 'High', 'Very High']
)

# Create opportunity categories
demand_metrics_clean['opportunity_category'] = pd.cut(
    demand_metrics_clean['opportunity_score'],
    bins=[-1, 15, 30, 45, 1000],
    labels=['Low', 'Medium', 'High', 'Excellent']
)

# Competition level
demand_metrics_clean['competition_level'] = pd.cut(
    demand_metrics_clean['clinic_count'],
    bins=[-1, 2, 5, 10, 1000],
    labels=['Low', 'Medium', 'High', 'Very High']
)

# Final demand metrics table
demand_metrics = demand_metrics_clean[[
    'id', 'service_category', 'zip_code', 'calculation_date',
    'search_demand_index', 'demand_category', 'search_volume_trend',
    'clinic_count', 'competition_level', 'avg_rating', 'total_review_count',
    'demand_to_competition_ratio', 'opportunity_score', 'opportunity_category',
    'created_at'
]]

# ============================================================================
# 5. VISIBILITY SCORES TABLE - Clinic visibility metrics
# ============================================================================
visibility_scores = pd.read_sql_query("SELECT * FROM visibility_scores", conn)

# Clean visibility scores
visibility_scores_clean = visibility_scores.copy()

# Convert dates
visibility_scores_clean['calculation_date'] = pd.to_datetime(visibility_scores_clean['calculation_date'])
visibility_scores_clean['created_at'] = pd.to_datetime(visibility_scores_clean['created_at'])

# Fill missing local_rank with high number (low priority)
visibility_scores_clean['local_rank'] = visibility_scores_clean['local_rank'].fillna(999)

# Create visibility categories
visibility_scores_clean['visibility_category'] = pd.cut(
    visibility_scores_clean['overall_visibility_score'],
    bins=[0, 30, 50, 70, 100],
    labels=['Low', 'Medium', 'High', 'Excellent']
)

# Create rank categories
visibility_scores_clean['rank_category'] = pd.cut(
    visibility_scores_clean['city_rank'],
    bins=[0, 10, 25, 50, 1000],
    labels=['Top 10', 'Top 25', 'Top 50', 'Below 50']
)

# Final visibility scores table
visibility_scores = visibility_scores_clean[[
    'id', 'clinic_id', 'calculation_date',
    'rating_score', 'review_volume_score', 'recency_score', 'geographic_score',
    'overall_visibility_score', 'visibility_category',
    'local_rank', 'city_rank', 'rank_category',
    'created_at'
]]

# ============================================================================
# 6. COMPETITOR ANALYSIS TABLE - Market competition
# ============================================================================
competitor_analysis = pd.read_sql_query("SELECT * FROM competitor_analysis", conn)

# Clean competitor analysis
competitor_analysis_clean = competitor_analysis.copy()

# Convert dates
competitor_analysis_clean['calculation_date'] = pd.to_datetime(competitor_analysis_clean['calculation_date'])
competitor_analysis_clean['created_at'] = pd.to_datetime(competitor_analysis_clean['created_at'])

# Create competition categories
competitor_analysis_clean['competition_intensity'] = pd.cut(
    competitor_analysis_clean['total_clinics'],
    bins=[-1, 3, 7, 12, 1000],
    labels=['Low', 'Medium', 'High', 'Very High']
)

# Market concentration
competitor_analysis_clean['market_concentration'] = pd.cut(
    competitor_analysis_clean['top_3_market_share'],
    bins=[0, 40, 60, 80, 100],
    labels=['Fragmented', 'Moderate', 'Concentrated', 'Highly Concentrated']
)

# Final competitor analysis table
competitor_analysis = competitor_analysis_clean[[
    'id', 'zip_code', 'calculation_date',
    'total_clinics', 'competition_intensity', 'by_type',
    'avg_rating', 'avg_review_count',
    'top_3_market_share', 'market_concentration',
    'high_rated_count', 'low_review_count',
    'created_at'
]]

# ============================================================================
# 7. DATA COLLECTION LOGS TABLE - System monitoring
# ============================================================================
data_collection_logs = pd.read_sql_query("SELECT * FROM data_collection_logs", conn)

# Clean logs
data_collection_logs_clean = data_collection_logs.copy()

# Convert dates
data_collection_logs_clean['start_time'] = pd.to_datetime(data_collection_logs_clean['start_time'])
data_collection_logs_clean['end_time'] = pd.to_datetime(data_collection_logs_clean['end_time'])
data_collection_logs_clean['created_at'] = pd.to_datetime(data_collection_logs_clean['created_at'])

# Calculate duration
data_collection_logs_clean['duration_seconds'] = (
    data_collection_logs_clean['end_time'] - data_collection_logs_clean['start_time']
).dt.total_seconds()

# Fill missing values
data_collection_logs_clean['records_updated'] = data_collection_logs_clean['records_updated'].fillna(0)
data_collection_logs_clean['error_message'] = data_collection_logs_clean['error_message'].fillna('None')

# Success rate
data_collection_logs_clean['success_rate'] = (
    data_collection_logs_clean['records_collected'] /
    (data_collection_logs_clean['records_collected'] + data_collection_logs_clean['records_failed'])
) * 100
data_collection_logs_clean['success_rate'] = data_collection_logs_clean['success_rate'].fillna(100)

# Final logs table
data_collection_logs = data_collection_logs_clean[[
    'id', 'collection_type', 'start_time', 'end_time', 'duration_seconds',
    'status', 'records_collected', 'records_updated', 'records_failed', 'success_rate',
    'created_at'
]]

# Close connection
conn.close()

# ============================================================================
# All cleaned tables are now ready for Power BI:
# - clinics
# - reviews
# - search_trends
# - demand_metrics
# - visibility_scores
# - competitor_analysis
# - data_collection_logs
# ============================================================================
