-- =====================================================
-- Chicago Clinic Intelligence - Data Quality Checks
-- =====================================================
-- Run these queries against your Neon PostgreSQL database
-- to audit completeness, consistency, and accuracy.
-- =====================================================


-- #####################################################
-- SECTION 1: DATABASE OVERVIEW & TABLE HEALTH
-- #####################################################

-- 1.1 Record counts per table
SELECT 'clinics' AS table_name, COUNT(*) AS total_rows FROM clinics
UNION ALL
SELECT 'reviews', COUNT(*) FROM reviews
UNION ALL
SELECT 'search_trends', COUNT(*) FROM search_trends
UNION ALL
SELECT 'visibility_scores', COUNT(*) FROM visibility_scores
UNION ALL
SELECT 'demand_metrics', COUNT(*) FROM demand_metrics
UNION ALL
SELECT 'competitor_analysis', COUNT(*) FROM competitor_analysis
UNION ALL
SELECT 'data_collection_logs', COUNT(*) FROM data_collection_logs
ORDER BY table_name;


-- 1.2 Active vs inactive clinics
SELECT
    COUNT(*) AS total_clinics,
    COUNT(*) FILTER (WHERE is_active = TRUE) AS active,
    COUNT(*) FILTER (WHERE is_active = FALSE) AS inactive,
    ROUND(COUNT(*) FILTER (WHERE is_active = TRUE) * 100.0 / NULLIF(COUNT(*), 0), 1) AS active_pct
FROM clinics;


-- 1.3 Data freshness — most recent record per table
SELECT 'clinics' AS table_name, MAX(last_updated) AS latest_record FROM clinics
UNION ALL
SELECT 'reviews', MAX(created_at) FROM reviews
UNION ALL
SELECT 'search_trends', MAX(date::timestamp) FROM search_trends
UNION ALL
SELECT 'visibility_scores', MAX(calculation_date::timestamp) FROM visibility_scores
UNION ALL
SELECT 'demand_metrics', MAX(calculation_date::timestamp) FROM demand_metrics
UNION ALL
SELECT 'competitor_analysis', MAX(calculation_date::timestamp) FROM competitor_analysis
UNION ALL
SELECT 'data_collection_logs', MAX(start_time) FROM data_collection_logs
ORDER BY table_name;


-- #####################################################
-- SECTION 2: CLINICS TABLE — NULL / MISSING VALUES
-- #####################################################

-- 2.1 Column-level completeness for clinics
SELECT
    COUNT(*) AS total,
    -- Identifiers
    COUNT(google_place_id)   AS has_google_id,
    COUNT(yelp_business_id)  AS has_yelp_id,
    -- Core fields
    COUNT(name)              AS has_name,
    COUNT(address)           AS has_address,
    COUNT(city)              AS has_city,
    COUNT(state)             AS has_state,
    COUNT(zip_code)          AS has_zip,
    COUNT(phone)             AS has_phone,
    COUNT(website)           AS has_website,
    -- Location
    COUNT(latitude)          AS has_lat,
    COUNT(longitude)         AS has_lon,
    -- Categorization
    COUNT(clinic_type)       AS has_clinic_type,
    -- Ratings
    COUNT(google_rating)     AS has_google_rating,
    COUNT(yelp_rating)       AS has_yelp_rating,
    COUNT(combined_rating)   AS has_combined_rating,
    -- Calculated
    COUNT(data_source)       AS has_data_source,
    COUNT(rating_category)   AS has_rating_category,
    COUNT(data_quality_score) AS has_quality_score
FROM clinics;


-- 2.2 Missing value percentages per column (active clinics only)
SELECT
    'name'              AS column_name, ROUND(100.0 * COUNT(*) FILTER (WHERE name IS NULL OR TRIM(name) = '') / COUNT(*), 1) AS pct_missing FROM clinics WHERE is_active = TRUE
