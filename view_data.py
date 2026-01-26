#!/usr/bin/env python3
"""
Database Viewer for Clinic Intelligence System
Interactive tool to view and query collected data
"""

import sys
from pathlib import Path
import pandas as pd

# Add project to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.database.init_db import get_session
from src.database.models import Clinic, Review, SearchTrend, VisibilityScore, DataCollectionLog
from sqlalchemy import func


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def view_summary():
    """Show database summary statistics."""
    print_header("DATABASE SUMMARY")

    session = get_session()
    try:
        # Clinic stats
        total_clinics = session.query(func.count(Clinic.id)).scalar()
        google_clinics = session.query(func.count(Clinic.id)).filter(Clinic.google_place_id.isnot(None)).scalar()
        yelp_clinics = session.query(func.count(Clinic.id)).filter(Clinic.yelp_business_id.isnot(None)).scalar()
        unique_zips = session.query(func.count(func.distinct(Clinic.zip_code))).scalar()

        print(f"Total Clinics:        {total_clinics}")
        print(f"From Google Places:   {google_clinics}")
        print(f"From Yelp:            {yelp_clinics}")
        print(f"Unique ZIP Codes:     {unique_zips}")

        # Review stats
        total_reviews = session.query(func.count(Review.id)).scalar()
        print(f"\nTotal Reviews:        {total_reviews}")

        # Trends stats
        total_trends = session.query(func.count(SearchTrend.id)).scalar()
        print(f"Search Trend Records: {total_trends}")

        # Collection logs
        total_logs = session.query(func.count(DataCollectionLog.id)).scalar()
        last_collection = session.query(func.max(DataCollectionLog.start_time)).scalar()
        print(f"\nCollection Logs:      {total_logs}")
        print(f"Last Collection:      {last_collection}")

    finally:
        session.close()


def view_top_clinics(limit=10):
    """Show top-rated clinics."""
    print_header(f"TOP {limit} RATED CLINICS")

    session = get_session()
    try:
        clinics = session.query(Clinic)\
            .filter(Clinic.google_rating.isnot(None))\
            .order_by(Clinic.google_rating.desc(), Clinic.google_review_count.desc())\
            .limit(limit)\
            .all()

        if clinics:
            data = []
            for clinic in clinics:
                data.append({
                    'Name': clinic.name[:40],
                    'Address': clinic.address[:35] if clinic.address else '',
                    'Google': f"{clinic.google_rating:.1f}" if clinic.google_rating else 'N/A',
                    'Yelp': f"{clinic.yelp_rating:.1f}" if clinic.yelp_rating else 'N/A',
                    'ZIP': clinic.zip_code or '',
                    'Phone': clinic.phone or ''
                })

            df = pd.DataFrame(data)
            print(df.to_string(index=False))
        else:
            print("No clinics found.")

    finally:
        session.close()


def view_by_zipcode():
    """Show clinic distribution by ZIP code."""
    print_header("CLINIC DISTRIBUTION BY ZIP CODE")

    session = get_session()
    try:
        results = session.query(
            Clinic.zip_code,
            func.count(Clinic.id).label('count'),
            func.avg(Clinic.google_rating).label('avg_rating')
        )\
        .filter(Clinic.zip_code.isnot(None))\
        .group_by(Clinic.zip_code)\
        .order_by(func.count(Clinic.id).desc())\
        .all()

        if results:
            data = []
            for zip_code, count, avg_rating in results:
                data.append({
                    'ZIP Code': zip_code,
                    'Clinics': count,
                    'Avg Rating': f"{avg_rating:.2f}" if avg_rating else 'N/A'
                })

            df = pd.DataFrame(data)
            print(df.to_string(index=False))
        else:
            print("No data found.")

    finally:
        session.close()


def view_clinic_details(clinic_name=None):
    """Show detailed information for a specific clinic."""
    session = get_session()
    try:
        if clinic_name:
            clinic = session.query(Clinic)\
                .filter(Clinic.name.ilike(f"%{clinic_name}%"))\
                .first()
        else:
            # Show first clinic as example
            clinic = session.query(Clinic).first()

        if clinic:
            print_header(f"CLINIC DETAILS: {clinic.name}")

            print(f"Name:              {clinic.name}")
            print(f"Address:           {clinic.address}")
            print(f"City:              {clinic.city}")
            print(f"State:             {clinic.state}")
            print(f"ZIP Code:          {clinic.zip_code}")
            print(f"Phone:             {clinic.phone}")
            print(f"Website:           {clinic.website}")
            print(f"\nGoogle Place ID:   {clinic.google_place_id}")
            print(f"Google Rating:     {clinic.google_rating} ({clinic.google_review_count} reviews)")
            print(f"\nYelp Business ID:  {clinic.yelp_business_id}")
            print(f"Yelp Rating:       {clinic.yelp_rating} ({clinic.yelp_review_count} reviews)")
            print(f"\nLatitude:          {clinic.latitude}")
            print(f"Longitude:         {clinic.longitude}")
            print(f"Clinic Type:       {clinic.clinic_type}")
            print(f"Is Active:         {clinic.is_active}")
            print(f"Last Updated:      {clinic.last_updated}")
            print(f"Created:           {clinic.created_at}")
        else:
            print(f"No clinic found matching: {clinic_name}")

    finally:
        session.close()


