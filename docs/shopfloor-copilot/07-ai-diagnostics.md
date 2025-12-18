# Chapter 7: AI-Grounded Diagnostics

**Sprint:** 3  
**Feature:** Explainable AI root cause analysis  
**Tab:** 17 (AI Diagnostics)

---

## Overview

The **AI Diagnostics** feature transforms Shopfloor Copilot from a monitoring tool into an intelligent decision support system. It provides **explainable, evidence-based diagnostic analysis** using AI reasoning grounded in real-time data.

### What Makes It Different?

**Traditional MES:**
> "Alarm: Line A01 down"

**Shopfloor Copilot AI Diagnostics:**
> **Section 1 - What is happening:**  
> Station ST18 (Motor Assembly) is in RUNNING state but with 0% speed (performance.reduced_speed loss category). Cycle time is 52s with zero good count.
> 
> **Section 2 - Why this is happening:**  
> The combination of zero speed and prolonged cycle time indicates the motor assembly process has stalled. This is classified as a performance loss, not an availability loss, meaning the station is powered but not producing.
> 
> **Section 3 - What to do now:**  
> Consult Work Instruction WI-23 for motor assembly troubleshooting. Check drive communication, motor encoder, and speed controller.
> 
> **Section 4 - What to check next:**  
> 1. Verify power supply to motor drive  
> 2. Inspect motor encoder connections  
> 3. Check speed controller setpoint  
> 4. Test motor manually

---

## Key Concepts

### The 4-Section Structure

Every diagnostic follows this **mandatory structure**:

```
┌─────────────────────────────────────────────────┐
│ Section 1: What is happening                    │
│ ────────────────────────────────                │
│ FACTS ONLY from runtime data                    │
│ • Semantic signals                               │
│ • Loss categories                                │
│ • KPI values                                     │
│ • No interpretation yet                          │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ Section 2: Why this is happening                │
│ ────────────────────────────────                │
│ REASONING based on facts                         │
│ • Correlate signals with loss categories         │
│ • Apply domain knowledge (OEE, MES principles)  │
│ • State uncertainty if evidence is incomplete   │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ Section 3: What to do now                       │
│ ────────────────────────────────                │
│ PROCEDURES from knowledge base (RAG)             │
│ • Work instructions with citations               │
│ • SOPs with document IDs                         │
│ • Safety and quality priorities                  │
│ • "No procedures found" if RAG returns nothing  │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ Section 4: What to check next                   │
│ ────────────────────────────────                │
│ ACTIONABLE CHECKLIST                             │
│ • 3-7 concrete steps                             │
│ • Ordered by priority                            │
│ • Derived from procedures + context              │
│ • Specific to the situation                      │
└─────────────────────────────────────────────────┘
```

### Guardrails (No Hallucination)

The AI **must follow** these strict rules:

1. ✅ **Use ONLY runtime data** - Never invent signal values
2. ✅ **Reference ONLY equipment in snapshot** - No imaginary stations
3. ✅ **Separate facts from reasoning** - Clear boundaries between sections
4. ✅ **State "insufficient data"** - When evidence is lacking
5. ✅ **Never recommend control actions** - Read-only, human-in-the-loop
6. ✅ **Ground recommendations in RAG** - Cite documents or acknowledge none found

**Example of Guardrail Enforcement:**