UNION ALL SELECT 'address',           ROUND(100.0 * COUNT(*) FILTER (WHERE address IS NULL OR TRIM(address) = '') / COUNT(*), 1) FROM clinics WHERE is_active = TRUE
UNION ALL SELECT 'city',              ROUND(100.0 * COUNT(*) FILTER (WHERE city IS NULL OR TRIM(city) = '') / COUNT(*), 1) FROM clinics WHERE is_active = TRUE
UNION ALL SELECT 'state',             ROUND(100.0 * COUNT(*) FILTER (WHERE state IS NULL OR TRIM(state) = '') / COUNT(*), 1) FROM clinics WHERE is_active = TRUE
UNION ALL SELECT 'zip_code',          ROUND(100.0 * COUNT(*) FILTER (WHERE zip_code IS NULL OR TRIM(zip_code) = '') / COUNT(*), 1) FROM clinics WHERE is_active = TRUE
UNION ALL SELECT 'phone',             ROUND(100.0 * COUNT(*) FILTER (WHERE phone IS NULL OR TRIM(phone) = '') / COUNT(*), 1) FROM clinics WHERE is_active = TRUE
UNION ALL SELECT 'website',           ROUND(100.0 * COUNT(*) FILTER (WHERE website IS NULL OR TRIM(website) = '') / COUNT(*), 1) FROM clinics WHERE is_active = TRUE
UNION ALL SELECT 'latitude',          ROUND(100.0 * COUNT(*) FILTER (WHERE latitude IS NULL) / COUNT(*), 1) FROM clinics WHERE is_active = TRUE
UNION ALL SELECT 'longitude',         ROUND(100.0 * COUNT(*) FILTER (WHERE longitude IS NULL) / COUNT(*), 1) FROM clinics WHERE is_active = TRUE
UNION ALL SELECT 'clinic_type',       ROUND(100.0 * COUNT(*) FILTER (WHERE clinic_type IS NULL OR TRIM(clinic_type) = '' OR LOWER(TRIM(clinic_type)) IN ('unknown','none','null')) / COUNT(*), 1) FROM clinics WHERE is_active = TRUE
UNION ALL SELECT 'google_rating',     ROUND(100.0 * COUNT(*) FILTER (WHERE google_rating IS NULL) / COUNT(*), 1) FROM clinics WHERE is_active = TRUE
UNION ALL SELECT 'yelp_rating',       ROUND(100.0 * COUNT(*) FILTER (WHERE yelp_rating IS NULL) / COUNT(*), 1) FROM clinics WHERE is_active = TRUE
UNION ALL SELECT 'combined_rating',   ROUND(100.0 * COUNT(*) FILTER (WHERE combined_rating IS NULL) / COUNT(*), 1) FROM clinics WHERE is_active = TRUE
UNION ALL SELECT 'rating_category',   ROUND(100.0 * COUNT(*) FILTER (WHERE rating_category IS NULL OR TRIM(rating_category) = '') / COUNT(*), 1) FROM clinics WHERE is_active = TRUE
UNION ALL SELECT 'data_quality_score',ROUND(100.0 * COUNT(*) FILTER (WHERE data_quality_score IS NULL) / COUNT(*), 1) FROM clinics WHERE is_active = TRUE
ORDER BY pct_missing DESC;


-- 2.3 Clinics with the MOST missing fields (worst data quality)
SELECT
    id,
    name,
    zip_code,
    data_source,
    data_quality_score,
    (CASE WHEN address IS NULL THEN 1 ELSE 0 END
     + CASE WHEN zip_code IS NULL OR TRIM(zip_code) = '' THEN 1 ELSE 0 END
     + CASE WHEN phone IS NULL OR TRIM(phone) = '' THEN 1 ELSE 0 END
     + CASE WHEN website IS NULL OR TRIM(website) = '' THEN 1 ELSE 0 END
     + CASE WHEN latitude IS NULL THEN 1 ELSE 0 END
     + CASE WHEN longitude IS NULL THEN 1 ELSE 0 END
     + CASE WHEN clinic_type IS NULL OR LOWER(TRIM(clinic_type)) IN ('unknown','none','null','') THEN 1 ELSE 0 END
     + CASE WHEN google_rating IS NULL THEN 1 ELSE 0 END
     + CASE WHEN yelp_rating IS NULL THEN 1 ELSE 0 END
     + CASE WHEN combined_rating IS NULL THEN 1 ELSE 0 END
    ) AS missing_field_count
FROM clinics
WHERE is_active = TRUE
ORDER BY missing_field_count DESC, data_quality_score ASC
LIMIT 20;


-- #####################################################
-- SECTION 3: DATA VALIDITY & RANGE CHECKS
-- #####################################################