def search_clinics(query):
    """Search clinics by name."""
    print_header(f"SEARCH RESULTS FOR: '{query}'")

    session = get_session()
    try:
        clinics = session.query(Clinic)\
            .filter(Clinic.name.ilike(f"%{query}%"))\
            .all()

        if clinics:
            print(f"Found {len(clinics)} clinics:\n")
            data = []
            for clinic in clinics:
                data.append({
                    'Name': clinic.name[:50],
                    'Address': clinic.address[:40] if clinic.address else '',
                    'Rating': f"{clinic.google_rating or clinic.yelp_rating or 0:.1f}",
                    'ZIP': clinic.zip_code or ''
                })

            df = pd.DataFrame(data)
            print(df.to_string(index=False))
        else:
            print(f"No clinics found matching: {query}")

    finally:
        session.close()


def export_to_csv(filename="clinic_data.csv"):
    """Export all clinic data to CSV."""
    print_header(f"EXPORTING DATA TO: {filename}")

    session = get_session()
    try:
        clinics = session.query(Clinic).all()

        if clinics:
            data = []
            for clinic in clinics:
                data.append({
                    'ID': clinic.id,
                    'Name': clinic.name,
                    'Address': clinic.address,
                    'City': clinic.city,
                    'State': clinic.state,
                    'ZIP': clinic.zip_code,
                    'Phone': clinic.phone,
                    'Website': clinic.website,
                    'Google Rating': clinic.google_rating,
                    'Google Reviews': clinic.google_review_count,
                    'Yelp Rating': clinic.yelp_rating,
                    'Yelp Reviews': clinic.yelp_review_count,
                    'Latitude': clinic.latitude,
                    'Longitude': clinic.longitude,
                    'Type': clinic.clinic_type,
                    'Active': clinic.is_active,
                    'Last Updated': clinic.last_updated
                })

            df = pd.DataFrame(data)
            df.to_csv(filename, index=False)
            print(f"✓ Exported {len(clinics)} clinics to {filename}")
        else:
            print("No data to export.")

    finally:
        session.close()


def interactive_menu():
    """Show interactive menu."""
    while True:
        print("\n" + "=" * 80)
        print("  CLINIC INTELLIGENCE DATABASE VIEWER")
        print("=" * 80)
        print("\n1. View Summary Statistics")
        print("2. View Top Rated Clinics")
        print("3. View Distribution by ZIP Code")
        print("4. View Clinic Details")
        print("5. Search Clinics by Name")
        print("6. Export to CSV")
        print("7. Exit")

        choice = input("\nEnter your choice (1-7): ").strip()

        if choice == '1':
            view_summary()
        elif choice == '2':
            limit = input("How many clinics? (default 10): ").strip()
            limit = int(limit) if limit.isdigit() else 10
            view_top_clinics(limit)
        elif choice == '3':
            view_by_zipcode()
        elif choice == '4':
            name = input("Enter clinic name (or press Enter for first clinic): ").strip()
            view_clinic_details(name if name else None)
        elif choice == '5':
            query = input("Enter search query: ").strip()
            if query:
                search_clinics(query)
        elif choice == '6':
            filename = input("Enter filename (default: clinic_data.csv): ").strip()
            filename = filename if filename else "clinic_data.csv"
            export_to_csv(filename)
        elif choice == '7':
            print("\nGoodbye!\n")
            break
        else:
            print("\nInvalid choice. Please try again.")


def main():
    """Main function."""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == 'summary':
            view_summary()
        elif command == 'top':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            view_top_clinics(limit)
        elif command == 'zip':
            view_by_zipcode()
        elif command == 'search':
            if len(sys.argv) > 2:
                search_clinics(sys.argv[2])
            else:
                print("Usage: python view_data.py search <query>")
        elif command == 'export':
            filename = sys.argv[2] if len(sys.argv) > 2 else "clinic_data.csv"
            export_to_csv(filename)
        elif command == 'details':
            name = sys.argv[2] if len(sys.argv) > 2 else None
            view_clinic_details(name)
        else:
            print(f"Unknown command: {command}")
            print("\nAvailable commands:")
            print("  summary       - View database summary")
            print("  top [N]       - View top N rated clinics")
            print("  zip           - View distribution by ZIP code")
            print("  search <name> - Search clinics by name")
            print("  details [name]- View clinic details")
            print("  export [file] - Export data to CSV")
    else:
        # Interactive mode
        interactive_menu()


if __name__ == "__main__":
    main()
