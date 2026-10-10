-- ============================================================================
-- Delivery Delay Analysis - schema and data load
-- SQL engine     : MySQL 8.0-compatible syntax (no engine-specific extensions used)
-- Tested on      : MariaDB 10.11.14 (MySQL-compatible). NOT yet tested on Oracle
--                  MySQL 8.0 itself - see docs/sql_guide.md.
-- Database name  : delivery_delay_analysis
-- Execution      : from the repository root, with a user that may create databases:
--                    mysql -u <user> -p < sql/setup.sql
--                  (re-runnable: tables are dropped and recreated)
-- Data           : 4 routes + 12 clean deliveries. The intentional duplicate
--                  (record_id 12 appears twice in data/raw/deliveries.csv) is NOT inserted.
-- ============================================================================

CREATE DATABASE IF NOT EXISTS delivery_delay_analysis;
USE delivery_delay_analysis;

DROP TABLE IF EXISTS deliveries;
DROP TABLE IF EXISTS routes;

CREATE TABLE routes (
    route_id     VARCHAR(10)  NOT NULL,
    route        VARCHAR(50)  NOT NULL,
    service_type VARCHAR(20)  NOT NULL,
    PRIMARY KEY (route_id)
);

CREATE TABLE deliveries (
    record_id     INT          NOT NULL,
    month         VARCHAR(3)   NOT NULL,
    route_id      VARCHAR(10)  NOT NULL,
    hub           VARCHAR(30)  NOT NULL,
    promised_days DECIMAL(6,2) NOT NULL,
    actual_days   DECIMAL(6,2) NOT NULL,
    PRIMARY KEY (record_id),
    CONSTRAINT fk_deliveries_route
        FOREIGN KEY (route_id) REFERENCES routes (route_id)
);

INSERT INTO routes (route_id, route, service_type) VALUES
    ('R1', 'Metro Link',      'Express'),
    ('R2', 'City Dash',       'Express'),
    ('R3', 'Highway Freight', 'Standard'),
    ('R4', 'Rural Feeder',    'Standard');

INSERT INTO deliveries (record_id, month, route_id, hub, promised_days, actual_days) VALUES
    ( 1, 'Jan', 'R1', 'Mumbai',  2,  2),
    ( 2, 'Jan', 'R2', 'Chennai', 3,  4),
    ( 3, 'Jan', 'R3', 'Delhi',   5,  8),
    ( 4, 'Jan', 'R4', 'Mumbai',  6, 10),
    ( 5, 'Feb', 'R1', 'Chennai', 2,  5),
    ( 6, 'Feb', 'R2', 'Delhi',   3,  3),
    ( 7, 'Feb', 'R3', 'Delhi',   5, 10),
    ( 8, 'Feb', 'R4', 'Chennai', 6,  7),
    ( 9, 'Mar', 'R1', 'Delhi',   2,  8),
    (10, 'Mar', 'R2', 'Mumbai',  3,  5),
    (11, 'Mar', 'R3', 'Chennai', 5,  5),
    (12, 'Mar', 'R4', 'Mumbai',  6, 15);

-- Post-load sanity check: expect routes = 4, deliveries = 12
SELECT (SELECT COUNT(*) FROM routes)     AS route_rows,
       (SELECT COUNT(*) FROM deliveries) AS delivery_rows;
