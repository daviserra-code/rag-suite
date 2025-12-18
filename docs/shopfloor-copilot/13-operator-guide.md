# Chapter 13: Operator Quick Reference Guide

**One-Page Guide for Daily Operations**

Print this page and keep it near your workstation!

---

## Quick Access

**Shopfloor Copilot:** http://localhost:8010

**Most Used Tabs:**
- **Tab 15:** OPC Explorer (browse live equipment data)
- **Tab 16:** Semantic Signals (view loss categories)
- **Tab 17:** AI Diagnostics (get troubleshooting help)
- **Tab 1:** Live Monitoring (plant overview)

---

## Common Tasks

### 1. Check Station Status

**Time:** 10 seconds

1. Go to **Tab 15: OPC Explorer**
2. Browse tree: **Line → Station → Status**
3. Read value:
   - 🟢 **RUNNING** = Normal
   - 🟡 **STARVED** = Waiting for upstream
   - 🟡 **BLOCKED** = Downstream full
   - 🔴 **FAULTED** = Problem!

### 2. Get AI Troubleshooting Help

**Time:** 30 seconds

1. Go to **Tab 17: AI Diagnostics**
2. Select **station**
3. Enter station ID (e.g., `ST18`)
4. Click **"Explain this situation"**
5. Read Section 4 (checklist)

### 3. Monitor Multiple Stations

**Time:** 2 minutes

1. Go to **Tab 15: OPC Explorer**
2. Navigate to each station
3. Click **"Add to Watchlist"**
4. Watch values update every second

### 4. Find What's Causing Loss

**Time:** 1 minute

1. Go to **Tab 16: Semantic Signals**
2. Enter Line + Station IDs
3. Click **"Load Semantic Signals"**
4. Look for colored borders:
   - 🔴 Red = Availability loss (station down)
   - 🟡 Yellow = Performance loss (running slow)
   - 🟠 Orange = Quality loss (bad parts)

---

## Station States Explained

| Status | What It Means | What To Do |
|--------|---------------|------------|
| **RUNNING** | ✅ Normal operation | Monitor, no action needed |
| **STARVED** | ⏸️ Waiting for parts from upstream | Check previous station |
| **BLOCKED** | 🚫 Can't output, next station full | Check next station |
| **FAULTED** | 🔴 Equipment problem | Request diagnostic, call maintenance |
| **IDLE** | ⏸️ Ready but not producing | Check if work order active |
| **CHANGEOVER** | 🔄 Product/tool change in progress | Normal during setup |
| **MAINTENANCE** | 🔧 Under maintenance | Normal during PM |

---

## Loss Categories Quick Guide

### Red Border = Availability Loss (Station Down)

| Category | Meaning | Action |
|----------|---------|--------|
| **equipment_failure** | Breakdown | Call maintenance immediately |
| **upstream_starvation** | No parts coming | Fix upstream bottleneck |
| **downstream_blocking** | Output backed up | Clear downstream |
| **material_shortage** | Out of material | Replenish supply |

### Yellow Border = Performance Loss (Running Slow)

| Category | Meaning | Action |
|----------|---------|--------|
| **reduced_speed** | Below target speed | Check for mechanical issues |
| **minor_stops** | Frequent short stops | Identify repetitive cause |

### Orange Border = Quality Loss (Bad Parts)

| Category | Meaning | Action |
|----------|---------|--------|
| **process_defect** | Quality test failing | Check quality parameters |
| **reduced_yield** | More scrap than normal | Investigate root cause |

---

## Troubleshooting Flowchart

```
┌─────────────────┐
│ Problem Occurs  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ Check OPC Explorer      │
│ (Tab 15)                │
│ What's the Status?      │
└────┬────────────────────┘
     │
     ├─ FAULTED ──────────────┐
     │                        │
     ├─ STARVED ──────────────┤
     │                        │
     ├─ BLOCKED ──────────────┤
     │                        │
     └─ RUNNING but slow ─────┤
                              │
                              ▼
                    ┌──────────────────┐
                    │ Request          │
                    │ AI Diagnostic    │
                    │ (Tab 17)         │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Follow Section 4 │
                    │ Checklist        │
                    └────────┬─────────┘
                             │
                             ├─ Quick fix? ──► Fix it
                             │
                             └─ Complex? ───► Call maintenance
```

---

## Keyboard Shortcuts

*(Not yet implemented - future feature)*

| Shortcut | Action |
|----------|--------|
| `Ctrl+1` | Go to Live Monitoring |
| `Ctrl+O` | Go to OPC Explorer |
| `Ctrl+D` | Go to AI Diagnostics |
| `F5` | Refresh current view |
| `Ctrl+F` | Search/Filter |

---

## Emergency Contacts

