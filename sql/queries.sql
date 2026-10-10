-- ============================================================================
-- Delivery Delay Analysis - analytical queries
-- SQL engine : MySQL 8.0-compatible (tested on MariaDB 10.11.14)
-- Prerequisite: sql/setup.sql has been run.
-- Run all   : mysql -u <user> -p < sql/queries.sql
-- delay_days = GREATEST(actual_days - promised_days, 0)
-- ============================================================================

USE delivery_delay_analysis;

-- ----------------------------------------------------------------------------
-- S2a - Total delay days by service type (highest first)
-- ----------------------------------------------------------------------------
SELECT r.service_type,
       SUM(GREATEST(d.actual_days - d.promised_days, 0)) AS total_delay_days
FROM deliveries AS d
JOIN routes     AS r ON r.route_id = d.route_id
GROUP BY r.service_type
ORDER BY total_delay_days DESC, r.service_type ASC;

-- ----------------------------------------------------------------------------
-- S2b - Routes with significant delay (total delay days strictly > 8)
-- ----------------------------------------------------------------------------
SELECT r.route_id,
       r.route,
       SUM(GREATEST(d.actual_days - d.promised_days, 0)) AS total_delay_days
FROM deliveries AS d
JOIN routes     AS r ON r.route_id = d.route_id
GROUP BY r.route_id, r.route
HAVING SUM(GREATEST(d.actual_days - d.promised_days, 0)) > 8
ORDER BY total_delay_days DESC, r.route_id ASC;

-- ----------------------------------------------------------------------------
-- S2c - Top two hubs by total delay days (ties broken alphabetically)
-- ----------------------------------------------------------------------------
SELECT d.hub,
       SUM(GREATEST(d.actual_days - d.promised_days, 0)) AS total_delay_days
FROM deliveries AS d
GROUP BY d.hub
ORDER BY total_delay_days DESC, d.hub ASC
LIMIT 2;

-- ----------------------------------------------------------------------------
-- Data integrity diagnostic - delivery rows whose route_id has no match.
-- Expected: 0 unmatched keys.
-- ----------------------------------------------------------------------------
SELECT COUNT(*)                                      AS delivery_rows_checked,
       COALESCE(SUM(r.route_id IS NULL), 0)          AS unmatched_route_keys,
       GROUP_CONCAT(DISTINCT CASE WHEN r.route_id IS NULL THEN d.route_id END) AS unmatched_ids
FROM deliveries AS d
LEFT JOIN routes AS r ON r.route_id = d.route_id;
