# Chapter 6: Loss Categories Reference

**ISO 22400 + Custom Extensions**

This chapter provides complete reference documentation for all 19 loss categories used in Shopfloor Copilot's Semantic Mapping Engine.

---

## Overview

Loss categories classify **why production is lost** according to international standards and industry best practices. They enable:

1. **Accurate OEE Calculation** - Separate availability, performance, quality losses
2. **Root Cause Analysis** - Understand what's really causing production loss
3. **AI Diagnostics** - Provide context for intelligent recommendations
4. **Trend Analysis** - Track improvement over time

### The Three Pillars of OEE

```
OEE = Availability × Performance × Quality

Availability = (Operating Time) / (Planned Production Time)
Performance = (Actual Output) / (Maximum Possible Output)
Quality = (Good Parts) / (Total Parts)
```

Each loss category impacts one of these three pillars.

---

## Loss Category Hierarchy

```
Loss Categories (19 total)
├── Availability Losses (7) - Station Down
│   ├── Equipment Failure
│   ├── Setup/Changeover (Unplanned)
│   ├── Upstream Starvation
│   ├── Downstream Blocking
│   ├── Operator Absence
│   ├── Material Shortage
│   └── Tool/Die Change
│
├── Performance Losses (6) - Running Slow
│   ├── Reduced Speed
│   ├── Minor Stops
│   ├── Idling
│   ├── Warm-up
│   ├── Cleaning
│   └── Adjustment
│
├── Quality Losses (3) - Making Bad Parts
│   ├── Process Defect
│   ├── Reduced Yield
│   └── Startup Scrap
│
└── Non-Productive Time (3) - Planned
    ├── Planned Maintenance
    ├── Changeover (Planned)
    └── No Orders
```

---

## Availability Losses

**Definition:** Time when station is **supposed to be running** but is **stopped**.

### 1. availability.equipment_failure

**Name:** Equipment Failure  
**Severity:** 🔴 Critical  
**ISO 22400 Code:** 6.3.1

**Description:**
Mechanical or electrical breakdown requiring repair. Station is completely stopped and cannot produce.

**Examples:**
- Motor burned out
- Pneumatic cylinder failure
- PLC communication lost
- Sensor malfunction
- Hydraulic leak

**Typical Conditions:**
```yaml
- condition: value == "FAULTED"
  loss_category: availability.equipment_failure
- condition: value == "ERROR"
  loss_category: availability.equipment_failure
```

**Impact on OEE:**
```
Availability ↓↓↓  (large impact)
Performance: —
Quality: —
```

**Resolution Time:** Minutes to days (depending on severity)

**MTTR Target:** < 2 hours

---

### 2. availability.upstream_starvation

**Name:** Upstream Starvation  
**Severity:** 🟡 Warning  
**ISO 22400 Code:** 6.3.4

**Description:**
Station is idle because **previous station** is not supplying parts fast enough. This is a dependency issue, not a fault at this station.

**Examples:**
- Buffer empty waiting for upstream parts
- Previous station is down
- Conveyor stopped upstream
- Parts stuck in transit

**Typical Conditions:**
```yaml
- condition: value == "STARVED"
  loss_category: availability.upstream_starvation
- condition: buffer_level < 5 AND state == "IDLE"
  loss_category: availability.upstream_starvation
```

**Impact on OEE:**
```
Availability ↓  (affects this station's availability)
Performance: —
Quality: —
```

**Resolution:** Fix upstream bottleneck

**Key Insight:** If multiple stations show this, identify the root cause upstream (usually a single bottleneck station).

---

### 3. availability.downstream_blocking

**Name:** Downstream Blocking  
**Severity:** 🟡 Warning  
**ISO 22400 Code:** 6.3.5

**Description:**
Station is idle because **next station** cannot accept output. Output buffer is full.

**Examples:**
- Output conveyor full
- Next station is down
- Accumulation table full
- Packaging line backed up

**Typical Conditions:**
```yaml
- condition: value == "BLOCKED"
  loss_category: availability.downstream_blocking
- condition: buffer_level > 95 AND state == "WAITING"
  loss_category: availability.downstream_blocking
```

**Impact on OEE:**
```
Availability ↓  (affects this station's availability)
Performance: —
Quality: —
```

**Resolution:** Clear downstream blockage or speed up downstream station

---

### 4. availability.material_shortage

**Name:** Material Shortage  
**Severity:** 🔴 Critical  
**ISO 22400 Code:** 6.3.3

**Description:**
Required raw materials, components, or consumables are not available.

**Examples:**
- Raw material bin empty
- Component feeder out of stock
- Consumable (grease, labels, etc.) depleted
- Wrong material loaded

