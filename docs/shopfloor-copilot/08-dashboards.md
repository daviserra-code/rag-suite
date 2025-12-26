# Chapter 8: Dashboard & Analytics Guide

**Feature Tabs:** KPI Dashboard, Operations Dashboard, Station Heatmap, Reports, Energy Tracking, Digital Twin, Ticket Insights  
**Version:** 0.3.1  
**Last Updated:** December 26, 2025

---

## Overview

Shopfloor Copilot provides **seven comprehensive dashboards** for monitoring, analyzing, and reporting on manufacturing operations. Each dashboard is designed for specific workflows and user roles.

### Dashboard Summary

| Dashboard | Primary User | Purpose | Key Metrics |
|-----------|--------------|---------|-------------|
| **KPI Dashboard** | Managers | High-level performance overview | OEE, Availability, Performance, Quality |
| **Operations Dashboard** | Operators, Supervisors | Real-time line monitoring | Station status, top losses, recent issues |
| **Station Heatmap** | Engineers | Failure pattern analysis | Downtime frequency, duration by station |
| **Reports** | Managers | Scheduled reporting | Automated email reports |
| **Energy Tracking** | Sustainability Managers | Energy consumption | Total energy, per-unit energy, CO₂ reduction |
| **Digital Twin** | Engineers, Analysts | Baseline comparison | OEE targets vs actuals |
| **Ticket Insights** | Project Managers | Sprint tracking | Jira ticket status, AI insights |

---

## KPI Dashboard

**Tab:** KPI Dashboard  
**Purpose:** Executive-level view of manufacturing performance  
**Users:** Plant Managers, Line Managers

### Features

#### 1. Performance Filters

The dashboard begins with an enhanced filter card featuring gradient styling:

[📸 SCREENSHOT PLACEHOLDER]
**File:** `screenshots/kpi-dashboard-filters.png`
**Caption:** KPI Dashboard filters with gradient blue background
**Instructions:**
1. Navigate to KPI Dashboard tab
2. Show filters section at top (gradient blue card)
3. Capture "Production Line" and "Time Period" dropdowns

**Filter Options:**
- **Production Line:** Select specific line or "All Lines"
- **Time Period:** 7, 14, 30, 60, or 90 days
- **Refresh Button:** Manual data reload

**Recent Improvements (v0.3.1):**
- ✅ Gradient card background (`bg-gradient-to-br from-blue-50 to-indigo-50`)
- ✅ White filter dropdowns with dark text
- ✅ Clear labels: "Production Line" (not "Line"), "Time Period (days)" (not "Days")
- ✅ Blue refresh button with hover effect

---

#### 2. KPI Summary Cards

Four main KPI cards display overall performance metrics:

[📸 SCREENSHOT PLACEHOLDER]
**File:** `screenshots/kpi-dashboard-cards.png`
**Caption:** KPI summary cards showing OEE, Availability, Performance, Quality
**Instructions:**
1. Show all four KPI cards in a row
2. Capture large bold percentages with colored backgrounds
3. Include trend indicators (↑/↓)

**Card Layout:**
```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│     OEE     │  │ Availability│  │ Performance │  │   Quality   │
│    87.5%    │  │    92.3%    │  │    94.2%    │  │    98.7%    │
│   ↑ +2.3%  │  │   ↓ -0.5%  │  │   ↑ +1.8%  │  │   → 0.0%   │
│             │  │             │  │             │  │             │
│ Target: 85% │  │ Target: 90% │  │ Target: 95% │  │ Target: 99% │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
```

**Visual Design:**
- **Values:** `text-4xl font-bold` in colored text (blue, green, yellow, red)
- **Trend Indicators:** Arrows with positive (green), negative (red), neutral (grey)
- **Targets:** Smaller text showing goal values
- **Cards:** Gradient backgrounds with 2px colored borders

**Interpretation:**
- **OEE (Overall Equipment Effectiveness):** Composite metric = Availability × Performance × Quality
- **Availability:** % of scheduled time equipment is operational
- **Performance:** % of maximum rated speed
- **Quality:** % of good parts (no defects)

**Best Practices:**
- Check trends daily to catch performance degradation early
- Investigate any metric consistently below target
- Compare across lines to identify best practices

---

#### 3. Recent Downtimes

Displays most recent downtime events with improved readability:

[📸 SCREENSHOT PLACEHOLDER]
**File:** `screenshots/kpi-dashboard-downtimes.png`
**Caption:** Recent downtimes list with improved text contrast
**Instructions:**
1. Scroll to "Recent Downtimes" section
2. Show list with time, station, duration, reason
3. Capture dark text on white cards

