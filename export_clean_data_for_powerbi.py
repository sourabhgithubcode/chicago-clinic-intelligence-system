#!/usr/bin/env python3
"""
CSV Export Script for Power BI
Exports all tables from Supabase PostgreSQL to CSV files
"""

import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Add project to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import get_database_url
from src.database.sqlalchemy_database_models import (
    Clinic, Review, SearchTrend, VisibilityScore,
    DemandMetric, CompetitorAnalysis, DataCollectionLog
)


def print_header(title):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def export_table_to_csv(engine, model, table_name, output_dir):
    """Export a single table to CSV."""
    print(f"Exporting {table_name}...", end=' ')

    try:
        # Query all data
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(query, engine)

        # Create output file
        output_file = output_dir / f"{table_name}.csv"
        df.to_csv(output_file, index=False)

        rows = len(df)
        cols = len(df.columns)
        size = output_file.stat().st_size / 1024  # KB

        print(f"✅ ({rows:,} rows, {cols} columns, {size:.1f} KB)")
        return True, rows

    except Exception as e:
        print(f"❌ Error: {e}")
        return False, 0


def main():
    """Main export process."""
    print_header("EXPORT DATABASE TO CSV FOR POWER BI")

    # Load environment
    load_dotenv()

    # Create output directory
    output_dir = Path("data/exports")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📂 Output directory: {output_dir.absolute()}")

    # Connect to database
    print_header("CONNECTING TO DATABASE")

    try:
        db_url = get_database_url()
        engine = create_engine(db_url, echo=False)

        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        print("✅ Connected to Supabase PostgreSQL")

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nMake sure:")
        print("  1. .env file has correct Supabase credentials")
        print("  2. DB_TYPE=postgresql")
        print("  3. Supabase project is active")
        sys.exit(1)

    # Export tables
    print_header("EXPORTING TABLES")

    tables_to_export = [
        ('clinics', Clinic),
        ('reviews', Review),
        ('search_trends', SearchTrend),
        ('visibility_scores', VisibilityScore),
        ('demand_metrics', DemandMetric),
        ('competitor_analysis', CompetitorAnalysis),
        ('data_collection_logs', DataCollectionLog),
    ]

    total_rows = 0
    successful = 0

    for table_name, model in tables_to_export:
        success, rows = export_table_to_csv(engine, model, table_name, output_dir)
        if success:
            successful += 1
            total_rows += rows

    # Summary
    print_header("EXPORT SUMMARY")

    print(f"✅ Exported {successful}/{len(tables_to_export)} tables")
    print(f"✅ Total records: {total_rows:,}")
    print(f"📂 Files saved to: {output_dir.absolute()}")

    print("\n" + "=" * 70)
    print("  NEXT STEPS - POWER BI")
    print("=" * 70)
    print("\n1. Go to https://app.powerbi.com")
    print("2. Click 'Get Data' → 'Files' → 'Local File'")
    print("3. Upload these CSV files:")

    for table_name, _ in tables_to_export:
        csv_file = output_dir / f"{table_name}.csv"
        if csv_file.exists():
            print(f"   - {csv_file.name}")

    print("\n4. Create relationships in Power BI:")
    print("   - clinics.id → reviews.clinic_id")
    print("   - clinics.id → visibility_scores.clinic_id")

    print("\n5. Build your dashboard!")

    print("\n💡 To refresh data:")
    print("   1. Run: python3 quickstart.py")
    print("   2. Run: python3 export_to_csv.py")
    print("   3. Re-upload CSVs to Power BI")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    try:
        # Import text for SQLAlchemy 2.0+
        from sqlalchemy import text
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Export interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
