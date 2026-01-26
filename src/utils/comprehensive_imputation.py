"""
Comprehensive Data Imputation Script

Imputes missing values for:
1. ZIP codes (using geographic proximity - K-Nearest Neighbors)
2. Clinic types (using name keywords, categories, and similar clinics)
3. Google ratings (using Yelp ratings, similar clinics, and averages)
4. Yelp ratings (using Google ratings, similar clinics, and averages)
5. Rating categories (recalculated based on imputed ratings)

IMPORTANT: Does NOT modify data_quality_score column.
"""

import sys
import re
from pathlib import Path
from math import radians, cos, sin, asin, sqrt
from loguru import logger
from sqlalchemy import or_, func
from collections import Counter

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.database.init_db import get_session
from src.database.models import Clinic


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points on Earth (in meters)."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return 6371000 * c  # Earth radius in meters


def find_nearest_zipcode(target_clinic, clinics_with_zip, k=3):
    """Find ZIP code from k nearest clinics."""
    if not target_clinic.latitude or not target_clinic.longitude:
        return None, None, 0

    distances = []
    for clinic in clinics_with_zip:
        if clinic.latitude and clinic.longitude and clinic.zip_code:
            dist = haversine_distance(
                target_clinic.latitude, target_clinic.longitude,
                clinic.latitude, clinic.longitude
            )
            distances.append((clinic, dist))

    if not distances:
        return None, None, 0

    distances.sort(key=lambda x: x[1])
    nearest = distances[:k]

    # Most common ZIP among k nearest neighbors
    zip_counts = {}
    for clinic, dist in nearest:
        zip_code = clinic.zip_code
        if zip_code not in zip_counts:
            zip_counts[zip_code] = {'count': 0, 'min_distance': dist}
        zip_counts[zip_code]['count'] += 1
        zip_counts[zip_code]['min_distance'] = min(zip_counts[zip_code]['min_distance'], dist)

    best_zip = max(zip_counts.items(), key=lambda x: (x[1]['count'], -x[1]['min_distance']))
    return best_zip[0], best_zip[1]['min_distance'], best_zip[1]['count']


def infer_clinic_type_from_name(name):
    """
    Infer clinic type from name using keyword matching.

    Returns: clinic_type or None
    """
    name_lower = name.lower()

    # Priority order matching (most specific first)
    type_keywords = {
        'urgent_care': ['urgent', 'immediate care', 'walk-in', 'express clinic', 'quick care'],
        'dental': ['dental', 'dentist', 'orthodont', 'teeth'],
        'pediatric': ['pediatric', 'children', 'kids', 'child health'],
        'specialty': ['surgery', 'plastic', 'cosmetic', 'dermatology', 'cardiology',
                      'oncology', 'neurology', 'orthopedic', 'urology', 'radiology',
                      'ophthalmology', 'ent', 'ear nose throat', 'allergy'],
        'mental_health': ['mental health', 'counseling', 'psychiatr', 'therapy', 'behavioral'],
        'womens_health': ['women', 'obstetric', 'gynecolog', 'obgyn', 'pregnancy', 'maternal'],
        'physical_therapy': ['physical therapy', 'rehab', 'physiotherapy', 'chiropract', 'massage'],
        'primary_care': ['family', 'primary care', 'general practice', 'internal medicine',
                         'medical center', 'health center', 'clinic', 'physician']
    }

    for clinic_type, keywords in type_keywords.items():
        for keyword in keywords:
            if keyword in name_lower:
                return clinic_type

    return None


def infer_clinic_type_from_categories(categories):
    """
    Infer clinic type from Yelp/Google categories.

    Args:
        categories: List of category strings (e.g., ['Urgent Care', 'Walk-in Clinics'])

    Returns: clinic_type or None
    """
    if not categories:
        return None

    categories_str = ' '.join(categories).lower()

    # Category-to-type mapping
    category_mapping = {
        'urgent_care': ['urgent care', 'walk-in clinic', 'emergency'],
        'dental': ['dentist', 'dental', 'orthodontist'],
        'pediatric': ['pediatrician', 'child health', 'kids'],
        'specialty': ['surgeon', 'plastic surgery', 'dermatologist', 'cardiologist',
                      'oncologist', 'neurologist', 'orthopedist', 'urologist',
                      'ophthalmologist', 'ear nose & throat', 'allergist'],
        'mental_health': ['counseling', 'mental health', 'psychiatrist', 'psychologist', 'therapy'],
        'womens_health': ['obstetrician', 'gynecologist', 'obgyn', 'women\'s health'],
        'physical_therapy': ['physical therapy', 'chiropractor', 'massage', 'acupuncture'],
        'primary_care': ['family practice', 'internal medicine', 'medical center',
                         'general practitioner', 'primary care', 'concierge medicine']
    }

    for clinic_type, keywords in category_mapping.items():
        for keyword in keywords:
            if keyword in categories_str:
                return clinic_type

    return None