**Typical Conditions:**
```yaml
- condition: material_level < 5
  loss_category: availability.material_shortage
- condition: state == "WAITING_MATERIAL"
  loss_category: availability.material_shortage
```

**Impact on OEE:**
```
Availability ↓↓  (large impact if prolonged)
Performance: —
Quality: —
```

**Prevention:** Implement Kanban, min/max inventory levels, automated alerts

---

### 5. availability.setup_changeover

**Name:** Setup/Changeover (Unplanned)  
**Severity:** 🟡 Warning  
**ISO 22400 Code:** 6.3.2

**Description:**
Unplanned tool change, product changeover, or adjustment required during production.

**Examples:**
- Emergency tool change due to wear
- Unscheduled product switch
- Unexpected calibration needed
- Format adjustment

**Typical Conditions:**
```yaml
- condition: state == "CHANGEOVER" AND planned == false
  loss_category: availability.setup_changeover
```

**Impact on OEE:**
```
Availability ↓  (usually brief)
Performance: —
Quality: —
```

**Improvement:** Move to planned changeovers, use SMED techniques

---

### 6. availability.operator_absence

**Name:** Operator Absence  
**Severity:** 🟠 Moderate  
**ISO 22400 Code:** 6.3.6

**Description:**
Station is idle because operator is not present (break, meeting, restroom, etc.).

**Examples:**
- Operator on break (unscheduled)
- Operator attending to different station
- Operator called to meeting
- Restroom break

**Typical Conditions:**
```yaml
- condition: state == "WAITING_OPERATOR"
  loss_category: availability.operator_absence
```

**Impact on OEE:**
```
Availability ↓  (brief impact)
Performance: —
Quality: —
```

**Improvement:** Multi-skill operators, better break scheduling

---

### 7. availability.tool_die_change

**Name:** Tool/Die Change  
**Severity:** 🟡 Warning  
**ISO 22400 Code:** 6.3.7

**Description:**
Production stopped for tool or die replacement due to wear or breakage.

**Examples:**
- Cutting tool worn out
- Drill bit broken
- Die needs replacement
- Mold change

**Typical Conditions:**
```yaml
- condition: tool_life < 5 AND state == "STOPPED"
  loss_category: availability.tool_die_change
```

**Impact on OEE:**
```
Availability ↓  (predictable if tracked)
Performance: —
Quality: —
```

**Improvement:** Predictive tool life monitoring, pre-staging tools

---

## Performance Losses

**Definition:** Station is **running** but producing **slower than maximum capacity**.

### 8. performance.reduced_speed

**Name:** Reduced Speed  
**Severity:** 🟡 Warning  
**ISO 22400 Code:** 6.4.1

**Description:**
Station running below target cycle time or speed. Output is reduced but not stopped.

**Examples:**
- Motor running at 50% speed
- Conveyor slowed down
- Cycle time 60s instead of 40s
- Throughput 80 parts/hr instead of 120

**Typical Conditions:**
```yaml
- condition: speed < 70
  loss_category: performance.reduced_speed
- condition: cycle_time > target_cycle_time * 1.2
  loss_category: performance.reduced_speed
```

**Impact on OEE:**
```
Availability: —
Performance ↓↓  (large impact)
Quality: —
```

**Causes:** Mechanical wear, control system detuning, operator overcaution

---

### 9. performance.minor_stops

**Name:** Minor Stops  
**Severity:** 🟡 Warning  
**ISO 22400 Code:** 6.4.2

**Description:**
Frequent short stops (< 5 minutes each) that disrupt production flow.

**Examples:**
- Part jams cleared quickly
- Sensor triggers brief stops
- Momentary blockages
- Quick resets

**Typical Conditions:**
```yaml
- condition: stop_count_per_hour > 10
  loss_category: performance.minor_stops
- condition: state == "PAUSED" AND duration < 300
  loss_category: performance.minor_stops
```

**Impact on OEE:**
```
Availability: — (stops too short to count)
Performance ↓  (cumulative effect)
Quality: —
```

**Improvement:** Identify repetitive patterns, fix root causes

---

### 10. performance.idling

**Name:** Idling  
**Severity:** 🟢 Low  
**ISO 22400 Code:** 6.4.3

**Description:**
Station is powered but not actively processing parts. Waiting in ready state.

**Examples:**
- Waiting for operator input
- Standby mode between batches
- Ready but no work assigned
- Auto-cycling without parts

**Typical Conditions:**
```yaml
- condition: state == "IDLE" AND power == "ON"
  loss_category: performance.idling
```

**Impact on OEE:**
```
Availability: —
Performance ↓  (minor impact)
Quality: —
```

