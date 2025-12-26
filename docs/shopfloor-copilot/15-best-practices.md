# Chapter 15: Best Practices

**Production-Proven Guidelines for Shopfloor Copilot**

This chapter contains best practices, lessons learned, and recommendations for getting the most value from the system.

---

## General Principles

### 1. Start Simple, Scale Up

**✅ DO:**
- Start with 5-10 critical stations
- Master OPC Explorer and diagnostics first
- Add more features gradually
- Train operators in phases

**❌ DON'T:**
- Try to monitor entire plant day 1
- Enable all features at once
- Skip training
- Deploy without pilot testing

---

### 2. Data Quality First

**✅ DO:**
- Verify OPC node mappings are correct
- Test semantic mappings with real scenarios
- Populate RAG knowledge base with quality documents
- Keep work instructions up to date

**❌ DON'T:**
- Use generic/default mappings
- Ingest outdated procedures
- Skip YAML validation
- Ignore data quality issues

---

### 3. Trust but Verify

**✅ DO:**
- Cross-check AI diagnostics with your experience
- Validate recommendations before acting
- Report when AI is wrong (helps improve it)
- Use diagnostics as a guide, not gospel

**❌ DON'T:**
- Blindly follow recommendations
- Skip Section 4 checklist steps
- Assume AI knows your plant better than you
- Ignore safety procedures

---

## OPC Explorer Best Practices

### Connection Management

**Best Practice:** Use persistent connections

```yaml
# Good: Single connection for whole shift
- Connect once at shift start
- Keep connection open
- Reconnect only if disconnected

# Bad: Connect/disconnect repeatedly
- Don't disconnect after each read
- Don't create new connection per request
```

**Monitoring:**
```
✅ Watch connection status indicator
✅ Set up reconnect on failure
✅ Log connection drops for IT review
```

---

### Node Browsing

**Best Practice:** Use targeted browsing

```
✅ Good Navigation Pattern:
Root → Plant → Line A01 → ST18 → Temperature

❌ Bad: Browse entire tree every time
```

