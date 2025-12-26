-- PERF-4: ClickHouse Query Optimization & Indexing Strategy
-- Expected improvements: 50-70% query performance improvement
-- Estimated impact: 2-3 week implementation

-- ============================================================================
-- 1. PRIMARY KEY AND PARTITION OPTIMIZATION
-- ============================================================================

-- Optimize events table for time-series queries
ALTER TABLE risk_events
MODIFY ORDER BY (portfolio_id, event_type, timestamp);

-- Add partition by date for better query pruning
ALTER TABLE risk_events
PARTITION BY toYYYYMMDD(timestamp);

-- Optimize aggregated metrics table
ALTER TABLE risk_metrics
MODIFY ORDER BY (portfolio_id, metric_type, date, hour);


-- ============================================================================
-- 2. SKIP INDEX CREATION
-- ============================================================================

-- Add data_skipping indexes for faster column filtering
ALTER TABLE risk_events
ADD INDEX event_risk_score risk_score TYPE minmax GRANULARITY 4;

ALTER TABLE risk_events
ADD INDEX event_status status TYPE set(10) GRANULARITY 4;

ALTER TABLE risk_events
ADD INDEX event_portfolio portfolio_id TYPE bloom_filter GRANULARITY 4;

-- Indexes for metrics table
ALTER TABLE risk_metrics
ADD INDEX metric_value metric_value TYPE minmax GRANULARITY 2;

ALTER TABLE risk_metrics
ADD INDEX metric_type metric_type TYPE set(20) GRANULARITY 2;


-- ============================================================================
-- 3. PROJECTION-BASED MATERIALIZATION
-- ============================================================================

-- Pre-aggregated view for dashboard performance
ALTER TABLE risk_events
ADD PROJECTION portfolio_daily_stats (
    SELECT 
        portfolio_id,
        toDate(timestamp) as event_date,
        event_type,
        COUNT(*) as count,
        AVG(risk_score) as avg_risk,
        MAX(risk_score) as max_risk,
        MIN(risk_score) as min_risk
    GROUP BY portfolio_id, event_date, event_type
);

-- Enable projection usage
ALTER TABLE risk_events MATERIALIZE PROJECTION portfolio_daily_stats;

-- Hourly metrics projection
ALTER TABLE risk_metrics
ADD PROJECTION hourly_portfolio_metrics (
    SELECT
        portfolio_id,
        toStartOfHour(timestamp) as hour_start,
        metric_type,
        AVG(metric_value) as avg_val,
        MAX(metric_value) as max_val
    GROUP BY portfolio_id, hour_start, metric_type
);

ALTER TABLE risk_metrics MATERIALIZE PROJECTION hourly_portfolio_metrics;


-- ============================================================================
-- 4. COLUMN COMPRESSION OPTIMIZATION
-- ============================================================================

-- Optimize codecs for better compression and performance
ALTER TABLE risk_events MODIFY COLUMN portfolio_id String CODEC(Dictionary);
ALTER TABLE risk_events MODIFY COLUMN event_type String CODEC(Dictionary);
ALTER TABLE risk_events MODIFY COLUMN status String CODEC(Dictionary);
ALTER TABLE risk_events MODIFY COLUMN risk_score Float32 CODEC(Gorilla);
ALTER TABLE risk_events MODIFY COLUMN timestamp DateTime CODEC(DoubleDelta);

-- Optimize metrics columns
ALTER TABLE risk_metrics MODIFY COLUMN portfolio_id String CODEC(Dictionary);
ALTER TABLE risk_metrics MODIFY COLUMN metric_type String CODEC(Dictionary);
ALTER TABLE risk_metrics MODIFY COLUMN metric_value Float32 CODEC(Gorilla);


-- ============================================================================
-- 5. QUERY OPTIMIZATION PATTERNS
-- ============================================================================

