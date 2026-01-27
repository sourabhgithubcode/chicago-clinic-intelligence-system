"""
Yelp API data collector for clinic information and reviews.
"""

import requests
import time
from datetime import datetime
from loguru import logger
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config.settings import (
    YELP_API_KEY,
    TARGET_CITY,
    TARGET_STATE,
    CHICAGO_ZIP_CODES,
    API_RATE_LIMIT_DELAY,
    MAX_RETRIES
)
from src.database.sqlalchemy_database_models import Clinic, Review, DataCollectionLog
from src.database.initialize_create_database_tables import get_session
from src.utils.clinic_matcher import ClinicMatcher, merge_clinic_data


class YelpCollector:
    """
    Collector for Yelp Fusion API data.
    """

    def __init__(self):
        self.api_key = YELP_API_KEY
        self.base_url = "https://api.yelp.com/v3"
        self.headers = {
            'Authorization': f'Bearer {self.api_key}'
        }
        self.session = get_session()
        self.collected_count = 0
        self.updated_count = 0
        self.failed_count = 0

    def search_businesses(self, location, categories='health', limit=50):
        """
        Search for businesses using Yelp API.
        """
        url = f"{self.base_url}/businesses/search"

        params = {
            'location': location,
            'categories': categories,
            'term': 'clinic',
            'limit': limit
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            data = response.json()
            return data.get('businesses', [])

        except Exception as e:
            logger.error(f"Yelp search failed for {location}: {e}")
            return []
    def get_business_details(self, business_id):
        """
        Get detailed business information.
        """
        url = f"{self.base_url}/businesses/{business_id}"

        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=15
            )

            if response.status_code == 404:
                logger.warning(
                    f"Yelp details not found (404) for business_id={business_id}"
                )
                return {}

            if response.status_code == 403:
                logger.warning(
                    f"Yelp details forbidden (403) for business_id={business_id}"
                )
                return {}

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            logger.warning(
                f"Yelp details HTTP error for business_id={business_id}: {e}"
            )
            return {}

        except requests.exceptions.RequestException as e:
            logger.warning(
                f"Yelp details request failed for business_id={business_id}: {e}"
            )
            return {}

        except Exception as e:
            logger.warning(
                f"Unexpected error in get_business_details for business_id={business_id}: {e}"
            )
            return {}

   
    def map_yelp_categories_to_clinic_type(self, categories):
        """
        Map Yelp categories to internal clinic_type.
        categories: list[str] of Yelp category titles or aliases
        """
        if not categories:
            return None

        cats = " ".join([c.lower() for c in categories])

        # Urgent care
        if "urgent care" in cats or "emergency" in cats:
            return "urgent_care"

        # Dental
        if "dentist" in cats or "dental" in cats or "orthodont" in cats:
            return "dental"

        # Pediatric
        if "pediatric" in cats or "children" in cats:
            return "pediatric"

        # Physical therapy
        if "physical therapy" in cats or "physiotherapy" in cats:
            return "specialty"

        # Dermatology
        if "dermatolog" in cats or "skin" in cats:
            return "specialty"

        # Primary care or general clinics
        if (
            "medical center" in cats
            or "family practice" in cats
            or "internal medicine" in cats
            or "clinic" in cats
        ):
            return "primary_care"

        return None

    def get_reviews(self, business_id):
        """
        Get reviews for a business.
        """
        url = f"{self.base_url}/businesses/{business_id}/reviews"

        try:
            response = requests.get(url, headers=self.headers, timeout=15)

            # Handle common Yelp API cases cleanly
            if response.status_code == 404:
                logger.warning(f"Yelp reviews not found (404) for business_id={business_id}")
                return []

            if response.status_code == 403:
                logger.warning(f"Yelp reviews forbidden (403) for business_id={business_id}")
                return []

            response.raise_for_status()

            data = response.json()
            return data.get("reviews", []) or []

        except requests.exceptions.HTTPError as e:
            # Any other non-2xx that made it past our explicit checks
            logger.warning(f"Yelp reviews HTTP error for business_id={business_id}: {e}")
            return []

        except requests.exceptions.RequestException as e:
            # Network, timeout, DNS, etc.
            logger.warning(f"Yelp reviews request failed for business_id={business_id}: {e}")
            return []

        except Exception as e:
            logger.warning(f"Unexpected error in get_reviews for business_id={business_id}: {e}")
            return []


    def match_or_create_clinic(self, business_data):
        """
        Match Yelp business to existing clinic or create new one.

        IMPROVED MATCHING LOGIC:
        ------------------------
        Uses ClinicMatcher for intelligent matching:
        1. First check by Yelp business ID (exact match)
        2. Then use fuzzy matching: name similarity, coordinates, phone, address

        EXAMPLE - Old vs New Matching:
        ------------------------------
        Old (basic LIKE query):
            Yelp: "ABC Family Clinic"
            DB:   "ABC Family Medical Clinic"
            Result: NO MATCH (LIKE fails) → Creates duplicate

        New (fuzzy matching):
            Yelp: "ABC Family Clinic"
            DB:   "ABC Family Medical Clinic"
            Normalized: "abc family" vs "abc family"
            Result: MATCH (93% similar) → Merges data

        EXAMPLE - Coordinate Matching:
        ------------------------------
            Yelp: lat=41.8965, lng=-87.6205
            DB clinic: lat=41.8967, lng=-87.6203
            Distance: 28 meters
            Result: MATCH (within 50m threshold) → Merges data
        """
        try:
            business_id = business_data.get('id')
            name = business_data.get('name')
            location = business_data.get('location', {})
            coordinates = business_data.get('coordinates', {})

            # Extract categories
            raw_cats = business_data.get('categories', []) or []
            category_titles = [c.get("title", "") for c in raw_cats if c.get("title")]
            category_aliases = [c.get("alias", "") for c in raw_cats if c.get("alias")]
            categories = category_titles + category_aliases
            mapped_type = self.map_yelp_categories_to_clinic_type(categories)

            # Step 1: Check exact Yelp ID match
            clinic = self.session.query(Clinic).filter_by(
                yelp_business_id=business_id
            ).first()

            if clinic:
                # Update existing Yelp clinic
                clinic.yelp_rating = business_data.get('rating')
                clinic.yelp_review_count = business_data.get('review_count')
                clinic.yelp_price_level = business_data.get('price')
                if mapped_type and (not clinic.clinic_type or clinic.clinic_type == "unknown"):
                    clinic.clinic_type = mapped_type
                clinic.last_updated = datetime.utcnow()
                self.updated_count += 1
                action = "Updated"

            else:
                # Step 2: INTELLIGENT MATCHING using ClinicMatcher
                # Prepare Yelp data for matching
                new_clinic_data = {
                    'name': name,
                    'address': location.get('address1'),
                    'phone': business_data.get('phone'),
                    'latitude': coordinates.get('latitude'),
                    'longitude': coordinates.get('longitude'),
                    'zip_code': location.get('zip_code')
                }

                # Get all potential matches (clinics without Yelp ID in same ZIP)
                zip_code = location.get('zip_code')
                potential_matches = self.session.query(Clinic).filter(
                    Clinic.yelp_business_id.is_(None),
                    Clinic.zip_code == zip_code
                ).all()

                # Also check clinics with different ZIP but close coordinates
                if coordinates.get('latitude') and coordinates.get('longitude'):
                    # Include nearby clinics (within ~0.005 degrees ≈ 500m)
                    lat, lng = coordinates.get('latitude'), coordinates.get('longitude')
                    nearby_clinics = self.session.query(Clinic).filter(
                        Clinic.yelp_business_id.is_(None),
                        Clinic.latitude.between(lat - 0.005, lat + 0.005),
                        Clinic.longitude.between(lng - 0.005, lng + 0.005)
                    ).all()
                    # Combine and deduplicate
                    existing_ids = {c.id for c in potential_matches}
                    for c in nearby_clinics:
                        if c.id not in existing_ids:
                            potential_matches.append(c)

                # Find best match
                matched_clinic, match_result = ClinicMatcher.find_matching_clinic(
                    new_clinic_data, potential_matches, same_zip_only=False
                )

                if matched_clinic:
                    # MERGE: Update existing clinic with Yelp data
                    clinic = matched_clinic
                    clinic.yelp_business_id = business_id
                    clinic.yelp_rating = business_data.get('rating')
                    clinic.yelp_review_count = business_data.get('review_count')
                    clinic.yelp_price_level = business_data.get('price')

                    # Fill gaps with Yelp data
                    if not clinic.latitude:
                        clinic.latitude = coordinates.get('latitude')
                    if not clinic.longitude:
                        clinic.longitude = coordinates.get('longitude')
                    if not clinic.phone:
                        clinic.phone = business_data.get('phone')
                    if not clinic.website:
                        clinic.website = business_data.get('url')
                    if mapped_type and (not clinic.clinic_type or clinic.clinic_type == "unknown"):
                        clinic.clinic_type = mapped_type

                    clinic.last_updated = datetime.utcnow()
                    self.updated_count += 1
                    action = f"MERGED (score={match_result['score']})"
                    logger.info(
                        f"🔗 Merged Yelp '{name}' with existing '{clinic.name}' - "
                        f"{match_result['match_reasons']}"
                    )

                else:
                    # Create new clinic (no match found)
                    clinic = Clinic(
                        yelp_business_id=business_id,
                        name=name,
                        address=location.get('address1'),
                        city=location.get('city'),
                        state=location.get('state'),
                        zip_code=location.get('zip_code'),
                        phone=business_data.get('phone'),
                        website=business_data.get('url'),
                        latitude=coordinates.get('latitude'),
                        longitude=coordinates.get('longitude'),
                        clinic_type=mapped_type,
                        yelp_rating=business_data.get('rating'),
                        yelp_review_count=business_data.get('review_count'),
                        yelp_price_level=business_data.get('price'),
                        categories=categories,
                        is_active=True
                    )

                    self.session.add(clinic)
                    self.collected_count += 1
                    action = "Added"

            self.session.commit()

            logger.info(f"{action} clinic from Yelp: {name} ({location.get('zip_code')})")

            return clinic

        except Exception as e:
            self.session.rollback()
            self.failed_count += 1
            logger.error(f"Failed to save Yelp clinic: {e}")
            return None

    def save_reviews(self, clinic_id, business_id):
        """
        Fetch and save reviews for a business.
        """
        reviews_data = self.get_reviews(business_id)

        for review_data in reviews_data:
            try:
                review_id = f"yelp_{review_data.get('id')}"

                # Check if review exists
                existing = self.session.query(Review).filter_by(
                    review_id=review_id
                ).first()

                if not existing:
                    # Parse date
                    time_created = review_data.get('time_created')
                    review_date = datetime.fromisoformat(time_created.replace('Z', '+00:00'))

                    review = Review(
                        clinic_id=clinic_id,
                        source='yelp',
                        review_id=review_id,
                        author_name=review_data.get('user', {}).get('name'),
                        rating=review_data.get('rating'),
                        text=review_data.get('text'),
                        review_date=review_date
                    )

                    self.session.add(review)

            except Exception as e:
                logger.error(f"Failed to save Yelp review: {e}")

        self.session.commit()

    def collect_by_location(self, location):
        """
        Collect Yelp data for a specific location.
        """
        logger.info(f"Collecting Yelp data for: {location}")

        # Search for businesses
        businesses = self.search_businesses(location)
        logger.info(f"Found {len(businesses)} businesses")

        for business in businesses:
            business_id = business.get('id')

            # Get detailed information
            details = self.get_business_details(business_id)

            if details:
                clinic = self.match_or_create_clinic(details)

                if clinic:
                    # Get and save reviews
                    self.save_reviews(clinic.id, business_id)

            # Rate limiting
            time.sleep(API_RATE_LIMIT_DELAY)

    def collect_all_chicago(self):
        """
        Collect Yelp data for all Chicago ZIP codes.
        """
        log = DataCollectionLog(
            collection_type='yelp',
            start_time=datetime.utcnow(),
            status='running'
        )
        self.session.add(log)
        self.session.commit()

        try:
            logger.info(f"Starting Yelp collection for {len(CHICAGO_ZIP_CODES)} ZIP codes")

            for zip_code in CHICAGO_ZIP_CODES:
                try:
                    location = f"{zip_code}, {TARGET_CITY}, {TARGET_STATE}"
                    self.collect_by_location(location)
                except Exception as e:
                    logger.error(f"Failed to collect {zip_code}: {e}")
                    self.failed_count += 1

            # Update log
            log.end_time = datetime.utcnow()
            log.status = 'success'
            log.records_collected = self.collected_count
            log.records_updated = self.updated_count
            log.records_failed = self.failed_count
            self.session.commit()

            logger.success(
                f"✓ Yelp collection complete: {self.collected_count} new, "
                f"{self.updated_count} updated, {self.failed_count} failed"
            )

        except Exception as e:
            log.end_time = datetime.utcnow()
            log.status = 'failed'
            log.error_message = str(e)
            self.session.commit()
            logger.error(f"Yelp collection failed: {e}")
            raise

    def close(self):
        """Close database session."""
        self.session.close()


if __name__ == "__main__":
    from src.database.initialize_create_database_tables import setup_logging

    setup_logging()

    collector = YelpCollector()
    try:
        collector.collect_all_chicago()
    finally:
        collector.close()