❌ **BAD (Hallucination):**
> "Station ST99 is also affected..." (ST99 doesn't exist)

✅ **GOOD (Grounded):**
> "Insufficient data: no similar issues detected on other stations in the snapshot."

---

## Tutorial: Requesting a Diagnostic

### Step 1: Navigate to AI Diagnostics

![AI Diagnostics Tab](screenshots/ai-diagnostics-tab.png)

1. Open Shopfloor Copilot: http://localhost:8010
2. Click on **Tab 17: AI Diagnostics**
3. You'll see the diagnostic request form

### Step 2: Select Scope

![Scope Selector](screenshots/ai-diagnostics-scope.png)

Choose the analysis scope:

| Scope | When to Use | Example |
|-------|-------------|---------|
| **Station** | Single equipment issue | Motor assembly running slow |
| **Line** | Multiple stations affected | Entire line performance drop |

**Select:** `station` for this tutorial

### Step 3: Enter Equipment ID

![Equipment Input](screenshots/ai-diagnostics-input.png)

Enter the equipment identifier:

**For Station Scope:**
- Enter station ID: `ST18`
- Format: Must match OPC snapshot IDs

**For Line Scope:**
- Enter line ID: `A01`
- Format: A01, A02, B01, C01

**Quick Examples:**
- Click **Station ST18** button to auto-fill
- Click **Line A01** button for line diagnostic

### Step 4: Request Explanation

![Explain Button](screenshots/ai-diagnostics-button.png)

1. Click **"Explain this situation"** button
2. You'll see a loading indicator:
   ```
   🔄 Analyzing runtime data and generating explanation...
   ```

3. Wait 10-30 seconds for AI generation

**What Happens Behind the Scenes:**
```
1. Fetch semantic snapshot from OPC Studio
2. Extract signals for ST18
3. Identify loss categories (e.g., performance.reduced_speed)
4. Query RAG knowledge base for procedures
5. Build structured prompt with all evidence
6. Call LLM (Ollama llama3.2)
7. Parse response into 4 sections
8. Display structured output
```

---

## Tutorial: Interpreting Diagnostic Output

### Section 1: What is happening (Blue)

![Section 1 Output](screenshots/ai-diagnostics-section1.png)

**Purpose:** Runtime evidence (facts only)

**Example Output:**
```markdown
## Section 1 — What is happening

Runtime Evidence (Facts Only):
- Station: ST18 (Motor Assembly)
- Line: A01
- Plant: TORINO
- State: RUNNING
- Cycle Time: 52 seconds
- Good Count: 0 parts
- Scrap Count: 0 parts
- Critical: True

Semantic Signals:
- station.speed_actual: 0% → loss_category: performance.reduced_speed
- station.cycle_time_actual: 52s (within normal range 20-120s)
- station.parts_count: 0 (no production)

Active Loss Categories:
- performance.reduced_speed (triggered by speed = 0%)

KPIs:
- OEE Availability: 100% (station is running)
- Throughput Actual: 0 parts/hour (no output)
```

**How to Read:**
- ✅ All values come from OPC snapshot
- ✅ Loss categories auto-detected by semantic engine
- ✅ No interpretation or reasoning yet
- ✅ Clear equipment identification

### Section 2: Why this is happening (Yellow)

![Section 2 Output](screenshots/ai-diagnostics-section2.png)

**Purpose:** Reasoned explanation based on facts

**Example Output:**
```markdown
## Section 2 — Why this is happening

Reasoned Explanation:

The combination of RUNNING state + 0% speed + zero good count 
indicates the station is powered on and in production mode, 
but the motor assembly process has stalled.

This is classified as a **performance loss** (not availability) 
because:
1. The station is not faulted (availability would be 0%)
2. The station is not idle (would show IDLE state)
3. The issue is reduced throughput, not complete stoppage

The prolonged cycle time (52s) suggests the station is attempting 
to cycle but encountering resistance or blockage in the assembly 
process. Zero speed indicates:
- Motor drive may have lost communication
- Speed sensor may be faulty
- Mechanical jam preventing motion
- E-stop or interlock active

The "Critical" flag indicates this station is on the critical 
path for Line A01 production, meaning downstream stations may 
soon starve.
```

**How to Read:**
- ✅ Correlates multiple signals (state + speed + count)
- ✅ Applies OEE domain knowledge (performance vs availability)
- ✅ Uses loss category taxonomy correctly
- ✅ States uncertainty where appropriate

### Section 3: What to do now (Green)

![Section 3 Output](screenshots/ai-diagnostics-section3.png)

**Purpose:** Procedures from RAG knowledge base

**Example Output (with RAG results):**
```markdown
## Section 3 — What to do now

Procedures (from Knowledge Base):

**WI-23: Motor Assembly Troubleshooting** (Relevance: 0.87)
Location: shopfloor_docs/work_instructions/WI-23-v2.1.pdf
Applicable to: Motor Assembly Stations (ST18, ST24, ST30)

Procedure:
1. Check drive communication:
   - Verify Profinet LED is green
   - Check error code on drive display
   - Reset communication if error 0x2301

2. Inspect motor encoder:
   - Check encoder cable for damage
   - Verify 5V power supply to encoder
   - Test encoder signals with oscilloscope

3. Verify speed controller:
   - Read setpoint value (should be 80-100%)
   - Check analog input 0-10V
   - Manually jog motor from HMI

**SOP-14: Safe Motor Inspection** (Relevance: 0.72)
Location: shopfloor_docs/sop/SOP-14-v1.5.pdf

Safety Requirements:
- Tag out motor power supply
- Wait 5 minutes for capacitor discharge
- Verify 0V with multimeter before touching
- Use lockout-tagout procedures per Site-001

Quality Considerations:
- Document all findings in maintenance log
- Take photos of any damaged components
- Report to quality if assembly defects suspected
```

**Example Output (no RAG results):**
```markdown
## Section 3 — What to do now

Insufficient Data:
No relevant procedures or documentation found in knowledge base 
for "motor assembly" + "performance reduced speed".

Recommendation:
Consult with line management or maintenance personnel for 
guidance on troubleshooting motor assembly issues. 

In the absence of documented procedures, follow general 
electrical troubleshooting best practices:
- Verify power supply
- Check communication connections
- Inspect for mechanical obstructions
- Review recent maintenance history
```

**How to Read:**
- ✅ Citations include document ID and location
- ✅ Relevance scores show RAG match quality
- ✅ Safety procedures prioritized
- ✅ Gracefully acknowledges if no procedures found (no fabrication)

### Section 4: What to check next (Purple)

![Section 4 Output](screenshots/ai-diagnostics-section4.png)

**Purpose:** Actionable checklist ordered by priority

**Example Output:**
```markdown
## Section 4 — What to check next

Actionable Checklist:

1. **Verify Power Supply** (Priority: High)
   - Check main power switch on motor drive
   - Verify 24VDC control power LED
   - Test for loose connections on power terminals
   - Expected: Green LED, 24V reading

2. **Inspect Motor Encoder** (Priority: High)
   - Locate encoder cable at motor shaft
   - Check for cuts, kinks, or damage
   - Verify encoder connector is fully seated
   - Expected: No visible damage, secure connection

3. **Check Speed Controller Setpoint** (Priority: Medium)
   - Access HMI screen for ST18
   - Navigate to Speed Control page
   - Read current setpoint value
   - Expected: 80-100% (0% indicates problem)

4. **Test Motor Manually** (Priority: Medium)
   - Use HMI manual jog function
   - Attempt slow forward/reverse motion
   - Listen for abnormal sounds
   - Expected: Motor moves smoothly, no grinding

5. **Review Recent Alarms** (Priority: Low)
   - Open alarm history on HMI
   - Look for drive faults in last 24 hours
   - Note error codes (especially 0x23xx range)
   - Expected: May reveal intermittent issues

6. **Inspect for Mechanical Jam** (Priority: Low, Safety Required)
   - Tag out motor power (see SOP-14)
   - Manually rotate motor shaft by hand
   - Check for resistance or binding
   - Expected: Smooth rotation, no obstruction

7. **Escalate if Unresolved** (Priority: Fallback)
   - Document all findings in maintenance ticket
   - Contact controls engineer for advanced diagnostics
   - Consider requesting spare motor drive
   - Expected: Issue resolved or escalation path clear
```

**How to Read:**
- ✅ Each step is concrete and specific
- ✅ Priority levels guide sequencing
- ✅ Expected outcomes help verification
- ✅ Safety notes included where needed
- ✅ Escalation path if steps don't resolve

---

## Advanced Features

### Comparing Line vs Station Diagnostics

**Station Diagnostic (ST18):**
- Focused on single equipment
- Detailed signal-by-signal analysis
- Specific procedures for that station type
- Faster generation (less data)

**Line Diagnostic (A01):**
- Analyzes all stations on the line
- Identifies correlated issues
- May reveal upstream/downstream dependencies
- Longer generation time (more data)

**Example Line Diagnostic:**
```markdown
## Section 1 — What is happening

Line: A01 (6 stations)
Plant: TORINO

Affected Stations:
- ST17 (Component Staging): RUNNING, no issues
- ST18 (Motor Assembly): RUNNING, 0% speed → performance.reduced_speed
- ST19 (Inverter Integration): BLOCKED → availability.downstream_blocking
- ST20 (Functional Test): STARVED → availability.upstream_starvation
- ST21 (Quality Inspection): STARVED → availability.upstream_starvation
- ST22 (Packaging): STARVED → availability.upstream_starvation

Root Cause:
ST18 is the bottleneck. Its reduced speed has caused downstream 
blocking (ST19) and upstream starvation (ST20-ST22).

Line KPIs:
- OEE Overall: 0% (line stopped)
- Availability: 16.7% (1/6 stations productive)
- Performance: Degraded
```

**How to Use:**
- Request line diagnostic when multiple stations show issues
- Helps identify cascade failures
- Reveals dependencies between stations

---

## Metadata Panel

![Metadata Panel](screenshots/ai-diagnostics-metadata.png)

**What It Shows:**

```
Diagnostic Metadata
───────────────────────────────────────
Equipment: station ST18
Plant: TORINO
Timestamp: 2025-12-16 08:01:21 UTC
Model: llama3.2:latest
Active Loss Categories: performance.reduced_speed
RAG Documents Retrieved: 2
```

**Fields Explained:**

| Field | Description | Use Case |
|-------|-------------|----------|
| **Equipment** | Scope + ID analyzed | Verify correct target |
| **Plant** | Plant identifier | Multi-site installations |
| **Timestamp** | When diagnostic ran | Track staleness |
| **Model** | LLM used | Version tracking |
| **Loss Categories** | Active losses found | Quick loss summary |
| **RAG Documents** | Number of procedures found | Knowledge coverage check |

---

## Best Practices

### When to Request Diagnostics

✅ **DO request when:**
- Alarm/fault occurred, need troubleshooting steps
- Performance degraded, need root cause
- Multiple failures, need correlation analysis
- Training new operators on troubleshooting
- Documenting incident for reports

❌ **DON'T request when:**
- Equipment is running normally (waste of resources)
- You just want live values (use OPC Explorer instead)
- You already know the fix (just do it)
- Issue is outside MES scope (electrical, mechanical)

### Interpreting AI Reasoning

**Trust the AI when:**
- Section 1 matches what you see on the floor
- Section 2 reasoning aligns with OEE principles
- Section 3 cites real documents you recognize
- Section 4 steps are safe and logical

**Question the AI when:**
- Section 1 mentions equipment you don't recognize (report bug)
- Section 2 contradicts known physics/mechanics
- Section 3 invents procedures without citations
- Section 4 suggests unsafe actions

**Remember:**
- AI is a **decision support tool**, not a decision maker
- Always verify recommendations against plant procedures
- Use human judgment for safety-critical decisions
- Report any hallucinations or errors to administrators

### Using Diagnostics for Training

**Onboarding New Operators:**
1. Show normal operation diagnostic (all green)
2. Simulate fault in demo server
3. Request diagnostic for faulted station
4. Walk through 4 sections together
5. Follow checklist as learning exercise

**Building Tribal Knowledge:**
1. Request diagnostics for recurring issues
2. Compare AI recommendations to expert fixes
3. Document gaps in RAG knowledge base
4. Update work instructions based on findings

---

## Common Scenarios

### Scenario 1: Station Fault

**Symptoms:**
- Alarm on HMI
- Station shows FAULTED in OPC Explorer
- Production stopped

**Steps:**
1. Go to AI Diagnostics
2. Select `station`, enter station ID (e.g., `ST20`)
3. Click "Explain this situation"
4. Read Section 1 to confirm fault
5. Read Section 2 for likely cause
6. Follow Section 3 procedures
7. Execute Section 4 checklist
8. Document findings

### Scenario 2: Slow Production

**Symptoms:**
- No alarms
- Line running but throughput low
- Cycle times increasing

**Steps:**
1. Check Semantic Signals tab first
2. Identify stations with `performance.*` loss categories
3. Go to AI Diagnostics
4. Request diagnostic for affected station
5. Section 2 will explain performance loss
6. Section 4 will guide optimization

### Scenario 3: Cascade Failure

**Symptoms:**
- Multiple stations showing issues
- Some STARVED, some BLOCKED
- Hard to find root cause

**Steps:**
1. Go to AI Diagnostics
2. Select `line` scope, enter line ID (e.g., `A01`)
3. Request diagnostic
4. Section 1 will list all affected stations
5. Section 2 will identify bottleneck
6. Focus troubleshooting on root cause station

### Scenario 4: Quality Issue

**Symptoms:**
- Scrap count increasing
- Quality alarms
- `quality.*` loss category

**Steps:**
1. Request station diagnostic
2. Section 1 will show quality metrics
3. Section 2 will correlate with process parameters
4. Section 3 will reference quality procedures (SOPs)
5. Section 4 will include quality checks

---

## Troubleshooting AI Diagnostics

### Problem: Diagnostic Times Out

**Symptoms:**
- Loading spinner for > 2 minutes
- No response

**Solutions:**
1. **Check Ollama service:**
   ```bash
   docker ps | grep ollama
   # Should show compassionate_thompson running
   ```

2. **Check Shopfloor logs:**
   ```bash
   docker-compose logs shopfloor --tail=50
   # Look for "LLM call failed" or timeout errors
   ```

3. **Restart services:**
   ```bash
   docker-compose restart shopfloor
   ```

4. **Reduce scope:** Try station instead of line

### Problem: Section 3 Always Says "No Procedures Found"

**Symptoms:**
- Every diagnostic shows "insufficient data" in Section 3
- RAG Documents: 0

**Solutions:**
1. **Check ChromaDB status:**
   ```bash
   docker-compose ps chroma
   # Should be "Up"
   ```

2. **Verify knowledge base is populated:**
   ```bash
   curl http://localhost:8001/api/v1/collections
   # Should show "shopfloor_docs" collection
   ```

3. **Populate knowledge base:**
   - See Chapter 9: RAG Knowledge Base
   - Ingest work instructions and SOPs

4. **Check metadata filters:**
   - Diagnostics queries with `doc_type` filter
   - Ensure documents have correct metadata

### Problem: AI Output Seems Wrong

**Symptoms:**
- Section 1 mentions non-existent equipment
- Section 2 reasoning is illogical
- Section 4 suggests unsafe actions

**Solutions:**
1. **Verify snapshot data:**
   ```bash
   curl http://localhost:8040/snapshot | jq '.data.lines.A01.stations.ST18'
   # Check if values match Section 1
   ```

2. **Check semantic signals:**
   ```bash
   curl http://localhost:8040/semantic/signals/A01/ST18
   # Verify loss categories are correct
   ```

3. **Report hallucination:**
   - Document the incorrect output
   - Check if station ID was typo
   - File bug report with diagnostic metadata

4. **Adjust LLM temperature:**
   - Edit `packages/diagnostics/explainer.py`
   - Lower temperature = more factual (current: 0.3)

### Problem: Diagnostics Work But Seem Generic

**Symptoms:**
- Section 4 always has same checklist
- No station-specific recommendations
- RAG Documents: 0

**Root Cause:**
- Knowledge base is empty
- No station-specific procedures indexed

**Solution:**
- Populate RAG with actual work instructions
- Ensure documents have station type metadata
- See Chapter 9 for knowledge base setup

---

## Integration with Other Features

### OPC Explorer → AI Diagnostics Workflow

1. **Discover Issue in OPC Explorer:**
   - Browse to faulted station
   - Note Node ID and current value
   - Add to watchlist to monitor

2. **Get Semantic Context:**
   - Switch to Semantic Signals tab
   - View loss_category classification
   - Note KPI impact

3. **Request Diagnostic:**
   - Switch to AI Diagnostics tab
   - Enter station ID from OPC Explorer
   - Get structured troubleshooting guide

### Semantic Signals → AI Diagnostics Workflow

1. **Monitor Semantic Signals:**
   - Watch for loss_category changes
   - Notice `performance.reduced_speed` appears

2. **Investigate with Diagnostics:**
   - Click station ID in semantic signals
   - Request diagnostic
   - Understand why speed reduced

### KPI Dashboard → AI Diagnostics Workflow

1. **Notice KPI Degradation:**
   - OEE drops on KPI Dashboard
   - Identify line or station responsible

2. **Drill Down with Diagnostics:**
   - Request line diagnostic for affected line
   - Section 1 will show which stations caused OEE drop
   - Follow recommendations to restore

---

## Performance Metrics

### Generation Times

| Scope | Typical Time | Max Time |
|-------|--------------|----------|
| **Station** | 10-15 seconds | 30 seconds |
| **Line** | 20-30 seconds | 60 seconds |

**Factors Affecting Speed:**
- LLM model size (llama3.2 = 3B params)
- Server CPU/GPU availability
- RAG query complexity
- Number of stations in line

### Resource Usage

**Per Diagnostic Request:**
- **OPC Snapshot:** < 100ms
- **Semantic Transform:** < 50ms per station
- **RAG Query:** < 1 second
- **LLM Inference:** 10-30 seconds (majority of time)

**Concurrent Users:**
- System can handle 5-10 simultaneous diagnostics
- Queue may form during peak usage
- Consider load balancing for > 20 users

---

## Future Enhancements

### Planned Features

1. **Diagnostic History:**
   - Save diagnostics to database
   - Compare current vs previous
   - Trend analysis of recurring issues

2. **Automated Diagnostics:**
   - Trigger on alarm
   - Email/SMS notification
   - Pre-generated troubleshooting guide

3. **Multi-Language:**
   - Italian, German, Chinese
   - Localized procedures
   - Cultural context awareness

4. **Diagnostic Confidence:**
   - Uncertainty quantification
   - "High confidence" vs "Low confidence"
   - Alternative explanations

5. **Visual Diagnostics:**
   - Annotated P&ID diagrams
   - Highlighted signal flows
   - Video troubleshooting clips

---

**Next Chapter:** [Understanding Diagnostic Output →](08-diagnostic-output.md)

**Previous Chapter:** [← Loss Category System](06-loss-categories.md)