**Column Layout:**
- **Time:** When downtime started (e.g., "14:23:15")
- **Station:** Equipment ID (e.g., "ST20 - Welding")
- **Duration:** How long downtime lasted (e.g., "12 min 34 sec")
- **Reason:** Loss category (e.g., "Equipment Failure")

**Recent Improvements (v0.3.1):**
- ✅ Time in `text-gray-800 font-medium` (was too light)
- ✅ Station in `text-gray-900 font-bold` for emphasis
- ✅ Duration in `text-orange-700 font-bold` to highlight impact
- ✅ Reason in `text-gray-900` for clarity
- ✅ Increased row padding for better readability

**Usage Tips:**
1. Click on a downtime row to see full details
2. Filter by line to focus on specific equipment
3. Look for patterns in reasons (e.g., recurring "Material Shortage")

---

### Workflow Example

**Scenario:** Daily morning review

1. **Select Line:** Choose "Line A01" from dropdown
2. **Set Period:** Select "7 days" to see weekly trend
3. **Click Refresh:** Load latest data
4. **Review OEE:** Check if meeting 85% target
5. **Analyze Losses:** Look at Recent Downtimes for patterns
6. **Take Action:**
   - If Availability low → Check equipment failures
   - If Performance low → Investigate speed reductions
   - If Quality low → Review defect patterns

---

## Operations Dashboard

**Tab:** Operations Dashboard  
**Purpose:** Real-time operational monitoring by production line  
**Users:** Operators, Shift Supervisors

### Features

#### 1. Line Selector

Choose which production line to monitor:

[📸 SCREENSHOT PLACEHOLDER]
**File:** `screenshots/operations-dashboard-line-selector.png`
**Caption:** Operations Dashboard line selector dropdown
**Instructions:**
1. Navigate to Operations Dashboard
2. Show line selector dropdown at top
3. Capture dropdown expanded showing available lines

**Fixed in v0.3.1:**
- ✅ Line selector now properly updates all tiles when changed
- ✅ Made content container refreshable with `@ui.refreshable` decorator
- ✅ All tiles (station performance, top losses, recent issues) now refresh correctly

---

#### 2. Station Performance Tiles

Grid of tiles showing each station's current status:

[📸 SCREENSHOT PLACEHOLDER]
**File:** `screenshots/operations-dashboard-tiles.png`
**Caption:** Station performance tiles showing status and metrics
**Instructions:**
1. Show grid of station tiles (e.g., ST10, ST11, ST12, etc.)
2. Capture mix of statuses (RUNNING green, IDLE yellow, FAULTED red)
3. Include OEE percentages on each tile

**Tile Layout:**
```
┌─────────────────┐
│  ST10 - Press   │
│   ● RUNNING     │ ← Status indicator (green)
│                 │
│   OEE: 92.5%    │
│   Cycle: 45s    │
│   Good: 1,234   │
└─────────────────┘
```

**Status Colors:**
- **Green (RUNNING):** Producing normally
- **Yellow (IDLE):** Not producing but no fault
- **Orange (STARVED/BLOCKED):** Waiting for material
- **Red (FAULTED):** Equipment failure
- **Grey (OFFLINE):** Not scheduled or maintenance

**Key Metrics per Tile:**
- **OEE:** Real-time calculated percentage
- **Cycle Time:** Current cycle duration
- **Good Count:** Total good parts produced

---

#### 3. Top Losses

Bar chart showing most impactful loss categories:

[📸 SCREENSHOT PLACEHOLDER]
**File:** `screenshots/operations-dashboard-losses.png`
**Caption:** Top losses bar chart showing loss categories by time
**Instructions:**
1. Scroll to "Top Losses" section
2. Show horizontal bar chart
3. Capture loss categories sorted by duration

**Chart Features:**
- **X-axis:** Loss duration (minutes or hours)
- **Y-axis:** Loss category names (e.g., "Equipment Failure", "Material Shortage")
- **Color Coding:** Red (availability), Orange (performance), Blue (quality), Grey (non-productive)

**Usage:**
1. Identify biggest time wasters
2. Focus improvement efforts on top 3 losses
3. Track over time to measure improvement

---

#### 4. Recent Issues

Scrollable list of recent alarms and events:

**Column Headers:**
- **Time:** When issue occurred
- **Station:** Which equipment
- **Issue Type:** Loss category
- **Status:** Active, Resolved, or Acknowledged
- **Duration:** How long (for resolved issues)

**Actions:**
- Click row to see full details
- Use color coding to prioritize (red = active, green = resolved)
- Filter by status if needed

---

### Workflow Example

**Scenario:** Shift supervisor monitoring Line A01

1. **Select Line:** Choose "Line A01" from dropdown
2. **Scan Stations:** Look for red (FAULTED) or orange (STARVED/BLOCKED) tiles
3. **Check Losses:** Review top losses chart for patterns
4. **Address Issues:** Click on red stations to see details
5. **Monitor Trends:** Watch OEE across all stations
6. **Escalate:** If multiple stations affected, call maintenance

