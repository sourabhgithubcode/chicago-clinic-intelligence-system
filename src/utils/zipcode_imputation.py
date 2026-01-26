"""
ZIP Code Imputation Script

Imputes missing ZIP codes using geographic proximity (K-Nearest Neighbors approach).
Uses Haversine formula to calculate distances between clinics and assigns the ZIP code
from the nearest clinic(s) that have valid ZIP codes.
"""

import sys
from pathlib import Path
from math import radians, cos, sin, asin, sqrt
from loguru import logger
from sqlalchemy import or_

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.database.init_db import get_session
from src.database.models import Clinic


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points on earth (in meters).

    Args:
        lat1, lon1: Latitude and longitude of point 1 in decimal degrees
        lat2, lon2: Latitude and longitude of point 2 in decimal degrees

    Returns:
        Distance in meters
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))

    # Radius of earth in meters
    r = 6371000

    return c * r


def find_nearest_zipcode(target_clinic, clinics_with_zip, k=3):
    """
    Find the ZIP code from the k nearest clinics.

    Args:
        target_clinic: Clinic object missing ZIP code
        clinics_with_zip: List of clinics that have ZIP codes
        k: Number of nearest neighbors to consider (default: 3)

    Returns:
        Tuple of (imputed_zipcode, distance_meters, neighbor_count)
    """
    if not target_clinic.latitude or not target_clinic.longitude:
        return None, None, 0

    # Calculate distances to all clinics with ZIP codes
    distances = []
    for clinic in clinics_with_zip:
        if clinic.latitude and clinic.longitude and clinic.zip_code:
            dist = haversine_distance(
                target_clinic.latitude,
                target_clinic.longitude,
                clinic.latitude,
                clinic.longitude
            )
            distances.append((clinic, dist))

    if not distances:
        return None, None, 0

    # Sort by distance
    distances.sort(key=lambda x: x[1])

    # Get k nearest neighbors
    nearest = distances[:k]

    # Count ZIP codes from nearest neighbors (most common)
    zip_counts = {}
    for clinic, dist in nearest:
        zip_code = clinic.zip_code
        if zip_code not in zip_counts:
            zip_counts[zip_code] = {'count': 0, 'min_distance': dist}
        zip_counts[zip_code]['count'] += 1
        zip_counts[zip_code]['min_distance'] = min(zip_counts[zip_code]['min_distance'], dist)

    # Choose the most common ZIP code among nearest neighbors
    # If tie, choose the one with smallest distance
    best_zip = max(zip_counts.items(), key=lambda x: (x[1]['count'], -x[1]['min_distance']))

    return best_zip[0], best_zip[1]['min_distance'], best_zip[1]['count']