-- 3.1 Ratings outside valid range (should be 1.0–5.0)
SELECT
    id, name,
    google_rating, yelp_rating, combined_rating,
    CASE
        WHEN google_rating < 1.0 OR google_rating > 5.0 THEN 'google_rating out of range'
        WHEN yelp_rating  < 1.0 OR yelp_rating  > 5.0 THEN 'yelp_rating out of range'
        WHEN combined_rating < 1.0 OR combined_rating > 5.0 THEN 'combined_rating out of range'
    END AS issue
FROM clinics
WHERE (google_rating IS NOT NULL AND (google_rating < 1.0 OR google_rating > 5.0))
   OR (yelp_rating   IS NOT NULL AND (yelp_rating   < 1.0 OR yelp_rating   > 5.0))
   OR (combined_rating IS NOT NULL AND (combined_rating < 1.0 OR combined_rating > 5.0));


-- 3.2 Review counts that are negative
SELECT id, name, google_review_count, yelp_review_count
FROM clinics
WHERE google_review_count < 0 OR yelp_review_count < 0;


-- 3.3 Coordinates outside Chicago metro bounding box
--     Approximate: lat 41.6–42.1, lon -88.0 to -87.4
SELECT id, name, latitude, longitude
FROM clinics
WHERE latitude IS NOT NULL
  AND longitude IS NOT NULL
  AND (latitude  < 41.6 OR latitude  > 42.1
       OR longitude < -88.0 OR longitude > -87.4);


-- 3.4 ZIP codes not matching Chicago-area patterns (should be 606xx)
SELECT id, name, zip_code
FROM clinics
WHERE zip_code IS NOT NULL
  AND zip_code !~ '^606[0-9]{2}$';


-- 3.5 Invalid rating_category values
SELECT rating_category, COUNT(*) AS cnt
FROM clinics
WHERE rating_category IS NOT NULL
GROUP BY rating_category
ORDER BY cnt DESC;
-- Expected: 'Excellent (4.0+)', 'Good (3.5-4.0)', 'Medium (2.5-3.5)', 'Low (0-2.5)'


-- 3.6 rating_category does NOT match actual combined_rating
SELECT
    id, name, combined_rating, rating_category,
    CASE
        WHEN combined_rating >= 4.0 THEN 'Excellent (4.0+)'
        WHEN combined_rating >= 3.5 THEN 'Good (3.5-4.0)'
        WHEN combined_rating >= 2.5 THEN 'Medium (2.5-3.5)'
        ELSE 'Low (0-2.5)'
    END AS expected_category
FROM clinics
WHERE combined_rating IS NOT NULL
  AND rating_category IS NOT NULL
  AND rating_category != (
      CASE
          WHEN combined_rating >= 4.0 THEN 'Excellent (4.0+)'
          WHEN combined_rating >= 3.5 THEN 'Good (3.5-4.0)'
          WHEN combined_rating >= 2.5 THEN 'Medium (2.5-3.5)'
          ELSE 'Low (0-2.5)'
      END
  );


-- 3.7 data_source flag consistency
-- Clinics marked "Both" should have both google_place_id AND yelp_business_id
SELECT id, name, data_source, google_place_id, yelp_business_id
FROM clinics
WHERE (data_source = 'Both' AND (google_place_id IS NULL OR yelp_business_id IS NULL))
   OR (data_source = 'Google Only' AND google_place_id IS NULL)
   OR (data_source = 'Yelp Only' AND yelp_business_id IS NULL);


-- 3.8 combined_rating does not match average of google + yelp
SELECT
    id, name,
    google_rating, yelp_rating, combined_rating,
    ROUND(
        CASE
            WHEN google_rating IS NOT NULL AND yelp_rating IS NOT NULL
                THEN (google_rating + yelp_rating) / 2.0
            WHEN google_rating IS NOT NULL THEN google_rating
            WHEN yelp_rating IS NOT NULL THEN yelp_rating
        END::numeric, 2
    ) AS expected_combined,
    ABS(combined_rating - CASE
            WHEN google_rating IS NOT NULL AND yelp_rating IS NOT NULL
                THEN (google_rating + yelp_rating) / 2.0
            WHEN google_rating IS NOT NULL THEN google_rating
            WHEN yelp_rating IS NOT NULL THEN yelp_rating
        END) AS diff
FROM clinics
WHERE combined_rating IS NOT NULL
  AND (google_rating IS NOT NULL OR yelp_rating IS NOT NULL)
  AND ABS(combined_rating - CASE
            WHEN google_rating IS NOT NULL AND yelp_rating IS NOT NULL
                THEN (google_rating + yelp_rating) / 2.0
            WHEN google_rating IS NOT NULL THEN google_rating
            WHEN yelp_rating IS NOT NULL THEN yelp_rating
        END) > 0.05  -- tolerance for rounding
