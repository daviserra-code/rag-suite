# Chapter 5: Semantic Mapping Engine

## Overview

The Semantic Mapping Engine (Sprint 2) transforms raw OPC UA signals into meaningful, contextualized data with **loss category classification**. Think of it as "Kepware KEPServerEX for Industrial AI" - it bridges the gap between raw PLC data and intelligent analytics.

### What It Does

**Before Semantic Mapping:**
```json
{
  "NodeId": "ns=2;s=TORINO.A01.ST18.Speed",
  "Value": 0,
  "StatusCode": "Good"
}
```

**After Semantic Mapping:**
```json
{
  "signal_key": "station.speed_actual",
  "value": 0,
  "unit": "%",
  "loss_category": "performance.reduced_speed",
  "severity": "warning",
  "description": "Motor speed significantly below target"
}
```

### Key Benefits

1. **Automatic Loss Classification:** Signals tagged with ISO 22400 categories
2. **Station-Type Awareness:** Same mapping rules for all assembly stations
3. **Engineering Units:** Converts raw values to meaningful units (%, °C, parts/hr)
4. **Alarm Context:** Explains why a signal is problematic
5. **AI-Ready:** Structured data perfect for LLM diagnostics

---

## Architecture

```
┌─────────────────┐
│  OPC UA Server  │ (raw PLC signals)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  OPC Studio     │ (read OPC nodes)
│  /snapshot      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Semantic Engine │ (YAML-based transformer)
│   - Load YAML   │
│   - Match rules │
│   - Classify    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Semantic Signal │ (enriched output)
│ + loss_category │
│ + severity      │
└─────────────────┘
```

---

## The YAML Configuration

### File Location

```
opc-studio/config/semantic_mappings.yaml
```

### Structure Overview

```yaml
version: "1.0"
loss_categories:
  # 19 ISO 22400-based categories
  
station_types:
  assembly:
    # Rules for assembly stations
  testing:
    # Rules for testing stations
  packaging:
    # Rules for packaging stations
  
station_assignments:
  # Map station IDs to types
```

### Full Configuration Example

