"""
Clinic Matching Utility - Match & Merge clinics from different APIs.

This module provides intelligent matching to identify the same physical clinic
across Google Places and Yelp APIs, ensuring ONE record per clinic.

MATCHING STRATEGY:
1. Fuzzy Name Matching - Handle variations like "ABC Clinic" vs "ABC Medical Clinic"
2. Coordinate Matching - Match clinics within 50 meters of each other
3. Address Normalization - Standardize addresses before comparing
4. Phone Matching - Same phone number = same clinic
"""

import re
import math
from difflib import SequenceMatcher
from loguru import logger


class ClinicMatcher:
    """
    Intelligent clinic matching across multiple data sources.

    EXAMPLES:
    ---------
    Example 1 - Fuzzy Name Match:
        Google: "Northwestern Memorial Hospital"
        Yelp:   "Northwestern Memorial"
        Result: MATCH (similarity = 0.87)

    Example 2 - Coordinate Match:
        Google: lat=41.8965, lng=-87.6205
        Yelp:   lat=41.8966, lng=-87.6204
        Result: MATCH (distance = 15 meters)

    Example 3 - Address Normalization:
        Google: "251 E. Huron Street, Suite 100"
        Yelp:   "251 East Huron St"
        Result: MATCH (normalized addresses match)
    """

    # Matching thresholds
    NAME_SIMILARITY_THRESHOLD = 0.75  # 75% name similarity required
    COORDINATE_DISTANCE_METERS = 50   # Within 50 meters = same location
    ADDRESS_SIMILARITY_THRESHOLD = 0.80  # 80% address similarity

    # Common words to remove for better name matching
    NOISE_WORDS = [
        'clinic', 'medical', 'center', 'healthcare', 'health', 'care',
        'hospital', 'group', 'practice', 'associates', 'physicians',
        'llc', 'inc', 'pc', 'md', 'dds', 'the', 'of', 'at', 'and'
    ]

    # Address abbreviation mappings
    ADDRESS_ABBREVIATIONS = {
        'street': 'st', 'st.': 'st', 'str': 'st',
        'avenue': 'ave', 'ave.': 'ave', 'av': 'ave',
        'boulevard': 'blvd', 'blvd.': 'blvd',
        'drive': 'dr', 'dr.': 'dr',
        'road': 'rd', 'rd.': 'rd',
        'lane': 'ln', 'ln.': 'ln',
        'court': 'ct', 'ct.': 'ct',
        'place': 'pl', 'pl.': 'pl',
        'north': 'n', 'n.': 'n',
        'south': 's', 's.': 's',
        'east': 'e', 'e.': 'e',
        'west': 'w', 'w.': 'w',
        'suite': 'ste', 'ste.': 'ste', 'unit': 'ste',
        'floor': 'fl', 'fl.': 'fl',
        'apartment': 'apt', 'apt.': 'apt',
    }

    @classmethod
    def normalize_name(cls, name):
        """
        Normalize clinic name for comparison.

        EXAMPLE:
            Input:  "Northwestern Memorial Hospital & Medical Center"
            Output: "northwestern memorial"

            Input:  "Dr. Smith's Family Practice, LLC"
            Output: "dr smiths family"
        """
        if not name:
            return ""

        # Lowercase
        normalized = name.lower()

        # Remove punctuation except spaces
        normalized = re.sub(r"[^\w\s]", " ", normalized)

        # Remove noise words
        words = normalized.split()
        words = [w for w in words if w not in cls.NOISE_WORDS]

        # Remove extra spaces
        normalized = " ".join(words).strip()

        return normalized

    @classmethod
    def normalize_address(cls, address):
        """
        Normalize address for comparison.

        EXAMPLE:
            Input:  "251 E. Huron Street, Suite 100, Chicago, IL 60611"
            Output: "251 e huron st ste 100 chicago il 60611"

            Input:  "251 East Huron St"
            Output: "251 e huron st"
        """
        if not address:
            return ""

        # Lowercase
        normalized = address.lower()

        # Remove punctuation
        normalized = re.sub(r"[^\w\s]", " ", normalized)

        # Split into words
        words = normalized.split()

        # Replace abbreviations
        normalized_words = []
        for word in words:
            normalized_words.append(cls.ADDRESS_ABBREVIATIONS.get(word, word))

        # Remove extra spaces
        normalized = " ".join(normalized_words).strip()

        return normalized

    @classmethod
    def normalize_phone(cls, phone):
        """
        Normalize phone number (digits only).

        EXAMPLE:
            Input:  "+1 (312) 926-2000"
            Output: "3129262000"

            Input:  "312.926.2000"
            Output: "3129262000"
        """
        if not phone:
            return ""

        # Extract digits only
        digits = re.sub(r"\D", "", phone)

        # Remove country code if present (assuming US)
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]

        return digits

    @classmethod
    def calculate_name_similarity(cls, name1, name2):
        """
        Calculate similarity between two clinic names.

        EXAMPLE:
            name1: "Northwestern Memorial Hospital"
            name2: "Northwestern Memorial"

            After normalization:
                norm1: "northwestern memorial"
                norm2: "northwestern memorial"

            Similarity: 1.0 (100% match)

        EXAMPLE 2:
            name1: "ABC Family Clinic"
            name2: "ABC Medical Center"

            After normalization:
                norm1: "abc family"
                norm2: "abc"

            Similarity: 0.67 (partial match)
        """
        norm1 = cls.normalize_name(name1)
        norm2 = cls.normalize_name(name2)

        if not norm1 or not norm2:
            return 0.0

        # Use SequenceMatcher for fuzzy comparison
        similarity = SequenceMatcher(None, norm1, norm2).ratio()

        return similarity

    @classmethod
    def calculate_distance_meters(cls, lat1, lng1, lat2, lng2):
        """
        Calculate distance between two coordinates using Haversine formula.

        EXAMPLE:
            Point 1: Northwestern Hospital (41.8965, -87.6205)
            Point 2: Same location from Yelp (41.8966, -87.6204)

            Distance: ~15 meters (MATCH - within 50m threshold)

        EXAMPLE 2:
            Point 1: Clinic A (41.8965, -87.6205)
            Point 2: Clinic B (41.9000, -87.6300)

            Distance: ~850 meters (NO MATCH - different locations)
        """
        if None in [lat1, lng1, lat2, lng2]:
            return float('inf')

        # Earth radius in meters
        R = 6371000

        # Convert to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)

        # Haversine formula
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lng / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c
        return distance

    @classmethod
    def calculate_address_similarity(cls, addr1, addr2):
        """
        Calculate similarity between two addresses.

        EXAMPLE:
            addr1: "251 E. Huron Street, Suite 100"
            addr2: "251 East Huron St"

            After normalization:
                norm1: "251 e huron st ste 100"
                norm2: "251 e huron st"

            Similarity: 0.85 (high match)
        """
        norm1 = cls.normalize_address(addr1)
        norm2 = cls.normalize_address(addr2)

        if not norm1 or not norm2:
            return 0.0

        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        return similarity

    @classmethod
    def is_phone_match(cls, phone1, phone2):
        """
        Check if two phone numbers match.

        EXAMPLE:
            phone1: "+1 (312) 926-2000"
            phone2: "312.926.2000"

            After normalization:
                norm1: "3129262000"
                norm2: "3129262000"

            Result: True (MATCH)
        """
        norm1 = cls.normalize_phone(phone1)
        norm2 = cls.normalize_phone(phone2)

        if not norm1 or not norm2:
            return False

        return norm1 == norm2

    @classmethod
    def calculate_match_score(cls, clinic1, clinic2):
        """
        Calculate overall match score between two clinics.

        Returns a dict with:
        - is_match: Boolean - whether clinics are the same
        - confidence: Float 0-1 - how confident we are
        - match_reasons: List of why we think they match

        SCORING:
        - Phone match: +40 points (strong signal)
        - Coordinate match (<50m): +35 points
        - Name similarity (>75%): +15 points
        - Address similarity (>80%): +10 points

        Total >= 50 points = MATCH

        EXAMPLE:
            Clinic 1 (Google):
                name: "Northwestern Memorial Hospital"
                address: "251 E Huron St"
                phone: "312-926-2000"
                lat: 41.8965, lng: -87.6205

            Clinic 2 (Yelp):
                name: "Northwestern Memorial"
                address: "251 East Huron Street"
                phone: "(312) 926-2000"
                lat: 41.8966, lng: -87.6204

            Scores:
                - Phone match: +40 (same number)
                - Coordinate: +35 (15m apart)
                - Name: +15 (87% similar)
                - Address: +10 (92% similar)
                Total: 100 points

            Result: MATCH with 100% confidence
        """
        score = 0
        reasons = []

        # Extract data from clinic objects or dicts
        def get_value(obj, key, default=''):
            if hasattr(obj, key):
                return getattr(obj, key, default)
            elif isinstance(obj, dict):
                return obj.get(key, default)
            return default

        name1 = get_value(clinic1, 'name', '')
        name2 = get_value(clinic2, 'name', '')

        addr1 = get_value(clinic1, 'address', '')
        addr2 = get_value(clinic2, 'address', '')

        phone1 = get_value(clinic1, 'phone', '')
        phone2 = get_value(clinic2, 'phone', '')

        lat1 = get_value(clinic1, 'latitude', None)
        lng1 = get_value(clinic1, 'longitude', None)
        lat2 = get_value(clinic2, 'latitude', None)
        lng2 = get_value(clinic2, 'longitude', None)

        # 1. Phone matching (strongest signal)
        if cls.is_phone_match(phone1, phone2):
            score += 40
            reasons.append(f"Phone match: {phone1}")

        # 2. Coordinate matching
        distance = cls.calculate_distance_meters(lat1, lng1, lat2, lng2)
        if distance <= cls.COORDINATE_DISTANCE_METERS:
            score += 35
            reasons.append(f"Location match: {distance:.0f}m apart")

        # 3. Name similarity
        name_sim = cls.calculate_name_similarity(name1, name2)
        if name_sim >= cls.NAME_SIMILARITY_THRESHOLD:
            score += 15
            reasons.append(f"Name match: {name_sim:.0%} similar")

        # 4. Address similarity
        addr_sim = cls.calculate_address_similarity(addr1, addr2)
        if addr_sim >= cls.ADDRESS_SIMILARITY_THRESHOLD:
            score += 10
            reasons.append(f"Address match: {addr_sim:.0%} similar")

        # Determine if match
        is_match = score >= 50
        confidence = min(score / 100, 1.0)

        return {
            'is_match': is_match,
            'confidence': confidence,
            'score': score,
            'match_reasons': reasons,
            'details': {
                'name_similarity': name_sim,
                'address_similarity': addr_sim,
                'distance_meters': distance,
                'phone_match': cls.is_phone_match(phone1, phone2)
            }
        }

    @classmethod
    def find_matching_clinic(cls, new_clinic_data, existing_clinics, same_zip_only=True):
        """
        Find the best matching existing clinic for new data.

        Args:
            new_clinic_data: Dict with new clinic info from API
            existing_clinics: List of Clinic ORM objects
            same_zip_only: If True, only compare within same ZIP code (faster)

        Returns:
            (matched_clinic, match_result) or (None, None) if no match

        EXAMPLE:
            New data from Yelp:
                {"name": "Rush Medical Center", "zip_code": "60612", ...}

            Existing clinics in DB:
                [Clinic(name="Rush University Medical Center", zip="60612"), ...]

            Process:
                1. Filter to same ZIP code (60612)
                2. Calculate match scores for each
                3. Return best match if score >= 50
        """
        new_zip = new_clinic_data.get('zip_code') or new_clinic_data.get('location', {}).get('zip_code')

        best_match = None
        best_result = None
        best_score = 0

        for clinic in existing_clinics:
            # Filter by ZIP code if enabled
            if same_zip_only and new_zip and clinic.zip_code != new_zip:
                continue

            # Calculate match score
            result = cls.calculate_match_score(new_clinic_data, clinic)

            if result['is_match'] and result['score'] > best_score:
                best_match = clinic
                best_result = result
                best_score = result['score']

        if best_match:
            logger.info(
                f"✓ MATCH FOUND: '{new_clinic_data.get('name')}' → '{best_match.name}' "
                f"(score={best_score}, reasons={best_result['match_reasons']})"
            )

        return best_match, best_result


