--
-- Material Evidence Schema
-- Sprint 4 Extension - STEP 2
--
-- Demo-realistic tables for material context and evidence.
-- In production, this data would come from ERP/MES/PLM/QMS systems.
--

-- ==============================================================================
-- TABLE: material_instances
-- Tracks material (serial/lot) binding to stations
-- ==============================================================================

CREATE TABLE IF NOT EXISTS material_instances (
    id SERIAL PRIMARY KEY,
    plant VARCHAR(50) NOT NULL,
    line VARCHAR(50) NOT NULL,
    station VARCHAR(50) NOT NULL,
    
    -- Material identification
    mode VARCHAR(20) NOT NULL CHECK (mode IN ('serial', 'lot')),
    serial VARCHAR(100),
    lot VARCHAR(100),
    
    -- Work order context
    work_order VARCHAR(100),
    operation VARCHAR(50),
    
    -- Engineering/revision control
    bom_revision VARCHAR(20),
    as_built_revision VARCHAR(20),
    
    -- Quality status
    quality_status VARCHAR(50) CHECK (quality_status IN ('RELEASED', 'HOLD', 'QUARANTINE')),
    
    -- Audit fields
    active BOOLEAN DEFAULT true,
    ts TIMESTAMP DEFAULT NOW(),
    
    -- Indexes
    CONSTRAINT unique_active_material UNIQUE (plant, line, station, active) 
        WHERE active = true
);

CREATE INDEX idx_material_instances_station ON material_instances(plant, line, station, active);
CREATE INDEX idx_material_instances_serial ON material_instances(serial) WHERE serial IS NOT NULL;
CREATE INDEX idx_material_instances_lot ON material_instances(lot) WHERE lot IS NOT NULL;

COMMENT ON TABLE material_instances IS 'Material (serial/lot) bound to stations - demo data for A&D/Pharma scenarios';
COMMENT ON COLUMN material_instances.mode IS 'serial = individual part tracking, lot = batch tracking';
COMMENT ON COLUMN material_instances.quality_status IS 'RELEASED = OK to process, HOLD = requires deviation, QUARANTINE = blocked';


-- ==============================================================================
-- TABLE: material_authorizations
-- Tracks dry-run authorizations and deviations
-- ==============================================================================

CREATE TABLE IF NOT EXISTS material_authorizations (
    id SERIAL PRIMARY KEY,
    station_id VARCHAR(50) NOT NULL,
    
    -- Authorization flags
    dry_run_authorization BOOLEAN DEFAULT false,
    deviation_id VARCHAR(100),
    
    -- Audit fields
    active BOOLEAN DEFAULT true,
    ts TIMESTAMP DEFAULT NOW(),
    authorized_by VARCHAR(100),
    reason TEXT,
    
    -- Indexes
    CONSTRAINT unique_active_auth UNIQUE (station_id, active) 
        WHERE active = true
);

CREATE INDEX idx_material_auth_station ON material_authorizations(station_id, active);

COMMENT ON TABLE material_authorizations IS 'Authorizations for dry-run operations and deviations - A&D compliance';
COMMENT ON COLUMN material_authorizations.dry_run_authorization IS 'True if station is authorized for zero-output dry runs';
COMMENT ON COLUMN material_authorizations.deviation_id IS 'Reference to QMS deviation record (Pharma/A&D)';


-- ==============================================================================
-- TABLE: tooling_status
-- Tracks tooling calibration status
-- ==============================================================================

CREATE TABLE IF NOT EXISTS tooling_status (
    id SERIAL PRIMARY KEY,
    tooling_id VARCHAR(100) NOT NULL,
    station_id VARCHAR(50) NOT NULL,
    
    -- Calibration status
    calibration_ok BOOLEAN DEFAULT false,
    calibration_due_date DATE,
    last_calibration_date DATE,
    
    -- Audit fields
    active BOOLEAN DEFAULT true,
    ts TIMESTAMP DEFAULT NOW(),
    calibrated_by VARCHAR(100),
    
    -- Indexes
    CONSTRAINT unique_active_tooling UNIQUE (station_id, active) 
        WHERE active = true
);

CREATE INDEX idx_tooling_status_station ON tooling_status(station_id, active);
CREATE INDEX idx_tooling_due_date ON tooling_status(calibration_due_date) WHERE calibration_ok = false;

COMMENT ON TABLE tooling_status IS 'Tooling calibration tracking - A&D/Pharma compliance requirement';
COMMENT ON COLUMN tooling_status.calibration_ok IS 'False if calibration is overdue or failed';


-- ==============================================================================
-- TABLE: operator_certifications
-- Tracks operator certifications for stations
-- ==============================================================================

CREATE TABLE IF NOT EXISTS operator_certifications (
    id SERIAL PRIMARY KEY,
    operator_id VARCHAR(100) NOT NULL,
    station_id VARCHAR(50) NOT NULL,
    
    -- Certification status
    certified BOOLEAN DEFAULT false,
    certification_date DATE,
    certification_expiry DATE,
    
    -- Audit fields
    active BOOLEAN DEFAULT true,
    ts TIMESTAMP DEFAULT NOW(),
    certified_by VARCHAR(100),
    
    -- Indexes
    CONSTRAINT unique_active_operator UNIQUE (station_id, active) 
        WHERE active = true
);

CREATE INDEX idx_operator_cert_station ON operator_certifications(station_id, active);
CREATE INDEX idx_operator_cert_expiry ON operator_certifications(certification_expiry) WHERE certified = true;

COMMENT ON TABLE operator_certifications IS 'Operator qualifications for stations - A&D/Pharma requirement';
COMMENT ON COLUMN operator_certifications.certified IS 'False if not certified or certification expired';


-- ==============================================================================
-- DEMO DATA VIEWS (for diagnostics/reporting)
-- ==============================================================================

CREATE OR REPLACE VIEW v_material_evidence AS
SELECT 
    mi.plant,
    mi.line,
    mi.station,
    mi.mode,
    mi.serial AS active_serial,
    mi.lot AS active_lot,
    mi.work_order,
    mi.operation,
    mi.bom_revision,
    mi.as_built_revision,
    mi.quality_status,
    ma.dry_run_authorization,
    ma.deviation_id,
    ts.calibration_ok AS tooling_calibration_ok,
    oc.certified AS operator_certified,
    mi.ts AS material_ts
FROM material_instances mi
LEFT JOIN material_authorizations ma ON mi.station = ma.station_id AND ma.active = true
LEFT JOIN tooling_status ts ON mi.station = ts.station_id AND ts.active = true
LEFT JOIN operator_certifications oc ON mi.station = oc.station_id AND oc.active = true
WHERE mi.active = true;

COMMENT ON VIEW v_material_evidence IS 'Consolidated material evidence for diagnostics - combines all evidence sources';