ORDER BY diff DESC;


-- 3.9 Review ratings outside valid range
SELECT id, clinic_id, source, rating
FROM reviews
WHERE rating < 1.0 OR rating > 5.0;


-- 3.10 Search trend interest_score outside 0–100
SELECT id, keyword, date, interest_score
FROM search_trends
WHERE interest_score < 0 OR interest_score > 100;


-- 3.11 Visibility component scores outside 0–100
SELECT id, clinic_id, calculation_date,
       rating_score, review_volume_score, recency_score, geographic_score,
       overall_visibility_score
FROM visibility_scores
WHERE rating_score < 0 OR rating_score > 100
   OR review_volume_score < 0 OR review_volume_score > 100
   OR recency_score < 0 OR recency_score > 100
   OR geographic_score < 0 OR geographic_score > 100
   OR overall_visibility_score < 0 OR overall_visibility_score > 100;


-- #####################################################
-- SECTION 4: DUPLICATE DETECTION
-- #####################################################

-- 4.1 Duplicate clinic names (active only)
SELECT name, COUNT(*) AS cnt
FROM clinics
WHERE is_active = TRUE
GROUP BY name
HAVING COUNT(*) > 1
ORDER BY cnt DESC;


-- 4.2 Duplicate google_place_id (should be unique)
SELECT google_place_id, COUNT(*) AS cnt
FROM clinics
WHERE google_place_id IS NOT NULL
GROUP BY google_place_id
HAVING COUNT(*) > 1;


-- 4.3 Duplicate yelp_business_id (should be unique)
SELECT yelp_business_id, COUNT(*) AS cnt
FROM clinics
WHERE yelp_business_id IS NOT NULL
GROUP BY yelp_business_id
HAVING COUNT(*) > 1;


-- 4.4 Duplicate reviews (same review_id)
SELECT review_id, COUNT(*) AS cnt
FROM reviews
WHERE review_id IS NOT NULL
GROUP BY review_id
HAVING COUNT(*) > 1;


-- 4.5 Clinics at the exact same coordinates (potential duplicates)
SELECT
    a.id AS clinic_a_id, a.name AS clinic_a_name,
    b.id AS clinic_b_id, b.name AS clinic_b_name,
    a.latitude, a.longitude
FROM clinics a
JOIN clinics b
    ON a.latitude = b.latitude
    AND a.longitude = b.longitude
    AND a.id < b.id
WHERE a.is_active = TRUE AND b.is_active = TRUE;


-- #####################################################
-- SECTION 5: REFERENTIAL INTEGRITY
-- #####################################################

-- 5.1 Reviews referencing non-existent clinics
SELECT r.id AS review_id, r.clinic_id
FROM reviews r
LEFT JOIN clinics c ON r.clinic_id = c.id
WHERE c.id IS NULL;


-- 5.2 Visibility scores referencing non-existent clinics
SELECT vs.id, vs.clinic_id
FROM visibility_scores vs
LEFT JOIN clinics c ON vs.clinic_id = c.id
WHERE c.id IS NULL;


-- 5.3 Reviews linked to inactive (merged/deactivated) clinics
SELECT
    r.id AS review_id,
    r.clinic_id,
    c.name AS clinic_name,
    c.is_active
FROM reviews r
JOIN clinics c ON r.clinic_id = c.id
WHERE c.is_active = FALSE;


-- #####################################################
-- SECTION 6: DISTRIBUTION & STATISTICAL CHECKS
-- #####################################################

-- 6.1 Rating distribution (Google)
SELECT
    ROUND(google_rating, 0) AS rating_bucket,
    COUNT(*) AS clinic_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM clinics
WHERE google_rating IS NOT NULL AND is_active = TRUE
GROUP BY ROUND(google_rating, 0)
ORDER BY rating_bucket;


-- 6.2 Rating distribution (Yelp)
SELECT
    ROUND(yelp_rating, 0) AS rating_bucket,
    COUNT(*) AS clinic_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM clinics
WHERE yelp_rating IS NOT NULL AND is_active = TRUE
GROUP BY ROUND(yelp_rating, 0)
ORDER BY rating_bucket;


