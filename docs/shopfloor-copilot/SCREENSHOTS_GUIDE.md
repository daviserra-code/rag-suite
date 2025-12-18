# Screenshot Capture Guide

**Purpose:** This guide will help you capture all required screenshots for the Shopfloor Copilot documentation.

**Time Required:** ~30 minutes  
**Tool Needed:** Windows Snipping Tool (Win + Shift + S) or any screenshot tool

---

## Before You Start

1. **Open Shopfloor Copilot:** http://localhost:8010
2. **Maximize Browser Window:** Press F11 for full screen
3. **Prepare Screenshot Tool:** Windows Snipping Tool (Win + Shift + S)
4. **Create Naming Convention:** Use descriptive names

---

## Screenshot List (By Chapter)

### Chapter 3: Quick Start Guide (10 screenshots)

#### 1. quickstart-opc-browse.png
- **Tab:** Tab 15: OPC Explorer
- **Action:** 
  - Expand tree: Root → Objects → TORINO Plant → Line A01 → ST18
  - Click on "Status" node
- **Capture:** Full tab showing tree on left, node inspector on right
- **Save as:** `screenshots/quickstart-opc-browse.png`

#### 2. quickstart-semantic-signals.png
- **Tab:** Tab 16: Semantic Signals
- **Action:**
  - Enter Line ID: `A01`
  - Enter Station ID: `ST18`
  - Click "Load Semantic Signals"
- **Capture:** Full signals table with loss categories visible
- **Save as:** `screenshots/quickstart-semantic-signals.png`

#### 3. quickstart-diagnostics-request.png
- **Tab:** Tab 17: AI Diagnostics
- **Action:**
  - Select scope: `station`
  - Enter ID: `ST18`
  - **Before clicking "Explain"**
- **Capture:** Form with inputs filled
- **Save as:** `screenshots/quickstart-diagnostics-request.png`

#### 4. quickstart-diagnostics-output.png
- **Tab:** Tab 17: AI Diagnostics
- **Action:**
  - After diagnostic completes
  - Expand all 4 sections
- **Capture:** All 4 sections visible with content
- **Save as:** `screenshots/quickstart-diagnostics-output.png`

#### 5. quickstart-live-monitoring.png
- **Tab:** Tab 1: Live Monitoring
- **Capture:** Main dashboard overview
- **Save as:** `screenshots/quickstart-live-monitoring.png`

#### 6. quickstart-production-lines.png
- **Tab:** Tab 2: Production Lines
- **Capture:** Grid of line cards
- **Save as:** `screenshots/quickstart-production-lines.png`

#### 7. quickstart-heatmap.png
- **Tab:** Tab 4: Station Heatmap
- **Capture:** Color-coded heatmap
- **Save as:** `screenshots/quickstart-heatmap.png`

#### 8. quickstart-watchlist.png
- **Tab:** Tab 15: OPC Explorer
- **Action:**
  - Add 3-4 nodes to watchlist
  - Show watchlist panel
- **Capture:** Watchlist with live updating values
- **Save as:** `screenshots/quickstart-watchlist.png`

#### 9. quickstart-kpis.png
- **Tab:** Tab 16: Semantic Signals
- **Action:**
  - Scroll down to KPI cards section
- **Capture:** KPI cards showing OEE metrics
- **Save as:** `screenshots/quickstart-kpis.png`

#### 10. quickstart-line-diagnostic.png
- **Tab:** Tab 17: AI Diagnostics
- **Action:**
  - Select scope: `line`
  - Enter ID: `A01`
  - Click "Explain", wait for output
  - Expand Section 1
- **Capture:** Section 1 showing all stations in line
- **Save as:** `screenshots/quickstart-line-diagnostic.png`

---

### Chapter 4: OPC Explorer (8 screenshots)

#### 11. opc-connection-panel.png
- **Tab:** Tab 15: OPC Explorer
- **Action:**
  - Focus on connection section (top)
  - Show URL input and Connect button
- **Capture:** Connection controls area
- **Save as:** `screenshots/opc-connection-panel.png`

#### 12. opc-browse-tree-expanded.png
- **Tab:** Tab 15: OPC Explorer
- **Action:**
  - Expand tree fully: TORINO → A01 → ST18 → all child nodes
- **Capture:** Browse tree with multiple levels visible
- **Save as:** `screenshots/opc-browse-tree-expanded.png`

#### 13. opc-node-inspector.png
- **Tab:** Tab 15: OPC Explorer
- **Action:**
  - Click on any node (e.g., ST18/Temperature)
  - Show node inspector panel on right
- **Capture:** Node inspector showing NodeId, DataType, Value, Quality, Timestamp
- **Save as:** `screenshots/opc-node-inspector.png`

