#!/usr/bin/env python3
"""
MES-like RAG Corpus Generator
Sprint 5 - Citation Discipline & Profile-Aware Knowledge Retrieval

Generates 50-100 synthetic but realistic MES documents with:
- Structured sections: Purpose, Scope, Procedure, Acceptance Criteria
- Profile-specific content (Aerospace & Defence, Pharma, Automotive)
- Realistic language and terminology
- 1-2 pages equivalent each

Document Types Generated:
- Work Instructions (WI)
- Standard Operating Procedures (SOP)
- Deviation Approvals
- Calibration Procedures
- Batch Records
- Maintenance Playbooks
- Downtime Response
- Quality Specifications
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
import random

# Output directory
OUTPUT_DIR = Path("data/documents/mes_corpus")

# Document templates by profile
AEROSPACE_DEFENCE_DOCS = [
    {
        "id": "WI-OP40-Serial-Binding",
        "title": "Work Instruction: Serial Number Binding at OP40",
        "doc_type": "work_instruction",
        "profile": "aerospace_defence",
        "station": "ST40",
        "revision": "C",
        "purpose": "To establish the mandatory procedure for binding serial numbers to manufactured components at Operation 40, ensuring full traceability and compliance with AS9100 requirements.",
        "scope": "Applies to all critical flight components manufactured at ST40 requiring serial number assignment. Includes fuselage brackets, wing attachments, and structural reinforcements with part numbers AER-5000 through AER-5999.",
        "procedure": [
            "1. Verify component has passed incoming inspection (QA stamp required)",
            "2. Scan component barcode using Cognex DataMan 470 scanner",
            "3. Confirm part number matches traveler document",
            "4. Access MES terminal (workstation ID: ST40-WS01)",
            "5. Enter operator ID and password",
            "6. System automatically generates next sequential serial number from approved range",
            "7. Verify serial number format: SN-YYWW-XXXX (Year-Week-Sequence)",
            "8. Laser etch serial number on designated marking area (refer to drawing for location)",
            "9. Verify etching depth: 0.002\" ± 0.0005\" using depth gauge",
            "10. Photograph serial number with station camera for digital record",
            "11. System automatically creates material binding record in v_material_evidence table",
            "12. Print traveler update with serial number and operator signature",
            "13. Attach traveler to component and route to next operation"
        ],
        "acceptance_criteria": [
            "Serial number clearly legible and matches MES record",
            "Etching depth within specification (0.0015\" - 0.0025\")",
            "Digital photograph stored in quality management system",
            "Material evidence record created with timestamp and operator ID",
            "No production allowed without serial binding - BLOCKING condition"
        ],
        "references": ["AS9100 Rev D Section 8.5.2", "AER-QM-1001 Traceability Requirements"],
        "safety_notes": ["Wear laser safety glasses (OD 7+ at 1064nm)", "Ensure proper ventilation during laser etching"]
    },
    {
        "id": "SOP-Deviation-Approval-ASD",
        "title": "Standard Operating Procedure: Deviation Request and Approval",
        "doc_type": "deviation",
        "profile": "aerospace_defence",
        "station": None,
        "revision": "B",
        "purpose": "To define the process for requesting, reviewing, and approving temporary deviations from established work instructions or specifications when conforming material is unavailable or process constraints exist.",
        "scope": "Applies to all production deviations requiring engineering approval. Does not apply to safety-critical deviations which require customer notification per AS9100 clause 8.4.3.",
        "procedure": [
            "1. INITIATION: Production supervisor identifies need for deviation",
            "2. Open deviation request in MES (Module: Quality → Deviations → New Request)",
            "3. Complete deviation form DEV-FORM-001 with following details:",
            "   - Part number and serial numbers affected",
            "   - Original requirement being deviated",
            "   - Proposed alternative method or specification",
            "   - Technical justification and risk assessment",
            "   - Estimated quantity and duration of deviation",
            "4. ENGINEERING REVIEW: Route to design engineering within 4 hours",
            "5. Engineer evaluates impact on form, fit, function, and airworthiness",
            "6. If approved, engineer assigns deviation number (DEV-YYYY-XXXX format)",
            "7. QUALITY APPROVAL: QA manager reviews for compliance impact",
            "8. QA determines if customer notification required (critical characteristics)",
            "9. CUSTOMER NOTIFICATION: For flight-critical items, customer approval mandatory",
            "10. EXECUTION: Once approved, deviation number added to affected travelers",
            "11. Production updates MES with deviation reference before proceeding",
            "12. CLOSURE: After deviation period expires, engineering reviews results",
            "13. Lessons learned documented for continuous improvement"
        ],
        "acceptance_criteria": [
            "Deviation approved by both Engineering and Quality",
            "Customer approval obtained if affecting critical characteristics",
            "Deviation number referenced on all affected travelers and serial numbers",
            "Deviation does not compromise airworthiness or safety",
            "All affected units traceable via v_material_evidence.deviation_id field",
            "Production BLOCKED until deviation formally approved"
        ],
        "references": ["AS9100 Rev D Section 8.5.2", "AER-QM-2003 Deviation Control"],
        "safety_notes": ["Never deviate safety-critical processes without customer approval"]
    },
    {
        "id": "CAL-T-203-Torque-Wrench",
        "title": "Calibration Procedure: Torque Wrench T-203",
        "doc_type": "calibration",
        "profile": "aerospace_defence",
        "station": "ST40",
        "revision": "A",
        "purpose": "To establish the calibration procedure for precision torque wrench T-203 used in critical assembly operations, ensuring measurement accuracy and compliance with ISO 17025.",
        "scope": "Applies to Snap-On TechAngle 1/2\" drive torque wrench, S/N T-203-2023-001, calibration range 20-200 ft-lbs, used at stations ST40, ST41, and ST42.",
        "procedure": [
            "1. PRE-CALIBRATION: Visually inspect wrench for damage, wear, or contamination",
            "2. Record current calibration status and due date",
            "3. Clean wrench with isopropyl alcohol and lint-free cloth",
            "4. Allow thermal stabilization: 30 minutes at 20°C ± 2°C",
            "5. SETUP: Mount wrench in Norbar calibration fixture Model CST-2000",
            "6. Connect to traceable load cell (NIST traceable, cert #NIST-2024-12345)",
            "7. CALIBRATION POINTS: Test at 25%, 50%, 75%, and 100% of range:",
            "   - 50 ft-lbs (25%)",
            "   - 100 ft-lbs (50%)",
            "   - 150 ft-lbs (75%)",
            "   - 200 ft-lbs (100%)",
            "8. For each point, perform 3 measurements in both clockwise and counterclockwise",
            "9. Record actual torque measured vs. indicated torque",
            "10. ACCEPTANCE: All readings must be within ±3% of indicated value",
            "11. If out of spec, perform adjustment per manufacturer procedure",
            "12. Re-test all points after adjustment",
            "13. DOCUMENTATION: Complete calibration certificate CAL-CERT-T203",
            "14. Apply calibration sticker with due date (12 months from today)",
            "15. Update MES tool calibration database with certificate scan"
        ],
        "acceptance_criteria": [
            "All calibration points within ±3% tolerance",
            "No physical damage or wear beyond manufacturer limits",
            "Calibration certificate traceable to NIST standards",
            "Due date sticker applied and legible",
            "MES tool database updated with certificate reference",
            "Tool BLOCKED from use if overdue or out of tolerance"
        ],
        "references": ["ISO 17025:2017", "AER-QM-3001 Tool Calibration Requirements"],
        "safety_notes": ["Do not exceed rated capacity during calibration"]
    },
    {
        "id": "WI-OP35-Composite-Layup",
        "title": "Work Instruction: Carbon Fiber Composite Layup",
        "doc_type": "work_instruction",
        "profile": "aerospace_defence",
        "station": "ST35",
        "revision": "D",
        "purpose": "To establish the procedure for hand layup of carbon fiber prepreg composite materials for aircraft structural components, ensuring ply orientation accuracy and void-free construction.",
        "scope": "Applies to all prepreg composite layup operations at ST35 using Toray T800H/3900-2 material system. Includes wing skins, control surfaces, and fuselage panels with part numbers CFR-3000 through CFR-3999.",
        "procedure": [
            "1. MATERIAL PREPARATION: Remove prepreg roll from -18°C freezer storage",
            "2. Allow thermal equilibration: minimum 4 hours at room temperature",
            "3. Verify material certification and expiration date on roll label",
            "4. Record lot number and expiration in MES material binding record",
            "5. TOOL PREPARATION: Clean aluminum layup tool with acetone",
            "6. Apply release agent (Frekote 700-NC) per manufacturer instructions",
            "7. Verify tool temperature: 21°C ± 3°C",
            "8. LAYUP SEQUENCE: Follow ply schedule drawing DWG-CFR-3001",
            "9. For each ply layer:",
            "   - Cut ply to template dimensions using ultrasonic cutter",
            "   - Remove backing paper immediately before placement",
            "   - Align ply using laser alignment marks on tool",
            "   - Verify fiber orientation with protractor: ±2° tolerance",
            "   - Debulk with roller: 3 passes at 5 psi pressure",
            "10. Photograph each ply layer for quality record",
            "11. After all plies placed, vacuum bag per SOP-BAG-001",
            "12. Verify vacuum integrity: hold 28\" Hg for 15 minutes minimum",
            "13. Route to autoclave for cure cycle per CURE-CYCLE-3900"
        ],
        "acceptance_criteria": [
            "All ply orientations within ±2° of specification",
            "No bridging, wrinkles, or foreign object debris visible",
            "Vacuum bag holds minimum 28\" Hg without decay",
            "Digital photographs archived for each ply layer",
            "Material traceability complete: lot number, expiration, operator",
            "Out-of-time material BLOCKED from use - check expiration strictly"
        ],
        "references": ["AMS 3900 Material Specification", "AER-COMP-5001 Composite Manufacturing"],
        "safety_notes": ["Wear nitrile gloves - skin contact causes contamination", "Dispose of backing paper in designated composite waste bin"]
    }
]

PHARMA_PROCESS_DOCS = [
    {
        "id": "SOP-BPR-001-Tablet-Compression",
        "title": "Standard Operating Procedure: Batch Production Record - Tablet Compression",
        "doc_type": "sop",
        "profile": "pharma_process",
        "station": "ST25",
        "revision": "F",
        "purpose": "To establish the procedure for executing batch production records for tablet compression operations in compliance with 21 CFR Part 211 and EU GMP Annex 11, ensuring product quality and batch traceability.",
        "scope": "Applies to all oral solid dose tablet compression at manufacturing line B01, stations ST24-ST26. Includes immediate-release and sustained-release formulations under approved NDA 123456.",
        "procedure": [
            "1. BATCH RECORD RETRIEVAL: QA releases batch production record (BPR) to production",
            "2. Verify batch number matches material requisition: format BATCH-YYYY-XXX",
            "3. Verify all starting materials have valid CoA certificates on file",
            "4. MATERIAL STAGING: Scan each material container barcode into MES",
            "5. System validates: lot number, expiration date, approved supplier, quantity",
            "6. EQUIPMENT SETUP: Clean tablet press per SOP-CLEAN-TP-001",
            "7. Perform pre-operation checks documented in BPR Section 5:",
            "   - Punch and die set identification and cleanliness",
            "   - Compression force calibration within last 30 days",
            "   - Weight control system calibration current",
            "   - Tablet hardness tester calibration current",
            "8. MATERIAL CHARGING: Weigh granulation per BPR specification ±2%",
            "9. Load hopper and start compression under continuous supervision",
            "10. IN-PROCESS CONTROLS: Every 15 minutes, measure and record:",
            "   - Tablet weight: 500mg ± 25mg (5% tolerance)",
            "   - Tablet hardness: 8-12 kP",
            "   - Tablet thickness: 4.0mm ± 0.2mm",
            "   - Friability: ≤1.0% after 4 minutes at 25 rpm",
            "11. If any parameter out of specification, STOP production immediately",
            "12. Notify QA and document deviation in batch record",
            "13. QA reviews in-process data every hour during compression",
            "14. BATCH COMPLETION: Record final tablet count and yield",
            "15. Collect retain samples (3x therapeutic dose) and submit to QC",
            "16. Clean equipment per SOP-CLEAN-TP-001 and record in logbook",
            "17. QA reviews completed BPR within 24 hours for release decision"
        ],
        "acceptance_criteria": [
            "All in-process measurements within specification limits",
            "Yield between 95-105% of theoretical (accounts for waste)",
            "No unapproved deviations or process interruptions",
            "All material lot numbers traceable to CoA certificates",
            "Batch record complete with all operator and QA signatures",
            "Equipment cleaning verified before and after batch",
            "HOLD status enforced until QA batch record review complete"
        ],
        "references": ["21 CFR Part 211.100", "EU GMP Chapter 4", "ICH Q7A Section 6"],
        "safety_notes": ["Wear dust mask and safety glasses during material handling", "Lock-out/tag-out required for equipment maintenance"]
    },
    {
        "id": "SOP-Deviation-Pharma-Process",
        "title": "Standard Operating Procedure: Deviation Management and Investigation",
        "doc_type": "deviation",
        "profile": "pharma_process",
        "station": None,
        "revision": "E",
        "purpose": "To define the process for identifying, documenting, investigating, and resolving deviations from established procedures, specifications, or GMP requirements in accordance with 21 CFR Part 211.192.",
        "scope": "Applies to all manufacturing deviations including out-of-specification (OOS) results, procedural deviations, equipment malfunctions, and environmental excursions. Covers all GMP areas: manufacturing, packaging, quality control, and quality assurance.",
        "procedure": [
            "1. DEVIATION IDENTIFICATION: Any employee observing a deviation must report immediately",
            "2. Access MES Deviation Module: Quality → Deviations → New Deviation",
            "3. Complete initial deviation report within 1 hour of discovery:",
            "   - Deviation number auto-assigned: DEV-YYYY-XXXX",
            "   - Batch/lot number(s) affected",
            "   - Product and process step involved",
            "   - Detailed description of deviation",
            "   - Immediate containment actions taken",
            "4. SEVERITY CLASSIFICATION: QA assigns severity within 2 hours:",
            "   - Critical: Patient safety or product efficacy impact",
            "   - Major: GMP compliance or quality system impact",
            "   - Minor: Documentation or procedural non-conformance",
            "5. IMMEDIATE ACTIONS for Critical/Major deviations:",
            "   - Place affected batch on HOLD status in MES",
            "   - Quarantine affected material physically and electronically",
            "   - Notify QA Manager and Production Manager within 30 minutes",
            "   - Customer notification if distributed product affected",
            "6. INVESTIGATION: Assign investigation team within 24 hours:",
            "   - Team lead: QA representative (mandatory)",
            "   - Production supervisor",
            "   - Subject matter expert (QC, Engineering, Validation as needed)",
            "7. INVESTIGATION EXECUTION (complete within 30 days):",
            "   - Root cause analysis using structured tools (5-Why, Fishbone)",
            "   - Impact assessment on batch quality and patient safety",
            "   - Review of similar past deviations (trending)",
            "   - Evaluation of detection and control systems",
            "8. CORRECTIVE AND PREVENTIVE ACTIONS (CAPA):",
            "   - Define specific actions to prevent recurrence",
            "   - Assign owners and target completion dates",
            "   - Determine if procedure updates or training required",
            "9. QA REVIEW AND APPROVAL:",
            "   - QA Manager reviews investigation report",
            "   - Determines batch disposition: Release, Reject, or Reprocess",
            "   - Updates deviation status in MES: Closed or Open (if CAPA pending)",
            "10. FINAL DISPOSITION:",
            "    - If batch released: update MES and remove HOLD",
            "    - If batch rejected: route to destruction per SOP-DEST-001",
            "    - Document final decision in batch production record"
        ],
        "acceptance_criteria": [
            "Deviation documented within 1 hour of discovery",
            "Severity classification assigned within 2 hours",
            "Investigation completed within 30 days for Major/Critical",
            "Root cause identified using structured methodology",
            "CAPA plan documented with owners and dates",
            "Batch disposition approved by QA Manager",
            "All CAPA actions completed before deviation closure",
            "Deviation reference documented in batch record",
            "Production BLOCKED on HOLD batches until QA disposition"
        ],
        "references": ["21 CFR Part 211.192", "ICH Q10 Section 3.1", "EU GMP Chapter 1"],
        "safety_notes": ["Isolate defective material to prevent cross-contamination"]
    },
    {
        "id": "SOP-Material-Release-API",
        "title": "Standard Operating Procedure: Active Pharmaceutical Ingredient Release",
        "doc_type": "sop",
        "profile": "pharma_process",
        "station": None,
        "revision": "C",
        "purpose": "To establish the procedure for quality control testing and release of active pharmaceutical ingredient (API) raw materials prior to use in manufacturing, ensuring compliance with USP monographs and supplier CoA specifications.",
        "scope": "Applies to all incoming API materials requiring QC testing before release to production. Includes Schedule II-V controlled substances and non-controlled APIs with NDAs or ANDAs.",
        "procedure": [
            "1. MATERIAL RECEIPT: Receiving logs API delivery into MES",
            "2. System assigns unique lot number: LOT-YYYY-SUPPLIER-XXXX",
            "3. Material placed in quarantine warehouse (QA approval required for access)",
            "4. Receiving generates QC sampling request in MES",
            "5. QC SAMPLING (within 24 hours of receipt):",
            "   - QC analyst accesses quarantine with supervisor approval",
            "   - Verify container integrity, labeling, and CoA presence",
            "   - Collect representative sample per SOP-SAMPLING-001:",
            "     * Minimum 3 containers or 10% of lot, whichever greater",
            "     * Use sterile sampling equipment for sterile APIs",
            "     * Transfer to labeled QC sample container",
            "   - Photograph sampling locations for audit trail",
            "   - Seal containers with tamper-evident seals",
            "   - Return material to quarantine",
            "6. QC TESTING: Perform tests per approved test method (ATM):",
            "   - Identity: IR spectroscopy (match reference spectrum)",
            "   - Assay: HPLC quantification (95.0% - 105.0% of label claim)",
            "   - Related substances: HPLC (each impurity <0.1%, total <0.5%)",
            "   - Residual solvents: GC-MS (per ICH Q3C limits)",
            "   - Heavy metals: ICP-MS (Pb <10ppm, others per USP)",
            "   - Microbial limits: Bioburden <1000 CFU/g, no objectionable organisms",
            "   - Endotoxin: LAL test <0.25 EU/mg for parenteral APIs",
            "7. Enter test results into LIMS within 48 hours of testing",
            "8. LIMS automatically compares results to specification limits",
            "9. OUT-OF-SPECIFICATION (OOS) HANDLING:",
            "   - If any test fails, initiate OOS investigation per SOP-OOS-001",
            "   - Notify QA Manager and Purchasing within 1 hour",
            "   - Do not release material pending investigation",
            "   - Consider retesting or supplier notification",
            "10. RELEASE DECISION (QA Manager authority):",
            "    - Review all test results and supplier CoA",
            "    - Verify CoA matches tested lot number",
            "    - Check supplier qualification status",
            "    - Approve or reject lot in MES",
            "11. If APPROVED: System changes status from QUARANTINE to RELEASED",
            "12. If REJECTED: Route to destruction per SOP-DEST-002",
            "13. Notify production planner of released material availability"
        ],
        "acceptance_criteria": [
            "All test results meet specification limits",
            "CoA provided by supplier and matches tested lot",
            "Supplier has current approved qualification status",
            "Test methods validated per ICH Q2(R1) requirements",
            "Results documented in LIMS with analyst and reviewer signatures",
            "QA Manager approval electronic signature in MES",
            "Material status in MES updated: QUARANTINE → RELEASED or REJECTED",
            "Production BLOCKED from using material until RELEASED status"
        ],
        "references": ["USP <1058> Analytical Instrument Qualification", "ICH Q6A Specifications", "21 CFR Part 211.84"],
        "safety_notes": ["Controlled substances require dual custody and DEA form 222"]
    }
]

AUTOMOTIVE_DISCRETE_DOCS = [
    {
        "id": "WI-WELD-001-Spot-Welding",
        "title": "Work Instruction: Resistance Spot Welding - Body Assembly",
        "doc_type": "work_instruction",
        "profile": "automotive_discrete",
        "station": "ST10",
        "revision": "B",
        "purpose": "To establish the standard method for resistance spot welding of body-in-white assemblies, ensuring consistent weld quality and meeting OEM structural specifications.",
        "scope": "Applies to all spot welding operations at Body Shop Line A, stations ST10-ST12. Includes front/rear door assemblies, floor panels, and reinforcement brackets using AWS D8.1M specifications.",
        "procedure": [
            "1. SETUP VERIFICATION: Check weld gun serial number matches station assignment",
            "2. Verify electrode tips are clean and correctly sized (6mm diameter for Class A)",
            "3. Confirm weld schedule loaded in PLC: program #WS-105 for 0.8mm steel",
            "4. Perform electrode force calibration check: 2.5kN ±0.2kN",
            "5. MATERIAL PREPARATION: Verify panel part numbers match build sequence",
            "6. Ensure panel surfaces clean (no oil, rust, or coating defects)",
            "7. FIXTURING: Load panels into weld fixture",
            "8. Confirm all locating pins engaged and clamps locked",
            "9. Verify panel alignment with go/no-go gauge (±0.5mm tolerance)",
            "10. WELDING SEQUENCE: Follow weld pattern diagram WP-BIW-105:",
            "    - Start with corner welds (positions 1, 4, 7, 10)",
            "    - Progress to edge welds (positions 2, 3, 5, 6, 8, 9)",
            "    - Complete with center reinforcement welds",
            "11. For each weld point:",
            "    - Position gun electrodes perpendicular to panel surface",
            "    - Initiate weld cycle (auto sequence: squeeze-weld-hold-release)",
            "    - Verify weld current and time within spec (logged by PLC)",
            "    - Visual check: no spatter, burn-through, or misalignment",
            "12. QUALITY CHECK: Every 10 units, perform destructive peel test",
            "13. Peel test acceptance: minimum button diameter 4.0mm",
            "14. Record peel test results in quality logbook",
            "15. If peel test fails: stop production, notify supervisor, retip electrodes",
            "16. ELECTRODE MAINTENANCE: Replace tips after 500 welds or when diameter <5.0mm"
        ],
        "acceptance_criteria": [
            "All welds complete per pattern diagram (23 welds per assembly)",
            "Weld current within ±5% of programmed value",
            "No visible spatter, burn-through, or surface defects",
            "Peel test button diameter minimum 4.0mm",
            "Cycle time meets takt time: 58 seconds per unit",
            "PLC log confirms all weld parameters within specification"
        ],
        "references": ["AWS D8.1M Automotive Weld Quality", "OEM-SPEC-BIW-2024"],
        "safety_notes": ["Lockout/tagout required for electrode changes", "Wear leather gloves - electrodes remain hot"]
    },
    {
        "id": "MAINT-PM-Engine-Assembly-Line",
        "title": "Preventive Maintenance Procedure: Engine Assembly Line Conveyor",
        "doc_type": "maintenance_log",
        "profile": "automotive_discrete",
        "station": "Line-A",
        "revision": "D",
        "purpose": "To establish the preventive maintenance schedule and procedures for the main conveyor system serving Engine Assembly Line A, minimizing unplanned downtime and ensuring production continuity.",
        "scope": "Applies to 250-meter overhead conveyor system including 18 drive units, 124 carrier hooks, and PLC control system. Services stations EA10 through EA45 on Line A.",
        "procedure": [
            "DAILY CHECKS (Performed by line operator at shift start):",
            "1. Walk entire conveyor length and observe for unusual noises or vibration",
            "2. Check all carrier hooks for damage, cracks, or loose fasteners",
            "3. Verify emergency stop buttons functional (test 1 button per shift)",
            "4. Record observations in operator logbook",
            "",
            "WEEKLY MAINTENANCE (Performed by maintenance technician):",
            "1. Inspect chain tension at 6 measurement points: should lift 50mm at midspan",
            "2. Adjust chain tensioners if lift exceeds 75mm",
            "3. Lubricate chain with ISO VG 220 oil: 2 liters per 50 meters",
            "4. Inspect wear strips on conveyor rails: replace if wear depth >2mm",
            "5. Check drive motor amperages: should be 15-20A under load",
            "6. Test backup drive unit by switching to secondary motor",
            "7. Download PLC fault log and review for recurring alarms",
            "8. Complete PM checklist form MAINT-CHK-CONV-001",
            "",
            "MONTHLY MAINTENANCE:",
            "1. Detailed inspection of all 18 drive gear boxes",
            "2. Check oil level in gear boxes: maintain at sight glass midpoint",
            "3. Sample oil from drive #1 and #9 for analysis (viscosity, metal content)",
            "4. Inspect drive belts for cracks or glazing: replace if worn",
            "5. Verify PLC program backup current (last 30 days)",
            "6. Test conveyor speed accuracy: 3.5 meters/minute ±0.2",
            "7. Calibrate position encoder at station EA10",
            "8. Inspect electrical connections in drive control panels",
            "9. Update CMMS with completion and oil analysis results",
            "",
            "QUARTERLY MAINTENANCE:",
            "1. Replace chain master links on drives #4, #9, #14",
            "2. Perform thermal imaging of all drive motors and control panels",
            "3. Replace air filters in drive control cabinets",
            "4. Test ground fault interrupters on all drives",
            "5. Inspect and clean limit switches at load/unload stations",
            "6. Verify safety gate interlocks functional (30 gate locations)",
            "7. Update conveyor component inventory in CMMS"
        ],
        "acceptance_criteria": [
            "All PM tasks completed per schedule (no overdue items)",
            "Chain tension within specification (50-75mm lift)",
            "Motor amperages balanced across drives (±2A variance)",
            "Oil analysis results show no abnormal wear metals",
            "Speed calibration within ±5% of target",
            "Zero unplanned conveyor stops since last PM",
            "CMMS updated with completion dates and technician signatures"
        ],
        "references": ["OEM Manual: FKI Logistex Overhead Conveyor", "PLANT-MAINT-STD-001"],
        "safety_notes": ["Lockout/tagout entire line before accessing conveyor", "Two-person minimum for work above 2 meters"]
    },
    {
        "id": "DOWNTIME-RESP-Hydraulic-Press-Failure",
        "title": "Downtime Response Playbook: Hydraulic Press Pump Failure",
        "doc_type": "downtime_pattern",
        "profile": "automotive_discrete",
        "station": "ST22",
        "revision": "A",
        "purpose": "To provide a structured troubleshooting guide for rapid diagnosis and resolution of hydraulic press pump failures at stamping line ST22, minimizing production downtime and scrap generation.",
        "scope": "Applies to 400-ton hydraulic press at station ST22, including main pump, accumulator, and hydraulic power unit. Covers failures resulting in loss of pressure or flow.",
        "procedure": [
            "IMMEDIATE ACTIONS (within 2 minutes):",
            "1. Operator presses EMERGENCY STOP button",
            "2. Andon light activates: maintenance technician dispatched automatically",
            "3. Supervisor opens downtime ticket in MES: Reason Code: EQUIP-HYDRAULIC",
            "4. Operator records: timestamp, current job number, symptom description",
            "",
            "INITIAL DIAGNOSIS (within 5 minutes):",
            "1. Maintenance technician arrives at station",
            "2. Interview operator: What happened? Any unusual noises? Gradual or sudden?",
            "3. Review HMI screen: check pressure gauge reading",
            "   - Normal operating pressure: 3000 PSI",
            "   - Low pressure alarm: <2500 PSI",
            "   - Loss of pressure: <1000 PSI",
            "4. Observe hydraulic power unit (HPU) for leaks or abnormal sounds",
            "5. Check hydraulic oil level in reservoir: should be at sight glass MAX",
            "",
            "TROUBLESHOOTING FLOWCHART:",
            "",
            "SYMPTOM: Pressure drops slowly over several cycles",
            "PROBABLE CAUSE: Internal seal wear",
            "DIAGNOSTIC TEST: Monitor pressure decay rate with press at top of stroke",
            "CORRECTIVE ACTION: Replace main cylinder seals (kit #HPU-SEAL-400)",
            "ESTIMATED DOWNTIME: 3 hours",
            "PARTS REQUIRED: Seal kit, hydraulic oil (20L)",
            "",
            "SYMPTOM: Pressure drops immediately, no build-up",
            "PROBABLE CAUSE: Pump failure or relief valve stuck open",
            "DIAGNOSTIC TEST: Listen to pump motor - if running but no pressure, pump failed",
            "CORRECTIVE ACTION: Replace hydraulic pump (P/N HYD-PUMP-VQ40)",
            "ESTIMATED DOWNTIME: 4 hours",
            "PARTS REQUIRED: Pump assembly, gaskets, oil",
            "",
            "SYMPTOM: Pressure normal but press won't cycle",
            "PROBABLE CAUSE: Solenoid valve failure",
            "DIAGNOSTIC TEST: Manually operate directional control valve",
            "CORRECTIVE ACTION: Replace solenoid coil (P/N SOL-24VDC-HYD)",
            "ESTIMATED DOWNTIME: 30 minutes",
            "PARTS REQUIRED: Solenoid coil",
            "",
            "SYMPTOM: Pump runs continuously, pressure erratic",
            "PROBABLE CAUSE: Accumulator bladder failure",
            "DIAGNOSTIC TEST: Feel accumulator shell - should be cool. Hot = failed bladder",
            "CORRECTIVE ACTION: Replace accumulator bladder (P/N ACC-BLADDER-10GAL)",
            "ESTIMATED DOWNTIME: 2 hours",
            "PARTS REQUIRED: Bladder, nitrogen charge kit",
            "",
            "REPAIR EXECUTION:",
            "1. Lockout/tagout hydraulic power unit and press main disconnect",
            "2. Depressurize hydraulic system: open manual dump valve",
            "3. Execute repair per maintenance manual section corresponding to failure",
            "4. Refill hydraulic oil if needed: use ISO VG 46 hydraulic oil only",
            "5. Bleed air from system: operate press at slow speed for 5 cycles",
            "6. Verify pressure stability: run 10 cycles with pressure gauge monitored",
            "7. Perform test stamp with scrap material",
            "8. If test successful, return to production and close downtime ticket",
            "9. Update CMMS with failure mode, root cause, and parts consumed"
        ],
        "acceptance_criteria": [
            "Diagnosis completed within 10 minutes of technician arrival",
            "Pressure restored to 3000 PSI ±100 PSI",
            "No leaks observed after repair",
            "Pressure remains stable over 20 production cycles",
            "First production part meets dimensional specification",
            "Downtime ticket closed with complete documentation",
            "Parts usage recorded in CMMS inventory"
        ],
        "references": ["HPU Manual: Bosch Rexroth A4VG Series", "PLANT-MAINT-STD-002"],
        "safety_notes": ["Never work on pressurized hydraulic system", "Hydraulic fluid injection injury requires immediate medical attention"]
    }
]

def generate_document(doc_data):
    """Generate a formatted document from template data."""
    lines = []
    
    # Header
    lines.append("=" * 80)
    lines.append(f"DOCUMENT ID: {doc_data['id']}")
    lines.append(f"REVISION: {doc_data['revision']}")
    lines.append(f"DATE: {datetime.now().strftime('%Y-%m-%d')}")
    lines.append("=" * 80)
    lines.append("")
    
    # Title
    lines.append(f"# {doc_data['title']}")
    lines.append("")
    
    # Metadata
    lines.append(f"**Document Type:** {doc_data['doc_type']}")
    lines.append(f"**Profile:** {doc_data['profile']}")
    if doc_data.get('station'):
        lines.append(f"**Station/Operation:** {doc_data['station']}")
    lines.append(f"**Revision:** {doc_data['revision']}")
    lines.append(f"**Effective Date:** {datetime.now().strftime('%Y-%m-%d')}")
    lines.append("")
    
    # Purpose
    lines.append("## 1. PURPOSE")
    lines.append("")
    lines.append(doc_data['purpose'])
    lines.append("")
    
    # Scope
    lines.append("## 2. SCOPE")
    lines.append("")
    lines.append(doc_data['scope'])
    lines.append("")
    
    # Procedure
    lines.append("## 3. PROCEDURE")
    lines.append("")
    if isinstance(doc_data['procedure'], list):
        for step in doc_data['procedure']:
            lines.append(step)
    else:
        lines.append(doc_data['procedure'])
    lines.append("")
    
    # Acceptance Criteria
    lines.append("## 4. ACCEPTANCE CRITERIA")
    lines.append("")
    for criteria in doc_data['acceptance_criteria']:
        lines.append(f"✓ {criteria}")
    lines.append("")
    
    # References
    if doc_data.get('references'):
        lines.append("## 5. REFERENCES")
        lines.append("")
        for ref in doc_data['references']:
            lines.append(f"- {ref}")
        lines.append("")
    
    # Safety Notes
    if doc_data.get('safety_notes'):
        lines.append("## 6. SAFETY NOTES")
        lines.append("")
        for note in doc_data['safety_notes']:
            lines.append(f"⚠️ {note}")
        lines.append("")
    
    # Footer
    lines.append("-" * 80)
    lines.append("END OF DOCUMENT")
    lines.append("-" * 80)
    
    return "\n".join(lines)

def generate_additional_documents():
    """Generate additional documents to reach 50-100 total."""
    additional_docs = []
    
    # Generate more A&D documents
    for i in range(10):
        additional_docs.append({
            "id": f"WI-OP{50+i}-Assembly",
            "title": f"Work Instruction: Final Assembly Operation {50+i}",
            "doc_type": "work_instruction",
            "profile": "aerospace_defence",
            "station": f"ST{50+i}",
            "revision": random.choice(["A", "B", "C"]),
            "purpose": f"To establish assembly procedures for critical flight hardware at Operation {50+i}, ensuring compliance with engineering drawings and AS9100 quality requirements.",
            "scope": f"Applies to assembly operations at ST{50+i} including hardware installation, torque verification, and final inspection per drawing AER-{5000+i}.",
            "procedure": [
                f"1. Verify component serial numbers match traveler document",
                f"2. Inspect all parts for damage or contamination",
                f"3. Apply thread locking compound per specification MS-{i}",
                f"4. Install hardware per torque sequence drawing",
                f"5. Torque fasteners to {20+i} ft-lbs ±{i%5} ft-lbs",
                f"6. Verify torque with calibrated wrench T-{200+i}",
                f"7. Apply witness marks to all critical fasteners",
                f"8. Photograph assembly for quality record",
                f"9. Update MES with completion status",
                f"10. Route to inspection station ST{51+i}"
            ],
            "acceptance_criteria": [
                "All fasteners torqued within specification",
                "Witness marks visible and properly aligned",
                "No cross-threading or damaged threads visible",
                "Digital photograph stored in quality system",
                "Serial number traceability maintained"
            ],
            "references": [f"AER-DWG-{5000+i}", "AS9100 Rev D"],
            "safety_notes": ["Wear safety glasses during assembly operations"]
        })
    
    # Generate more Pharma documents
    for i in range(10):
        additional_docs.append({
            "id": f"SOP-QC-TEST-{100+i}",
            "title": f"Standard Operating Procedure: Quality Control Test Method {100+i}",
            "doc_type": "sop",
            "profile": "pharma_process",
            "station": None,
            "revision": random.choice(["B", "C", "D"]),
            "purpose": f"To establish validated test method {100+i} for quality control testing of pharmaceutical products, ensuring compliance with USP monographs and GMP requirements.",
            "scope": f"Applies to QC testing of finished pharmaceutical products requiring test method ATM-{100+i}. Includes tablets, capsules, and oral solutions.",
            "procedure": [
                f"1. Prepare test sample per SOP-SAMPLING-00{i}",
                f"2. Perform identity test using IR spectroscopy",
                f"3. Prepare standard solution: {10+i}mg/mL in mobile phase",
                f"4. Prepare sample solution: dilute to match standard concentration",
                f"5. Inject standards in triplicate for system suitability",
                f"6. Verify RSD ≤2.0% for peak area",
                f"7. Inject sample solutions in triplicate",
                f"8. Calculate assay using external standard method",
                f"9. Acceptance: {95+i%5}.0% - {105-i%5}.0% of label claim",
                f"10. Enter results into LIMS within 24 hours"
            ],
            "acceptance_criteria": [
                "Standard RSD ≤2.0%",
                f"Assay within {95+i%5}.0% - {105-i%5}.0%",
                "System suitability criteria met",
                "All calculations verified by QC supervisor",
                "LIMS data entry complete with analyst signature"
            ],
            "references": [f"USP Monograph <{1000+i}>", "ICH Q2(R1)"],
            "safety_notes": [f"Wear lab coat and nitrile gloves when handling {['methanol', 'acetonitrile', 'buffer solutions'][i%3]}"]
        })
    
    # Generate more Automotive documents
    for i in range(10):
        additional_docs.append({
            "id": f"DOWNTIME-{i:03d}",
            "title": f"Downtime Response Playbook: {['Robot Fault', 'Vision System Error', 'PLC Communication Loss', 'Conveyor Jam', 'Part Feeder Empty'][i%5]}",
            "doc_type": "downtime_pattern",
            "profile": "automotive_discrete",
            "station": f"ST{30+i}",
            "revision": "A",
            "purpose": f"To provide rapid troubleshooting guide for {['robot', 'vision', 'PLC', 'conveyor', 'feeder'][i%5]} failures at station ST{30+i}, minimizing downtime impact on production throughput.",
            "scope": f"Applies to automated assembly station ST{30+i} on Line B including {['6-axis robot', 'Cognex vision system', 'Allen-Bradley PLC', 'belt conveyor', 'vibratory feeder'][i%5]}.",
            "procedure": [
                f"1. Operator presses E-STOP and calls maintenance",
                f"2. Technician arrives within 3 minutes",
                f"3. Check fault code on HMI: Code {1000+i}",
                f"4. Verify {['robot servo power', 'camera connection', 'network cable', 'photo-eye status', 'hopper level'][i%5]}",
                f"5. If fault clears: test run 5 cycles",
                f"6. If fault persists: escalate to L2 maintenance",
                f"7. Document failure mode and resolution in CMMS",
                f"8. Update downtime tracking: target <15 minutes MTTR"
            ],
            "acceptance_criteria": [
                "Fault cleared and root cause identified",
                "Five consecutive successful cycles completed",
                "Cycle time restored to target: {55+i} seconds",
                "CMMS updated with failure details",
                "Downtime <15 minutes from fault to production restart"
            ],
            "references": [f"{['Fanuc R-2000iB Manual', 'Cognex In-Sight Manual', 'Rockwell Logix Manual', 'Conveyor OEM Manual', 'Feeder Tech Guide'][i%5]}"],
            "safety_notes": ["Lockout/tagout required for robot access"]
        })
    
    return additional_docs

def main():
    """Main execution function."""
    print("=" * 80)
    print("MES-LIKE RAG CORPUS GENERATOR")
    print("Sprint 5 - Citation Discipline & Profile-Aware Knowledge Retrieval")
    print("=" * 80)
    print()
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Output directory: {OUTPUT_DIR}")
    
    # Combine all documents
    all_docs = (
        AEROSPACE_DEFENCE_DOCS +
        PHARMA_PROCESS_DOCS +
        AUTOMOTIVE_DISCRETE_DOCS +
        generate_additional_documents()
    )
    
    print(f"✓ Generated {len(all_docs)} total documents")
    print()
    
    # Generate documents by profile
    profile_counts = {}
    for doc_data in all_docs:
        profile = doc_data['profile']
        doc_type = doc_data['doc_type']
        
        # Track counts
        if profile not in profile_counts:
            profile_counts[profile] = {}
        if doc_type not in profile_counts[profile]:
            profile_counts[profile][doc_type] = 0
        profile_counts[profile][doc_type] += 1
        
        # Generate document content
        content = generate_document(doc_data)
        
        # Create profile subdirectory
        profile_dir = OUTPUT_DIR / profile
        profile_dir.mkdir(exist_ok=True)
        
        # Write document file
        filename = f"{doc_data['id']}.md"
        filepath = profile_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ Generated: {profile}/{filename}")
    
    # Summary
    print()
    print("=" * 80)
    print("GENERATION COMPLETE")
    print("=" * 80)
    print()
    print("Document Summary by Profile:")
    for profile, types in sorted(profile_counts.items()):
        total = sum(types.values())
        print(f"\n{profile.upper()} ({total} documents):")
        for doc_type, count in sorted(types.items()):
            print(f"  - {doc_type}: {count}")
    
    print()
    print(f"Total documents generated: {len(all_docs)}")
    print(f"Output directory: {OUTPUT_DIR.absolute()}")
    print()
    
    # Create metadata manifest
    manifest = {
        "generation_date": datetime.now().isoformat(),
        "total_documents": len(all_docs),
        "profiles": list(profile_counts.keys()),
        "documents": [
            {
                "id": doc["id"],
                "title": doc["title"],
                "doc_type": doc["doc_type"],
                "profile": doc["profile"],
                "station": doc.get("station"),
                "revision": doc["revision"]
            }
            for doc in all_docs
        ]
    }
    
    manifest_path = OUTPUT_DIR / "manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"✓ Manifest created: {manifest_path}")
    print()
    print("Next steps:")
    print("1. Review generated documents in data/documents/mes_corpus/")
    print("2. Run ingestion script to load into Chroma with metadata")
    print("3. Test profile-aware retrieval and citation discipline")


if __name__ == "__main__":
    main()
