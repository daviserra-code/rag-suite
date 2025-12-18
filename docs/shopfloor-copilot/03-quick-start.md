# Chapter 3: Quick Start Guide

**Time to Complete:** 15 minutes  
**Difficulty:** Beginner

This guide will get you from zero to monitoring your first OPC UA station and requesting an AI diagnostic.

---

## Prerequisites

✅ Docker and Docker Compose installed  
✅ Ollama installed with llama3.2 model  
✅ Repository cloned  
✅ Services running (`docker-compose up -d`)

If not, see [Chapter 2: Installation](02-installation.md).

---

## 5-Minute Quick Start

### Step 1: Verify Services (30 seconds)

```bash
# Check all services are running
docker-compose ps

# All should show "Up"
```

### Step 2: Open Shopfloor Copilot (10 seconds)

Open browser: **http://localhost:8010**

You should see the main dashboard with 23 tabs.

### Step 3: Browse OPC Nodes (2 minutes)

1. Click **Tab 15: OPC Explorer**
2. Connection should already be active to demo server
3. In the browse tree, expand:
   - **Root**
   - **Objects**
   - **TORINO Plant**
   - **Line A01**
   - **ST18 - Motor Assembly**
4. Click on **Status** node
5. See current value: `RUNNING`

![OPC Explorer Browse](screenshots/quickstart-opc-browse.png)

### Step 4: View Semantic Signals (2 minutes)

1. Click **Tab 16: Semantic Signals**
2. Enter:
   - Line ID: `A01`
   - Station ID: `ST18`
3. Click **Load Semantic Signals**
4. See transformed signals with loss categories

![Semantic Signals](screenshots/quickstart-semantic-signals.png)

**Notice:**
- `station.state`: RUNNING (no loss category)
- `station.speed_actual`: 0% → **performance.reduced_speed** (yellow border!)

### Step 5: Request AI Diagnostic (30 seconds)

1. Click **Tab 17: AI Diagnostics**
2. Select scope: `station`
3. Enter ID: `ST18`
4. Click **"Explain this situation"**
5. Wait 10-20 seconds

![AI Diagnostics Request](screenshots/quickstart-diagnostics-request.png)

### Step 6: Read Diagnostic Output (1 minute)

Review the 4 sections:

**Section 1 - What is happening:**
```
Station ST18 is RUNNING with 0% speed, classified as 
performance.reduced_speed. Zero good count indicates 
no production output.
```

**Section 2 - Why this is happening:**
```
The combination of RUNNING state + 0% speed suggests 
motor stall or drive communication issue. This is a 
performance loss (not availability) because the station 
is powered but not producing.
```

**Section 3 - What to do now:**
```
Insufficient data: no relevant procedures found.
Recommend checking motor drive communication and 
mechanical obstructions.
```

**Section 4 - What to check next:**
```
1. Verify power supply
2. Inspect motor encoder
3. Check speed controller setpoint
4. Test motor manually
```

![Diagnostic Output](screenshots/quickstart-diagnostics-output.png)

**Congratulations!** You've completed the basic workflow:
1. ✅ Browse OPC data
2. ✅ View semantic signals with loss categories
3. ✅ Request AI diagnostic explanation

---

## 15-Minute Tutorial: Full Workflow

### Part 1: Explore the Plant (5 minutes)

#### View Live Monitoring Dashboard

1. Click **Tab 1: Live Monitoring**
2. See real-time plant overview
3. Note line statuses and KPIs

![Live Monitoring](screenshots/quickstart-live-monitoring.png)

#### Check Production Lines

1. Click **Tab 2: Production Lines**
2. See all 4 lines (A01, A02, B01, C01)
3. Click on **Line A01** card
4. View line details and station list

![Production Lines](screenshots/quickstart-production-lines.png)

#### Explore Station Heatmap

1. Click **Tab 4: Station Heatmap**
2. See color-coded station performance
3. Identify problem stations (red/yellow)

![Station Heatmap](screenshots/quickstart-heatmap.png)

### Part 2: Deep Dive into OPC (5 minutes)

#### Add Nodes to Watchlist

1. Go to **Tab 15: OPC Explorer**
2. Navigate to: `A01 → ST18 → Temperature`
3. Click **Add to Watchlist**
4. Repeat for: `Speed`, `CycleTime`, `Status`
5. Watch values update every 1 second