**Improvement:** Better scheduling, reduce idle time between batches

---

### 11. performance.warm_up

**Name:** Warm-up  
**Severity:** 🟢 Low  
**ISO 22400 Code:** 6.4.4

**Description:**
Initial period after startup where equipment reaches operating temperature/pressure.

**Examples:**
- Heating elements warming up
- Hydraulic pressure building
- Thermal stabilization
- Spindle speed ramping

**Typical Conditions:**
```yaml
- condition: state == "WARMING_UP"
  loss_category: performance.warm_up
- condition: temperature < operating_temp AND startup == true
  loss_category: performance.warm_up
```

**Impact on OEE:**
```
Availability: —
Performance ↓  (brief, predictable)
Quality: —
```

**Improvement:** Pre-heat systems during planned downtime

---

### 12. performance.cleaning

**Name:** Cleaning  
**Severity:** 🟢 Low  
**ISO 22400 Code:** 6.4.5

**Description:**
Routine cleaning during production (not scheduled maintenance).

**Examples:**
- Quick wipe-down of sensors
- Chip removal
- Dust extraction
- Conveyor cleaning

**Typical Conditions:**
```yaml
- condition: state == "CLEANING" AND planned == false
  loss_category: performance.cleaning
```

**Impact on OEE:**
```
Availability: —
Performance ↓  (brief)
Quality: —
```

**Improvement:** Schedule cleaning during planned downtime

---

### 13. performance.adjustment

**Name:** Adjustment  
**Severity:** 🟡 Warning  
**ISO 22400 Code:** 6.4.6

**Description:**
Fine-tuning equipment parameters during production run.

**Examples:**
- Speed adjustment
- Pressure tuning
- Sensor calibration
- Fixture alignment

**Typical Conditions:**
```yaml
- condition: state == "ADJUSTING"
  loss_category: performance.adjustment
```

**Impact on OEE:**
```
Availability: —
Performance ↓  (brief)
Quality: —
```

**Improvement:** Stabilize processes to reduce need for adjustments

---

## Quality Losses

**Definition:** Parts are **produced** but are **defective** or scrapped.

### 14. quality.process_defect

**Name:** Process Defect  
**Severity:** 🔴 Critical  
**ISO 22400 Code:** 6.5.1

**Description:**
Parts fail quality inspection due to process issues.

**Examples:**
- Dimensional out of tolerance
- Surface finish defect
- Assembly error
- Contamination

**Typical Conditions:**
```yaml
- condition: scrap_count > 5
  loss_category: quality.process_defect
- condition: test_result == "FAIL"
  loss_category: quality.process_defect
- condition: quality_score < 95
  loss_category: quality.process_defect
```

**Impact on OEE:**
```
Availability: —
Performance: —
Quality ↓↓  (large impact)
```

**Cost Impact:** Highest (material + labor wasted)

---

### 15. quality.reduced_yield

**Name:** Reduced Yield  
**Severity:** 🟡 Warning  
**ISO 22400 Code:** 6.5.2

**Description:**
Overall good output percentage is below target (e.g., 92% instead of 98%).

**Examples:**
- Gradual quality degradation
- Tool wear causing defects
- Process drift
- Material variation

**Typical Conditions:**
```yaml
- condition: (good_count / total_count) < 0.95
  loss_category: quality.reduced_yield
```

**Impact on OEE:**
```
Availability: —
Performance: —
Quality ↓  (moderate impact)
```

**Improvement:** SPC monitoring, tighter process control

---

### 16. quality.startup_scrap

**Name:** Startup Scrap  
**Severity:** 🟢 Low  
**ISO 22400 Code:** 6.5.3

**Description:**
Initial parts scrapped during equipment startup or changeover.

**Examples:**
- First parts after changeover
- Calibration runs
- Purge material
- Process stabilization waste

**Typical Conditions:**
```yaml
- condition: parts_since_startup < 10 AND scrap == true
  loss_category: quality.startup_scrap
```

**Impact on OEE:**
```
Availability: —
Performance: —
Quality ↓  (predictable, minor)
```

**Improvement:** Reduce startup time, improve changeover procedures

---

## Non-Productive Time

**Definition:** **Planned** events where production is not expected.

### 17. non_productive.planned_maintenance

**Name:** Planned Maintenance  
**Severity:** ℹ️ Info  
**ISO 22400 Code:** 6.6.1

**Description:**
Scheduled preventive maintenance activities.

**Examples:**
- Lubrication
- Inspection
- Preventive part replacement
- Calibration

