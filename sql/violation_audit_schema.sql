--
-- Violation Audit Schema
-- Sprint 4 Extension - STEP 3
--
-- Audit-grade persistence for expectation violations.
-- Supports A&D compliance, traceability, and human acknowledgment.
--

-- ==============================================================================
-- TABLE: violations
-- Stores all expectation violations detected by diagnostics
-- ==============================================================================

CREATE TABLE IF NOT EXISTS violations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Profile context
    profile VARCHAR(100) NOT NULL,
    
    -- Location context
    plant VARCHAR(50) NOT NULL,
    line VARCHAR(50) NOT NULL,
    station VARCHAR(50) NOT NULL,
    
    -- Violation metadata
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('normal', 'warning', 'critical')),
    requires_human_confirmation BOOLEAN DEFAULT false,
    
    -- Timing
    ts_start TIMESTAMP NOT NULL DEFAULT NOW(),
    ts_end TIMESTAMP,  -- NULL while active, set when resolved
    
    -- Violation details (JSON for flexibility)
    violated_expectations JSONB DEFAULT '[]'::jsonb,
    blocking_conditions JSONB DEFAULT '[]'::jsonb,
    warnings JSONB DEFAULT '[]'::jsonb,
    
    -- References
    material_ref JSONB,  -- Material context at time of violation
    snapshot_ref JSONB,  -- Runtime snapshot reference
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    CHECK (ts_end IS NULL OR ts_end >= ts_start)
);

-- Indexes for efficient queries
CREATE INDEX idx_violations_active ON violations(station, ts_end) WHERE ts_end IS NULL;
CREATE INDEX idx_violations_station_ts ON violations(station, ts_start DESC);
CREATE INDEX idx_violations_profile ON violations(profile);
CREATE INDEX idx_violations_severity ON violations(severity) WHERE ts_end IS NULL;
CREATE INDEX idx_violations_blocking ON violations(requires_human_confirmation) WHERE requires_human_confirmation = true AND ts_end IS NULL;

COMMENT ON TABLE violations IS 'Audit trail of all expectation violations - A&D compliance ready';
COMMENT ON COLUMN violations.ts_end IS 'NULL = active violation, NOT NULL = resolved/closed';
COMMENT ON COLUMN violations.material_ref IS 'Material context snapshot at violation time';
COMMENT ON COLUMN violations.snapshot_ref IS 'OPC snapshot reference for traceability';


-- ==============================================================================
-- TABLE: violation_ack
-- Stores human acknowledgments of violations
-- ==============================================================================

CREATE TABLE IF NOT EXISTS violation_ack (
    id SERIAL PRIMARY KEY,
    violation_id UUID NOT NULL REFERENCES violations(id) ON DELETE CASCADE,
    
    -- Acknowledgment metadata
    ts TIMESTAMP NOT NULL DEFAULT NOW(),
    ack_by VARCHAR(100) NOT NULL,  -- User ID/name
    ack_type VARCHAR(50) NOT NULL CHECK (ack_type IN (
        'acknowledged',      -- Seen and noted
        'justified',         -- Acceptable deviation with reason
        'false_positive',    -- Not actually a violation
        'resolved'           -- Issue fixed
    )),
    
    -- Evidence
    comment TEXT,
    evidence_ref VARCHAR(200),  -- Document ID, deviation ID, work order, etc.
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_violation_ack_violation ON violation_ack(violation_id, ts DESC);
CREATE INDEX idx_violation_ack_user ON violation_ack(ack_by, ts DESC);
CREATE INDEX idx_violation_ack_type ON violation_ack(ack_type);

COMMENT ON TABLE violation_ack IS 'Human acknowledgments of violations - audit trail';
COMMENT ON COLUMN violation_ack.ack_type IS 'acknowledged = seen, justified = OK with reason, false_positive = not real, resolved = fixed';
COMMENT ON COLUMN violation_ack.evidence_ref IS 'Reference to external evidence (deviation, work order, doc ID)';


-- ==============================================================================
-- VIEWS for common queries
-- ==============================================================================

-- Active violations (currently open)
CREATE OR REPLACE VIEW v_violations_active AS
SELECT 
    v.id,
    v.profile,
    v.plant,
    v.line,
    v.station,
    v.severity,
    v.requires_human_confirmation,
    v.ts_start,
    v.violated_expectations,
    v.blocking_conditions,
    v.warnings,
    v.material_ref,
    COUNT(va.id) AS ack_count,
    MAX(va.ts) AS last_ack_ts,
    MAX(va.ack_by) AS last_ack_by
FROM violations v
LEFT JOIN violation_ack va ON v.id = va.violation_id
WHERE v.ts_end IS NULL
GROUP BY v.id, v.profile, v.plant, v.line, v.station, v.severity, 
         v.requires_human_confirmation, v.ts_start, v.violated_expectations,
         v.blocking_conditions, v.warnings, v.material_ref
ORDER BY v.ts_start DESC;

COMMENT ON VIEW v_violations_active IS 'Currently active (open) violations with acknowledgment counts';


-- Violation history (closed violations)
CREATE OR REPLACE VIEW v_violations_history AS
SELECT 
    v.id,
    v.profile,
    v.plant,
    v.line,
    v.station,
    v.severity,
    v.requires_human_confirmation,
    v.ts_start,
    v.ts_end,
    EXTRACT(EPOCH FROM (v.ts_end - v.ts_start)) / 60 AS duration_minutes,
    v.violated_expectations,
    v.blocking_conditions,
    COUNT(va.id) AS ack_count,
    MAX(va.ts) AS last_ack_ts,
    MAX(va.ack_type) FILTER (WHERE va.ack_type = 'resolved') AS was_resolved
FROM violations v
LEFT JOIN violation_ack va ON v.id = va.violation_id
WHERE v.ts_end IS NOT NULL
GROUP BY v.id, v.profile, v.plant, v.line, v.station, v.severity,
         v.requires_human_confirmation, v.ts_start, v.ts_end,
         v.violated_expectations, v.blocking_conditions
ORDER BY v.ts_end DESC;

COMMENT ON VIEW v_violations_history IS 'Historical (closed) violations with resolution metadata';


-- Violation statistics by station
CREATE OR REPLACE VIEW v_violation_stats_by_station AS
SELECT 
    station,
    profile,
    COUNT(*) AS total_violations,
    COUNT(*) FILTER (WHERE ts_end IS NULL) AS active_violations,
    COUNT(*) FILTER (WHERE requires_human_confirmation = true) AS blocking_violations,
    COUNT(*) FILTER (WHERE severity = 'critical') AS critical_violations,
    MIN(ts_start) AS first_violation_ts,
    MAX(ts_start) AS last_violation_ts,
    AVG(EXTRACT(EPOCH FROM (COALESCE(ts_end, NOW()) - ts_start)) / 60) AS avg_duration_minutes
FROM violations
GROUP BY station, profile
ORDER BY active_violations DESC, total_violations DESC;

COMMENT ON VIEW v_violation_stats_by_station IS 'Violation statistics aggregated by station and profile';


-- ==============================================================================
-- TRIGGER: Update updated_at timestamp
-- ==============================================================================

CREATE OR REPLACE FUNCTION update_violations_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_violations_updated_at
BEFORE UPDATE ON violations
FOR EACH ROW
EXECUTE FUNCTION update_violations_timestamp();

COMMENT ON FUNCTION update_violations_timestamp IS 'Automatically update updated_at timestamp on violations table';
