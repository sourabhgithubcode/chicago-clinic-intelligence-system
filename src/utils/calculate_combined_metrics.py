"""
Data Enrichment Script - Populates calculated fields in the database.

This script runs AFTER data collection to:
1. Calculate combined ratings and review counts
2. Determine data source (Both/Google Only/Yelp Only)
3. Assign rating and review volume categories
4. Calculate data quality scores

RUN THIS: python3 -m src.utils.data_enrichment

After this runs, the database contains CLEAN data ready for Power BI.
Power BI only needs a simple SELECT query - no cleaning needed there.
"""

import sys
from pathlib import Path
from datetime import datetime
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.database.sqlalchemy_database_models import Clinic, Review
from src.database.initialize_create_database_tables import get_session


class DataEnrichment:
    """
    Enrich clinic data with calculated fields.

    This moves ALL data cleaning/transformation from Power BI
    into the data pipeline, so the database is always clean.
    """

    def __init__(self):
        self.session = get_session()
        self.enriched_count = 0

    def enrich_all_clinics(self):
        """
        Enrich all active clinics with calculated fields.
        """
        logger.info("=" * 60)
        logger.info("DATA ENRICHMENT - Calculating fields for all clinics")
        logger.info("=" * 60)

        clinics = self.session.query(Clinic).filter(Clinic.is_active == True).all()
        logger.info(f"Processing {len(clinics)} clinics...")

        for clinic in clinics:
            self._enrich_clinic(clinic)
            self.enriched_count += 1

        self.session.commit()
        logger.info(f"Enriched {self.enriched_count} clinics")

    def _enrich_clinic(self, clinic):
        """
        Calculate and populate all derived fields for a clinic.
        """
        # 1. Data Source flags
        clinic.has_google_data = clinic.google_place_id is not None
        clinic.has_yelp_data = clinic.yelp_business_id is not None

        # 2. Data Source label
        if clinic.has_google_data and clinic.has_yelp_data:
            clinic.data_source = 'Both'
        elif clinic.has_google_data:
            clinic.data_source = 'Google Only'
        elif clinic.has_yelp_data:
            clinic.data_source = 'Yelp Only'
        else:
            clinic.data_source = 'Unknown'

        # 3. Combined Rating (average of available ratings)
        ratings = []
        if clinic.google_rating:
            ratings.append(clinic.google_rating)
        if clinic.yelp_rating:
            ratings.append(clinic.yelp_rating)

        if ratings:
            clinic.combined_rating = round(sum(ratings) / len(ratings), 2)
        else:
            clinic.combined_rating = None

        # 4. Combined Review Count (sum of both)
        clinic.combined_review_count = (clinic.google_review_count or 0) + (clinic.yelp_review_count or 0)

        # 5. Rating Category
        if clinic.combined_rating is not None:
            if clinic.combined_rating >= 4.0:
                clinic.rating_category = 'Excellent (4.0+)'
            elif clinic.combined_rating >= 3.5:
                clinic.rating_category = 'Good (3.5-4.0)'
            elif clinic.combined_rating >= 2.5:
                clinic.rating_category = 'Medium (2.5-3.5)'
            else:
                clinic.rating_category = 'Low (0-2.5)'
        else:
            clinic.rating_category = 'Unknown'

        # 6. Review Volume Category
        if clinic.combined_review_count >= 100:
            clinic.review_volume_category = 'Very High (100+)'
        elif clinic.combined_review_count >= 50:
            clinic.review_volume_category = 'High (51-100)'
        elif clinic.combined_review_count >= 10:
            clinic.review_volume_category = 'Medium (11-50)'
        else:
            clinic.review_volume_category = 'Low (0-10)'

        # 7. Data Quality Score (0-100)
        score = 0
        if clinic.name:
            score += 10
        if clinic.address:
            score += 10
        if clinic.phone:
            score += 10
        if clinic.latitude and clinic.longitude:
            score += 10
        if clinic.google_place_id:
            score += 15
        if clinic.yelp_business_id:
            score += 15
        if clinic.google_rating:
            score += 10
        if clinic.yelp_rating:
            score += 10
        if clinic.website:
            score += 5
        if clinic.clinic_type:
            score += 5

        clinic.data_quality_score = score

        # 8. Update timestamp
        clinic.last_updated = datetime.utcnow()

    def enrich_reviews(self):
        """
        Enrich reviews with calculated fields.
        """
        logger.info("Enriching reviews...")

        reviews = self.session.query(Review).all()

        for review in reviews:
            # Rating category
            if review.rating >= 5:
                review.sentiment_label = 'excellent'
            elif review.rating >= 4:
                review.sentiment_label = 'positive'
            elif review.rating >= 3:
                review.sentiment_label = 'neutral'
            else:
                review.sentiment_label = 'negative'

            # Simple sentiment score based on rating
            review.sentiment_score = (review.rating - 3) / 2  # Maps 1-5 to -1 to 1

        self.session.commit()
        logger.info(f"Enriched {len(reviews)} reviews")

    def run_full_enrichment(self):
        """
        Run complete data enrichment pipeline.
        """
        start_time = datetime.now()

        logger.info("=" * 70)
        logger.info("FULL DATA ENRICHMENT PIPELINE")
        logger.info("=" * 70)
        logger.info(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("")

        # Enrich clinics
        self.enrich_all_clinics()
        logger.info("")

        # Enrich reviews
        self.enrich_reviews()
        logger.info("")

        # Summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info("=" * 70)
        logger.info("ENRICHMENT COMPLETE!")
        logger.info("=" * 70)
        logger.info(f"Duration: {duration:.1f} seconds")
        logger.info(f"Clinics enriched: {self.enriched_count}")
        logger.info("")
        logger.info("Database now contains clean, analysis-ready data.")
        logger.info("Power BI can use simple SELECT queries - no Python cleaning needed!")

    def close(self):
        """Close database session."""
        self.session.close()


def add_new_columns_to_db():
    """
    Add the new calculated columns to existing database.
    Run this once to migrate existing databases.
    """
    import sqlite3
    from config.settings import SQLITE_DB_PATH

    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()

    # Check if columns exist, add if not
    cursor.execute("PRAGMA table_info(clinics)")
    existing_columns = [col[1] for col in cursor.fetchall()]

    new_columns = [
        ("combined_rating", "REAL"),
        ("combined_review_count", "INTEGER"),
        ("data_source", "VARCHAR(20)"),
        ("has_google_data", "BOOLEAN"),
        ("has_yelp_data", "BOOLEAN"),
        ("rating_category", "VARCHAR(30)"),
        ("review_volume_category", "VARCHAR(30)"),
        ("data_quality_score", "INTEGER"),
    ]

    for col_name, col_type in new_columns:
        if col_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE clinics ADD COLUMN {col_name} {col_type}")
                logger.info(f"Added column: {col_name}")
            except Exception as e:
                logger.warning(f"Column {col_name} might already exist: {e}")

    conn.commit()
    conn.close()
    logger.info("Database schema updated!")


if __name__ == "__main__":
    from src.database.init_db import setup_logging

    setup_logging()

    # First, add new columns to database
    logger.info("Step 1: Adding new columns to database...")
    add_new_columns_to_db()
    logger.info("")

    # Then, run enrichment
    logger.info("Step 2: Running data enrichment...")
    enricher = DataEnrichment()
    try:
        enricher.run_full_enrichment()
    finally:
        enricher.close()
