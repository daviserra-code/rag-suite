-- OPC Studio Historian schema (v0.2)
-- Run once in your Postgres (ragdb)

CREATE TABLE IF NOT EXISTS opc_kpi_samples (
  id BIGSERIAL PRIMARY KEY,
  ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  plant TEXT NOT NULL,
  line TEXT NOT NULL,
  oee DOUBLE PRECISION,
  availability DOUBLE PRECISION,
  performance DOUBLE PRECISION,
  quality DOUBLE PRECISION,
  status TEXT
);

CREATE INDEX IF NOT EXISTS idx_opc_kpi_samples_ts ON opc_kpi_samples(ts);
CREATE INDEX IF NOT EXISTS idx_opc_kpi_samples_dim ON opc_kpi_samples(plant, line, ts);

CREATE TABLE IF NOT EXISTS opc_station_samples (
  id BIGSERIAL PRIMARY KEY,
  ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  plant TEXT NOT NULL,
  line TEXT NOT NULL,
  station TEXT NOT NULL,
  state TEXT,
  cycle_time_s DOUBLE PRECISION,
  good_count BIGINT,
  scrap_count BIGINT,
  alarms JSONB DEFAULT '[]'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_opc_station_samples_ts ON opc_station_samples(ts);
CREATE INDEX IF NOT EXISTS idx_opc_station_samples_dim ON opc_station_samples(plant, line, station, ts);

CREATE TABLE IF NOT EXISTS opc_events (
  id BIGSERIAL PRIMARY KEY,
  ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  plant TEXT NOT NULL,
  line TEXT NOT NULL,
  station TEXT NOT NULL,
  event_type TEXT NOT NULL,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_opc_events_ts ON opc_events(ts);
CREATE INDEX IF NOT EXISTS idx_opc_events_dim ON opc_events(plant, line, station, ts);
