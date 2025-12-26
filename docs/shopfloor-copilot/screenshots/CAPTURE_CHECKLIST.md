# Screenshot Capture Checklist
**Shopfloor Copilot & OPC Studio Documentation**  
**Date:** December 26, 2025  
**Version:** 0.3.1

## Pre-Capture Setup

### Environment Preparation
- [ ] Application running: `http://localhost:8010` OR `http://46.224.66.48:8010` (production)
- [ ] OPC Studio running: `http://localhost:8040` OR `http://46.224.66.48:8040` (production)
- [ ] Demo seed data loaded (if local) OR production stations available
- [ ] Browser: Chrome/Firefox (latest)
- [ ] Browser zoom: 100% (Ctrl+0)
- [ ] Window size: 1920x1080 or maximized
- [ ] Theme: **Dark mode enabled**
- [ ] Clear browser cache if needed

**📍 Deployment Mode:**
- **Local:** Use `localhost` endpoints above
- **Production (Hetzner):** Use `http://46.224.66.48:8010` and `http://46.224.66.48:8040`

### Test Stations Ready
- [ ] **ST18** - A&D blocking scenario (missing material)
- [ ] **ST25** - Pharma blocking scenario (missing deviation)  
- [ ] **ST17** - Happy path (no issues)

**⚠️ IMPORTANT:** Production OPC server has ST17 and ST18 only.
- **ST17**: Available for "happy path" screenshots
- **ST18**: Available for "blocking" screenshots
- ST25 and other stations may not exist in OPC but have material data

### Capture Tool
- [ ] Tool selected: Windows Snipping Tool (Win+Shift+S) or ShareX
- [ ] Save location: `C:\Users\Davide\VS-Code Solutions\rag-suite\docs\shopfloor-copilot\screenshots\`

---

## SECTION 1 — Landing & Navigation

### ✅ Screenshot 01 — Landing Page Overview
- **Filename:** `manual_01_landing_overview.png`
- **Profile:** aerospace_defence
- **Page:** Landing Page (http://localhost:8010)
- **Steps:**
  1. Navigate to Shopfloor Copilot home
  2. Ensure aerospace_defence profile is selected
  3. Verify dark theme visible
  4. Capture full window showing:
     - All dashboard tiles (KPI, Operations, etc.)
     - OPC Studio entry point
     - Navigation sidebar/menu
     - Profile indicator
- **Checklist:**
  - [ ] Dark theme visible
  - [ ] All tiles displayed
  - [ ] No loading spinners
  - [ ] Professional appearance
- **Status:** ⬜ Not captured | ✅ Captured

---

### ✅ Screenshot 02 — OPC Studio Entry Point
- **Filename:** `manual_02_opc_studio_overview.png`
- **Page:** OPC Studio main (http://localhost:8040 or http://46.224.66.48:8040)
- **Steps:**
  1. Navigate to OPC Studio dashboard
  2. **OPC Connection:**
     - **Local:** endpoint = `opc.tcp://opc-demo:4850`
     - **Production:** endpoint = `opc.tcp://46.224.66.48:4850` OR `opc.tcp://localhost:4850` (if SSH tunneled)
  3. Click "Connect" if not already connected
  4. Wait for connection status: Connected (green)
  5. Capture showing:
     - OPC Studio header/branding
     - Main features (Browse, Tags, Simulation)
     - Connection status indicator: Connected ✅
     - Distinct from Shopfloor Copilot
- **Checklist:**
  - [ ] Connection status: Connected
  - [ ] Dark theme
  - [ ] Clear separation from Diagnostics
  - [ ] Correct endpoint used (see troubleshooting if failed)
- **Status:** ⬜ Not captured | ✅ Captured

---

## SECTION 2 — Domain Profiles

