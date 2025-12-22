CREATE TABLE events_ck (
    event_date   Date DEFAULT toDate(ts),
    ts           DateTime64(3, 'UTC'),
    entity_id    String,
    cell_id      UInt64,
    amount       Decimal(18, 4),
    event_type   String,
    attrs        String
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(event_date)
ORDER BY (cell_id, ts);

CREATE TABLE forecast_scenarios (
    event_date   Date DEFAULT toDate(generation_ts),
    generation_ts DateTime64(3, 'UTC'),
    zone_id      UInt64,
    horizon_sec  UInt32,
    scenario_id  UInt16,
    risk_value   Float32
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(event_date)
ORDER BY (zone_id, horizon_sec, scenario_id, generation_ts);