#### 14. opc-watchlist-multi.png
- **Tab:** Tab 15: OPC Explorer
- **Action:**
  - Add 5-6 nodes to watchlist
  - Include nodes from different stations
- **Capture:** Watchlist table with multiple rows
- **Save as:** `screenshots/opc-watchlist-multi.png`

#### 15. opc-write-value.png
- **Tab:** Tab 15: OPC Explorer
- **Action:**
  - Select a writable node (if available)
  - Show write value dialog/form
- **Capture:** Write value interface
- **Save as:** `screenshots/opc-write-value.png`

#### 16. opc-connection-status.png
- **Tab:** Tab 15: OPC Explorer
- **Action:**
  - Show connection status indicator (green dot or badge)
- **Capture:** Connection status display
- **Save as:** `screenshots/opc-connection-status.png`

#### 17. opc-node-tree-root.png
- **Tab:** Tab 15: OPC Explorer
- **Action:**
  - Collapse all, show only root level
- **Capture:** Root node + first level
- **Save as:** `screenshots/opc-node-tree-root.png`

#### 18. opc-example-scenario.png
- **Tab:** Tab 15: OPC Explorer
- **Action:**
  - Navigate to ST18
  - Show Status=FAULTED or other interesting state
- **Capture:** Example troubleshooting scenario
- **Save as:** `screenshots/opc-example-scenario.png`

---

### Chapter 7: AI Diagnostics (10 screenshots)

#### 19. diagnostics-tab-header.png
- **Tab:** Tab 17: AI Diagnostics
- **Action:**
  - Show tab button and header
- **Capture:** Tab 17 button in navigation
- **Save as:** `screenshots/diagnostics-tab-header.png`

#### 20. diagnostics-scope-selector.png
- **Tab:** Tab 17: AI Diagnostics
- **Action:**
  - Click scope dropdown
  - Show options: station, line
- **Capture:** Dropdown expanded
- **Save as:** `screenshots/diagnostics-scope-selector.png`

#### 21. diagnostics-input-form.png
- **Tab:** Tab 17: AI Diagnostics
- **Action:**
  - Fill form with scope + ID
  - Show example buttons (ST18, A01, etc.)
- **Capture:** Full form with all controls
- **Save as:** `screenshots/diagnostics-input-form.png`

#### 22. diagnostics-loading.png
- **Tab:** Tab 17: AI Diagnostics
- **Action:**
  - Click "Explain this situation"
  - **Immediately capture** while spinner showing
- **Capture:** Loading state with spinner
- **Save as:** `screenshots/diagnostics-loading.png`

#### 23. diagnostics-section1.png
- **Tab:** Tab 17: AI Diagnostics
- **Action:**
  - After completion, expand only Section 1
  - Collapse others
- **Capture:** Section 1 expanded (blue background)
- **Save as:** `screenshots/diagnostics-section1.png`

#### 24. diagnostics-section2.png
- **Tab:** Tab 17: AI Diagnostics
- **Action:**
  - Expand only Section 2
- **Capture:** Section 2 expanded (yellow background)
- **Save as:** `screenshots/diagnostics-section2.png`

#### 25. diagnostics-section3.png
- **Tab:** Tab 17: AI Diagnostics
- **Action:**
  - Expand only Section 3
- **Capture:** Section 3 expanded (green background)
- **Save as:** `screenshots/diagnostics-section3.png`

#### 26. diagnostics-section4.png
- **Tab:** Tab 17: AI Diagnostics
- **Action:**
  - Expand only Section 4
- **Capture:** Section 4 expanded (purple background)
- **Save as:** `screenshots/diagnostics-section4.png`

#### 27. diagnostics-metadata.png
- **Tab:** Tab 17: AI Diagnostics
- **Action:**
  - Scroll to metadata panel at bottom
- **Capture:** Metadata showing plant, timestamp, model, loss categories, RAG docs
- **Save as:** `screenshots/diagnostics-metadata.png`

#### 28. diagnostics-all-sections.png
- **Tab:** Tab 17: AI Diagnostics
- **Action:**
  - Expand all 4 sections + metadata
  - May need to scroll and take multiple shots, then stitch
- **Capture:** Full diagnostic output (can be tall screenshot)
- **Save as:** `screenshots/diagnostics-all-sections.png`

---

### General UI Screenshots (Optional but Recommended)

#### 29. main-dashboard.png
- **Tab:** Tab 1: Live Monitoring
- **Capture:** Full dashboard overview
- **Save as:** `screenshots/main-dashboard.png`

#### 30. tab-navigation.png
- **Tab:** Any
- **Capture:** Full tab bar showing all 23 tabs
- **Save as:** `screenshots/tab-navigation.png`