### ✅ Screenshot 03 — Profile Selector
- **Filename:** `manual_03_profile_selector.png`
- **Page:** Profile selection dropdown/page
- **Steps:**
  1. Open profile selector (dropdown or settings)
  2. Ensure aerospace_defence is selected/highlighted
  3. Capture showing:
     - All available profiles (aerospace_defence, pharma_process, automotive_assembly)
     - Current selection highlighted
     - Profile descriptions (if visible)
- **Checklist:**
  - [ ] aerospace_defence clearly selected
  - [ ] Other profiles visible
  - [ ] Dropdown/selector open
- **Status:** ⬜ Not captured | ✅ Captured

---

## SECTION 3 — Semantic Snapshot

### ✅ Screenshot 04 — Semantic Runtime Snapshot
- **Filename:** `manual_05_semantic_snapshot.png`
- **Profile:** aerospace_defence
- **Station:** ST18
- **Page:** Diagnostics → Semantic Snapshot tab
- **Steps:**
  1. Select aerospace_defence profile
  2. Navigate to AI Diagnostics (Tab 17)
  3. Enter station: ST18
  4. Click "Explain this situation"
  5. Navigate to Semantic Snapshot section
  6. Capture showing:
     - Runtime state (BLOCKED/FAULTED)
     - Cycle time value
     - Good count = 0
     - Critical station indicator/badge
     - Semantic signals with colors
- **Checklist:**
  - [ ] Station: ST18 visible
  - [ ] Runtime state shown
  - [ ] Good count = 0
  - [ ] Critical indicator visible
- **Status:** ⬜ Not captured | ✅ Captured

---

## SECTION 4 — Material Evidence

### ✅ Screenshot 05 — Material Context Present (Healthy Operation)
- **Filename:** `manual_06_material_context_present.png`
- **Profile:** aerospace_defence
- **Station:** **ST17** (healthy station)
- **Page:** Diagnostics → Full explanation for healthy station
- **⚠️ IMPORTANT:** The UI does NOT have a dedicated "Material Evidence" section. Material context appears in the LLM-generated explanation text if relevant.
- **Steps:**
  1. Select aerospace_defence profile
  2. Navigate to AI Diagnostics (Tab 17)
  3. Enter station: **ST17**
  4. Click "Explain this situation"
  5. Review all 4 sections (What is happening, Why, What to do, What to check)
  6. Capture showing:
     - **No BLOCKING** indicators (green/healthy state)
     - Explanation describes normal operation
     - May mention material traceability if available (NOT required)
     - Professional, clean diagnostics view
- **Checklist:**
  - [ ] No BLOCKING/CRITICAL badges (healthy state)
  - [ ] Explanation shows normal operation
  - [ ] All 4 sections visible and populated
  - [ ] Professional appearance (dark theme)
- **Status:** ⬜ Not captured | ✅ Captured
- **Note:** If ST17 explanation mentions material evidence (serial numbers, quality status), that's a bonus but not required for this screenshot

---

### ✅ Screenshot 06 — Missing Material Evidence (CRITICAL)
- **Filename:** `manual_07_missing_material_evidence_ad.png`
- **Profile:** aerospace_defence
- **Station:** ST18 (blocking scenario)
- **Page:** Diagnostics → Explanation text mentioning material evidence
- **⚠️ IMPORTANT:** The UI does NOT have a dedicated "Material Evidence" section. Material context is internal to the backend and appears in the LLM-generated explanation text.
- **Steps:**
  1. Select aerospace_defence profile
  2. Navigate to AI Diagnostics (Tab 17)
  3. Enter station: ST18
  4. Click "Explain this situation"
  5. Expand **Section 1 — What is happening** (Runtime Evidence)
  6. Capture showing:
     - Explanation mentions **missing material evidence** or **missing serial number**
     - Text describes blocked/critical state
     - Material traceability issues mentioned
     - **BLOCKING** or **CRITICAL** indicators visible
- **Checklist:**
  - [ ] Explanation text mentions material evidence issues
  - [ ] BLOCKING or CRITICAL badge visible
  - [ ] Text references missing serial/traceability
  - [ ] Professional appearance (dark theme, clear text)