def impute_clinic_type(clinic, all_clinics):
    """
    Impute clinic type using multiple strategies.

    Strategy:
    1. Extract from clinic name (keywords like "urgent", "dental", etc.)
    2. Extract from categories (Yelp/Google categories)
    3. Use most common type among 3 nearest clinics with same ZIP
    4. Fallback: "primary_care"
    """
    # Strategy 1: Infer from name
    type_from_name = infer_clinic_type_from_name(clinic.name)
    if type_from_name:
        return type_from_name, 'name_inference'

    # Strategy 2: Infer from categories
    if clinic.categories:
        type_from_categories = infer_clinic_type_from_categories(clinic.categories)
        if type_from_categories:
            return type_from_categories, 'category_inference'

    # Strategy 3: Use K-Nearest Neighbors in same ZIP code
    if clinic.zip_code and clinic.latitude and clinic.longitude:
        # Find clinics in same ZIP with valid types
        same_zip_clinics = [
            c for c in all_clinics
            if c.zip_code == clinic.zip_code
            and c.clinic_type
            and c.clinic_type.strip() != ''
            and c.clinic_type.strip().lower() not in ['unknown', 'none', 'null']
            and c.latitude
            and c.longitude
            and c.id != clinic.id
        ]

        if same_zip_clinics:
            # Calculate distances
            distances = []
            for c in same_zip_clinics:
                dist = haversine_distance(
                    clinic.latitude, clinic.longitude,
                    c.latitude, c.longitude
                )
                distances.append((c, dist))

            # Get 3 nearest
            distances.sort(key=lambda x: x[1])
            nearest_3 = distances[:3]

            # Most common type among nearest 3
            types = [c.clinic_type for c, _ in nearest_3]
            if types:
                most_common = Counter(types).most_common(1)[0][0]
                return most_common, f'knn_same_zip'

    # Fallback: primary_care (most common clinic type)
    return 'primary_care', 'fallback_default'


def impute_google_rating(clinic, all_clinics):
    """
    Impute Google rating using multiple strategies.

    Strategy:
    1. If has Yelp rating, use it as proxy (Google ratings trend ~0.1 higher)
    2. Use average Google rating of same clinic type in same ZIP
    3. Use K-NN: average Google rating of 5 nearest clinics with Google ratings
    4. Fallback: City-wide average for clinic type
    """
    # Strategy 1: Use Yelp rating as proxy (Google ~0.1 higher)
    if clinic.yelp_rating:
        # Google ratings tend to be slightly higher than Yelp
        imputed = min(5.0, clinic.yelp_rating + 0.1)
        return round(imputed, 1), 'yelp_proxy'

    # Strategy 2: Average of same type in same ZIP
    if clinic.clinic_type and clinic.zip_code:
        same_type_zip = [
            c.google_rating for c in all_clinics
            if c.clinic_type == clinic.clinic_type
            and c.zip_code == clinic.zip_code
            and c.google_rating is not None
            and c.id != clinic.id
        ]
        if same_type_zip:
            avg = sum(same_type_zip) / len(same_type_zip)
            return round(avg, 1), f'avg_same_type_zip'

    # Strategy 3: K-Nearest Neighbors (5 nearest with Google ratings)
    if clinic.latitude and clinic.longitude:
        clinics_with_google = [
            c for c in all_clinics
            if c.google_rating is not None
            and c.latitude and c.longitude
            and c.id != clinic.id
        ]

        if clinics_with_google:
            distances = []
            for c in clinics_with_google:
                dist = haversine_distance(
                    clinic.latitude, clinic.longitude,
                    c.latitude, c.longitude
                )
                distances.append((c, dist))

            distances.sort(key=lambda x: x[1])
            nearest_5 = distances[:5]

            ratings = [c.google_rating for c, _ in nearest_5]
            if ratings:
                avg = sum(ratings) / len(ratings)
                return round(avg, 1), 'knn_5_nearest'

    # Strategy 4: City-wide average for clinic type
    if clinic.clinic_type:
        same_type = [
            c.google_rating for c in all_clinics
            if c.clinic_type == clinic.clinic_type
            and c.google_rating is not None
        ]
        if same_type:
            avg = sum(same_type) / len(same_type)
            return round(avg, 1), f'avg_citywide_type'

    # Final fallback: City-wide average
    all_google = [c.google_rating for c in all_clinics if c.google_rating is not None]
    if all_google:
        avg = sum(all_google) / len(all_google)
        return round(avg, 1), 'avg_citywide_all'

    # Absolute fallback
    return 4.0, 'fallback_default'