-- 6.3 Clinics per ZIP code
SELECT
    zip_code,
    COUNT(*) AS clinic_count,
    ROUND(AVG(combined_rating), 2) AS avg_combined_rating,
    SUM(COALESCE(google_review_count, 0) + COALESCE(yelp_review_count, 0)) AS total_reviews
FROM clinics
WHERE is_active = TRUE AND zip_code IS NOT NULL
GROUP BY zip_code
ORDER BY clinic_count DESC;


-- 6.4 Clinic type distribution
SELECT
    clinic_type,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct,
    ROUND(AVG(combined_rating), 2) AS avg_rating
FROM clinics
WHERE is_active = TRUE
GROUP BY clinic_type
ORDER BY cnt DESC;


-- 6.5 Data source distribution
SELECT
    data_source,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM clinics
WHERE is_active = TRUE
GROUP BY data_source
ORDER BY cnt DESC;


-- 6.6 Rating statistics summary
SELECT
    COUNT(*) AS total_active,
    ROUND(AVG(google_rating), 2)   AS avg_google,
    ROUND(MIN(google_rating), 2)   AS min_google,
    ROUND(MAX(google_rating), 2)   AS max_google,
    ROUND(STDDEV(google_rating), 2) AS stddev_google,
    ROUND(AVG(yelp_rating), 2)     AS avg_yelp,
    ROUND(MIN(yelp_rating), 2)     AS min_yelp,
    ROUND(MAX(yelp_rating), 2)     AS max_yelp,
    ROUND(STDDEV(yelp_rating), 2)  AS stddev_yelp,
    ROUND(AVG(combined_rating), 2) AS avg_combined,
    ROUND(MIN(combined_rating), 2) AS min_combined,
    ROUND(MAX(combined_rating), 2) AS max_combined
FROM clinics
WHERE is_active = TRUE;


-- 6.7 Review count per source
SELECT
    source,
    COUNT(*) AS review_count,
    ROUND(AVG(rating), 2) AS avg_rating,
    MIN(review_date) AS earliest_review,
    MAX(review_date) AS latest_review
FROM reviews
GROUP BY source;


-- #####################################################
-- SECTION 7: DATA QUALITY SCORE ANALYSIS
-- #####################################################

-- 7.1 Data quality score distribution
SELECT
    CASE
        WHEN data_quality_score >= 90 THEN 'Excellent (90-100)'
        WHEN data_quality_score >= 70 THEN 'Good (70-89)'
        WHEN data_quality_score >= 50 THEN 'Fair (50-69)'
        WHEN data_quality_score >= 30 THEN 'Poor (30-49)'
        ELSE 'Critical (0-29)'
    END AS quality_tier,
    COUNT(*) AS clinic_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM clinics
WHERE is_active = TRUE AND data_quality_score IS NOT NULL
GROUP BY quality_tier
ORDER BY MIN(data_quality_score) DESC;


-- 7.2 Average data quality score by data source
SELECT
    data_source,
    COUNT(*) AS cnt,
    ROUND(AVG(data_quality_score), 1) AS avg_quality_score,
    MIN(data_quality_score) AS min_score,
    MAX(data_quality_score) AS max_score
FROM clinics
WHERE is_active = TRUE
GROUP BY data_source
ORDER BY avg_quality_score DESC;


-- 7.3 Average data quality score by ZIP code
SELECT
    zip_code,
    COUNT(*) AS cnt,
    ROUND(AVG(data_quality_score), 1) AS avg_quality_score
FROM clinics
WHERE is_active = TRUE AND zip_code IS NOT NULL
GROUP BY zip_code
ORDER BY avg_quality_score ASC;


-- #####################################################
-- SECTION 8: CROSS-TABLE CONSISTENCY
-- #####################################################

-- 8.1 Active clinics with zero reviews in reviews table
SELECT c.id, c.name, c.google_review_count, c.yelp_review_count,
       COUNT(r.id) AS actual_review_rows
FROM clinics c
LEFT JOIN reviews r ON c.id = r.clinic_id
WHERE c.is_active = TRUE
GROUP BY c.id, c.name, c.google_review_count, c.yelp_review_count
HAVING COUNT(r.id) = 0
   AND (COALESCE(c.google_review_count, 0) + COALESCE(c.yelp_review_count, 0)) > 0
ORDER BY (COALESCE(c.google_review_count, 0) + COALESCE(c.yelp_review_count, 0)) DESC;