```yaml
version: "1.0"

# ========================================
# LOSS CATEGORIES (ISO 22400 + Extensions)
# ========================================
loss_categories:
  # AVAILABILITY LOSSES (Station Down)
  - id: availability.equipment_failure
    name: Equipment Failure
    description: Mechanical or electrical breakdown
    category: availability
    severity: critical
    
  - id: availability.upstream_starvation
    name: Upstream Starvation
    description: Waiting for parts from previous station
    category: availability
    severity: warning
    
  - id: availability.downstream_blocking
    name: Downstream Blocking
    description: Cannot output parts, next station full
    category: availability
    severity: warning
    
  # PERFORMANCE LOSSES (Running Slow)
  - id: performance.reduced_speed
    name: Reduced Speed
    description: Running below target cycle time
    category: performance
    severity: warning
    
  - id: performance.minor_stops
    name: Minor Stops
    description: Frequent short interruptions
    category: performance
    severity: warning
    
  # QUALITY LOSSES (Making Bad Parts)
  - id: quality.process_defect
    name: Process Defect
    description: Parts failing quality checks
    category: quality
    severity: critical
    
  - id: quality.reduced_yield
    name: Reduced Yield
    description: Lower than expected good output
    category: quality
    severity: warning
    
  # NON-PRODUCTIVE TIME (Planned)
  - id: non_productive.changeover
    name: Changeover
    description: Product or tool changeover
    category: non_productive
    severity: info
    
  - id: non_productive.planned_maintenance
    name: Planned Maintenance
    description: Scheduled preventive maintenance
    category: non_productive
    severity: info

# ========================================
# STATION TYPES (Mapping Rules)
# ========================================
station_types:
  assembly:
    description: "Motor or component assembly stations"
    signals:
      - key: station.state
        opc_pattern: "Status"
        type: string
        unit: null
        loss_mapping:
          - condition: value == "FAULTED"
            loss_category: availability.equipment_failure
          - condition: value == "STARVED"
            loss_category: availability.upstream_starvation
          - condition: value == "BLOCKED"
            loss_category: availability.downstream_blocking
            
      - key: station.speed_actual
        opc_pattern: "Speed"
        type: numeric
        unit: "%"
        loss_mapping:
          - condition: value < 10
            loss_category: performance.reduced_speed
          - condition: value < 50
            loss_category: performance.minor_stops
            
      - key: station.temperature
        opc_pattern: "Temperature"
        type: numeric
        unit: "°C"
        loss_mapping:
          - condition: value > 85
            loss_category: performance.reduced_speed
            description: "Overheating causing slowdown"
            
      - key: production.cycle_time
        opc_pattern: "CycleTime"
        type: numeric
        unit: "seconds"
        loss_mapping:
          - condition: value > 60
            loss_category: performance.reduced_speed
            
      - key: production.good_count
        opc_pattern: "GoodCount"
        type: numeric
        unit: "parts"
        loss_mapping: []
        
      - key: production.scrap_count
        opc_pattern: "ScrapCount"
        type: numeric
        unit: "parts"
        loss_mapping:
          - condition: value > 5
            loss_category: quality.process_defect
            
  testing:
    description: "Quality testing and inspection stations"
    signals:
      - key: station.state
        opc_pattern: "Status"
        type: string
        unit: null
        loss_mapping:
          - condition: value == "FAULTED"
            loss_category: availability.equipment_failure
            
      - key: quality.test_result
        opc_pattern: "TestResult"
        type: string
        unit: null
        loss_mapping:
          - condition: value == "FAIL"
            loss_category: quality.process_defect
            
      - key: quality.score
        opc_pattern: "QualityScore"
        type: numeric
        unit: "%"
        loss_mapping:
          - condition: value < 95
            loss_category: quality.reduced_yield
            
      - key: production.cycle_time
        opc_pattern: "CycleTime"
        type: numeric
        unit: "seconds"
        loss_mapping:
          - condition: value > 45
            loss_category: performance.reduced_speed

# ========================================
# STATION ASSIGNMENTS (ID → Type Mapping)
# ========================================
station_assignments:
  ST17: assembly
  ST18: assembly
  ST19: assembly
  ST20: testing
  ST21: assembly
  ST22: assembly
```

---

## How Mapping Works

### Step 1: OPC Node Matching

Engine reads OPC snapshot:

```json
{
  "NodeId": "ns=2;s=TORINO.A01.ST18.Speed",
  "Value": 0
}
```

Matches against `opc_pattern`:
- Pattern: `"Speed"`
- Match: ✅ "ST18.**Speed**" contains "Speed"

### Step 2: Signal Key Assignment

Maps to semantic key:
- Pattern matched: `Speed`
- Signal definition: `key: station.speed_actual`
- Result: Signal labeled `station.speed_actual`

### Step 3: Loss Category Evaluation

Evaluates conditions in `loss_mapping`:

```yaml
loss_mapping:
  - condition: value < 10  # ✅ 0 < 10
    loss_category: performance.reduced_speed
```

**Result:**
```json
{
  "signal_key": "station.speed_actual",
  "value": 0,
  "loss_category": "performance.reduced_speed",
  "severity": "warning"
}
```

### Step 4: Output Formatting

Final semantic signal:

```json
{
  "signal_key": "station.speed_actual",
  "value": 0,
  "unit": "%",
  "opc_node_id": "ns=2;s=TORINO.A01.ST18.Speed",
  "loss_category": "performance.reduced_speed",
  "severity": "warning",
  "description": "Motor speed significantly below target",
  "timestamp": "2025-01-15T14:32:18Z"
}
```

---

## Tutorial: Adding a New Station Type