def merge_clinic_data(existing_clinic, new_data, source='yelp'):
    """
    Merge new API data into existing clinic record.

    Strategy: Keep existing data, fill gaps with new data.

    EXAMPLE:
        Existing (from Google):
            name: "Northwestern Memorial Hospital"
            google_rating: 4.5
            google_review_count: 1200
            yelp_rating: None
            phone: "312-926-2000"

        New (from Yelp):
            name: "Northwestern Memorial"
            yelp_rating: 4.0
            yelp_review_count: 890
            phone: "(312) 926-2000"

        Merged Result:
            name: "Northwestern Memorial Hospital"  (kept original)
            google_rating: 4.5                      (kept)
            google_review_count: 1200               (kept)
            yelp_rating: 4.0                        (added from Yelp)
            yelp_review_count: 890                  (added from Yelp)
            phone: "312-926-2000"                   (kept original)
    """
    if source == 'yelp':
        # Update Yelp-specific fields
        existing_clinic.yelp_business_id = new_data.get('id')
        existing_clinic.yelp_rating = new_data.get('rating')
        existing_clinic.yelp_review_count = new_data.get('review_count')
        existing_clinic.yelp_price_level = new_data.get('price')

        # Fill gaps with Yelp data
        if not existing_clinic.phone:
            existing_clinic.phone = new_data.get('phone')
        if not existing_clinic.website:
            existing_clinic.website = new_data.get('url')
        if not existing_clinic.latitude:
            coords = new_data.get('coordinates', {})
            existing_clinic.latitude = coords.get('latitude')
            existing_clinic.longitude = coords.get('longitude')

    elif source == 'google':
        # Update Google-specific fields
        existing_clinic.google_place_id = new_data.get('place_id')
        existing_clinic.google_rating = new_data.get('rating')
        existing_clinic.google_review_count = new_data.get('user_ratings_total')
        existing_clinic.google_price_level = new_data.get('price_level')

        # Fill gaps with Google data
        if not existing_clinic.phone:
            existing_clinic.phone = new_data.get('formatted_phone_number')
        if not existing_clinic.website:
            existing_clinic.website = new_data.get('website')
        if not existing_clinic.latitude:
            location = new_data.get('geometry', {}).get('location', {})
            existing_clinic.latitude = location.get('lat')
            existing_clinic.longitude = location.get('lng')

    return existing_clinic