def impute_yelp_rating(clinic, all_clinics):
    """
    Impute Yelp rating using multiple strategies.

    Strategy:
    1. If has Google rating, use it as proxy (Yelp ratings trend ~0.1 lower)
    2. Use average Yelp rating of same clinic type in same ZIP
    3. Use K-NN: average Yelp rating of 5 nearest clinics with Yelp ratings
    4. Fallback: City-wide average for clinic type
    """
    # Strategy 1: Use Google rating as proxy (Yelp ~0.1 lower)
    if clinic.google_rating:
        # Yelp ratings tend to be slightly lower than Google
        imputed = max(1.0, clinic.google_rating - 0.1)
        return round(imputed, 1), 'google_proxy'

    # Strategy 2: Average of same type in same ZIP
    if clinic.clinic_type and clinic.zip_code:
        same_type_zip = [
            c.yelp_rating for c in all_clinics
            if c.clinic_type == clinic.clinic_type
            and c.zip_code == clinic.zip_code
            and c.yelp_rating is not None
            and c.id != clinic.id
        ]
        if same_type_zip:
            avg = sum(same_type_zip) / len(same_type_zip)
            return round(avg, 1), f'avg_same_type_zip'

    # Strategy 3: K-Nearest Neighbors (5 nearest with Yelp ratings)
    if clinic.latitude and clinic.longitude:
        clinics_with_yelp = [
            c for c in all_clinics
            if c.yelp_rating is not None
            and c.latitude and c.longitude
            and c.id != clinic.id
        ]

        if clinics_with_yelp:
            distances = []
            for c in clinics_with_yelp:
                dist = haversine_distance(
                    clinic.latitude, clinic.longitude,
                    c.latitude, c.longitude
                )
                distances.append((c, dist))

            distances.sort(key=lambda x: x[1])
            nearest_5 = distances[:5]

            ratings = [c.yelp_rating for c, _ in nearest_5]
            if ratings:
                avg = sum(ratings) / len(ratings)
                return round(avg, 1), 'knn_5_nearest'

    # Strategy 4: City-wide average for clinic type
    if clinic.clinic_type:
        same_type = [
            c.yelp_rating for c in all_clinics
            if c.clinic_type == clinic.clinic_type
            and c.yelp_rating is not None
        ]
        if same_type:
            avg = sum(same_type) / len(same_type)
            return round(avg, 1), f'avg_citywide_type'

    # Final fallback: City-wide average
    all_yelp = [c.yelp_rating for c in all_clinics if c.yelp_rating is not None]
    if all_yelp:
        avg = sum(all_yelp) / len(all_yelp)
        return round(avg, 1), 'avg_citywide_all'

    # Absolute fallback
    return 3.8, 'fallback_default'


def calculate_rating_category(combined_rating):
    """
    Calculate rating category based on combined rating.

    Categories:
    - Excellent (4.0+)
    - Good (3.5-4.0)
    - Medium (2.5-3.5)
    - Low (0-2.5)
    """
    if combined_rating is None:
        return None

    if combined_rating >= 4.0:
        return 'Excellent (4.0+)'
    elif combined_rating >= 3.5:
        return 'Good (3.5-4.0)'
    elif combined_rating >= 2.5:
        return 'Medium (2.5-3.5)'
    else:
        return 'Low (0-2.5)'