#### 31. kpi-dashboard.png
- **Tab:** Tab 7: KPI Dashboard
- **Capture:** KPI cards and charts
- **Save as:** `screenshots/kpi-dashboard.png`

#### 32. semantic-signals-table.png
- **Tab:** Tab 16: Semantic Signals
- **Capture:** Full signals table with loss category borders
- **Save as:** `screenshots/semantic-signals-table.png`

---

## Capturing Instructions

### Windows (Snipping Tool)

1. Press **Win + Shift + S**
2. Select **Rectangular Snip**
3. Drag to select area
4. Click notification to edit
5. **File → Save As**
6. Navigate to: `c:\Users\Davide\VS-Code Solutions\rag-suite\docs\shopfloor-copilot\screenshots\`
7. Enter filename (see list above)
8. Save as PNG

### Alternative: Browser Screenshot Extension

1. Install Chrome extension: "Full Page Screen Capture"
2. Click extension icon
3. Choose "Capture visible part" or "Capture entire page"
4. Download as PNG
5. Rename and move to screenshots folder

### macOS

1. Press **Cmd + Shift + 4**
2. Drag to select area
3. File saved to Desktop
4. Move to screenshots folder and rename

---

## Image Quality Guidelines

✅ **DO:**
- Use PNG format (not JPG)
- Capture at full resolution (1920x1080 minimum)
- Include relevant context (don't crop too tight)
- Ensure text is readable
- Use full browser window (hide dev tools)

❌ **DON'T:**
- Use low resolution
- Include personal data if present
- Crop out important UI elements
- Include unrelated windows/tabs

---

## After Capturing All Screenshots

### Step 1: Verify File Names

```powershell
# List all screenshots
cd "c:\Users\Davide\VS-Code Solutions\rag-suite\docs\shopfloor-copilot\screenshots"
Get-ChildItem -Name

# Should see 32 PNG files
```

### Step 2: Update Markdown Files

Replace placeholders like:
```markdown
![OPC Explorer Browse](screenshots/opc-browse-tree-expanded.png)
```

With actual filenames (already done in documentation).

### Step 3: Test Image Links

Open markdown preview in VS Code:
1. Open `docs/shopfloor-copilot/04-opc-explorer.md`
2. Press **Ctrl+Shift+V** (Preview)
3. Scroll through - images should load
4. Repeat for chapters 3 and 7

---

## Screenshot Checklist

Copy this checklist and check off as you go:

### Chapter 3: Quick Start
- [ ] quickstart-opc-browse.png
- [ ] quickstart-semantic-signals.png
- [ ] quickstart-diagnostics-request.png
- [ ] quickstart-diagnostics-output.png
- [ ] quickstart-live-monitoring.png
- [ ] quickstart-production-lines.png
- [ ] quickstart-heatmap.png
- [ ] quickstart-watchlist.png
- [ ] quickstart-kpis.png
- [ ] quickstart-line-diagnostic.png

### Chapter 4: OPC Explorer
- [ ] opc-connection-panel.png
- [ ] opc-browse-tree-expanded.png
- [ ] opc-node-inspector.png
- [ ] opc-watchlist-multi.png
- [ ] opc-write-value.png
- [ ] opc-connection-status.png
- [ ] opc-node-tree-root.png
- [ ] opc-example-scenario.png

### Chapter 7: AI Diagnostics
- [ ] diagnostics-tab-header.png
- [ ] diagnostics-scope-selector.png
- [ ] diagnostics-input-form.png
- [ ] diagnostics-loading.png
- [ ] diagnostics-section1.png
- [ ] diagnostics-section2.png
- [ ] diagnostics-section3.png
- [ ] diagnostics-section4.png
- [ ] diagnostics-metadata.png
- [ ] diagnostics-all-sections.png

### General UI (Optional)
- [ ] main-dashboard.png
- [ ] tab-navigation.png
- [ ] kpi-dashboard.png
- [ ] semantic-signals-table.png

---

## Troubleshooting

**Problem: UI not loading at http://localhost:8010**
```powershell
docker-compose ps
# Check shopfloor service is "Up"

docker-compose logs shopfloor --tail=20
# Check for errors
```

**Problem: OPC Explorer shows "Disconnected"**
```powershell
docker-compose restart opc-studio opc-demo
# Wait 10 seconds
# Refresh browser
```

**Problem: AI Diagnostics times out**
```powershell
docker ps | grep ollama
# Verify Ollama container running

# Update .env if needed
OLLAMA_BASE_URL=http://<container-name>:11434

docker-compose restart shopfloor
```

---

**Next Step:** After capturing screenshots, proceed to create remaining documentation chapters (6, 8-15).
