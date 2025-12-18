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

**Shopfloor Copilot Version:** 0.3.0  
**Last Updated:** January 2025  
**Next Review:** April 2025