- **Status:** ⬜ Not captured | ✅ Captured
- **⚠️ CRITICAL:** This is the most important screenshot for A&D reviewers - focus on the explanation describing material evidence problems

---

## SECTION 5 — Diagnostics & Violations

### ✅ Screenshot 07 — Diagnostics with Blocking (A&D) - Full View
- **Filename:** `manual_08_diagnostics_blocking_ad.png`
- **Profile:** aerospace_defence
- **Station:** ST18
- **Page:** Diagnostics full view
- **⚠️ NOTE:** This is the SAME query as Screenshot 06, but captured differently:
  - **Screenshot 06** = Close crop of Section 1 text (material evidence details)
  - **Screenshot 07** = Full page view showing BLOCKING badge + all sections
- **Steps:**
  1. **Use the same ST18 query result from Screenshot 06** (no need to requery)
  2. Scroll to top to show full page layout
  3. Capture showing:
     - **BLOCKING** badge/indicator at top (if visible)
     - Equipment ID: ST18
     - All 4 sections visible (collapsed or expanded)
     - Metadata showing critical/blocked state
     - Overall diagnostics layout
- **Checklist:**
  - [ ] Full diagnostics layout visible
  - [ ] All 4 sections shown (can be collapsed)
  - [ ] Equipment ID ST18 clear
  - [ ] Dark theme consistent
- **Status:** ⬜ Not captured | ✅ Captured
- **TIP:** Capture this immediately after Screenshot 06 from the same screen

---

## SECTION 6 — Violations Management

### ✅ Screenshot 08 — Violations List
- **Filename:** `manual_09_violations_list.png`
- **Page:** Violations Management tab (Tab 18)
- **Steps:**
  1. Navigate to Violations tab
  2. Wait for active violations to load
  3. Capture showing:
     - List of violations (cards or table)
     - At least one OPEN or ACKNOWLEDGED violation
     - Severity indicators (Critical/Warning)
     - Station references (ST18, etc.)
     - State badges (OPEN, ACKNOWLEDGED, JUSTIFIED, RESOLVED)
     - Action buttons (View, Acknowledge, Justify, Resolve)
- **Checklist:**
  - [ ] Multiple violations visible
  - [ ] State badges clear (color-coded)
  - [ ] Severity indicators shown
  - [ ] Action buttons visible
  - [ ] Dark theme consistent
- **Status:** ⬜ Not captured | ✅ Captured

---

### ✅ Screenshot 09 — Violation Timeline
- **Filename:** `manual_10_violation_timeline.png`
- **Page:** Violations Management → Violation Details
- **Steps:**
  1. Navigate to Violations tab
  2. Click "View" on a JUSTIFIED or RESOLVED violation
  3. Timeline panel should appear on right side
  4. Capture showing:
     - Violation creation event
     - State transitions (OPEN → ACKNOWLEDGED → JUSTIFIED)
     - Timestamps for each event
     - Operator names (ack_by field)
     - Comments/justification text
     - Evidence references (if any)
- **Checklist:**
  - [ ] Timeline shows multiple states
  - [ ] Timestamps visible
  - [ ] Operator names shown
  - [ ] Comments/justification displayed
  - [ ] Clear progression path
- **Status:** ⬜ Not captured | ✅ Captured

---

## SECTION 7 — RAG & Explanations

### ✅ Screenshot 10 — Explanation with Citations
- **Filename:** `manual_11_rag_citations.png`
- **Profile:** aerospace_defence
- **Station:** ST18
- **Page:** Diagnostics → Explanation section
- **Steps:**
  1. Select aerospace_defence profile
  2. Navigate to AI Diagnostics
  3. Enter station: ST18
  4. Click "Explain this situation"
  5. Scroll to explanation text (usually Section 4 or main explanation)
  6. Capture showing:
     - AI-generated explanation text (paragraph)
     - At least 1 citation (numbered [1] or similar)
     - Citation details: Document name (WI-XXX, SOP-XXX)
     - Citations panel or section
     - Clean, readable formatting