def impute_missing_zipcodes(k_neighbors=3, max_distance_meters=5000, dry_run=False):
    """
    Impute missing ZIP codes for all clinics.

    Args:
        k_neighbors: Number of nearest neighbors to consider (default: 3)
        max_distance_meters: Maximum distance to consider for imputation (default: 5000m = 5km)
        dry_run: If True, only show what would be changed without committing

    Returns:
        Dictionary with imputation statistics
    """
    logger.info("Starting ZIP code imputation process...")

    session = get_session()

    try:
        # Get clinics with valid ZIP codes
        clinics_with_zip = session.query(Clinic).filter(
            Clinic.is_active == True,
            Clinic.zip_code.isnot(None),
            Clinic.zip_code != '',
            Clinic.latitude.isnot(None),
            Clinic.longitude.isnot(None)
        ).all()

        logger.info(f"Found {len(clinics_with_zip)} clinics with valid ZIP codes")

        # Get clinics missing ZIP codes
        clinics_missing_zip = session.query(Clinic).filter(
            Clinic.is_active == True,
            or_(Clinic.zip_code.is_(None), Clinic.zip_code == ''),
            Clinic.latitude.isnot(None),
            Clinic.longitude.isnot(None)
        ).all()

        logger.info(f"Found {len(clinics_missing_zip)} clinics missing ZIP codes")

        # Statistics
        stats = {
            'total_missing': len(clinics_missing_zip),
            'imputed': 0,
            'too_far': 0,
            'no_neighbors': 0,
            'imputation_details': []
        }

        # Impute each clinic
        for clinic in clinics_missing_zip:
            imputed_zip, distance, neighbor_count = find_nearest_zipcode(
                clinic,
                clinics_with_zip,
                k=k_neighbors
            )

            if imputed_zip is None:
                stats['no_neighbors'] += 1
                logger.warning(f"No neighbors found for: {clinic.name}")
                continue

            if distance > max_distance_meters:
                stats['too_far'] += 1
                logger.warning(
                    f"Nearest neighbor too far ({distance:.0f}m) for: {clinic.name}"
                )
                continue

            # Record imputation details
            detail = {
                'clinic_id': clinic.id,
                'clinic_name': clinic.name,
                'old_zipcode': clinic.zip_code or 'NULL',
                'new_zipcode': imputed_zip,
                'distance_meters': round(distance, 1),
                'neighbor_count': neighbor_count,
                'latitude': clinic.latitude,
                'longitude': clinic.longitude
            }
            stats['imputation_details'].append(detail)

            # Log the imputation
            logger.info(
                f"{'[DRY RUN] ' if dry_run else ''}Imputing ZIP {imputed_zip} for: "
                f"{clinic.name[:50]} (distance: {distance:.0f}m, neighbors: {neighbor_count})"
            )

            # Update the clinic
            if not dry_run:
                clinic.zip_code = imputed_zip
                stats['imputed'] += 1

        # Commit changes
        if not dry_run and stats['imputed'] > 0:
            session.commit()
            logger.success(f"✓ Successfully imputed {stats['imputed']} ZIP codes")
        elif dry_run:
            logger.info(f"[DRY RUN] Would impute {len(stats['imputation_details'])} ZIP codes")

        # Print summary
        logger.info("\n=== Imputation Summary ===")
        logger.info(f"Total clinics missing ZIP: {stats['total_missing']}")
        logger.info(f"Successfully imputed: {len(stats['imputation_details'])}")
        logger.info(f"Too far from neighbors: {stats['too_far']}")
        logger.info(f"No valid neighbors: {stats['no_neighbors']}")

        if stats['imputation_details']:
            logger.info("\n=== Imputation Details ===")
            for detail in stats['imputation_details'][:10]:  # Show first 10
                logger.info(
                    f"  {detail['clinic_name'][:40]:40} | "
                    f"{detail['old_zipcode']:5} → {detail['new_zipcode']:5} | "
                    f"Distance: {detail['distance_meters']:6.0f}m | "
                    f"Neighbors: {detail['neighbor_count']}"
                )

            if len(stats['imputation_details']) > 10:
                logger.info(f"  ... and {len(stats['imputation_details']) - 10} more")

        return stats

    except Exception as e:
        session.rollback()
        logger.error(f"Error during imputation: {e}")
        raise

    finally:
        session.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Impute missing ZIP codes using geographic proximity')
    parser.add_argument(
        '--k-neighbors',
        type=int,
        default=3,
        help='Number of nearest neighbors to consider (default: 3)'
    )
    parser.add_argument(
        '--max-distance',
        type=int,
        default=5000,
        help='Maximum distance in meters for imputation (default: 5000)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without committing'
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
    stats = impute_missing_zipcodes(
        k_neighbors=args.k_neighbors,
        max_distance_meters=args.max_distance,
        dry_run=args.dry_run
    )

    if not args.dry_run:
        logger.success("\n✓ ZIP code imputation complete! Power BI will show updated data on next refresh.")
    else:
        logger.info("\n[DRY RUN] No changes were made. Run without --dry-run to apply changes.")