# Example usage and testing
if __name__ == "__main__":
    print("=" * 70)
    print("CLINIC MATCHER - EXAMPLES")
    print("=" * 70)

    matcher = ClinicMatcher()

    # Example 1: Name Normalization
    print("\n1. NAME NORMALIZATION")
    print("-" * 40)
    names = [
        "Northwestern Memorial Hospital & Medical Center",
        "Dr. Smith's Family Practice, LLC",
        "ABC Urgent Care Clinic"
    ]
    for name in names:
        print(f"  Input:  '{name}'")
        print(f"  Output: '{matcher.normalize_name(name)}'")
        print()

    # Example 2: Address Normalization
    print("\n2. ADDRESS NORMALIZATION")
    print("-" * 40)
    addresses = [
        "251 E. Huron Street, Suite 100, Chicago, IL",
        "251 East Huron St",
        "500 North Michigan Avenue, Floor 3"
    ]
    for addr in addresses:
        print(f"  Input:  '{addr}'")
        print(f"  Output: '{matcher.normalize_address(addr)}'")
        print()

    # Example 3: Match Score Calculation
    print("\n3. MATCH SCORE CALCULATION")
    print("-" * 40)

    clinic1 = {
        'name': 'Northwestern Memorial Hospital',
        'address': '251 E Huron St',
        'phone': '312-926-2000',
        'latitude': 41.8965,
        'longitude': -87.6205
    }

    clinic2 = {
        'name': 'Northwestern Memorial',
        'address': '251 East Huron Street',
        'phone': '(312) 926-2000',
        'latitude': 41.8966,
        'longitude': -87.6204
    }

    print(f"  Clinic 1: {clinic1['name']}")
    print(f"  Clinic 2: {clinic2['name']}")
    print()

    result = matcher.calculate_match_score(clinic1, clinic2)
    print(f"  Is Match: {result['is_match']}")
    print(f"  Confidence: {result['confidence']:.0%}")
    print(f"  Score: {result['score']}/100")
    print(f"  Reasons: {result['match_reasons']}")
    print()

    # Example 4: Non-matching clinics
    print("\n4. NON-MATCHING CLINICS")
    print("-" * 40)

    clinic3 = {
        'name': 'Rush University Medical Center',
        'address': '1653 W Congress Pkwy',
        'phone': '312-942-5000',
        'latitude': 41.8747,
        'longitude': -87.6690
    }

    print(f"  Clinic 1: {clinic1['name']}")
    print(f"  Clinic 3: {clinic3['name']}")
    print()

    result2 = matcher.calculate_match_score(clinic1, clinic3)
    print(f"  Is Match: {result2['is_match']}")
    print(f"  Confidence: {result2['confidence']:.0%}")
    print(f"  Score: {result2['score']}/100")
    print(f"  Reasons: {result2['match_reasons'] or 'No matching criteria met'}")

    print("\n" + "=" * 70)