-- Pattern 1: Avoid SELECT * - always specify columns
-- BAD:
-- SELECT * FROM risk_events WHERE portfolio_id = 'port_123';
-- GOOD:
SELECT portfolio_id, timestamp, event_type, risk_score 
FROM risk_events 
WHERE portfolio_id = 'port_123' 
AND timestamp >= now() - INTERVAL 24 HOUR
ORDER BY timestamp DESC;

-- Pattern 2: Use final keyword for consistency (if not using ReplicatedMergeTree)
-- SELECT * FROM risk_events FINAL WHERE portfolio_id = 'port_123';

-- Pattern 3: Pre-aggregate in ClickHouse, not application
SELECT 
    portfolio_id,
    toDate(timestamp) as date,
    event_type,
    COUNT(*) as event_count,
    AVG(risk_score) as avg_risk,
    MAX(risk_score) as max_risk
FROM risk_events
WHERE timestamp >= now() - INTERVAL 7 DAY
GROUP BY portfolio_id, date, event_type
ORDER BY date DESC, avg_risk DESC;

-- Pattern 4: Use approximate algorithms for large datasets
SELECT 
    portfolio_id,
    uniqApprox(event_type) as approx_event_types,
    quantilesApprox(0.5, 0.95, 0.99)(risk_score) as risk_percentiles
FROM risk_events
WHERE timestamp >= now() - INTERVAL 30 DAY
GROUP BY portfolio_id;


-- ============================================================================
-- 6. TABLE SETTINGS FOR PERFORMANCE
-- ============================================================================

-- Enable adaptive granularity
ALTER TABLE risk_events MODIFY SETTING index_granularity_bytes = 10485760;

-- Set merge settings for better performance
ALTER TABLE risk_events MODIFY SETTING
    parts_to_throw_insert = 300,
    parts_to_delay_insert = 200,
    max_parts_in_total = 500;

-- TTL for old data cleanup
ALTER TABLE risk_events
MODIFY TTL timestamp + INTERVAL 90 DAY DELETE WHERE 1;


-- ============================================================================
-- 7. REPLICATION AND DISTRIBUTION (OPTIONAL - for multi-node)
-- ============================================================================

-- For cluster deployment:
-- CREATE TABLE risk_events_distributed ON CLUSTER 'mycluster'
AS risk_events
ENGINE = Distributed('mycluster', 'default', 'risk_events_local', rand());


-- ============================================================================
-- 8. MONITORING QUERIES
-- ============================================================================

-- Check table size and compression ratio
SELECT 
    table,
    bytes_on_disk,
    bytes_on_disk / (uncompressed_bytes + 1) as compression_ratio,
    row_count
FROM system.parts
WHERE database = 'default'
ORDER BY bytes_on_disk DESC;

-- Check mutation status (for ALTER operations)
SELECT 
    database,
    table,
    mutation_id,
    command,
    create_time,
    is_done
FROM system.mutations
ORDER BY create_time DESC;

-- Check slowest queries
SELECT 
    query_start_time,
    query_duration_ms,
    query
FROM system.query_log
WHERE query_start_time >= now() - INTERVAL 1 HOUR
ORDER BY query_duration_ms DESC
LIMIT 10;


-- ============================================================================
-- 9. VALIDATION QUERIES (AFTER OPTIMIZATION)
-- ============================================================================

-- Verify indexes are being used
SELECT 
    table,
    name,
    type,
    granularity
FROM system.part_log
WHERE database = 'default'
AND table = 'risk_events';

-- Check projection effectiveness
SELECT 
    table,
    name,
    create_time
FROM system.projections
WHERE database = 'default';

-- Benchmark query performance
-- Run before and after optimization:
SELECT 
    portfolio_id,
    COUNT(*) as events,
    AVG(risk_score) as avg_risk
FROM risk_events
WHERE timestamp >= '2024-01-01' AND timestamp < '2024-02-01'
GROUP BY portfolio_id;

EXPLAIN SELECT * FROM risk_events WHERE risk_score > 0.75;