### Scenario: Add "Packaging" Stations

**Goal:** Create mappings for packaging stations (ST30-ST35) with specific loss rules.

#### Step 1: Define Loss Categories (If New)

If your packaging stations have unique losses:

```yaml
loss_categories:
  # ... existing categories ...
  
  - id: availability.label_printer_jam
    name: Label Printer Jam
    description: Label printer paper jam or ribbon issue
    category: availability
    severity: critical
    
  - id: quality.seal_failure
    name: Seal Failure
    description: Package seal quality below threshold
    category: quality
    severity: critical
```

#### Step 2: Define Station Type

Add under `station_types`:

```yaml
station_types:
  # ... existing types ...
  
  packaging:
    description: "Product packaging and labeling stations"
    signals:
      - key: station.state
        opc_pattern: "Status"
        type: string
        unit: null
        loss_mapping:
          - condition: value == "FAULTED"
            loss_category: availability.equipment_failure
          - condition: value == "LABEL_JAM"
            loss_category: availability.label_printer_jam
          - condition: value == "STARVED"
            loss_category: availability.upstream_starvation
            
      - key: packaging.seal_pressure
        opc_pattern: "SealPressure"
        type: numeric
        unit: "bar"
        loss_mapping:
          - condition: value < 3.5
            loss_category: quality.seal_failure
            description: "Seal pressure below minimum"
            
      - key: packaging.label_applied
        opc_pattern: "LabelApplied"
        type: boolean
        unit: null
        loss_mapping:
          - condition: value == false
            loss_category: quality.process_defect
            description: "Label not properly applied"
            
      - key: production.throughput
        opc_pattern: "PackagesPerHour"
        type: numeric
        unit: "packages/hour"
        loss_mapping:
          - condition: value < 200
            loss_category: performance.reduced_speed
```

#### Step 3: Assign Station IDs

Add station assignments:

```yaml
station_assignments:
  # ... existing assignments ...
  ST30: packaging
  ST31: packaging
  ST32: packaging
  ST33: packaging
  ST34: packaging
  ST35: packaging
```

#### Step 4: Restart OPC Studio

```bash
docker-compose restart opc-studio

# Verify YAML is valid
docker-compose logs opc-studio --tail=20
# Should see: "Loaded semantic mappings: 3 station types, 45 assignments"
```

#### Step 5: Test New Mappings

1. Go to **Tab 16: Semantic Signals**
2. Enter Line ID: `C01` (or wherever ST30 is)
3. Enter Station ID: `ST30`
4. Click **Load Semantic Signals**
5. Verify new signals appear with correct loss categories

---

## Advanced Mapping Techniques

### Conditional Logic with Multiple Rules

**Scenario:** Speed warnings should escalate based on severity.

```yaml
- key: station.speed_actual
  opc_pattern: "Speed"
  type: numeric
  unit: "%"
  loss_mapping:
    - condition: value == 0
      loss_category: availability.equipment_failure
      description: "Complete stop - equipment failure"
    - condition: value > 0 AND value < 30
      loss_category: performance.reduced_speed
      description: "Severely reduced speed"
    - condition: value >= 30 AND value < 70
      loss_category: performance.minor_stops
      description: "Moderately reduced speed"
```

**Note:** Conditions evaluated top-to-bottom. First match wins.

### Derived Signals (Calculated)

**Scenario:** Calculate OEE components from raw signals.

```yaml
- key: oee.availability
  opc_pattern: "AvailabilityPercent"
  type: numeric
  unit: "%"
  loss_mapping:
    - condition: value < 85
      loss_category: availability.equipment_failure
      description: "Availability below target (85%)"
      
- key: oee.performance
  opc_pattern: "PerformancePercent"
  type: numeric
  unit: "%"
  loss_mapping:
    - condition: value < 90
      loss_category: performance.reduced_speed
      description: "Performance below target (90%)"
      
- key: oee.quality
  opc_pattern: "QualityPercent"
  type: numeric
  unit: "%"
  loss_mapping:
    - condition: value < 98
      loss_category: quality.reduced_yield
      description: "Quality below target (98%)"
```