- **Checklist:**
  - [ ] Explanation text visible
  - [ ] Citation markers [1], [2], etc.
  - [ ] Document names shown
  - [ ] Professional typography
- **Status:** ⬜ Not captured | ✅ Captured

---

## SECTION 8 — OPC Studio Core Features

### ✅ Screenshot 11 — OPC Browsing
- **Filename:** `manual_13_opc_browsing.png`
- **Filename:** `manual_13_opc_browsing.png`
- **Page:** OPC Studio → Browse tab
- **Steps:**
  1. Navigate to OPC Studio (http://46.224.66.48:8040)
  2. **Connect to OPC server** (if not connected): (if not connected):
     - **Local:** Use endpoint `opc.tcp://opc-demo:4850`
     - **Production:** Use endpoint `opc.tcp://46.224.66.48:4850`
     - Click "Connect" button
     - Wait for status: Connected ✅
  3. Expand namespace tree (Plant → Line → Station)
  4. Capture showing:
     - Server connection status: Connected (green)
     - Namespace tree visible (folders/nodes)
     - At least 2-3 levels expanded
     - Tag names visible
     - Node types (variable, object, etc.)
- **Checklist:**
  - [ ] Connection status: Connected
  - [ ] Tree expanded (not collapsed root)
  - [ ] Tag names readable
  - [ ] Dark theme
  - [ ] Correct endpoint used(variable, object, etc.)
- **Checklist:**
  - [ ] Connection status: Connected
  - [ ] Tree expanded (not collapsed root)
  - [ ] Tag names readable
  - [ ] Dark theme
- **Status:** ⬜ Not captured | ✅ Captured

---

### ✅ Screenshot 12 — Custom Tags
- **Filename:** `manual_14_custom_tags.png`
- **Page:** OPC Studio → Custom Tags configuration
- **Steps:**
  1. Navigate to OPC Studio custom tags section
  2. If no custom tags, create one: "TestTag" → semantic name
  3. Capture showing:
     - Custom tag definition form or list
     - Tag name (OPC path)
     - Semantic alias/name
     - Data type
     - Save/Apply button
- **Checklist:**
  - [ ] Custom tag visible
  - [ ] Semantic naming shown
  - [ ] Configuration UI clear
- **Status:** ⬜ Not captured | ✅ Captured

---

### ✅ Screenshot 13 — Simulation
- **Filename:** `manual_15_simulation.png`
- **Page:** OPC Studio → Simulation tab
- **Steps:**
  1. Navigate to OPC Studio simulation
  2. Start a simulation (line/station)
  3. Wait for values to update (few seconds)
  4. Capture showing:
     - Simulation controls (Start/Stop/Reset)
     - Simulated station/line indicator
     - Values changing (timestamps or live updates)
     - Status indicator (RUNNING, SIMULATED)
- **Checklist:**
  - [ ] Simulation active
  - [ ] Values visible
  - [ ] Control buttons shown
  - [ ] Station/line clearly indicated
- **Status:** ⬜ Not captured | ✅ Captured

---

## SECTION 9 — Demo Scenarios

### ✅ Screenshot 14 — Demo A&D Blocking
- **Filename:** `manual_16_demo_ad_blocking.png`
- **Scenario:** ST18 (A&D blocking)
- **Profile:** aerospace_defence
- **Page:** Full diagnostics view for ST18
- **Steps:**
  1. Select aerospace_defence profile
  2. Navigate to AI Diagnostics
  3. Enter station: ST18
  4. Click "Explain this situation"
  5. Capture full page showing:
     - BLOCKING badge
     - Material evidence missing
     - RAG explanation with citation
     - Violation indicator (if visible)
     - All sections visible (scroll to fit or capture longest section)
- **Checklist:**
  - [ ] BLOCKING visible
  - [ ] Citation present
  - [ ] Violation visible or referenced
  - [ ] Professional, complete view
- **Status:** ⬜ Not captured | ✅ Captured

---

### ✅ Screenshot 15 — Demo Pharma Blocking
- **Filename:** `manual_17_demo_pharma_blocking.png`
- **Profile:** pharma_process
- **Station:** ST25
- **Page:** Full diagnostics view for ST25
- **Steps:**
  1. **Switch profile to pharma_process** (critical!)
  2. Navigate to AI Diagnostics
  3. Enter station: ST25
  4. Click "Explain this situation"
  5. Capture full page showing:
     - **HOLD** status (pharma-specific)
     - Missing deviation approval
     - SOP citation (pharma work instruction)
     - Quality indicators
- **Checklist:**
  - [ ] Profile = pharma_process (verify UI shows this)
  - [ ] HOLD status visible
  - [ ] Deviation-related violation
  - [ ] SOP citation visible
- **Status:** ⬜ Not captured | ✅ Captured

---

### ✅ Screenshot 16 — Demo Happy Path
- **Filename:** `manual_18_demo_happy_path.png`
- **Profile:** aerospace_defence
- **Station:** **ST17** (healthy station)
- **Page:** Full diagnostics view for ST17
- **Steps:**
  1. Select aerospace_defence profile
  2. Navigate to AI Diagnostics
  3. Enter station: **ST17**
  4. Click "Explain this situation"
  5. Capture full page showing:
     - **No blocking** (green/success indicator)
     - Informational explanation (no warnings)
     - Clean, healthy state
     - Normal operation indicators
- **Checklist:**
  - [ ] No BLOCKING badge
  - [ ] No critical warnings
  - [ ] Positive/healthy indicators (green/blue colors)
  - [ ] Explanation shows normal operation
- **Status:** ⬜ Not captured | ✅ Captured
- **Note:** Material evidence may not be visible in production - focus on healthy operational state

---

## Post-Capture Verification

### File Check
Run verification script:
```powershell
.\verify_screenshots.ps1
```

Or manually verify:
- [ ] All 16 screenshots present
- [ ] Naming convention correct (`manual_XX_description.png`)
- [ ] File sizes reasonable (50KB - 2MB each)
- [ ] No duplicate filenames

### Quality Check
For each screenshot:
- [ ] Resolution: 1920x1080 or similar (not tiny)
- [ ] Theme: Dark mode consistent
- [ ] Text: Readable (no blur, no compression artifacts)
- [ ] Content: Matches specification exactly
- [ ] No personal data visible (if applicable)
- [ ] No browser UI clutter (tabs, bookmarks, etc.)

### Final Checklist
- [ ] **16/16 screenshots captured**
- [ ] **All filenames match specification**
- [ ] **Dark theme consistent across all**
- [ ] **Profiles correct (A&D primary, Pharma for ST25)**
- [ ] **No placeholder data visible**
- [ ] **Ready for STEP C (manual assembly)**
OPC connection failed - "opc.tcp://opc-demo:4850" doesn't work
**Cause:** `opc-demo` is Docker internal hostname, not accessible externally

**Solution - Use correct endpoint:**

**If accessing production (46.224.66.48):**
```
Endpoint: opc.tcp://46.224.66.48:4850
```

**If accessing locally (localhost:8010):**
```
Endpoint: opc.tcp://opc-demo:4850
OR
Endpoint: opc.tcp://localhost:4850
```

**Steps to fix:**
1. Navigate to OPC Explorer (Tab 15)
2. Look for endpoint/connection input field
3. Change from `opc.tcp://opc-demo:4850` to `opc.tcp://46.224.66.48:4850`
4. Click "Connect"
5. Wait for status: Connected ✅

**If still failing:**
```powershell
# Check if OPC server is running
curl http://46.224.66.48:4850

# Or via OPC Studio health check
curl http://46.224.66.48:8040/status

# Expected: {"status": "ok", "opc_connected": true}
```

### Problem: Application not running
```powershell
# Start services (local)
docker-compose up -d

# Check status
docker-compose ps

# For production, verify services running
curl http://46.224.66.48:8010/health
curl http://46.224.66.48:8040/status
```

### Problem: Can't find OPC endpoint configuration in UI
**Solution:**

**Option 1: Check environment variable (backend)**
```powershell
# For production deployment
ssh root@46.224.66.48
cd /root/rag-suite
cat .env | grep OPC_DEMO_ENDPOINT

# Should show: OPC_DEMO_ENDPOINT=opc.tcp://46.224.66.48:4850
```

**Option 2: OPC Explorer may auto-detect**
- Some implementations have endpoint pre-configured
- Just click "Connect" button without entering endpoint
- Check connection status turns green

**Option 3: Configure in OPC Studio settings**
- Look for Settings/Configuration tab
- Find "OPC Server Endpoint" field
- Enter: `opc.tcp://46.224.66.48:4850Check status
docker-composSpecific stations (ST10, ST18, ST25) don't exist
**Solution:**
```powershell
# Find available stations in your deployment
# Method 1: Via OPC Explorer
1. Navigate to Tab 15: OPC Explorer
2. Connect to OPC server
3. Browse: Root → Plant → Line → Stations
4. Note station IDs visible (e.g., ST01, ST02, ST20, etc.)

# Method 2: Via API
curl http://46.224.66.48:8040/opc/browse/stations
```

**Alternative Station Selection:**
- **Happy Path (ST10 replacement):** Use any station with state=RUNNING, no faults
- **Blocking Path (ST18 replacement):** Use any station with state=BLOCKED or FAULTED
- **Pharma Path (ST25 replacement):** Switch to pharma_process profile, use any blocked station

### Problem: Demo data missing
```bash
# If running locally, re-run seed script
python scripts/seed_demo_data.py

# For production deployment at 46.224.66.48
# Demo data may not be available - use real stations instead
```

### Problem: Material Evidence section not showing
**Cause:** Material context data not seeded in database

**Solution - Seed the database:**
```powershell
# For production (Hetzner)
ssh root@46.224.66.48
cd /opt/shopfloor/rag-suite
docker exec shopfloor-copilot python scripts/seed_demo_material_data.py

# For local development
python scripts/seed_demo_material_data.py
```

**Expected output:**
```
✓ ST18 (A&D): No serial → BLOCKING
✓ ST25 (Pharma): HOLD without deviation → BLOCKING  
✓ ST10 (Normal): SN-100234, all OK → NO VIOLATIONS
```

**After seeding:**
- **ST10** will show: Serial SN-100234, RELEASED, all evidence OK
- **ST18** will show: Missing serial, no tooling, no operator → BLOCKING
- **ST25** will show: LOT-2025-0042 in HOLD status → BLOCKING

### Problem: Demo data missing
```bash
# Re-run seed script
python scripts/seed_demo_data.py
```

### Problem: Screenshots too large
```powershell
# Compress all screenshots (lossless)
Get-ChildItem *.png | ForEach-Object {
    magick $_.Name -quality 85 -resize 1920x1080\> $_.Name
}
```

### Problem: Dark theme not showing
- Check Settings → Appearance → Theme: Dark
- Clear browser cache (Ctrl+Shift+Delete)
- Try incognito mode

---

## Next Steps

After completing this checklist:
1. Run `verify_screenshots.ps1` to confirm all files present
2. Review each screenshot for quality
3. Proceed to **STEP C** (manual assembly)
4. Use screenshots in documentation chapters as placeholders are replaced

**Estimated Time:** 45-60 minutes for all 16 screenshots

---

**Capture Date:** _______________  
**Captured By:** _______________  
**Verified By:** _______________
