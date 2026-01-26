"""
Data Cleaning & Export for Power BI Dashboard.

This script:
1. Finds and merges duplicate clinics in the database
2. Cleans and standardizes data
3. Creates combined metrics from both APIs
4. Exports clean CSVs ready for Power BI

RUN THIS BEFORE IMPORTING TO POWER BI!
"""

import sys
import re
import csv
from pathlib import Path
from datetime import datetime
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.database.models import Clinic, Review, VisibilityScore, DemandMetric
from src.database.init_db import get_session
from src.utils.clinic_matcher import ClinicMatcher


class DataCleaner:
    """
    Clean and prepare clinic data for Power BI.

    WHAT IT DOES:
    -------------
    1. DEDUPLICATION: Finds duplicate clinics and merges them
    2. STANDARDIZATION: Normalizes phones, addresses, names
    3. COMBINED METRICS: Creates avg_rating, total_reviews from both APIs
    4. DATA QUALITY FLAGS: Marks incomplete/suspicious records
    5. POWER BI EXPORT: Creates clean CSVs with proper formatting
    """

    def __init__(self):
        self.session = get_session()
        self.duplicates_found = 0
        self.records_merged = 0
        self.records_cleaned = 0

    def find_and_merge_duplicates(self):
        """
        Find duplicate clinics in the database and merge them.

        EXAMPLE:
        --------
        Before:
            Row 1: id=5, name="Rush Medical", google_place_id="G123", yelp_business_id=NULL
            Row 2: id=8, name="Rush Medical Center", google_place_id=NULL, yelp_business_id="Y456"

        After merging:
            Row 1: id=5, name="Rush Medical", google_place_id="G123", yelp_business_id="Y456"
            Row 2: DELETED

        Reviews from Row 2 are reassigned to Row 1.
        """
        logger.info("=" * 60)
        logger.info("STEP 1: Finding and merging duplicate clinics")
        logger.info("=" * 60)

        # Get all clinics
        all_clinics = self.session.query(Clinic).filter(
            Clinic.is_active == True
        ).all()

        logger.info(f"Total active clinics: {len(all_clinics)}")

        # Group by potential duplicates
        processed_ids = set()
        merge_groups = []

        for i, clinic1 in enumerate(all_clinics):
            if clinic1.id in processed_ids:
                continue

            group = [clinic1]
            processed_ids.add(clinic1.id)

            for clinic2 in all_clinics[i + 1:]:
                if clinic2.id in processed_ids:
                    continue

                # Check if they match
                result = ClinicMatcher.calculate_match_score(clinic1, clinic2)

                if result['is_match']:
                    group.append(clinic2)
                    processed_ids.add(clinic2.id)
                    self.duplicates_found += 1
                    logger.info(
                        f"  DUPLICATE FOUND: '{clinic1.name}' <-> '{clinic2.name}' "
                        f"(score={result['score']}, {result['match_reasons']})"
                    )

            if len(group) > 1:
                merge_groups.append(group)

        # Merge each group
        for group in merge_groups:
            self._merge_clinic_group(group)

        logger.info(f"Duplicates found: {self.duplicates_found}")
        logger.info(f"Records merged: {self.records_merged}")

    def _merge_clinic_group(self, clinics):
        """
        Merge a group of duplicate clinics into one.

        Strategy: Keep the record with the most data, merge in missing fields.
        """
        if len(clinics) < 2:
            return

        # Sort by data completeness (most complete first)
        def completeness_score(c):
            score = 0
            if c.google_place_id:
                score += 10
            if c.yelp_business_id:
                score += 10
            if c.google_rating:
                score += 5
            if c.yelp_rating:
                score += 5
            if c.phone:
                score += 3
            if c.website:
                score += 3
            if c.address:
                score += 2
            return score

        clinics.sort(key=completeness_score, reverse=True)
        primary = clinics[0]
        duplicates = clinics[1:]

        logger.info(f"  Merging into: '{primary.name}' (id={primary.id})")

        for dup in duplicates:
            # Merge Yelp data if primary doesn't have it
            if not primary.yelp_business_id and dup.yelp_business_id:
                primary.yelp_business_id = dup.yelp_business_id
                primary.yelp_rating = dup.yelp_rating
                primary.yelp_review_count = dup.yelp_review_count
                primary.yelp_price_level = dup.yelp_price_level
            elif primary.yelp_business_id and dup.yelp_business_id:
                # Both have Yelp data - keep primary's, just take better ratings if applicable
                if dup.yelp_rating and (not primary.yelp_rating or dup.yelp_review_count > primary.yelp_review_count):
                    primary.yelp_rating = dup.yelp_rating
                    primary.yelp_review_count = dup.yelp_review_count

            # Merge Google data if primary doesn't have it
            if not primary.google_place_id and dup.google_place_id:
                primary.google_place_id = dup.google_place_id
                primary.google_rating = dup.google_rating
                primary.google_review_count = dup.google_review_count
                primary.google_price_level = dup.google_price_level
            elif primary.google_place_id and dup.google_place_id:
                # Both have Google data - keep primary's, just take better ratings if applicable
                if dup.google_rating and (not primary.google_rating or dup.google_review_count > primary.google_review_count):
                    primary.google_rating = dup.google_rating
                    primary.google_review_count = dup.google_review_count

            # Fill other gaps
            if not primary.phone and dup.phone:
                primary.phone = dup.phone
            if not primary.website and dup.website:
                primary.website = dup.website
            if not primary.latitude and dup.latitude:
                primary.latitude = dup.latitude
                primary.longitude = dup.longitude
            if not primary.zip_code and dup.zip_code:
                primary.zip_code = dup.zip_code
            if not primary.address and dup.address:
                primary.address = dup.address

            # Clear the duplicate's unique IDs before deactivating to avoid constraint issues
            dup.google_place_id = None
            dup.yelp_business_id = None

            # Commit this change first to release the unique constraint
            self.session.flush()

            # Reassign reviews from duplicate to primary
            reviews = self.session.query(Review).filter_by(clinic_id=dup.id).all()
            for review in reviews:
                review.clinic_id = primary.id
                logger.info(f"    Moved review {review.id} to primary clinic")

            # Mark duplicate as inactive (soft delete)
            dup.is_active = False
            self.records_merged += 1
            logger.info(f"    Merged and deactivated: '{dup.name}' (id={dup.id})")

        primary.last_updated = datetime.utcnow()
        self.session.commit()

    def clean_and_standardize(self):
        """
        Clean and standardize all clinic data.

        CLEANING OPERATIONS:
        --------------------
        1. Phone: Format as (XXX) XXX-XXXX
        2. Name: Trim whitespace, fix capitalization
        3. Address: Standardize abbreviations
        4. ZIP: Ensure 5-digit format
        """
        logger.info("=" * 60)
        logger.info("STEP 2: Cleaning and standardizing data")
        logger.info("=" * 60)

        clinics = self.session.query(Clinic).filter(
            Clinic.is_active == True
        ).all()

        for clinic in clinics:
            changed = False

            # Clean phone number
            if clinic.phone:
                clean_phone = self._format_phone(clinic.phone)
                if clean_phone != clinic.phone:
                    clinic.phone = clean_phone
                    changed = True

            # Clean name
            if clinic.name:
                clean_name = self._clean_name(clinic.name)
                if clean_name != clinic.name:
                    clinic.name = clean_name
                    changed = True

            # Clean ZIP code
            if clinic.zip_code:
                clean_zip = self._clean_zip(clinic.zip_code)
                if clean_zip != clinic.zip_code:
                    clinic.zip_code = clean_zip
                    changed = True

            if changed:
                self.records_cleaned += 1

        self.session.commit()
        logger.info(f"Records cleaned: {self.records_cleaned}")

    def _format_phone(self, phone):
        """
        Format phone number as (XXX) XXX-XXXX.

        EXAMPLE:
            Input:  "+1-312-926-2000"
            Output: "(312) 926-2000"
        """
        if not phone:
            return phone

        # Extract digits
        digits = re.sub(r'\D', '', phone)

        # Remove country code
        if len(digits) == 11 and digits.startswith('1'):
            digits = digits[1:]

        # Format if we have 10 digits
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"

        return phone  # Return original if can't format

    def _clean_name(self, name):
        """
        Clean clinic name.

        EXAMPLE:
            Input:  "  RUSH MEDICAL CENTER  "
            Output: "Rush Medical Center"
        """
        if not name:
            return name

        # Trim whitespace
        name = name.strip()

        # Fix ALL CAPS (convert to title case)
        if name.isupper():
            name = name.title()

        return name

    def _clean_zip(self, zip_code):
        """
        Clean ZIP code to 5-digit format.

        EXAMPLE:
            Input:  "60612-1234"
            Output: "60612"
        """
        if not zip_code:
            return zip_code

        # Extract first 5 digits
        digits = re.sub(r'\D', '', str(zip_code))
        if len(digits) >= 5:
            return digits[:5]

        return zip_code

    def create_combined_metrics(self):
        """
        Create combined metrics from both APIs for Power BI.

        NEW COLUMNS ADDED:
        ------------------
        - combined_rating: Average of Google + Yelp ratings
        - total_review_count: Sum of reviews from both sources
        - data_sources: "Google+Yelp", "Google Only", "Yelp Only"
        - data_quality_score: 0-100 based on completeness
        """
        logger.info("=" * 60)
        logger.info("STEP 3: Creating combined metrics")
        logger.info("=" * 60)

        clinics = self.session.query(Clinic).filter(
            Clinic.is_active == True
        ).all()

        metrics = []
        for clinic in clinics:
            metric = self._calculate_combined_metrics(clinic)
            metrics.append(metric)

        logger.info(f"Calculated metrics for {len(metrics)} clinics")
        return metrics

    def _calculate_combined_metrics(self, clinic):
        """
        Calculate combined metrics for a single clinic.
        """
        # Determine data sources
        has_google = clinic.google_place_id is not None
        has_yelp = clinic.yelp_business_id is not None

        if has_google and has_yelp:
            data_sources = "Google+Yelp"
        elif has_google:
            data_sources = "Google Only"
        elif has_yelp:
            data_sources = "Yelp Only"
        else:
            data_sources = "Unknown"

        # Calculate combined rating
        ratings = []
        if clinic.google_rating:
            ratings.append(clinic.google_rating)
        if clinic.yelp_rating:
            ratings.append(clinic.yelp_rating)

        combined_rating = sum(ratings) / len(ratings) if ratings else None

        # Calculate total reviews
        total_reviews = (clinic.google_review_count or 0) + (clinic.yelp_review_count or 0)

        # Calculate data quality score (0-100)
        quality_score = 0
        if clinic.name:
            quality_score += 10
        if clinic.address:
            quality_score += 10
        if clinic.phone:
            quality_score += 10
        if clinic.latitude and clinic.longitude:
            quality_score += 10
        if clinic.google_place_id:
            quality_score += 15
        if clinic.yelp_business_id:
            quality_score += 15
        if clinic.google_rating:
            quality_score += 10
        if clinic.yelp_rating:
            quality_score += 10
        if clinic.website:
            quality_score += 5
        if clinic.clinic_type:
            quality_score += 5

        return {
            'clinic_id': clinic.id,
            'name': clinic.name,
            'address': clinic.address,
            'city': clinic.city,
            'state': clinic.state,
            'zip_code': clinic.zip_code,
            'phone': clinic.phone,
            'website': clinic.website,
            'latitude': clinic.latitude,
            'longitude': clinic.longitude,
            'clinic_type': clinic.clinic_type,
            # Google metrics
            'google_place_id': clinic.google_place_id,
            'google_rating': clinic.google_rating,
            'google_review_count': clinic.google_review_count,
            # Yelp metrics
            'yelp_business_id': clinic.yelp_business_id,
            'yelp_rating': clinic.yelp_rating,
            'yelp_review_count': clinic.yelp_review_count,
            # COMBINED METRICS (new for Power BI)
            'combined_rating': round(combined_rating, 2) if combined_rating else None,
            'total_review_count': total_reviews,
            'data_sources': data_sources,
            'data_quality_score': quality_score,
            'is_complete': quality_score >= 70,
            'has_both_apis': has_google and has_yelp,
        }

    def export_for_powerbi(self, output_dir=None):
        """
        Export clean data as CSVs for Power BI.

        OUTPUT FILES:
        -------------
        1. clinics_clean.csv - Deduplicated clinics with combined metrics
        2. clinics_summary.csv - Aggregated stats by ZIP/type
        3. data_quality_report.csv - Data quality issues
        """
        logger.info("=" * 60)
        logger.info("STEP 4: Exporting clean data for Power BI")
        logger.info("=" * 60)

        if output_dir is None:
            output_dir = Path(__file__).resolve().parent.parent.parent / "data" / "exports"

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Get combined metrics
        metrics = self.create_combined_metrics()

        # 1. Export clean clinics
        clinics_file = output_dir / "clinics_clean.csv"
        self._export_csv(metrics, clinics_file)
        logger.info(f"Exported: {clinics_file} ({len(metrics)} records)")

        # 2. Export summary by ZIP
        summary = self._create_zip_summary(metrics)
        summary_file = output_dir / "clinics_by_zip_summary.csv"
        self._export_csv(summary, summary_file)
        logger.info(f"Exported: {summary_file} ({len(summary)} ZIP codes)")

        # 3. Export data quality report
        quality_report = self._create_quality_report(metrics)
        quality_file = output_dir / "data_quality_report.csv"
        self._export_csv(quality_report, quality_file)
        logger.info(f"Exported: {quality_file}")

        return {
            'clinics_file': str(clinics_file),
            'summary_file': str(summary_file),
            'quality_file': str(quality_file),
            'total_records': len(metrics)
        }

    def _export_csv(self, data, filepath):
        """Export list of dicts to CSV."""
        if not data:
            return

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

    def _create_zip_summary(self, metrics):
        """
        Create summary statistics by ZIP code.

        EXAMPLE OUTPUT:
        ---------------
        zip_code | clinic_count | avg_rating | total_reviews | pct_complete
        60601    | 15           | 4.2        | 1250          | 80%
        60602    | 8            | 3.9        | 560           | 62%
        """
        zip_stats = {}

        for m in metrics:
            zip_code = m['zip_code'] or 'Unknown'

            if zip_code not in zip_stats:
                zip_stats[zip_code] = {
                    'zip_code': zip_code,
                    'clinic_count': 0,
                    'ratings': [],
                    'total_reviews': 0,
                    'complete_count': 0,
                    'both_apis_count': 0,
                }

            stats = zip_stats[zip_code]
            stats['clinic_count'] += 1
            stats['total_reviews'] += m['total_review_count']

            if m['combined_rating']:
                stats['ratings'].append(m['combined_rating'])
            if m['is_complete']:
                stats['complete_count'] += 1
            if m['has_both_apis']:
                stats['both_apis_count'] += 1

        # Calculate averages
        summary = []
        for zip_code, stats in zip_stats.items():
            avg_rating = (
                round(sum(stats['ratings']) / len(stats['ratings']), 2)
                if stats['ratings'] else None
            )
            pct_complete = round(stats['complete_count'] / stats['clinic_count'] * 100, 1)
            pct_both_apis = round(stats['both_apis_count'] / stats['clinic_count'] * 100, 1)

            summary.append({
                'zip_code': zip_code,
                'clinic_count': stats['clinic_count'],
                'avg_rating': avg_rating,
                'total_reviews': stats['total_reviews'],
                'pct_complete_data': pct_complete,
                'pct_both_apis': pct_both_apis,
            })

        # Sort by clinic count
        summary.sort(key=lambda x: x['clinic_count'], reverse=True)
        return summary

    def _create_quality_report(self, metrics):
        """
        Create data quality report for Power BI.
        """
        total = len(metrics)
        google_only = sum(1 for m in metrics if m['data_sources'] == 'Google Only')
        yelp_only = sum(1 for m in metrics if m['data_sources'] == 'Yelp Only')
        both = sum(1 for m in metrics if m['data_sources'] == 'Google+Yelp')
        complete = sum(1 for m in metrics if m['is_complete'])
        missing_phone = sum(1 for m in metrics if not m['phone'])
        missing_coords = sum(1 for m in metrics if not m['latitude'])

        return [
            {'metric': 'Total Clinics', 'value': total, 'percentage': '100%'},
            {'metric': 'Both APIs (Google+Yelp)', 'value': both, 'percentage': f'{both/total*100:.1f}%'},
            {'metric': 'Google Only', 'value': google_only, 'percentage': f'{google_only/total*100:.1f}%'},
            {'metric': 'Yelp Only', 'value': yelp_only, 'percentage': f'{yelp_only/total*100:.1f}%'},
            {'metric': 'Complete Records (70%+ quality)', 'value': complete, 'percentage': f'{complete/total*100:.1f}%'},
            {'metric': 'Missing Phone', 'value': missing_phone, 'percentage': f'{missing_phone/total*100:.1f}%'},
            {'metric': 'Missing Coordinates', 'value': missing_coords, 'percentage': f'{missing_coords/total*100:.1f}%'},
            {'metric': 'Duplicates Found', 'value': self.duplicates_found, 'percentage': '-'},
            {'metric': 'Records Merged', 'value': self.records_merged, 'percentage': '-'},
        ]

    def run_full_cleaning(self):
        """
        Run the complete data cleaning pipeline.
        """
        logger.info("=" * 70)
        logger.info("CLINIC DATA CLEANING FOR POWER BI")
        logger.info("=" * 70)
        logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("")

        # Step 1: Find and merge duplicates
        self.find_and_merge_duplicates()
        logger.info("")

        # Step 2: Clean and standardize
        self.clean_and_standardize()
        logger.info("")

        # Step 3 & 4: Create metrics and export
        result = self.export_for_powerbi()
        logger.info("")

        # Summary
        logger.info("=" * 70)
        logger.info("CLEANING COMPLETE!")
        logger.info("=" * 70)
        logger.info(f"Duplicates found:  {self.duplicates_found}")
        logger.info(f"Records merged:    {self.records_merged}")
        logger.info(f"Records cleaned:   {self.records_cleaned}")
        logger.info(f"Total exported:    {result['total_records']}")
        logger.info("")
        logger.info("OUTPUT FILES (import these to Power BI):")
        logger.info(f"  1. {result['clinics_file']}")
        logger.info(f"  2. {result['summary_file']}")
        logger.info(f"  3. {result['quality_file']}")

        return result

    def close(self):
        """Close database session."""
        self.session.close()


if __name__ == "__main__":
    from src.database.init_db import setup_logging

    setup_logging()

    cleaner = DataCleaner()
    try:
        cleaner.run_full_cleaning()
    finally:
        cleaner.close()