### Time-Based Conditions (Future Enhancement)

**Scenario:** Trigger loss only if condition persists.

```yaml
- key: station.temperature
  opc_pattern: "Temperature"
  type: numeric
  unit: "°C"
  loss_mapping:
    - condition: value > 85 FOR 300 seconds
      loss_category: performance.reduced_speed
      description: "Sustained overheating"
```

*(Not yet implemented - roadmap feature)*

---

## Loss Category Best Practices

### DO's ✅

1. **Use ISO 22400 Categories When Possible**
   - Ensures standardization across industry
   - Easier to compare with benchmarks

2. **Be Specific with Custom Categories**
   - ❌ `custom.problem`
   - ✅ `availability.label_printer_jam`

3. **Assign Appropriate Severity**
   - **critical:** Stops production entirely
   - **warning:** Reduces output or quality
   - **info:** Planned events (changeover, maintenance)

4. **Provide Clear Descriptions**
   - Operators must understand what it means
   - Include recommended action if possible

5. **Test on Real Data**
   - Load semantic signals for all stations
   - Verify loss categories match actual conditions

### DON'Ts ❌

1. **Don't Over-Classify**
   - Not every signal needs a loss category
   - Only classify problematic states

2. **Don't Use Overlapping Conditions**
   - ❌ `value < 50` AND `value < 30` (ambiguous)
   - ✅ `value < 30` then `value < 50`

3. **Don't Hardcode Station-Specific Logic**
   - Use station types, not individual IDs
   - Exception: Truly unique stations

4. **Don't Ignore Units**
   - Always specify: `%`, `°C`, `bar`, `parts/hour`
   - Helps AI understand magnitude

---

## API Reference

### GET /semantic/{scope}/{id}

**Description:** Get semantic signals for a station or line.

**Parameters:**
- `scope`: `station` or `line`
- `id`: Station ID (ST18) or Line ID (A01)

**Example Request:**
```bash
curl http://localhost:8040/semantic/station/ST18 | jq
```

**Example Response:**
```json
{
  "scope": "station",
  "id": "ST18",
  "station_type": "assembly",
  "signals": [
    {
      "signal_key": "station.state",
      "value": "RUNNING",
      "loss_category": null,
      "severity": null
    },
    {
      "signal_key": "station.speed_actual",
      "value": 0,
      "unit": "%",
      "loss_category": "performance.reduced_speed",
      "severity": "warning",
      "description": "Motor speed significantly below target"
    }
  ],
  "timestamp": "2025-01-15T14:32:18Z"
}
```

### GET /semantic/mappings

**Description:** Get loaded YAML configuration.

**Example Request:**
```bash
curl http://localhost:8040/semantic/mappings | jq
```

**Example Response:**
```json
{
  "version": "1.0",
  "station_types": ["assembly", "testing", "packaging"],
  "loss_categories_count": 19,
  "station_assignments_count": 45
}
```

---

## Troubleshooting

### Problem: Signals Show "generic" Instead of Station Type

**Symptom:**
```json
{
  "station_type": "generic",
  "signals": [...]
}
```

**Cause:** Station ID not found in `station_assignments`.

**Solution:**
1. Edit `opc-studio/config/semantic_mappings.yaml`
2. Add station assignment:
   ```yaml
   station_assignments:
     ST99: assembly  # Add your station
   ```
3. Restart OPC Studio:
   ```bash
   docker-compose restart opc-studio
   ```

### Problem: Loss Category Not Appearing

**Symptom:** Signal has no `loss_category` field even though value matches condition.

**Cause:** Condition syntax error or type mismatch.