---

## Station Heatmap

**Tab:** Station Heatmap  
**Purpose:** Visualize failure patterns across all stations and time  
**Users:** Maintenance Engineers, Reliability Engineers

### Features

#### 1. Time Range Filter

[📸 SCREENSHOT PLACEHOLDER]
**File:** `screenshots/station-heatmap-filters.png`
**Caption:** Station Heatmap time range filter
**Instructions:**
1. Navigate to Station Heatmap tab
2. Show time range dropdown
3. Capture filter set to "Last 7 Days"

**Filter Options:**
- Last 7 Days
- Last 14 Days
- Last 30 Days
- Last 90 Days

**Fixed in v0.3.1:**
- ✅ Filter now properly affects displayed data
- ✅ Fixed SQL `INTERVAL` syntax
- ✅ Connected time_range selector to data load function
- ✅ Removed duplicate event handler

---

#### 2. Heatmap Visualization

Color-coded grid showing downtime frequency:

[📸 SCREENSHOT PLACEHOLDER]
**File:** `screenshots/station-heatmap-visualization.png`
**Caption:** Station heatmap showing failure patterns
**Instructions:**
1. Show full heatmap grid
2. Capture mix of colors (green, yellow, red)
3. Include legend explaining color scale

**Grid Layout:**
```
         Mon   Tue   Wed   Thu   Fri   Sat   Sun
ST10     ■■    ■■■   ■     ■■    ■     ■■■   ■■
ST11     ■     ■     ■■    ■     ■■■   ■■    ■
ST12     ■■■   ■■■   ■■■   ■■    ■■    ■     ■■
...
```

**Color Legend:**
- **Dark Green:** 0-1 failures (good)
- **Light Green:** 2-3 failures
- **Yellow:** 4-6 failures (monitor)
- **Orange:** 7-9 failures (attention needed)
- **Red:** 10+ failures (critical - prioritize maintenance)

---

#### 3. Interpreting the Heatmap

**Patterns to Look For:**

1. **Vertical Red Lines:** Specific day had plant-wide issues (e.g., power outage)
2. **Horizontal Red Lines:** Specific station has chronic problems
3. **Clusters:** Related stations failing together (upstream/downstream dependencies)
4. **Weekly Patterns:** Issues on specific weekdays (e.g., Monday startup problems)

**Action Items:**
- **Red Stations:** Schedule preventive maintenance
- **Pattern Clusters:** Investigate root cause (material quality, shift differences)
- **Trend Analysis:** Compare week-over-week to measure improvement

---

### Workflow Example

**Scenario:** Weekly reliability review

1. **Set Filter:** "Last 30 Days" to see monthly pattern
2. **Identify Red Stations:** Find chronic failure stations
3. **Check Details:** Click red cells to see specific failure times
4. **Correlate with Losses:** Cross-reference with loss category data
5. **Schedule PM:** Add worst stations to preventive maintenance plan
6. **Track Improvement:** Monitor next month to validate fixes

---

## Reports

**Tab:** Reports  
**Purpose:** Schedule automated email reports  
**Users:** Managers, Supervisors

### Features

#### 1. Report Configuration Card

[📸 SCREENSHOT PLACEHOLDER]
**File:** `screenshots/reports-configuration.png`
**Caption:** Reports configuration card with gradient background
**Instructions:**
1. Navigate to Reports tab
2. Show report configuration section (gradient teal card)
3. Capture form fields for report setup

**Recent Improvements (v0.3.1):**
- ✅ Gradient background: `bg-gradient-to-br from-teal-50 to-cyan-50 border-2 border-teal-200`
- ✅ Title in `text-xl font-bold text-gray-900`
- ✅ Labels in `text-base font-semibold text-gray-900`
- ✅ Better visual hierarchy

**Configuration Fields:**
- **Report Name:** Descriptive name (e.g., "Daily OEE Summary")
- **Report Type:** OEE, Downtime, Loss Pareto, Energy
- **Production Line:** Which line to include
- **Time Period:** Daily, Weekly, Monthly
- **Email Recipients:** Comma-separated email addresses
- **Schedule:** Time of day to send (e.g., "06:00 AM")

---

#### 2. Scheduled Reports List

[📸 SCREENSHOT PLACEHOLDER]
**File:** `screenshots/reports-scheduled.png`
**Caption:** List of scheduled reports with improved readability
**Instructions:**
1. Scroll to "Scheduled Reports" section
2. Show list of existing scheduled reports
3. Capture row with schedule details

