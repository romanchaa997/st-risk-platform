-- Розширення
CREATE EXTENSION IF NOT EXISTS postgis;

-- Сирі події (якщо треба зберігати до нормалізації)
CREATE TABLE events_raw (
    event_id      BIGSERIAL PRIMARY KEY,
    entity_id     VARCHAR(64) NOT NULL,
    ts            TIMESTAMPTZ NOT NULL,
    lat           DOUBLE PRECISION,
    lon           DOUBLE PRECISION,
    amount        NUMERIC(18, 4),
    attrs         JSONB,
    ingested_at   TIMESTAMPTZ DEFAULT now()
);

-- Зони / клітини
CREATE TABLE grid_cells (
    cell_id   BIGSERIAL PRIMARY KEY,
    geom      GEOMETRY(POLYGON, 4326) NOT NULL,
    meta      JSONB
);

CREATE INDEX idx_grid_cells_geom
    ON grid_cells
    USING GIST (geom);

-- Нормалізовані події з прив'язкою до cell
CREATE TABLE events (
    event_id     BIGSERIAL PRIMARY KEY,
    entity_id    VARCHAR(64) NOT NULL,
    ts           TIMESTAMPTZ NOT NULL,
    cell_id      BIGINT NOT NULL REFERENCES grid_cells(cell_id),
    amount       NUMERIC(18,4),
    event_type   VARCHAR(64),
    attrs        JSONB
);

CREATE INDEX idx_events_cell_ts
    ON events (cell_id, ts);

-- ST features (агрегати по вікнах)
CREATE TABLE st_features (
    feature_id     BIGSERIAL PRIMARY KEY,
    cell_id        BIGINT NOT NULL REFERENCES grid_cells(cell_id),
    window_start   TIMESTAMPTZ NOT NULL,
    window_end     TIMESTAMPTZ NOT NULL,
    horizon        INTERVAL,
    features       JSONB NOT NULL,   -- {count_1h, rate_24h, avg_amount_7d, ...}
    created_at     TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_st_features_cell_window
    ON st_features (cell_id, window_start, window_end);
