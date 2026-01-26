"""
Migrate data from SQLite to Neon PostgreSQL database.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from loguru import logger
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.database.models import (
    Clinic, Review, SearchTrend, VisibilityScore,
    DemandMetric, CompetitorAnalysis, DataCollectionLog
)

def migrate_data():
    """Migrate all data from SQLite to Neon PostgreSQL."""

    # SQLite connection
    sqlite_url = "sqlite:///data/clinic_intelligence.db"
    logger.info(f"Connecting to SQLite: {sqlite_url}")
    sqlite_engine = create_engine(sqlite_url, echo=False)
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    sqlite_session = SQLiteSession()

    # Neon PostgreSQL connection
    neon_url = "postgresql://neondb_owner:npg_fcp6hyHUrPS7@ep-calm-recipe-a8tryfj4-pooler.eastus2.azure.neon.tech:5432/neondb"
    logger.info(f"Connecting to Neon: {neon_url.split('@')[-1]}")
    neon_engine = create_engine(neon_url, echo=False)
    NeonSession = sessionmaker(bind=neon_engine)
    neon_session = NeonSession()

    try:
        # Migrate tables in order (respecting foreign key dependencies)
        tables_to_migrate = [
            (Clinic, "Clinics"),
            (Review, "Reviews"),
            (SearchTrend, "Search Trends"),
            (VisibilityScore, "Visibility Scores"),
            (DemandMetric, "Demand Metrics"),
            (CompetitorAnalysis, "Competitor Analysis"),
            (DataCollectionLog, "Data Collection Logs")
        ]

        total_migrated = 0

        for model, name in tables_to_migrate:
            logger.info(f"\nMigrating {name}...")

            # Get all records from SQLite
            records = sqlite_session.query(model).all()
            count = len(records)

            if count == 0:
                logger.info(f"  No {name} to migrate")
                continue

            logger.info(f"  Found {count} records")

            # Copy records to Neon
            for record in records:
                # Create a new instance with same data
                neon_session.merge(record)

            # Commit after each table
            neon_session.commit()
            logger.success(f"  ✓ Migrated {count} {name}")
            total_migrated += count

        logger.success(f"\n✓ Migration complete! Total records migrated: {total_migrated}")

        # Verify migration
        logger.info("\nVerifying migration:")
        logger.info(f"  Clinics: {neon_session.query(Clinic).count()}")
        logger.info(f"  Reviews: {neon_session.query(Review).count()}")
        logger.info(f"  Search Trends: {neon_session.query(SearchTrend).count()}")
        logger.info(f"  Visibility Scores: {neon_session.query(VisibilityScore).count()}")
        logger.info(f"  Demand Metrics: {neon_session.query(DemandMetric).count()}")
        logger.info(f"  Competitor Analysis: {neon_session.query(CompetitorAnalysis).count()}")
        logger.info(f"  Data Collection Logs: {neon_session.query(DataCollectionLog).count()}")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        neon_session.rollback()
        raise

    finally:
        sqlite_session.close()
        neon_session.close()


if __name__ == "__main__":
    logger.add(sys.stderr, level="INFO")
    logger.info("Starting SQLite to Neon migration...")
    migrate_data()
    logger.success("Migration script completed!")