**Recent Improvements (v0.3.1):**
- ✅ Title: `font-semibold text-base text-gray-900`
- ✅ Time: `text-sm text-gray-800`
- ✅ Recipients: `text-sm text-gray-900 font-medium`
- ✅ Row padding: `p-4` with `border border-gray-200`
- ✅ Card: `bg-white border-2 border-gray-200`

**List Columns:**
- **Report Name:** What report is scheduled
- **Schedule:** When it runs (e.g., "Daily at 06:00 AM")
- **Recipients:** Who receives it
- **Status:** Active, Paused, or Failed
- **Last Run:** When it last executed
- **Actions:** Edit, Pause, Delete buttons

---

#### 3. Creating a New Report

**Step-by-Step:**

1. **Enter Report Name:**
   ```
   Daily Line A01 OEE Report
   ```

2. **Select Report Type:**
   - Choose "OEE Summary" from dropdown

3. **Choose Line:**
   - Select "Line A01" or "All Lines"

4. **Set Time Period:**
   - Choose "Daily" (covers previous 24 hours)

5. **Add Recipients:**
   ```
   manager@company.com, supervisor@company.com, engineer@company.com
   ```

6. **Set Schedule Time:**
   - Enter "06:00" for 6 AM delivery

7. **Click "Create Report":**
   - System validates configuration
   - Adds to scheduled reports list
   - First run will be at next scheduled time

**Report Format:**
- **Subject:** `[Shopfloor Copilot] Daily Line A01 OEE Report - {date}`
- **Format:** PDF attachment + HTML email body
- **Content:** Charts, tables, summary text

---

### Available Report Types

#### 1. OEE Summary
- **Frequency:** Daily, Weekly, Monthly
- **Content:**
  - OEE, Availability, Performance, Quality trends
  - Target vs actual comparison
  - Top 5 losses
  - Downtime list

#### 2. Downtime Report
- **Frequency:** Daily, Weekly
- **Content:**
  - All downtime events
  - Duration per event
  - Loss category breakdown
  - MTBF (Mean Time Between Failures)
  - MTTR (Mean Time To Repair)

#### 3. Loss Pareto
- **Frequency:** Weekly, Monthly
- **Content:**
  - Pareto chart of loss categories
  - Cumulative percentage line
  - Loss category descriptions
  - Improvement recommendations

#### 4. Energy Report
- **Frequency:** Daily, Weekly, Monthly
- **Content:**
  - Total energy consumption
  - Energy per unit produced
  - Peak power events
  - Cost estimates
  - CO₂ emissions

---

### Workflow Example

**Scenario:** Setup weekly management report

1. **Navigate:** Go to Reports tab
2. **Name:** "Weekly Plant Summary"
3. **Type:** "OEE Summary"
4. **Line:** "All Lines"
5. **Period:** "Weekly"
6. **Recipients:** `plantmanager@company.com, operations@company.com`
7. **Schedule:** "Monday at 06:00"
8. **Create:** Click "Create Report" button
9. **Verify:** Check scheduled reports list shows new report
10. **Wait:** Report will be sent next Monday at 6 AM
11. **Review:** Open first report to ensure format is correct
12. **Adjust:** Edit schedule or recipients if needed

---

## Energy Tracking

**Tab:** Energy Tracking  
**Purpose:** Monitor energy consumption and sustainability metrics  
**Users:** Sustainability Managers, Plant Engineers

### Features

#### 1. Energy Stat Cards

Four primary metrics displayed in colored cards:

[📸 SCREENSHOT PLACEHOLDER]
**File:** `screenshots/energy-tracking-stats.png`
**Caption:** Energy tracking stat cards with large bold values
**Instructions:**
1. Navigate to Energy Tracking tab
2. Show all four stat cards in a row
3. Capture large values with colored backgrounds

**Recent Improvements (v0.3.1):**
- ✅ Main values: `text-4xl font-bold` (increased from `text-3xl`)
- ✅ Value colors: `text-yellow-900`, `text-green-900`, `text-orange-900`, `text-blue-900`
- ✅ Labels: `text-base font-semibold text-gray-900`
- ✅ Cards: Added `border-2 border-*-300` with `p-4` padding
- ✅ Backgrounds: `bg-yellow-50`, `bg-green-50`, `bg-orange-50`, `bg-blue-50`

**Card Layout:**
```
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Total Energy    │  │ Energy per Unit  │  │   Peak Power     │  │  CO₂ Reduction   │
│                  │  │                  │  │                  │  │                  │
│   12,450 kWh     │  │   0.85 kWh/unit  │  │    450 kW        │  │   5,200 kg       │
│                  │  │                  │  │                  │  │                  │
│ Today: +5.2%     │  │ Target: 0.80     │  │  Time: 14:23     │  │ vs Baseline      │
└──────────────────┘  └──────────────────┘  └──────────────────┘  └──────────────────┘
```