![Watchlist](screenshots/quickstart-watchlist.png)

#### Read Multiple Nodes

1. Browse to different stations: ST19, ST20, ST21
2. Click on their **Status** nodes
3. Compare states across stations
4. Look for patterns (all RUNNING, some STARVED, etc.)

#### Write a Test Value (Optional)

1. Navigate to a writable node (if available)
2. Enter a test value
3. Click **Write Value**
4. Verify write succeeded

### Part 3: Semantic Analysis (5 minutes)

#### Compare Multiple Stations

1. Go to **Tab 16: Semantic Signals**
2. Load signals for ST18 (assembly)
3. Note the loss categories present
4. Switch to ST20 (testing)
5. Compare loss patterns

**Example Comparison:**

| Station | Type | Active Losses | Key Issue |
|---------|------|---------------|-----------|
| ST18 | Assembly | performance.reduced_speed | Speed at 0% |
| ST20 | Testing | quality.process_defect | Quality score low |

#### View Derived KPIs

In the Semantic Signals screen, scroll down to **KPIs** section:

```
KPI: oee.availability
Value: 100%
Target: 85%
Status: ✅ Above target

KPI: throughput.actual
Value: 0 parts/hour
Target: 120 parts/hour
Status: ❌ Below target
```

![KPI Cards](screenshots/quickstart-kpis.png)

#### Identify Loss Categories

Color coding guide:
- 🔴 **Red border:** Availability losses (station down)
- 🟡 **Yellow border:** Performance losses (running slow)
- 🟠 **Orange border:** Quality losses (defects)
- ⚫ **Gray border:** Non-productive (planned downtime)

### Part 4: AI-Powered Diagnostics (5 minutes)

#### Line-Level Diagnostic

1. Go to **Tab 17: AI Diagnostics**
2. Select scope: `line`
3. Enter ID: `A01`
4. Click **"Explain this situation"**
5. Wait ~20 seconds (longer than station)

**Line Diagnostic Output:**

Section 1 will show **all 6 stations** on the line:
```
Line A01 Status:
- ST17: RUNNING (no issues)
- ST18: RUNNING (performance.reduced_speed)
- ST19: BLOCKED (availability.downstream_blocking)
- ST20: STARVED (availability.upstream_starvation)
- ST21: STARVED (availability.upstream_starvation)
- ST22: STARVED (availability.upstream_starvation)

Root Cause: ST18 bottleneck causing cascade failure
```

Section 2 explains the **correlation**:
```
ST18's reduced speed has created a bottleneck. ST19 
cannot feed fast enough and is blocked. ST20-ST22 
are starving due to lack of input from upstream.
```

![Line Diagnostic](screenshots/quickstart-line-diagnostic.png)

#### Station-Level Diagnostic with RAG

If you've populated the knowledge base (see Chapter 9):

1. Request diagnostic for ST18
2. Section 3 will show **actual procedures**:
   ```
   WI-23: Motor Assembly Troubleshooting
   Document: shopfloor_docs/work_instructions/WI-23.pdf
   
   1. Check Profinet communication
   2. Verify encoder signals
   3. Test speed controller
   ```

#### Compare Diagnostics

Request diagnostics for multiple stations:
- ST18 (performance issue)
- ST20 (quality issue)
- ST17 (normal operation)

Compare how the AI explains each differently.

---

## Common First-Time Tasks

### Task 1: Monitor a Station in Real-Time

**Goal:** Watch ST18 status continuously

**Steps:**
1. OPC Explorer → Navigate to ST18
2. Add `Status`, `Speed`, `Temperature` to watchlist
3. Leave watchlist panel open
4. Watch for any state changes
5. If state changes to FAULTED, request diagnostic

**Expected Behavior:**
- Values update every 1 second
- Timestamps show last update time
- Can leave running in background

### Task 2: Identify Performance Bottleneck

**Goal:** Find which station is slowing down the line

**Steps:**
1. Semantic Signals → Load each station on A01
2. Note which have `performance.*` loss categories
3. Compare cycle times (look for longest)
4. Request line diagnostic for correlation
5. Focus troubleshooting on bottleneck station

**Expected Finding:**
- ST18 likely has `performance.reduced_speed`
- Cycle time is 52s (normal range)
- But speed is 0% (abnormal)

