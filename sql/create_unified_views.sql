-- Unified PostgreSQL Views for OPC Studio + Simulation Data
-- Phase B: Prefer OPC data when recent, fallback to simulation

-- v_runtime_kpi: Unified KPI view
-- Prefers opc_kpi_samples when data is recent (< 2 minutes old)
-- Falls back to oee_line_shift for historical/simulation data
CREATE OR REPLACE VIEW v_runtime_kpi AS
WITH opc_recent AS (
    SELECT 
        line as line_id,
        ts,
        ts::date as date,
        CASE 
            WHEN EXTRACT(HOUR FROM ts) >= 6 AND EXTRACT(HOUR FROM ts) < 14 THEN 'M'
            WHEN EXTRACT(HOUR FROM ts) >= 14 AND EXTRACT(HOUR FROM ts) < 22 THEN 'A'
            ELSE 'N'
        END as shift,
        oee,
        availability,
        performance,
        quality,
        NULL::integer as total_units_produced,
        NULL::integer as scrap_units,
        'opc-historian' as source
    FROM opc_kpi_samples
    WHERE ts >= NOW() - INTERVAL '2 minutes'
),
sim_data AS (
    SELECT 
        line_id,
        date::timestamp as ts,
        date,
        shift,
        oee,
        availability,
        performance,
        quality,
        total_units_produced,
        scrap_units,
        'simulation' as source
    FROM oee_line_shift
    WHERE date >= CURRENT_DATE - INTERVAL '30 days'
)
SELECT * FROM opc_recent
UNION ALL
SELECT * FROM sim_data
WHERE line_id NOT IN (SELECT DISTINCT line_id FROM opc_recent)
ORDER BY ts DESC;

COMMENT ON VIEW v_runtime_kpi IS 'Unified KPI view: prefers OPC data when recent, falls back to simulation';


-- v_runtime_events: Unified events view
-- Merges opc_events with oee_downtime_events
-- OPC events are marked as 'opc-events', simulation events as 'simulation'
CREATE OR REPLACE VIEW v_runtime_events AS
WITH opc_events_formatted AS (
    SELECT 
        ts,
        ts::date as date,
        line as line_id,
        station as station_id,
        event_type,
        event_type as loss_category,
        'medium'::text as severity,
        'opc-events' as source,
        NULL::integer as duration_min,
        NULL::text as description
    FROM opc_events
    WHERE ts >= NOW() - INTERVAL '30 days'
),
sim_events_formatted AS (
    SELECT 
        start_timestamp as ts,
        date,
        line_id,
        NULL::text as station_id,
        loss_category as event_type,
        loss_category,
        'medium' as severity,
        'simulation' as source,
        duration_min,
        description
    FROM oee_downtime_events
    WHERE date >= CURRENT_DATE - INTERVAL '30 days'
)
SELECT * FROM opc_events_formatted
UNION ALL
SELECT * FROM sim_events_formatted
ORDER BY ts DESC;

COMMENT ON VIEW v_runtime_events IS 'Unified events view: merges OPC events with simulation downtime events';


-- v_runtime_line_status: Current line status
-- Shows most recent KPI for each line, with source indicator
CREATE OR REPLACE VIEW v_runtime_line_status AS
WITH ranked_kpis AS (
    SELECT 
        line_id,
        ts,
        oee,
        availability,
        performance,
        quality,
        source,
        ROW_NUMBER() OVER (PARTITION BY line_id ORDER BY ts DESC) as rn
    FROM v_runtime_kpi
)
SELECT 
    line_id,
    ts as last_update,
    oee,
    availability,
    performance,
    quality,
    source,
    CASE 
        WHEN availability >= 0.85 THEN 'RUNNING'
        WHEN availability >= 0.5 THEN 'DEGRADED'
        ELSE 'STOPPED'
    END as status
FROM ranked_kpis
WHERE rn = 1;

COMMENT ON VIEW v_runtime_line_status IS 'Current status of each line with latest KPIs';


-- v_runtime_events_summary: Recent events summary (last 24 hours)
-- Groups events by line, station, event_type with counts
CREATE OR REPLACE VIEW v_runtime_events_summary AS
SELECT 
    line_id,
    station_id,
    event_type,
    source,
    COUNT(*) as event_count,
    MIN(ts) as first_occurrence,
    MAX(ts) as last_occurrence,
    AVG(duration_min) as avg_downtime_min
FROM v_runtime_events
WHERE ts >= NOW() - INTERVAL '24 hours'
GROUP BY line_id, station_id, event_type, source
ORDER BY last_occurrence DESC;

COMMENT ON VIEW v_runtime_events_summary IS 'Summary of events in last 24 hours grouped by line/station/type';