-- 8.2 Active clinics with no visibility scores
SELECT c.id, c.name, c.zip_code
FROM clinics c
LEFT JOIN visibility_scores vs ON c.id = vs.clinic_id
WHERE c.is_active = TRUE
GROUP BY c.id, c.name, c.zip_code
HAVING COUNT(vs.id) = 0;


-- 8.3 Demand metrics for ZIP codes not in clinics table
SELECT DISTINCT dm.zip_code
FROM demand_metrics dm
LEFT JOIN clinics c ON dm.zip_code = c.zip_code AND c.is_active = TRUE
WHERE c.id IS NULL;


-- 8.4 Competitor analysis ZIP codes not in clinics table
SELECT DISTINCT ca.zip_code
FROM competitor_analysis ca
LEFT JOIN clinics c ON ca.zip_code = c.zip_code AND c.is_active = TRUE
WHERE c.id IS NULL;


-- #####################################################
-- SECTION 9: COLLECTION LOG HEALTH
-- #####################################################

-- 9.1 Collection success/failure rates
SELECT
    collection_type,
    COUNT(*) AS total_runs,
    COUNT(*) FILTER (WHERE status = 'success') AS successes,
    COUNT(*) FILTER (WHERE status = 'failed')  AS failures,
    COUNT(*) FILTER (WHERE status = 'partial') AS partial,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*), 0), 1) AS success_rate_pct
FROM data_collection_logs
GROUP BY collection_type
ORDER BY collection_type;


-- 9.2 Recent collection errors
SELECT
    collection_type,
    start_time,
    status,
    records_collected,
    records_failed,
    error_message
FROM data_collection_logs
WHERE status != 'success'
ORDER BY start_time DESC
LIMIT 10;


-- 9.3 Collections with zero records
SELECT id, collection_type, start_time, status, records_collected
FROM data_collection_logs
WHERE records_collected = 0 OR records_collected IS NULL
ORDER BY start_time DESC;


-- #####################################################
-- SECTION 10: OVERALL DATA QUALITY SCORECARD
-- #####################################################

-- Single-query scorecard summarizing all quality dimensions
SELECT
    -- Completeness
    ROUND(100.0 * COUNT(zip_code) FILTER (WHERE TRIM(zip_code) != '') / COUNT(*), 1)
        AS pct_has_zip,
    ROUND(100.0 * COUNT(clinic_type) FILTER (WHERE LOWER(TRIM(clinic_type)) NOT IN ('unknown','none','null','') AND clinic_type IS NOT NULL) / COUNT(*), 1)
        AS pct_has_clinic_type,
    ROUND(100.0 * COUNT(google_rating) / COUNT(*), 1)
        AS pct_has_google_rating,
    ROUND(100.0 * COUNT(yelp_rating) / COUNT(*), 1)
        AS pct_has_yelp_rating,
    ROUND(100.0 * COUNT(combined_rating) / COUNT(*), 1)
        AS pct_has_combined_rating,
    ROUND(100.0 * COUNT(latitude) / COUNT(*), 1)
        AS pct_has_coordinates,
    ROUND(100.0 * COUNT(phone) FILTER (WHERE TRIM(phone) != '') / COUNT(*), 1)
        AS pct_has_phone,
    ROUND(100.0 * COUNT(website) FILTER (WHERE TRIM(website) != '') / COUNT(*), 1)
        AS pct_has_website,
    -- Average quality score
    ROUND(AVG(data_quality_score), 1) AS avg_data_quality_score,
    -- Overall completeness (average of all field completeness rates)
    ROUND((
        100.0 * COUNT(zip_code) FILTER (WHERE TRIM(zip_code) != '') / COUNT(*)
      + 100.0 * COUNT(clinic_type) FILTER (WHERE LOWER(TRIM(clinic_type)) NOT IN ('unknown','none','null','') AND clinic_type IS NOT NULL) / COUNT(*)
      + 100.0 * COUNT(google_rating) / COUNT(*)
      + 100.0 * COUNT(yelp_rating) / COUNT(*)
      + 100.0 * COUNT(combined_rating) / COUNT(*)
      + 100.0 * COUNT(latitude) / COUNT(*)
      + 100.0 * COUNT(phone) FILTER (WHERE TRIM(phone) != '') / COUNT(*)
      + 100.0 * COUNT(website) FILTER (WHERE TRIM(website) != '') / COUNT(*)
    ) / 8.0, 1) AS overall_completeness_pct
FROM clinics
WHERE is_active = TRUE;