### Task 3: Troubleshoot a Quality Issue

**Goal:** Investigate high scrap count

**Steps:**
1. OPC Explorer → Browse to ST20 (testing station)
2. Check `ScrapCount` value
3. Semantic Signals → Load ST20
4. Look for `quality.*` loss categories
5. AI Diagnostics → Request station diagnostic
6. Follow Section 4 checklist

**Expected Output:**
- Section 1: Show scrap count and quality score
- Section 2: Correlate low quality with process parameters
- Section 3: Reference quality SOPs
- Section 4: Quality inspection checklist

### Task 4: Generate a Shift Report

**Goal:** Document what happened during your shift

**Steps:**
1. Go to **Tab 23: Reports**
2. Select report type: "Shift Summary"
3. Choose date range: Today, 6am-2pm (your shift)
4. Click **Generate Report**
5. Review KPIs, downtime events, diagnostics
6. Click **Export PDF**

**Report Contents:**
- OEE metrics per line
- Top loss categories
- Alarm history
- AI diagnostics summary
- Recommendations

---

## Quick Reference Commands

### Checking Service Status
```bash
# View all services
docker-compose ps

# Check specific service logs
docker-compose logs shopfloor --tail=20
docker-compose logs opc-studio --tail=20

# Restart a service
docker-compose restart shopfloor
```

### Health Checks
```bash
# Shopfloor UI
curl http://localhost:8010/health

# OPC Studio
curl http://localhost:8040/health

# Diagnostics API
curl http://localhost:8010/api/diagnostics/health

# OPC Connection Status
curl http://localhost:8040/status
```

### Quick Diagnostics Test
```bash
# Test station diagnostic via API
curl -X POST http://localhost:8010/api/diagnostics/explain \
  -H "Content-Type: application/json" \
  -d '{"scope": "station", "id": "ST18"}'

# Should return JSON with 4 sections
```

### Viewing OPC Snapshot
```bash
# Get full plant snapshot
curl http://localhost:8040/snapshot | jq > snapshot.json

# View specific station
curl http://localhost:8040/snapshot | jq '.data.lines.A01.stations.ST18'
```

---

## Next Steps

Now that you've completed the quick start:

### For Operators
→ Read [Chapter 13: Operator Quick Reference](13-operator-guide.md)  
→ Learn [Best Practices](15-best-practices.md)

### For Engineers
→ Explore [Semantic Mapping Engine](05-semantic-mapping.md)  
→ Configure [Loss Categories](06-loss-categories.md)  
→ Customize [Configuration](11-configuration.md)

### For Managers
→ Review [Manager Dashboard Guide](14-manager-guide.md)  
→ Understand [KPI Calculations](19-kpi-reference.md)

### For Troubleshooting
→ Check [Troubleshooting Guide](12-troubleshooting.md)  
→ Review [API Reference](10-api-reference.md)

---

## Common Questions

**Q: Why is my OPC connection showing "Disconnected"?**  
A: Check that opc-demo service is running: `docker-compose ps opc-demo`

**Q: AI Diagnostics times out - why?**  
A: Verify Ollama is running: `docker ps | grep ollama`

**Q: Semantic Signals show "generic" instead of specific mappings?**  
A: Station type may not be in YAML config. Check [Chapter 5](05-semantic-mapping.md).

**Q: Section 3 always says "No procedures found"?**  
A: RAG knowledge base is empty. Populate it following [Chapter 9](09-rag-knowledge.md).

**Q: Can I connect to my real OPC server instead of demo?**  
A: Yes! Go to OPC Explorer, enter your server URL, click Connect.

**Q: How do I add more station types?**  
A: Edit `opc-studio/config/semantic_mappings.yaml`, see [Chapter 11](11-configuration.md).

---

## Summary

You've learned:
- ✅ How to navigate the Shopfloor Copilot UI
- ✅ Browse OPC UA nodes in real-time
- ✅ View semantic signals with loss categories
- ✅ Request AI diagnostics for troubleshooting
- ✅ Interpret the 4-section diagnostic output

**You're ready to start using Shopfloor Copilot in production!**

---

**Next Chapter:** [OPC Explorer Deep Dive →](04-opc-explorer.md)

**Previous Chapter:** [← Installation & Setup](02-installation.md)