---

#### 2. Total Energy
- **Metric:** Cumulative kWh consumed
- **Period:** Configurable (today, this week, this month)
- **Trend:** % change vs previous period
- **Color:** Yellow (⚡ electricity theme)

**Interpretation:**
- Daily consumption should be consistent day-to-day
- Investigate spikes (equipment running inefficiently)
- Compare to production output (kWh per unit)

---

#### 3. Energy per Unit
- **Metric:** kWh consumed per unit produced
- **Period:** Same as total energy
- **Target:** Configurable target (e.g., 0.80 kWh/unit)
- **Color:** Green (efficiency theme)

**Interpretation:**
- **Below target:** Good - efficient production
- **Above target:** Investigate - energy waste or low production
- **Trending up:** Equipment degradation or process changes

**Improvement Actions:**
- Optimize cycle times (reduce idle power consumption)
- Upgrade to energy-efficient motors
- Improve maintenance (worn equipment uses more energy)

---

#### 4. Peak Power
- **Metric:** Maximum instantaneous power draw (kW)
- **Time:** When peak occurred
- **Threshold:** Warning level (e.g., > 400 kW)
- **Color:** Orange (warning theme)

**Interpretation:**
- High peaks increase electricity costs (demand charges)
- Multiple equipment starting simultaneously causes spikes
- Look for opportunities to stagger equipment startup

**Reduction Strategies:**
- Stagger production line startup
- Use soft starters for motors
- Schedule heavy loads during off-peak hours

---

#### 5. CO₂ Reduction
- **Metric:** kg CO₂ emissions avoided
- **Baseline:** Comparison vs previous year or industry average
- **Period:** Cumulative for reporting period
- **Color:** Blue (sustainability theme)

**Calculation:**
```
CO₂ Reduction (kg) = (Baseline kWh - Current kWh) × CO₂ per kWh factor
CO₂ factor: ~0.42 kg/kWh (varies by region and energy mix)
```

**Reporting:**
- Use for sustainability reports
- Track progress toward carbon neutrality goals
- Communicate improvements to stakeholders

---

### Workflow Example

**Scenario:** Monthly energy review meeting

1. **Navigate:** Go to Energy Tracking tab
2. **Set Period:** Choose "This Month" from filter
3. **Review Total:** Check if total kWh increased vs last month
4. **Check Efficiency:** Is kWh/unit trending up or down?
5. **Analyze Peaks:** Note peak power times - can we stagger?
6. **Calculate Savings:**
   - Energy cost = Total kWh × $0.12/kWh (example rate)
   - Demand charge = Peak kW × $15/kW (example rate)
7. **Set Goals:** Target kWh/unit reduction for next month
8. **Generate Report:** Use Reports tab to schedule monthly energy report

---

## Digital Twin

**Tab:** Digital Twin  
**Purpose:** Compare current performance to baseline targets  
**Users:** Process Engineers, Continuous Improvement Teams

### Features

#### 1. Baseline Data Table

[📸 SCREENSHOT PLACEHOLDER]
**File:** `screenshots/digital-twin-baseline.png`
**Caption:** Digital Twin baseline comparison table
**Instructions:**
1. Navigate to Digital Twin tab
2. Show baseline data table with blue header
3. Capture rows showing current vs target values

**Recent Improvements (v0.3.1):**
- ✅ Title: `text-2xl font-bold text-gray-900`
- ✅ Header row: `bg-blue-100 p-3 rounded`
- ✅ Header text: `text-gray-900`
- ✅ Line name: `font-semibold text-gray-900`
- ✅ Table values: `text-gray-900 font-medium`
- ✅ OEE badges: `text-base font-bold`
- ✅ Row padding: `p-3` with `border-t border-gray-300`

**Table Columns:**
- **Line:** Production line name
- **Target OEE:** Baseline goal (e.g., 85%)
- **Current OEE:** Actual performance (e.g., 87.5%)
- **Delta:** Difference (e.g., +2.5% in green)
- **Target Cycle Time:** Expected cycle duration (e.g., 45s)
- **Current Cycle Time:** Actual cycle duration (e.g., 43s)
- **Status:** Meeting target ✅ or Below target ⚠️

---

#### 2. Performance Comparison Chart

Visual comparison of actual vs target performance:

**Chart Types:**
- **Bar Chart:** Side-by-side comparison of target vs actual for each line
- **Gauge Chart:** Dial showing current performance against target
- **Trend Line:** Historical performance vs target band

**Color Coding:**
- **Green:** Exceeding target
- **Blue:** Meeting target (within ±2%)
- **Yellow:** Below target but within acceptable range
- **Red:** Significantly below target (requires action)

---

#### 3. Deviation Analysis