*(Fill in your facility's contacts)*

| Issue | Contact | Phone | Extension |
|-------|---------|-------|-----------|
| **Equipment Breakdown** | Maintenance | ___________ | ___ |
| **Material Shortage** | Warehouse | ___________ | ___ |
| **Quality Issue** | Quality Manager | ___________ | ___ |
| **IT/System Issue** | IT Support | ___________ | ___ |
| **Safety Issue** | Safety Officer | ___________ | ___ |

---

## Do's and Don'ts

### ✅ DO:

- **Check OPC Explorer first** when investigating issues
- **Request AI Diagnostic** before calling maintenance (saves time)
- **Add important nodes to Watchlist** for continuous monitoring
- **Report patterns** if you see same issue repeatedly
- **Document what you did** if you fixed something

### ❌ DON'T:

- **Don't ignore warnings** - yellow/orange borders mean problems brewing
- **Don't restart equipment** without checking diagnostic first
- **Don't clear alarms** without understanding root cause
- **Don't skip Section 4** - it has the checklist to follow
- **Don't write values in OPC Explorer** unless you're trained and authorized

---

## Common Questions

**Q: Why is my diagnostic taking so long?**  
A: Diagnostics typically take 10-20 seconds. If > 30 seconds, refresh page.

**Q: What if "No procedures found" in Section 3?**  
A: System doesn't have work instructions uploaded yet. Follow Section 4 checklist instead.

**Q: Can I trust the AI recommendations?**  
A: Yes - AI only suggests based on actual data and documented procedures. But always use your judgment!

**Q: How do I know if a station is critical vs. just slow?**  
A: Check severity:
- 🔴 Red = Critical (needs immediate action)
- 🟡 Yellow = Warning (monitor, may need action)
- 🟢 Green = Info (normal operation)

**Q: Should I request line or station diagnostic?**  
A: 
- **Station:** If only one station has problem
- **Line:** If multiple stations affected or you suspect cascade failure

**Q: What if OPC Explorer shows "Disconnected"?**  
A: Refresh browser. If still disconnected, call IT support.

---

## Example Scenarios

### Scenario 1: ST18 Stopped

**Symptoms:** Production line backed up, ST18 not moving

**Steps:**
1. OPC Explorer → Navigate to ST18 → Check Status
2. Status shows: **FAULTED**
3. AI Diagnostics → Station → ST18 → Explain
4. Section 4 says: "Check motor encoder, verify power supply"
5. Check power supply ✅ (OK)
6. Check encoder cable ❌ (loose!)
7. Reconnect encoder cable
8. Reset fault → **RUNNING** ✅

**Resolution time:** 5 minutes  
**Downtime avoided:** 45 minutes (waiting for maintenance)

---

### Scenario 2: Line A01 Running Slow

**Symptoms:** Line producing 80 parts/hr instead of 120

**Steps:**
1. Check each station's speed in OPC Explorer
2. ST18 speed = 0% (all others 100%)
3. Semantic Signals → Load ST18
4. See: **performance.reduced_speed** (yellow border)
5. AI Diagnostics → Station → ST18
6. Section 2 explains: "Motor speed at 0% suggests stall"
7. Section 4: "Test motor manually, check drive communication"
8. Call maintenance with specific issue
9. Maintenance fixes drive communication in 15 minutes

**Resolution time:** 20 minutes  
**Specificity:** Saved 2 hours of troubleshooting by pinpointing drive issue

---

### Scenario 3: Quality Problems at ST20

**Symptoms:** Parts failing test, high scrap count

**Steps:**
1. OPC Explorer → ST20 → ScrapCount = 15 (high!)
2. Semantic Signals → Load ST20
3. See: **quality.process_defect** (orange border)
4. AI Diagnostics → Station → ST20
5. Section 1: "ScrapCount elevated, QualityScore at 87%"
6. Section 3: References "WI-45: Quality Troubleshooting"
7. Follow work instruction procedure
8. Adjust test fixture, quality returns to normal

**Resolution time:** 30 minutes  
**Parts saved:** Caught early, only 15 scrapped (vs. potentially 100+)

---

## Tips from Experienced Operators

💡 **"Check Watchlist first thing every shift"**  
Add your critical stations to watchlist at start of shift. Watch for changes.

💡 **"Use line diagnostics for cascade failures"**  
If 3+ stations are starved/blocked, request line diagnostic to find root cause.

💡 **"Screenshot the diagnostic output"**  
Take a photo with your phone if you need to show maintenance.

💡 **"Look for patterns over days"**  
If ST18 faults every Tuesday afternoon, there's a pattern (maybe delivery truck vibration?).

💡 **"Trust the loss categories more than the state"**  
A station can show RUNNING but have **performance.reduced_speed** - that's the real issue.

---

## Quick Command Reference

### Check System Health
```
Open browser → http://localhost:8010
All tabs should load (green checkmark in tab 1)
```

### Force Refresh Data
```
Click refresh button in tab
Or press F5
```

### Export Diagnostic for Email
*(Future feature - not yet implemented)*

---

## Your Notes

*(Use this space to write station-specific notes, common issues, or local procedures)*

---

---

**Need more help?**
- Read [Full User Guide](01-introduction.md)
- Check [Troubleshooting Guide](12-troubleshooting.md)
- Ask your shift supervisor

**System Version:** Shopfloor Copilot v0.3.0

**Last Updated:** January 2025