**Solution:**
1. Check condition syntax:
   - ✅ `value < 10`
   - ❌ `value less than 10`
2. Verify type matches:
   - Numeric signal: Use `value < 10`
   - String signal: Use `value == "FAULTED"`
3. Check YAML indentation (must be exact)
4. View logs:
   ```bash
   docker-compose logs opc-studio | grep "Mapping error"
   ```

### Problem: Wrong Loss Category Assigned

**Symptom:** Signal has `performance.reduced_speed` but should be `availability.equipment_failure`.

**Cause:** Condition order - first match wins.

**Solution:**
Reorder conditions (most specific first):
```yaml
loss_mapping:
  - condition: value == 0  # Most specific
    loss_category: availability.equipment_failure
  - condition: value < 30  # Less specific
    loss_category: performance.reduced_speed
```

### Problem: YAML Syntax Error

**Symptom:** OPC Studio fails to start, logs show `YAML parse error`.

**Cause:** Invalid YAML syntax (indentation, quotes, etc.).

**Solution:**
1. Validate YAML online: https://www.yamllint.com/
2. Check common issues:
   - Consistent indentation (2 spaces, not tabs)
   - Quoted strings with special chars: `"value: \"test\""`
   - No trailing spaces
3. View exact error:
   ```bash
   docker-compose logs opc-studio --tail=50
   ```

---

## Integration with AI Diagnostics

The Semantic Engine is critical for AI Diagnostics (Sprint 3). Here's how they connect:

### 1. Semantic Signals → Diagnostic Input

AI Diagnostics calls:
```
GET /semantic/station/ST18
```

Gets enriched signals with loss categories:
```json
{
  "station.speed_actual": {
    "value": 0,
    "loss_category": "performance.reduced_speed"
  }
}
```

### 2. Loss Categories → Section 1 (Evidence)

In diagnostic output:
```
Section 1 - What is happening:
Station ST18 is RUNNING with 0% speed, classified as 
performance.reduced_speed.
```

The loss category **prevents hallucination** - AI can only reference categories present in semantic data.

### 3. Severity → Prioritization

AI uses severity to prioritize issues:
```yaml
- critical: Mention first, highest urgency
- warning: Mention second, moderate urgency
- info: Mention last, low urgency
```

### 4. Description → Natural Language

YAML descriptions become AI explanations:
```yaml
description: "Motor speed significantly below target"
```

Becomes:
```
The motor is not reaching expected speed, indicating 
a drive or mechanical issue.
```

---

## Performance Considerations

### Caching Strategies

**YAML Load:** Cached in memory at startup (not reloaded per request)

**Semantic Transform:** Computed per request (no caching)

**Recommendation:** For high-frequency polling (>1 Hz), consider:
1. Pre-compute semantic signals for all stations
2. Cache results for 1-5 seconds
3. Update only on OPC value change

### Scalability

**Current Capacity:**
- 100 stations: < 50ms per semantic request
- 500 stations: < 200ms per semantic request

**Bottleneck:** OPC snapshot fetch (not semantic mapping)

**Optimization:** Use line-level snapshots to get all stations in one request.

---

## Future Enhancements

**Roadmap for Sprint 4+:**

1. **Conditional Time Delays**
   ```yaml
   condition: value > 85 FOR 300 seconds
   ```

2. **Multi-Signal Correlations**
   ```yaml
   condition: station.speed < 10 AND station.temperature > 80
   ```

3. **Dynamic Thresholds**
   ```yaml
   condition: value < station.speed_target * 0.5
   ```

4. **Historical Context**
   ```yaml
   condition: value DECREASED_BY 50% IN LAST 60 seconds
   ```

5. **Machine Learning Rules**
   - Auto-generate mappings from historical data
   - Anomaly-based loss detection

---

**Next Chapter:** [Loss Categories Reference →](06-loss-categories.md)

**Previous Chapter:** [← OPC Explorer](04-opc-explorer.md)