def run_comprehensive_imputation(dry_run=False, include_inactive=True):
    """
    Run comprehensive imputation for all missing fields.

    Args:
        dry_run: If True, only show what would be changed without committing
        include_inactive: If True, also impute inactive clinics (for Power BI)

    Returns:
        Dictionary with imputation statistics
    """
    logger.info("=" * 80)
    logger.info("COMPREHENSIVE DATA IMPUTATION (ULTRA-ROBUST)")
    logger.info("=" * 80)

    session = get_session()

    try:
        # Load ALL clinics (including inactive for Power BI completeness)
        if include_inactive:
            all_clinics = session.query(Clinic).all()
            active_count = session.query(Clinic).filter(Clinic.is_active == True).count()
            logger.info(f"Total clinics: {len(all_clinics)} (Active: {active_count}, Inactive: {len(all_clinics) - active_count})")
        else:
            all_clinics = session.query(Clinic).filter(Clinic.is_active == True).all()
            logger.info(f"Total active clinics: {len(all_clinics)}")

        total = len(all_clinics)
        logger.info("")

        stats = {
            'zip_codes_imputed': 0,
            'clinic_types_imputed': 0,
            'google_ratings_imputed': 0,
            'yelp_ratings_imputed': 0,
            'rating_categories_updated': 0,
            'imputation_details': []
        }

        # =================================================================
        # STEP 1: ZIP CODE IMPUTATION
        # =================================================================
        logger.info("STEP 1: ZIP Code Imputation")
        logger.info("-" * 80)

        clinics_with_zip = [c for c in all_clinics if c.zip_code and c.zip_code.strip() != '' and c.latitude and c.longitude]
        clinics_missing_zip = [c for c in all_clinics if (not c.zip_code or c.zip_code.strip() == '') and c.latitude and c.longitude]

        logger.info(f"Clinics with ZIP codes: {len(clinics_with_zip)}")
        logger.info(f"Clinics missing ZIP codes: {len(clinics_missing_zip)}")

        for clinic in clinics_missing_zip:
            imputed_zip, distance, neighbor_count = find_nearest_zipcode(clinic, clinics_with_zip, k=3)

            if imputed_zip and distance <= 5000:  # Max 5km
                if not dry_run:
                    clinic.zip_code = imputed_zip
                stats['zip_codes_imputed'] += 1
                logger.info(f"{'[DRY RUN] ' if dry_run else ''}ZIP {imputed_zip} → {clinic.name[:50]} (distance: {distance:.0f}m)")

        logger.info(f"✓ Imputed {stats['zip_codes_imputed']} ZIP codes")
        logger.info("")

        # =================================================================
        # STEP 2: CLINIC TYPE IMPUTATION
        # =================================================================
        logger.info("STEP 2: Clinic Type Imputation")
        logger.info("-" * 80)

        clinics_missing_type = [
            c for c in all_clinics
            if not c.clinic_type or c.clinic_type.strip() == '' or c.clinic_type.strip().lower() in ['unknown', 'none', 'null']
        ]

        logger.info(f"Clinics missing/unknown type: {len(clinics_missing_type)}")

        for clinic in clinics_missing_type:
            imputed_type, method = impute_clinic_type(clinic, all_clinics)

            if not dry_run:
                clinic.clinic_type = imputed_type
            stats['clinic_types_imputed'] += 1
            logger.info(f"{'[DRY RUN] ' if dry_run else ''}{imputed_type:20} → {clinic.name[:40]:40} (method: {method})")

        logger.info(f"✓ Imputed {stats['clinic_types_imputed']} clinic types")
        logger.info("")

        # =================================================================
        # STEP 3: GOOGLE RATING IMPUTATION
        # =================================================================
        logger.info("STEP 3: Google Rating Imputation")
        logger.info("-" * 80)

        clinics_missing_google = [c for c in all_clinics if c.google_rating is None]

        logger.info(f"Clinics missing Google rating: {len(clinics_missing_google)}")

        for clinic in clinics_missing_google:
            imputed_rating, method = impute_google_rating(clinic, all_clinics)

            if not dry_run:
                clinic.google_rating = imputed_rating
            stats['google_ratings_imputed'] += 1

            if stats['google_ratings_imputed'] <= 10:  # Show first 10
                logger.info(f"{'[DRY RUN] ' if dry_run else ''}{imputed_rating:.1f} → {clinic.name[:40]:40} (method: {method})")

        if stats['google_ratings_imputed'] > 10:
            logger.info(f"... and {stats['google_ratings_imputed'] - 10} more")

        logger.info(f"✓ Imputed {stats['google_ratings_imputed']} Google ratings")
        logger.info("")

        # =================================================================
        # STEP 4: YELP RATING IMPUTATION
        # =================================================================
        logger.info("STEP 4: Yelp Rating Imputation")
        logger.info("-" * 80)

        clinics_missing_yelp = [c for c in all_clinics if c.yelp_rating is None]

        logger.info(f"Clinics missing Yelp rating: {len(clinics_missing_yelp)}")

        for clinic in clinics_missing_yelp:
            imputed_rating, method = impute_yelp_rating(clinic, all_clinics)

            if not dry_run:
                clinic.yelp_rating = imputed_rating
            stats['yelp_ratings_imputed'] += 1

            if stats['yelp_ratings_imputed'] <= 10:  # Show first 10
                logger.info(f"{'[DRY RUN] ' if dry_run else ''}{imputed_rating:.1f} → {clinic.name[:40]:40} (method: {method})")

        if stats['yelp_ratings_imputed'] > 10:
            logger.info(f"... and {stats['yelp_ratings_imputed'] - 10} more")

        logger.info(f"✓ Imputed {stats['yelp_ratings_imputed']} Yelp ratings")
        logger.info("")

        # =================================================================
        # STEP 5: UPDATE COMBINED RATING & RATING CATEGORY
        # =================================================================
        logger.info("STEP 5: Update Combined Rating & Rating Category")
        logger.info("-" * 80)

        for clinic in all_clinics:
            # Calculate combined rating
            ratings = []
            if clinic.google_rating:
                ratings.append(clinic.google_rating)
            if clinic.yelp_rating:
                ratings.append(clinic.yelp_rating)

            if ratings:
                new_combined = round(sum(ratings) / len(ratings), 1)

                # Update combined rating if changed
                if clinic.combined_rating != new_combined:
                    if not dry_run:
                        clinic.combined_rating = new_combined

                # Update rating category based on combined rating
                new_category = calculate_rating_category(new_combined)
                if clinic.rating_category != new_category:
                    if not dry_run:
                        clinic.rating_category = new_category
                    stats['rating_categories_updated'] += 1

        logger.info(f"✓ Updated {stats['rating_categories_updated']} rating categories")
        logger.info("")

        # Commit changes
        if not dry_run:
            session.commit()
            logger.success("✓ All changes committed to database")
        else:
            logger.info("[DRY RUN] No changes were made to database")

        # Print summary
        logger.info("")
        logger.info("=" * 80)
        logger.info("IMPUTATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"ZIP codes imputed:         {stats['zip_codes_imputed']}")
        logger.info(f"Clinic types imputed:      {stats['clinic_types_imputed']}")
        logger.info(f"Google ratings imputed:    {stats['google_ratings_imputed']}")
        logger.info(f"Yelp ratings imputed:      {stats['yelp_ratings_imputed']}")
        logger.info(f"Rating categories updated: {stats['rating_categories_updated']}")
        logger.info("")
        logger.info("NOTE: data_quality_score column was NOT modified")

        return stats

    except Exception as e:
        session.rollback()
        logger.error(f"Error during imputation: {e}")
        raise

    finally:
        session.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Comprehensive data imputation for missing values')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without committing'
    )
    parser.add_argument(
        '--active-only',
        action='store_true',
        help='Only impute active clinics (default: impute all clinics)'
    )

    args = parser.parse_args()

    # Setup logging
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    )

    # Run imputation
    stats = run_comprehensive_imputation(
        dry_run=args.dry_run,
        include_inactive=not args.active_only
    )

    if not args.dry_run:
        logger.success("\n✓ Comprehensive imputation complete! Power BI will show updated data on next refresh.")
    else:
        logger.info("\n[DRY RUN] No changes were made. Run without --dry-run to apply changes.")