**Performance Tips:**
- Bookmark frequently used nodes (future feature)
- Use Watchlist for continuous monitoring
- Limit browse depth (don't expand all)

---

### Watchlist Usage

**Best Practice:** Strategic node selection

**Recommended Watchlist (Per Line):**
```
Priority 1 (Critical):
- Line status
- Bottleneck station status
- Emergency stop signals

Priority 2 (Important):
- All station speeds
- Buffer levels
- Alarm counts

Priority 3 (Nice-to-have):
- Temperatures
- Cycle times
- Quality scores
```

**Limit:** 20-30 nodes per watchlist (performance)

---

### Reading/Writing Values

**Best Practice:** Read-only default

```
✅ DO:
- Use read-only mode for operators
- Require authorization for writes
- Log all write operations
- Validate values before writing

❌ DON'T:
- Allow unrestricted writes
- Skip validation
- Write without understanding impact
```

**Write Authorization Matrix:**

| Role | Read | Write | Restart |
|------|------|-------|---------|
| Operator | ✅ | ❌ | ❌ |
| Technician | ✅ | ⚠️ Limited | ❌ |
| Engineer | ✅ | ✅ | ✅ |
| Manager | ✅ | ❌ | ❌ |

---

## Semantic Mapping Best Practices

### YAML Configuration

**Best Practice:** Hierarchical organization

```yaml
# ✅ Good: Organized by station type
station_types:
  assembly:
    description: "Motors, components"
    signals: [...]
  testing:
    description: "Quality inspection"
    signals: [...]
  packaging:
    description: "Final packaging"
    signals: [...]

# ❌ Bad: Flat structure with duplicates
station_ST18: [...]
station_ST19: [...]
station_ST20: [...]
```

---

### Loss Category Assignment

**Best Practice:** Start with the big 6

Focus on these high-impact categories first:

1. **availability.equipment_failure** (breakdowns)
2. **availability.upstream_starvation** (bottlenecks)
3. **performance.reduced_speed** (slow production)
4. **quality.process_defect** (scrap)
5. **performance.minor_stops** (micro-stops)
6. **availability.material_shortage** (no materials)

Add others as needed.

---

### Condition Logic

**Best Practice:** Specific to general ordering

```yaml
# ✅ Good: Most specific first
loss_mapping:
  - condition: value == 0
    loss_category: availability.equipment_failure
  - condition: value < 30
    loss_category: performance.reduced_speed
  - condition: value < 70
    loss_category: performance.minor_stops

# ❌ Bad: General first (blocks specific)
loss_mapping:
  - condition: value < 70
    loss_category: performance.minor_stops  # This matches first!
  - condition: value == 0  # Never reached
    loss_category: availability.equipment_failure
```

---

### Testing Mappings

**Best Practice:** Test before deploy

```bash
# 1. Edit YAML
nano opc-studio/config/semantic_mappings.yaml

# 2. Validate syntax
yamllint semantic_mappings.yaml

# 3. Restart OPC Studio
docker-compose restart opc-studio

# 4. Test with known scenarios
curl http://localhost:8040/semantic/station/ST18 | jq

# 5. Verify loss categories are correct
```

**Test Cases:**
- Normal operation (no loss categories)
- Each loss category scenario
- Edge cases (e.g., speed = 0, 50, 99, 100)

---

## AI Diagnostics Best Practices

### When to Request Diagnostics

**✅ Request Diagnostic When:**
- Station status changes to FAULTED
- Performance drops below 70%
- Quality issues arise
- Cascade failure (multiple stations affected)
- Before calling maintenance (save time)

**❌ Don't Request When:**
- Everything is normal (wastes LLM cycles)
- Issue already diagnosed 5 minutes ago
- Problem is obvious (e.g., emergency stop pressed)

**Frequency Guidelines:**
```
Same station/issue: Wait 5+ minutes between requests
Different stations: No limit
Line diagnostics: Wait 10+ minutes (expensive)
```

---

### Interpreting Output

**Best Practice:** Read all 4 sections

```
Section 1: WHAT is happening
↓
Section 2: WHY it's happening
↓
Section 3: WHAT TO DO (procedures)
↓
Section 4: WHAT TO CHECK (checklist)
```

**Common Mistake:** Jumping to Section 3, skipping Section 2

**Why Section 2 matters:**
- Explains root cause
- Helps prevent recurrence
- Educates operators

---

### Acting on Recommendations

**Best Practice:** Follow the checklist

```
✅ DO:
1. Read Section 4 completely
2. Work through checklist top-to-bottom
3. Check off each item as you go
4. Document what you found
5. If stuck, call maintenance with findings

❌ DON'T:
1. Skip steps ("I know the problem")
2. Randomize troubleshooting
3. Ignore safety warnings
4. Skip documentation
```

**Example Workflow:**

```
Diagnostic Section 4 says:
□ 1. Check power supply
□ 2. Verify encoder signals
□ 3. Test motor manually
□ 4. Inspect drive communication

Operator follows:
☑ 1. Power supply OK (logged: 24.1V)
☑ 2. Encoder OK (green LED on)
☐ 3. Motor doesn't respond to manual jog
   └─ STOP HERE
   └─ Call maintenance: "Motor not responding to manual jog, suspect drive issue"
```

**Result:** Maintenance knows exactly where to start, saves 30+ minutes.

---

### Line vs. Station Diagnostics

**Best Practice:** Use line for cascade failures

**When to use Line Diagnostic:**
```
✅ Multiple stations STARVED/BLOCKED
✅ Domino effect across line
✅ Unknown bottleneck location
✅ Performance drop across entire line
```

**When to use Station Diagnostic:**
```
✅ Single station FAULTED
✅ Isolated quality issue
✅ Known problem station
✅ Quick troubleshooting
```

**Performance:**
- Station: ~10s response time
- Line: ~20s response time (more data to analyze)

---

## RAG Knowledge Base Best Practices

### Document Preparation

**Best Practice:** Structure for AI consumption

**✅ Good Document Format:**
```markdown
# WI-23: Motor Assembly Troubleshooting

## Symptom: Motor Not Starting

**Checklist:**
1. Verify power supply (24V DC)
2. Check emergency stop released
3. Inspect encoder cable connection
4. Test motor drive communication

## Symptom: Motor Running Slow

**Checklist:**
1. Check speed controller setpoint
2. Verify PLC program
3. Inspect mechanical coupling
```

**❌ Bad Document Format:**
```
Motor stuff:
- idk check power???
- maybe encoder
- call John if broken
```

---

### Document Types Priority

**High Value (Ingest First):**
1. Work instructions (WI-*)
2. Troubleshooting guides
3. Equipment manuals (relevant sections)
4. Standard operating procedures (SOP)

**Medium Value:**
5. Maintenance logs (recent, relevant)
6. Quality procedures
7. Training materials

**Low Value (Ingest Later):**
8. General safety docs
9. Administrative procedures
10. Historical documents

---

### Ingestion Process

**Best Practice:** Batch ingest with metadata

```bash
# Good: Organized ingestion
python ingest_documents.py \
  --source docs/work_instructions/ \
  --doc-type work_instruction \
  --metadata '{"department": "assembly", "line": "A01"}'

# Bad: Dump everything
python ingest_documents.py --source all_docs/
```

**Metadata Tagging:**
```json
{
  "doc_type": "work_instruction",
  "station_type": "assembly",
  "equipment": "motor",
  "date_updated": "2025-01-15",
  "author": "Engineering",
  "version": "2.1"
}
```

**Benefits:**
- AI can filter relevant docs
- Easier to update later
- Track document lineage

---

### Keeping RAG Fresh

**Best Practice:** Regular updates

**Update Schedule:**
```
Daily:   - New work instructions
Weekly:  - Updated procedures
Monthly: - Equipment manual revisions
Yearly:  - Archive outdated docs
```

**Update Process:**
```bash
# 1. Delete outdated
curl -X DELETE http://localhost:8000/api/rag/document/WI-23-v1.0

# 2. Ingest new version
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source": "docs/work_instructions/WI-23-v2.0.pdf",
    "doc_type": "work_instruction"
  }'
```

---

## Deployment Best Practices

### Pilot Program

**Best Practice:** Start with one line

**Phase 1 (Week 1-2):** One line, OPC Explorer only
```
- Connect to demo/pilot line
- Train 2-3 operators
- Gather feedback
- Fix issues
```

**Phase 2 (Week 3-4):** Add Semantic Signals
```
- Configure YAML for pilot line station types
- Validate loss categories
- Train operators on semantic signals
```

**Phase 3 (Week 5-6):** Enable AI Diagnostics
```
- Populate RAG with pilot line documents
- Test diagnostics with real issues
- Compare AI recommendations vs. actual fixes
```

**Phase 4 (Week 7+):** Expand to other lines
```
- Replicate YAML for similar station types
- Scale training program
- Monitor system performance
```

---

### Training Program

**Best Practice:** Hands-on training

**Operator Training (2 hours):**
1. System overview (15 min)
2. OPC Explorer tutorial (30 min)
   - Browse tree
   - Watchlist
   - Read values
3. Semantic Signals (20 min)
   - Load signals
   - Interpret loss categories
4. AI Diagnostics (30 min)
   - Request diagnostic
   - Read output
   - Follow checklist
5. Hands-on practice (25 min)
   - Troubleshoot simulated scenario

**Engineer Training (4 hours):**
- All operator content +
- YAML configuration
- Loss category design
- RAG document ingestion
- API usage
- Troubleshooting system issues

---

### Success Metrics

**Best Practice:** Track KPIs

**System Usage Metrics:**
```
- Diagnostics requested per shift
- OPC nodes monitored
- Semantic signals loaded
- Average time to diagnosis
```

**Business Impact Metrics:**
```
- MTTR (Mean Time To Repair) reduction
- Downtime reduction
- False maintenance calls reduction
- Operator self-service rate
```

**Example Targets:**
```
MTTR: Reduce from 45min → 20min (55% improvement)
Diagnostics usage: 10+ per shift
Self-service: 30% of issues resolved by operators
```

---

## Security Best Practices

### Access Control

**Best Practice:** Role-based permissions

**Recommended Roles:**

**Operator:**
```
- Read OPC nodes
- View semantic signals
- Request diagnostics
- View reports
```

**Technician:**
```
- All operator permissions +
- Write OPC nodes (limited)
- Export reports
```

**Engineer:**
```
- All technician permissions +
- Edit YAML configs
- Ingest documents
- Access API
```

**Manager:**
```
- Read-only dashboards
- Reports
- Analytics
```

---

### Network Security

**Best Practice:** Isolate OT network

```
┌─────────────┐
│ IT Network  │ (Corporate, Internet)
└──────┬──────┘
       │
   Firewall
       │
┌──────┴──────┐
│ DMZ         │ (Shopfloor Copilot UI)
└──────┬──────┘
       │
   Firewall
       │
┌──────┴──────┐
│ OT Network  │ (OPC Servers, PLCs)
└─────────────┘
```

**Rules:**
- Allow UI → OPC Studio (read-only)
- Block direct IT → PLC access
- Log all OPC write operations
- Use VPN for remote access

---

### Data Protection

**Best Practice:** Secure sensitive data

**PII/Confidential Data:**
```
✅ DO:
- Anonymize production data if exporting
- Encrypt database backups
- Use HTTPS for UI access
- Secure API with authentication

❌ DON'T:
- Include operator names in logs
- Export customer data in reports
- Share API keys in plaintext
- Use default passwords
```

---

## Performance Optimization

### Database Tuning

**Best Practice:** Index frequently queried fields

```sql
-- Create indexes for common queries
CREATE INDEX idx_shift_records_timestamp ON shift_records(timestamp);
CREATE INDEX idx_oee_data_line_id ON oee_data(line_id);
CREATE INDEX idx_station_status ON station_status(station_id, timestamp);
```

**Retention Policy:**
```
Raw OPC data:   7 days (high frequency)
Semantic data:  90 days
Diagnostics:    1 year
Reports:        3 years
```

---

### Caching Strategy

**Best Practice:** Cache expensive queries

**What to Cache:**
```
✅ OPC snapshots (1-5 seconds)
✅ Semantic signals (1-5 seconds)
✅ Diagnostics output (5 minutes)
✅ Reports (15 minutes)

❌ Don't cache:
- Real-time alarms
- Watchlist updates
- Write operations
```

---

### Scaling Considerations

**Current Capacity:**
```
Stations:     Up to 500
OPC nodes:    Up to 10,000
Diagnostics:  Up to 100/hour
Users:        Up to 50 concurrent
```

**When to Scale:**
```
CPU > 80% sustained:     Add application replicas
Database > 80% storage:  Implement retention policy
RAG queries slow:        Add ChromaDB replicas
LLM queue > 10 requests: Add Ollama instances
```

---

## Troubleshooting Best Practices

### Systematic Approach

**Best Practice:** Layer-by-layer diagnosis

```
Layer 1: UI
- Can you access http://localhost:8010?
- Are tabs loading?

Layer 2: API
- Is API responding? (curl http://localhost:8010/health)

Layer 3: Services
- Are containers running? (docker-compose ps)

Layer 4: OPC Connection
- Is OPC Studio connected? (curl http://localhost:8040/status)

Layer 5: Data
- Is OPC server responding?
- Is data flowing?
```

**Stop at first failure, fix, retest.**

---

### Logging Strategy

**Best Practice:** Structured logging

**Log Levels:**
```
ERROR:   System failures, exceptions
WARNING: Degraded performance, missing data
INFO:    Normal operations, diagnostics requested
DEBUG:   Detailed troubleshooting (disable in production)
```

**What to Log:**
```
✅ All diagnostics requests + responses
✅ OPC connection changes
✅ YAML config reloads
✅ Failed API calls
✅ Performance metrics

❌ Don't log:
- Every OPC read (too verbose)
- Full snapshots (too large)
- Sensitive data
```

---

### Common Issue Resolution

**OPC Connection Issues:**
```bash
# Check OPC demo server
docker-compose logs opc-demo --tail=20

# Restart OPC stack
docker-compose restart opc-demo opc-studio

# Verify connection
curl http://localhost:8040/status
```

**Diagnostic Timeouts:**
```bash
# Check Ollama
docker ps | grep ollama

# Test LLM directly
curl http://compassionate_thompson:11434/api/generate \
  -d '{"model": "llama3.2", "prompt": "test"}'

# Check .env config
cat .env | grep OLLAMA_BASE_URL
```

**Semantic Signals Not Appearing:**
```bash
# Validate YAML
yamllint opc-studio/config/semantic_mappings.yaml

# Check OPC Studio logs
docker-compose logs opc-studio | grep "semantic"

# Test endpoint
curl http://localhost:8040/semantic/station/ST18 | jq
```

---

## Continuous Improvement

### Feedback Loop

**Best Practice:** Regular reviews

**Weekly:**
- Review diagnostic usage
- Collect operator feedback
- Identify missing features

**Monthly:**
- Analyze MTTR trends
- Update YAML mappings
- Refresh RAG documents

**Quarterly:**
- System performance review
- ROI calculation
- Roadmap prioritization

---

### Metrics Dashboard

**Best Practice:** Track key metrics

**Create Weekly Report:**
```
Diagnostics Requested:    45 (↑ 12% vs last week)
Average Response Time:    14.2s (↓ 2.1s vs last week)
MTTR:                     23min (↓ 35% vs baseline)
Operator Self-Service:    38% (↑ 15% vs last week)
False Positives:          3 (↓ 50% vs last week)
```

---

## Future-Proofing

### Design for Scale

**Best Practice:** Modular architecture

```
✅ Good:
- Microservices design (OPC Studio, Core API, Diagnostics separate)
- Stateless services (easy to replicate)
- Externalized config (YAML, .env)

❌ Bad:
- Monolithic application
- Hardcoded configurations
- Tight coupling between components
```

---

### Version Control

**Best Practice:** Track configuration changes

```bash
# Initialize git repo for configs
cd opc-studio/config
git init
git add semantic_mappings.yaml
git commit -m "Initial semantic mappings"

# Track changes
git log --oneline
# Shows history of mapping changes

# Rollback if needed
git revert <commit-hash>
```

---

### Documentation Maintenance

**Best Practice:** Living documentation

**Update Triggers:**
```
When adding station type    → Update semantic mapping chapter
When adding loss category    → Update loss categories reference
When changing API            → Update API reference
When fixing common issue     → Update troubleshooting guide
```

**Documentation Review Schedule:**
```
Monthly:   Update screenshots if UI changed
Quarterly: Review for accuracy
Yearly:    Major revision
```

---

## Summary Checklist

### Before Going Live

- [ ] OPC connection tested and stable
- [ ] Semantic YAML validated for all station types
- [ ] RAG knowledge base populated with work instructions
- [ ] Operators trained (2-hour session)
- [ ] Pilot tested on one line (2+ weeks)
- [ ] Success metrics defined and tracked
- [ ] Emergency contacts documented
- [ ] Backup/restore procedures tested
- [ ] Security hardening completed
- [ ] Documentation updated and accessible

---

**Next Steps:**

1. **Operators:** Print [Quick Reference Guide](13-operator-guide.md) and keep it handy
2. **Engineers:** Review [Configuration Guide](11-configuration.md)
3. **Managers:** Read [Manager Dashboard Guide](14-manager-guide.md)
4. **All:** Bookmark [Troubleshooting Guide](12-troubleshooting.md)

---

## UX Best Practices (v0.3.1+) 🆕

### Design System Guidelines

**Best Practice:** Consistent visual language across all screens

**Color Palette:**
```css
/* Backgrounds (Gradients) */
bg-gradient-to-br from-blue-50 to-indigo-50    /* Primary gradient */
bg-gradient-to-br from-green-50 to-emerald-50  /* Success states */
bg-gradient-to-br from-purple-50 to-pink-50    /* Special features */

/* Text Colors */
text-gray-900      /* Primary text (WCAG AA: 4.5:1 contrast) */
text-gray-700      /* Secondary text */
text-blue-700      /* Links and interactive elements */
text-green-700     /* Success messages */
text-red-700       /* Errors and warnings */

/* Card Backgrounds */
bg-white           /* Standard cards */
bg-gray-50         /* Secondary panels */
```

**Typography Scale:**
```css
text-3xl font-bold     /* Page headers */
text-xl font-semibold  /* Section headers */
text-base              /* Body text */
text-sm text-gray-600  /* Helper text */
```

**Spacing System:**
```css
p-6        /* Large padding (cards, containers) */
p-4        /* Medium padding (nested sections) */
p-3        /* Small padding (buttons, badges) */
gap-6      /* Large gaps (grid columns) */
gap-4      /* Medium gaps (form elements) */
gap-2      /* Small gaps (inline elements) */
```

**Component Patterns:**
```python
# Gradient Card with Shadow
with ui.card().classes('p-6 shadow-lg bg-gradient-to-br from-blue-50 to-indigo-50'):
    ui.label('Dashboard Title').classes('text-3xl font-bold text-gray-900 mb-4')
    ui.label('Subtitle text').classes('text-base text-gray-700')

# Interactive Button
ui.button('Action', on_click=handler).props('color=primary').classes('text-base')

# Status Badge
ui.badge('RUNNING', color='green').classes('text-sm font-semibold')
```

**Why This Matters:**
- ✅ Users instantly recognize familiar patterns
- ✅ Reduced cognitive load
- ✅ Faster task completion
- ✅ Professional appearance
- ✅ Easier maintenance (consistent codebase)

See [CHANGELOG.md](CHANGELOG.md#visual-design-system) for complete design token reference.

---

### Accessibility Guidelines (WCAG AA)

**Best Practice:** Design for all users

**Contrast Requirements:**
```
Text on Background:
✅ PASS: text-gray-900 on bg-white (18.6:1 ratio)
✅ PASS: text-gray-700 on bg-gray-50 (8.2:1 ratio)
❌ FAIL: text-gray-400 on bg-white (2.8:1 ratio) → USE text-gray-900

Required Minimums:
- Normal text: 4.5:1 contrast ratio
- Large text (18pt+): 3:1 contrast ratio
- UI components: 3:1 contrast ratio
```

**Color-Blind Safe Design:**
```python
# DON'T rely only on color
❌ ui.label('Error').style('color: red')  # Color-blind users might miss

# DO combine color with icons/text
✅ with ui.row().classes('gap-2 items-center'):
       ui.icon('error', color='red').classes('text-xl')
       ui.label('Error: Station not found').classes('text-red-700 font-semibold')
```

**Keyboard Navigation:**
```
All interactive elements must be keyboard accessible:
✅ Buttons: Tab to focus, Enter to activate
✅ Dropdowns: Arrow keys to navigate, Enter to select
✅ Cards: Focus visible with ring-2 ring-blue-500
✅ Skip links: Allow bypassing repeated navigation
```

**Screen Reader Support:**
```python
# Add semantic HTML and ARIA labels
ui.button('Search', on_click=search).props('aria-label="Search stations"')
ui.input('Station ID').props('aria-describedby="station-help"')
ui.label('Enter station number (1-50)').props('id="station-help"')
```

**Focus Indicators:**
```css
/* Always visible focus states */
focus:ring-2 focus:ring-blue-500 focus:ring-offset-2

/* Example */
ui.button('Filter').classes('focus:ring-2 focus:ring-blue-500')
```

**Testing Checklist:**
```
- [ ] All text meets 4.5:1 contrast (use WebAIM Contrast Checker)
- [ ] Interactive elements have visible focus indicators
- [ ] Color is not the only way to convey information
- [ ] All images have alt text
- [ ] Forms have proper labels and error messages
- [ ] Keyboard navigation works without mouse
- [ ] Screen reader announces all important state changes
```

**Tools:**
```bash
# Install axe DevTools extension (Chrome/Firefox)
# Audit page:
1. Open DevTools → axe tab
2. Click "Scan ALL of my page"
3. Fix issues flagged as "Violations"

# Manual checks:
1. Tab through interface (no trapped focus)
2. Zoom to 200% (text still readable)
3. View in grayscale (color not sole indicator)
```

**Common Fixes Applied in v0.3.1:**
```
Issue:                  Fix:
Grey text (WCAG fail)   → text-gray-900 (WCAG pass)
No focus indicator      → focus:ring-2 focus:ring-blue-500
Color-only status       → Icon + text + color
Unlabeled input         → aria-label added
Low contrast button     → bg-blue-700 → bg-blue-600 with border
```

See [THIRD_ROUND_FIXES.md](../THIRD_ROUND_FIXES.md) for accessibility improvements across all dashboards.

---

### Dashboard Design Best Practices

**Best Practice:** Information hierarchy and progressive disclosure

**Layout Patterns:**
```python
# 1. Header with Key Actions
with ui.row().classes('justify-between items-center mb-6'):
    ui.label('Dashboard Title').classes('text-3xl font-bold text-gray-900')
    with ui.row().classes('gap-2'):
        ui.button('Export', icon='download')
        ui.button('Refresh', icon='refresh')

# 2. Filters in Prominent Card
with ui.card().classes('p-6 mb-6 bg-white shadow-md'):
    ui.label('Filters').classes('text-xl font-semibold mb-4')
    with ui.grid(columns=3).classes('gap-4'):
        ui.select(['Line A01', 'Line A02'], label='Line')
        ui.input('Station ID', placeholder='e.g., ST18')
        ui.button('Apply Filters', on_click=filter_data)

# 3. Metrics Grid (Top Priority Info)
with ui.grid(columns=4).classes('gap-6 mb-6'):
    for metric in ['OEE', 'Availability', 'Performance', 'Quality']:
        with ui.card().classes('p-6 bg-gradient-to-br from-blue-50 to-indigo-50'):
            ui.label(metric).classes('text-sm text-gray-600')
            ui.label('87.3%').classes('text-3xl font-bold text-gray-900')

# 4. Detailed Data Table (Lower Priority)
with ui.card().classes('p-6 bg-white'):
    ui.label('Recent Events').classes('text-xl font-semibold mb-4')
    ui.table(columns=[...], rows=[...])
```

**Information Density:**
```
✅ DO:
- Most important data largest and at top
- Use white space generously (p-6 padding)
- Group related information in cards
- Limit to 7±2 items per section (cognitive limit)

❌ DON'T:
- Cram everything on one screen
- Use tiny fonts (text-xs) for important data
- Mix unrelated metrics in same card
- Create horizontal scrolling (breaks flow)
```

**Loading States:**
```python
# Show skeleton while loading
if loading:
    with ui.card().classes('p-6 animate-pulse'):
        ui.skeleton().classes('h-8 w-48 mb-4')  # Title
        ui.skeleton().classes('h-32 w-full')    # Content
else:
    # Real content
    with ui.card().classes('p-6'):
        ui.label('Dashboard Title').classes('text-xl font-semibold')
        # ... data ...
```

**Empty States:**
```python
# Helpful message when no data
if not data:
    with ui.card().classes('p-12 text-center bg-gray-50'):
        ui.icon('inbox', size='64px').classes('text-gray-400 mb-4')
        ui.label('No data available').classes('text-xl text-gray-600 mb-2')
        ui.label('Select a line and date range to view metrics').classes('text-gray-500')
        ui.button('Configure Filters', on_click=show_filters).classes('mt-4')
```

**Real-Time Updates:**
```python
# Poll for updates without jarring refresh
ui.timer(5.0, lambda: update_dashboard())  # Refresh every 5s

# Show update indicator
with ui.row().classes('gap-2 items-center text-sm text-gray-600'):
    ui.spinner(size='sm')
    ui.label('Updating...')  # Only show while fetching
```

See [Chapter 8](08-dashboards.md) for dashboard-specific design patterns.

---

### Form Design Best Practices

**Best Practice:** Clear, forgiving input validation

**Input Flexibility (Fuzzy Matching):**
```python
# Example from AI Diagnostics (v0.3.1)
def normalize_station_id(raw_input: str) -> str:
    """Accept flexible station ID formats."""
    cleaned = raw_input.strip().upper()
    
    # Extract number: "ST18", "st18", "18", "Station 18" → "ST18"
    if cleaned.startswith('ST'):
        return cleaned  # Already formatted
    elif cleaned.startswith('STATION'):
        num = cleaned.replace('STATION', '').strip()
        return f'ST{num}'
    elif cleaned.isdigit():
        return f'ST{cleaned}'  # Just number → add prefix
    else:
        raise ValueError(f'Invalid format: {raw_input}')

# User Experience:
✅ "18" → Accepts and converts to "ST18"
✅ "st18" → Accepts and normalizes to "ST18"
✅ "Station 18" → Accepts and converts to "ST18"
❌ "abc" → Clear error: "Invalid format: abc"
```

**Error Messages:**
```python
# BAD: Technical jargon
❌ "KeyError: 'station_id' not in request.json"

# GOOD: Actionable guidance
✅ "Station ID is required. Please enter a station number (e.g., ST18 or 18)."

# BETTER: Suggest correction
✅ "Station 'ST99' not found. Did you mean ST09? Available: ST01-ST50."
```

**Form Layout:**
```python
# Vertical layout for complex forms (easier to scan)
with ui.column().classes('gap-4 max-w-md'):
    ui.input('Line ID', placeholder='A01').classes('w-full')
    ui.input('Station ID', placeholder='18').classes('w-full')
    ui.select(['Day', 'Night'], label='Shift').classes('w-full')
    with ui.row().classes('gap-2 justify-end w-full'):
        ui.button('Cancel', on_click=close).props('flat')
        ui.button('Submit', on_click=submit).props('color=primary')
```

**Validation Feedback:**
```python
# Real-time validation (not just on submit)
station_input = ui.input('Station ID')

def validate_station(e):
    value = e.value
    if not value:
        station_input.props('error error-message="Required"')
    elif not is_valid_station(value):
        station_input.props('error error-message="Invalid format (use ST## or ##)"')
    else:
        station_input.props('error=false')  # Clear error

station_input.on('blur', validate_station)
```

See [Chapter 7](07-ai-diagnostics.md#flexible-station-id-input) for fuzzy matching implementation.

---

### Performance Best Practices

**Best Practice:** Optimize for perceived speed

**Lazy Loading:**
```python
# Don't load all data upfront
❌ stations = fetch_all_stations()  # 10,000 rows, 5s wait

# Load on demand
✅ stations = []  # Start empty
✅ ui.button('Load Stations', on_click=lambda: fetch_stations())  # User-triggered
```

**Debouncing:**
```python
# Don't search on every keystroke
import asyncio

search_input = ui.input('Search')
search_timer = None

async def debounced_search(e):
    global search_timer
    if search_timer:
        search_timer.cancel()
    
    async def do_search():
        await asyncio.sleep(0.3)  # Wait 300ms
        perform_search(e.value)
    
    search_timer = asyncio.create_task(do_search())

search_input.on('input', debounced_search)
```

**Pagination:**
```python
# Limit rows per page
ui.table(
    columns=[...],
    rows=data[page*50:(page+1)*50],  # 50 rows per page
    pagination={'rowsPerPage': 50}
)
```

**Progress Indicators:**
```python
# Show progress for long operations
with ui.dialog() as progress_dialog:
    with ui.card():
        ui.label('Loading data...').classes('text-lg mb-4')
        progress = ui.linear_progress(value=0)

async def load_data():
    progress_dialog.open()
    for i in range(100):
        # Simulate work
        await asyncio.sleep(0.05)
        progress.value = i / 100
    progress_dialog.close()
```

**Connection Timeouts:**
```python
# Extended timeout for OPC connections (v0.3.1)
async def connect_opc(endpoint: str):
    client = Client(endpoint)
    try:
        # Increased from 10s → 15s (handles slow networks)
        await asyncio.wait_for(client.connect(), timeout=15.0)
        return client
    except asyncio.TimeoutError:
        raise ConnectionError(
            f'Connection to {endpoint} timed out after 15 seconds. '
            f'Check: 1) Server is running, 2) Firewall allows 4840, '
            f'3) Network is stable.'
        )
```

See [Chapter 4](04-opc-explorer.md#connection-improvements-v031) for connection optimization details.

---

### Testing Best Practices

**Best Practice:** Test with real user workflows

**User Acceptance Testing (UAT):**
```
Test Scenario: Shift handover workflow
1. Login as operator
2. Navigate to Shift Handover tab
3. Select: Day shift, Line A01, Today
4. Verify filters are readable (white background, dark text)
5. Generate report
6. Verify text contrast meets WCAG AA
7. Add notes
8. Email report to next shift
9. Confirm email received

Expected: Complete workflow in < 3 minutes with no confusion
```

**Accessibility Testing:**
```bash
# Keyboard-only navigation test
1. Unplug mouse
2. Tab through entire interface
3. Verify all functions accessible
4. Check focus indicators visible
5. Test Escape key closes dialogs

# Screen reader test (NVDA on Windows)
1. Download NVDA (free)
2. Close eyes
3. Navigate interface by ear only
4. Verify all elements announced correctly
5. Check form errors are read aloud
```

**Cross-Browser Testing:**
```
Test in:
- Chrome (primary)
- Firefox
- Edge
- Safari (if macOS available)

Check:
- Layout consistent
- Gradients render correctly
- Interactions work
- Performance acceptable
```

**Load Testing:**
```bash
# Simulate 50 concurrent users
ab -n 1000 -c 50 http://localhost:8010/api/diagnostics/ST18

# Check:
- Response time < 2s (p95)
- No errors
- CPU < 80%
- Memory stable
```

---

## Screenshot Capture Best Practices 🆕

**Best Practice:** Consistent, high-quality screenshots for documentation

**Preparation:**
```
Before capturing:
1. Clear browser cache (Ctrl+Shift+Delete)
2. Zoom to 100% (Ctrl+0)
3. Resize window to 1920x1080 (or document actual size)
4. Close unnecessary tabs/windows in screenshot
5. Use clean test data (avoid sensitive info)
```

**Capture Tools:**
```
Windows:
- Snipping Tool (Win+Shift+S) → Rectangular selection
- ShareX (advanced, free) → https://getsharex.com

macOS:
- Cmd+Shift+4 → Drag to select area
- Cmd+Shift+3 → Full screen

Browser Extensions:
- Awesome Screenshot (Chrome/Firefox)
- Full Page Screen Capture
```

**Naming Convention:**
```
Format: <chapter>-<feature>-<state>-<number>.png

Examples:
08-kpi-dashboard-overview-01.png
08-kpi-dashboard-filters-02.png
09-operator-qna-chat-interface-01.png
09-operator-qna-citations-panel-02.png
CHANGELOG-shift-handover-before-01.png
CHANGELOG-shift-handover-after-02.png
```

**Image Processing:**
```bash
# Resize to max 1200px wide (keeps file size reasonable)
magick input.png -resize 1200x input.png

# Add border (helps visibility in docs)
magick input.png -bordercolor gray -border 2 input.png

# Compress
optipng -o7 input.png  # Lossless
```

**Organization:**
```
docs/
  shopfloor-copilot/
    images/
      chapter-01/
        01-introduction-overview-01.png
        01-introduction-architecture-02.png
      chapter-08/
        08-kpi-dashboard-overview-01.png
        08-kpi-dashboard-filters-02.png
      changelog/
        shift-handover-before-01.png
        shift-handover-after-02.png
```

**Markdown Embedding:**
```markdown
<!-- Standard image -->
![KPI Dashboard Overview](images/chapter-08/08-kpi-dashboard-overview-01.png)
*Figure 8.1: KPI Dashboard showing OEE metrics for Line A01*

<!-- Image with caption -->
<figure>
  <img src="images/chapter-08/08-kpi-dashboard-overview-01.png" alt="KPI Dashboard">
  <figcaption>Figure 8.1: KPI Dashboard with filters and metrics tiles</figcaption>
</figure>

<!-- Before/After comparison -->
| Before (v0.3.0) | After (v0.3.1) |
|-----------------|----------------|
| ![Before](images/changelog/shift-handover-before-01.png) | ![After](images/changelog/shift-handover-after-02.png) |
| Grey text hard to read | Dark text, high contrast |
```

**Placeholder Format (Used in Documentation):**
```markdown
> **📸 SCREENSHOT PLACEHOLDER:**  
> **Filename:** `08-kpi-dashboard-overview-01.png`  
> **Caption:** "KPI Dashboard Overview - Line A01 Day Shift"  
> **What to Capture:**
> - Navigate to Tab 2 (KPI Dashboard)
> - Select: Line A01, Day Shift, Last 7 Days
> - Ensure 4 KPI tiles visible (OEE, Availability, Performance, Quality)
> - Show recent downtimes table below
> - Capture full viewport (1920x1080)
```

---

**Shopfloor Copilot Version:** 0.3.1  
**Last Updated:** December 2025  
**Next Review:** March 2026