Automatically highlights lines/stations with largest deviations:

**Metrics:**
- **Overperforming:** Exceed target by > 5% (investigate for best practices)
- **On Target:** Within ±2% of target
- **Underperforming:** Below target by > 2% (needs improvement)

**Analysis Questions:**
1. **Overperforming:** What are they doing differently? Can we replicate?
2. **Underperforming:** What's causing shortfall? Equipment? Material? Process?

---

### Workflow Example

**Scenario:** Quarterly baseline review

1. **Navigate:** Go to Digital Twin tab
2. **Review Table:** Look for red deltas (below target)
3. **Identify Trends:** Are deviations consistent or sporadic?
4. **Focus on Worst:** Select line with largest negative delta
5. **Deep Dive:** Cross-reference with loss categories in KPI Dashboard
6. **Root Cause:** Use AI Diagnostics to understand why underperforming
7. **Action Plan:** Create improvement plan with specific actions
8. **Update Baseline:** If performance consistently exceeds target, raise the target
9. **Monitor:** Track weekly to measure improvement

---

## Ticket Insights

**Tab:** Ticket Insights  
**Purpose:** Track software development tickets and sprint progress (Jira integration)  
**Users:** Project Managers, Development Team

### Features

#### 1. Sprint Header

[📸 SCREENSHOT PLACEHOLDER]
**File:** `screenshots/ticket-insights-sprint.png`
**Caption:** Ticket Insights sprint header with gradient background
**Instructions:**
1. Navigate to Ticket Insights tab
2. Show sprint header card at top
3. Capture sprint name, dates, and goal

**Recent Improvements (v0.3.1):**
- ✅ Sprint card: `bg-gradient-to-r from-teal-50 to-cyan-50 border-2 border-teal-200`
- ✅ Sprint title: `text-2xl font-bold text-gray-900`
- ✅ Sprint dates: `text-base font-semibold text-gray-800`

**Sprint Info:**
- **Sprint Name:** e.g., "Sprint 6 - Diagnostics V2"
- **Dates:** Start and end date
- **Goal:** Sprint objective description
- **Status:** Active, Completed, or Planned

---

#### 2. Stats Cards

Five colorful cards showing ticket counts:

[📸 SCREENSHOT PLACEHOLDER]
**File:** `screenshots/ticket-insights-stats.png`
**Caption:** Ticket stats cards with gradient backgrounds and large numbers
**Instructions:**
1. Show all five stat cards in a row
2. Capture large white numbers on colored gradient backgrounds
3. Include card labels (Total, To Do, In Progress, Done, Blocked)

**Recent Improvements (v0.3.1):**
- ✅ All cards: `p-6 bg-gradient-to-br border-2 border-*-800`
- ✅ Numbers: `text-5xl font-bold text-white` (increased from `text-4xl`)
- ✅ Labels: `text-base font-medium text-white opacity-95`
- ✅ Card sizes increased significantly for better visibility

**Card Layout:**
```
┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐
│   Total    │  │   To Do    │  │In Progress │  │    Done    │  │  Blocked   │
│  (grey)    │  │   (blue)   │  │  (yellow)  │  │  (green)   │  │   (red)    │
│     42     │  │     12     │  │      8     │  │     20     │  │      2     │
│  tickets   │  │  tickets   │  │  tickets   │  │  tickets   │  │  tickets   │
└────────────┘  └────────────┘  └────────────┘  └────────────┘  └────────────┘
```

**Interpretation:**
- **Total:** All tickets in sprint
- **To Do:** Not started yet
- **In Progress:** Currently being worked
- **Done:** Completed
- **Blocked:** Cannot proceed (dependency or issue)

**Health Indicators:**
- **Good Sprint:** Most tickets done or in progress, few blocked
- **At Risk:** Many to-do late in sprint, multiple blocked
- **Overloaded:** Too many in progress (team spread thin)

---

#### 3. Progress Bar

Visual representation of sprint completion:

**Recent Improvements (v0.3.1):**
- ✅ Card: `p-6 border-2 border-gray-200`
- ✅ Title: `text-xl font-bold text-gray-900`
- ✅ Bar height: `h-10` with `shadow-inner`
- ✅ Percentage labels: `text-base font-semibold text-gray-900`

**Bar Segments:**
- **Green (Done):** Percentage completed
- **Yellow (In Progress):** Currently being worked
- **Red (Blocked):** Stuck issues
- **Grey (To Do):** Not started

**Example:**
```
Progress: 48% Complete
[████████████░░░░░░░░░░░░] 
  Done: 48%   In Progress: 19%   Blocked: 5%   To Do: 28%
```

---

#### 4. Issues List

Scrollable list of individual tickets:

**Columns:**
- **Key:** Ticket ID (e.g., "RAG-123")
- **Summary:** Brief description
- **Status:** Current state (To Do, In Progress, Done, Blocked)
- **Assignee:** Who's working on it
- **Priority:** High, Medium, Low

**Recent Improvements (v0.3.1):**
- ✅ Title: `text-xl font-bold text-gray-900`
- ✅ Issue summary: `text-sm font-medium text-gray-900`
- ✅ Assignee: `text-sm text-gray-800 font-medium`

**Actions:**
- Click row to see full details
- Filter by status or assignee
- Sort by priority or due date

---

#### 5. AI Insights Panel

AI-generated insights about sprint health:

**Recent Improvements (v0.3.1):**
- ✅ Section title: `text-xl font-bold text-gray-900`
- ✅ Pattern cards with `p-4` padding
- ✅ Type label: `text-sm font-bold text-gray-900`
- ✅ Insight text: `text-base text-gray-900`

**Insight Types:**

1. **Velocity Trend:**
   ```
   📈 Pattern: Velocity Increasing
   The team completed 15% more story points this sprint compared to last sprint.
   Consider increasing capacity planning for next sprint.
   ```

2. **Blocker Alert:**
   ```
   🚨 Blocker: RAG-145 Blocked for 5 Days
   Ticket "Database migration" has been blocked for 5 days.
   Issue: Waiting for DBA approval. Recommend escalation to unblock.
   ```

3. **Late Items:**
   ```
   ⚠️ Pattern: Late Sprint Items
   8 tickets still in "To Do" with 2 days remaining in sprint.
   Risk: Sprint goal may not be achieved. Consider moving items to next sprint.
   ```

**Usage:**
- Review insights during daily standup
- Use to identify risks early
- Take corrective action on blockers immediately

---

### Workflow Example

**Scenario:** Sprint planning and monitoring

**Sprint Start (Day 1):**
1. Navigate to Ticket Insights
2. Review sprint goal and total ticket count
3. Verify all tickets assigned to team members
4. Check for any blocked tickets before sprint starts
5. Take screenshot of stats for "Sprint Start" baseline

**Mid-Sprint (Day 7):**
1. Check progress bar - should be ~50% done
2. Review AI insights for velocity trends
3. Look for blocked tickets - unblock immediately
4. If too many "To Do" items, consider moving some to next sprint
5. Update sprint board based on current status

**Sprint End (Day 14):**
1. Verify "Done" percentage is close to 100%
2. Review any unfinished tickets - why incomplete?
3. Check AI insights for sprint retrospective data
4. Compare final stats to baseline
5. Calculate velocity for next sprint planning
6. Export sprint report for stakeholders

---

## Best Practices Across All Dashboards

### 1. Daily Review Routine

**Morning (Start of Shift):**
- Check Operations Dashboard for overnight issues
- Review KPI Dashboard for previous day summary
- Look at Station Heatmap for emerging failure patterns

**During Shift:**
- Monitor Operations Dashboard for real-time issues
- Use AI Diagnostics when issues arise
- Update Ticket Insights if working on improvements

**End of Shift:**
- Review energy consumption for the day
- Check if KPI targets were met
- Prepare notes for Shift Handover report

---

### 2. Weekly Management Review

**Every Monday (15 minutes):**
1. KPI Dashboard → Check weekly OEE trend
2. Station Heatmap → Identify stations needing PM
3. Energy Tracking → Review last week's consumption
4. Digital Twin → Compare to baseline targets
5. Reports → Verify automated reports were sent

---

### 3. Monthly Leadership Meeting

**First Monday of Month (30 minutes):**
1. KPI Dashboard → Month-over-month trends
2. Energy Tracking → Monthly consumption and cost
3. Digital Twin → Are baselines still realistic?
4. Reports → Generate custom monthly report
5. Ticket Insights → Review completed improvement projects

---

### 4. Accessibility Tips

All dashboards now follow WCAG AA standards:

- ✅ **High Contrast Text:** All text is dark (gray-900) on white backgrounds
- ✅ **Large Fonts:** Important values are `text-4xl` to `text-5xl`
- ✅ **Color Coding:** Not the only indicator (icons and text labels also used)
- ✅ **Keyboard Navigation:** Tab through all interactive elements
- ✅ **Screen Readers:** All charts have text descriptions

**For Visually Impaired Users:**
- Use browser zoom (Ctrl + +) to enlarge text
- Enable high contrast mode in browser
- Use keyboard shortcuts instead of mouse
- Screen reader support for critical data

---

### 5. Mobile Access

While optimized for desktop (1920x1080), dashboards work on tablets:

**Supported:**
- iPad Pro (12.9") - Full layout
- iPad (10.2") - Stacked layout
- Surface Pro - Full layout

**Not Recommended:**
- Smartphones (screen too small for data density)
- Use desktop or tablet for best experience

---

## Troubleshooting Common Issues

### Dashboard Not Updating

**Symptoms:** Data appears stale, no new values  
**Solutions:**
1. Click "Refresh" button if available
2. Check that backend services are running: `docker ps`
3. Verify network connectivity to OPC server
4. Check browser console for JavaScript errors (F12 → Console tab)
5. Try hard refresh: Ctrl + Shift + R (Windows) or Cmd + Shift + R (Mac)

---

### Filter Not Working

**Symptoms:** Changing filter doesn't affect displayed data  
**Solutions:**
1. Verify you clicked "Apply" or "Refresh" button after changing filter
2. Check that filter value is valid (not empty or null)
3. Clear browser cache and reload page
4. Check for error messages in notification area (top-right)

**Fixed in v0.3.1:**
- ✅ Station Heatmap filter now properly connected
- ✅ All filter dropdowns have white backgrounds with dark text
- ✅ Better visual feedback when filter is applied

---

### Chart Not Displaying

**Symptoms:** Empty space where chart should be  
**Solutions:**
1. Check that data exists for selected time period
2. Verify database connection: Settings → System Status
3. Try expanding time range (e.g., 7 days → 30 days)
4. Check browser console for rendering errors
5. Ensure JavaScript is enabled in browser

---

### Slow Performance

**Symptoms:** Dashboard takes long time to load or update  
**Solutions:**
1. Reduce time range (e.g., 90 days → 30 days)
2. Filter to specific line instead of "All Lines"
3. Check server CPU/memory usage: `docker stats`
4. Close unused tabs to free browser memory
5. Clear browser cache and cookies
6. Consider upgrading server hardware if consistently slow

---

## Advanced Tips

### 1. Bookmarking Favorite Views

Create browser bookmarks for frequently used dashboard configurations:

```
# KPI Dashboard - Line A01, Last 7 Days
http://localhost:8010/#tab=kpi&line=A01&days=7

# Operations Dashboard - Line A02
http://localhost:8010/#tab=operations&line=A02

# Station Heatmap - Last 30 Days
http://localhost:8010/#tab=heatmap&days=30
```

---

### 2. Exporting Data

Most dashboards support data export:

**Methods:**
1. **Right-click chart** → "Save Image As..." → Save as PNG
2. **Use browser print** → Ctrl + P → "Save as PDF"
3. **Export button** (if available) → Download CSV or Excel
4. **API access:** Use REST API for programmatic data access (see Chapter 10)

---

### 3. Custom Dashboards

Advanced users can create custom dashboards:

**Requirements:**
- Knowledge of Python and NiceGUI
- Access to source code
- Familiarity with database schema

**Process:**
1. Create new screen file in `apps/shopfloor_copilot/screens/`
2. Import required libraries and components
3. Query database or call APIs for data
4. Build UI with NiceGUI components
5. Register screen in main menu
6. Test thoroughly before deploying

**Example (simplified):**
```python
from nicegui import ui
from packages.db import get_db_connection

@ui.page('/my-dashboard')
async def my_dashboard():
    ui.label('My Custom Dashboard').classes('text-3xl font-bold')
    
    # Query data
    conn = get_db_connection()
    data = conn.execute('SELECT * FROM oee_metrics WHERE line = ?', ('A01',))
    
    # Display data
    with ui.row():
        for row in data:
            with ui.card():
                ui.label(f"OEE: {row['oee']}%").classes('text-2xl')
```

---

## Summary

Shopfloor Copilot provides **seven comprehensive dashboards** covering all aspects of manufacturing operations:

1. **KPI Dashboard** - Executive overview with OEE metrics
2. **Operations Dashboard** - Real-time line monitoring
3. **Station Heatmap** - Failure pattern visualization
4. **Reports** - Automated email reporting
5. **Energy Tracking** - Sustainability metrics
6. **Digital Twin** - Baseline comparison
7. **Ticket Insights** - Sprint tracking (Jira integration)

All dashboards feature:
- ✅ **WCAG AA compliant** text contrast
- ✅ **Modern UI** with gradient cards and bold typography
- ✅ **Responsive design** for desktop and tablet
- ✅ **Real-time updates** with manual refresh options
- ✅ **Filtering and customization** for specific workflows

**Recent improvements (v0.3.1):** 21 issues fixed, 15 screens enhanced, complete accessibility overhaul

---

**Next Chapter:** [Operator Q&A Guide →](09-operator-qna.md)

**Related Chapters:**
- [AI Diagnostics](07-ai-diagnostics.md) - Request diagnostics from dashboards
- [Best Practices](15-best-practices.md) - Workflow optimization
- [Troubleshooting](12-troubleshooting.md) - Fix common issues