**Typical Conditions:**
```yaml
- condition: state == "MAINTENANCE" AND planned == true
  loss_category: non_productive.planned_maintenance
```

**Impact on OEE:**
```
Not counted against OEE (planned downtime excluded)
```

**Best Practice:** Schedule during shift changeovers or weekends

---

### 18. non_productive.changeover_planned

**Name:** Planned Changeover  
**Severity:** ℹ️ Info  
**ISO 22400 Code:** 6.6.2

**Description:**
Scheduled product or format change.

**Examples:**
- Scheduled product switch
- Planned tool change
- Format changeover
- Recipe change

**Typical Conditions:**
```yaml
- condition: state == "CHANGEOVER" AND planned == true
  loss_category: non_productive.changeover_planned
```

**Impact on OEE:**
```
Not counted against OEE (planned downtime excluded)
```

**Improvement:** Use SMED (Single-Minute Exchange of Die) techniques

---

### 19. non_productive.no_orders

**Name:** No Orders  
**Severity:** ℹ️ Info  
**ISO 22400 Code:** 6.6.3

**Description:**
No production scheduled due to lack of customer orders.

**Examples:**
- Low demand period
- Intentional production hold
- Inventory full
- End of shift with no next batch

**Typical Conditions:**
```yaml
- condition: state == "IDLE" AND scheduled == false
  loss_category: non_productive.no_orders
```

**Impact on OEE:**
```
Not counted against OEE (no production planned)
```

---

## Using Loss Categories Effectively

### In Semantic Mappings

**Example:** Escalating severity based on value:

```yaml
- key: station.speed_actual
  opc_pattern: "Speed"
  type: numeric
  unit: "%"
  loss_mapping:
    - condition: value == 0
      loss_category: availability.equipment_failure
      severity: critical
    - condition: value < 30
      loss_category: performance.reduced_speed
      severity: warning
    - condition: value < 70
      loss_category: performance.minor_stops
      severity: warning
```

### In AI Diagnostics

Loss categories **prevent hallucination**:

```
✅ Correct (using loss category):
"Station is experiencing performance.reduced_speed due to 
0% motor speed."

❌ Hallucination (without loss category):
"Station has a broken transmission gear that needs replacement."
```

The AI can only reference **observed loss categories**, not invent explanations.

### In Reports

Group losses by category:

```
Availability Losses: 45 minutes
- equipment_failure: 30 min
- upstream_starvation: 15 min

Performance Losses: 120 minutes
- reduced_speed: 120 min

Quality Losses: 0 minutes
```

---

## Quick Reference Table

| Category ID | Name | Severity | OEE Pillar | Typical Duration |
|-------------|------|----------|------------|------------------|
| availability.equipment_failure | Equipment Failure | 🔴 Critical | Availability | 30min - 8hr |
| availability.upstream_starvation | Upstream Starvation | 🟡 Warning | Availability | 5min - 2hr |
| availability.downstream_blocking | Downstream Blocking | 🟡 Warning | Availability | 5min - 1hr |
| availability.material_shortage | Material Shortage | 🔴 Critical | Availability | 15min - 4hr |
| availability.setup_changeover | Setup/Changeover | 🟡 Warning | Availability | 10min - 1hr |
| availability.operator_absence | Operator Absence | 🟠 Moderate | Availability | 5min - 30min |
| availability.tool_die_change | Tool/Die Change | 🟡 Warning | Availability | 5min - 30min |
| performance.reduced_speed | Reduced Speed | 🟡 Warning | Performance | Continuous |
| performance.minor_stops | Minor Stops | 🟡 Warning | Performance | < 5min each |
| performance.idling | Idling | 🟢 Low | Performance | Varies |
| performance.warm_up | Warm-up | 🟢 Low | Performance | 5min - 15min |
| performance.cleaning | Cleaning | 🟢 Low | Performance | 2min - 10min |
| performance.adjustment | Adjustment | 🟡 Warning | Performance | 2min - 15min |
| quality.process_defect | Process Defect | 🔴 Critical | Quality | Per part |
| quality.reduced_yield | Reduced Yield | 🟡 Warning | Quality | Continuous |
| quality.startup_scrap | Startup Scrap | 🟢 Low | Quality | First 10 parts |
| non_productive.planned_maintenance | Planned Maintenance | ℹ️ Info | None | 30min - 4hr |
| non_productive.changeover_planned | Planned Changeover | ℹ️ Info | None | 10min - 1hr |
| non_productive.no_orders | No Orders | ℹ️ Info | None | Varies |

---

**Next Chapter:** [OPC Explorer →](04-opc-explorer.md)

**Previous Chapter:** [← Semantic Mapping Engine](05-semantic-mapping.md)
