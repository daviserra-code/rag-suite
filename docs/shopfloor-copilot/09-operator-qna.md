# Chapter 9: Operator Q&A - Interactive Knowledge Assistant

**Tab:** Operator Q&A  
**Feature:** RAG-powered question answering system  
**Version:** 0.3.1 (Complete Redesign)  
**Last Updated:** December 26, 2025

---

## Overview

The **Operator Q&A** feature provides an intelligent, conversational interface for operators to ask questions about procedures, equipment, safety, and quality standards. It uses **Retrieval-Augmented Generation (RAG)** to ground all answers in your organization's actual documentation.

### What Makes It Unique?

**Traditional Search:**
> Search for "motor assembly troubleshooting"  
> Results: 47 documents, read them all yourself

**Operator Q&A:**
> Ask: "Motor ST20 is running slow, what should I check?"  
> Answer: Specific troubleshooting steps with citations to WI-23, section 4.2

---

## Complete Redesign (v0.3.1)

The Operator Q&A interface received a **complete redesign** in December 2025 to match modern chat application standards.

### Before & After

**Before (v0.3.0):**
- ❌ Plain white interface with grey text
- ❌ Difficult to read filters
- ❌ No visual hierarchy
- ❌ Citations hard to understand
- ❌ Generic appearance

**After (v0.3.1):**
- ✅ Modern gradient backgrounds
- ✅ Clear blue/white message bubbles
- ✅ Prominent filters with white dropdowns
- ✅ Beautiful citation cards
- ✅ Professional chat interface

[📸 SCREENSHOT PLACEHOLDER]
**File:** `screenshots/operator-qna-full-interface.png`
**Caption:** Complete Operator Q&A interface showing redesigned layout
**Instructions:**
1. Navigate to Operator Q&A tab
2. Show full interface with filters, suggestions, chat, and citations
3. Capture the modern gradient design

---

## Interface Components

### 1. Header

**Design:**
- Gradient background: `bg-gradient-to-r from-blue-600 to-indigo-600`
- Large smart_toy icon in white
- White title text: "Ask Questions About Procedures & Equipment"
- Clear Chat button with modern styling

[📸 SCREENSHOT PLACEHOLDER]
**File:** `screenshots/operator-qna-header.png`
**Caption:** Operator Q&A header with gradient blue background
**Instructions:**
1. Show header section at top of screen
2. Capture gradient from blue to indigo
3. Include smart_toy icon and title

**Purpose:**
- Clear identification of feature
- Easy access to clear chat function
- Professional branding

---

### 2. Filters Section

**Design:**
- Gradient card: `bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200`
- White filter dropdowns with dark text (`color: #111827`)
- Proper Material Design props: `outlined dense`
- Generous spacing: `gap-3`, `p-6`
- Clear section title with emoji: "🎯 Filters"

[📸 SCREENSHOT PLACEHOLDER]
**File:** `screenshots/operator-qna-filters.png`
**Caption:** Filter section with gradient background and white dropdowns
**Instructions:**
1. Show filters card at top of interface
2. Capture gradient blue background
3. Show one dropdown expanded to demonstrate white background

**Available Filters:**

#### Station Type Filter
**Options:**
- All Station Types (default)
- Assembly
- Press
- Welding
- Packaging
- Test
- Labeling
- Inspection
- Material Handling

**Purpose:** Narrows search to procedures relevant to specific equipment type

**Example:**
```
Question: "How do I calibrate the sensor?"
Filter: Welding
Result: Returns welding-specific calibration procedures
```

---

#### Document Type Filter
**Options:**
- All Document Types (default)
- Work Instructions (WI)
- Standard Operating Procedures (SOP)
- Troubleshooting Guides (TSG)
- Safety Procedures (SP)
- Quality Standards (QS)
- Maintenance Procedures (MP)
- Training Materials (TM)

**Purpose:** Focuses answers on specific document category

**Example:**
```
Question: "What's the lockout/tagout procedure?"
Filter: Safety Procedures
Result: Returns SP-LOTO-001 procedure specifically
```

---

#### Topic Filter
**Options:**
- All Topics (default)
- Safety
- Quality
- Maintenance
- Operation
- Troubleshooting
- Calibration
- Material Handling
- Emergency Response

**Purpose:** Groups content by subject matter

**Example:**
```
Question: "What should I do if I see smoke?"
Filter: Emergency Response
Result: Returns emergency shutdown procedures
```

---

#### Clear All Filters Button
- Modern button styling
- Located at bottom-right of filters card
- Resets all filters to "All" default
- Immediately refreshes suggestions

**Recent Improvements (v0.3.1):**
- ✅ All filter selectors have explicit white background
- ✅ Text color: `#111827` (dark grey-900) for maximum readability
- ✅ Proper Material Design props: `outlined dense bg-color=white`
- ✅ Clear visual separation from chat area
- ✅ Section title: `text-xl font-bold`

---

### 3. Quick Questions (Suggestions)

**Design:**
- Gradient card: `bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-200`
- Large heading: `text-xl font-bold text-gray-900`
- Button grid layout with icons
- Hover effects on buttons
- Icons aligned properly with text

[📸 SCREENSHOT PLACEHOLDER]
**File:** `screenshots/operator-qna-suggestions.png`
**Caption:** Quick questions section with gradient green background
**Instructions:**
1. Show suggestions card below filters
2. Capture green gradient background
3. Show all suggestion buttons with icons

**Suggested Questions:**

#### Safety Questions
- 🦺 "What are the lockout/tagout procedures?"
- 🚨 "How do I report a safety incident?"
- ⚠️ "What PPE is required for welding?"
- 🔥 "What's the fire extinguisher procedure?"

#### Quality Questions
- ✓ "How do I check torque values?"
- 📏 "What are the dimensional tolerances for part X?"
- 🔍 "How do I perform a first-article inspection?"
- 📊 "Where do I log quality issues?"

#### Troubleshooting Questions
- 🔧 "Motor is running slow, what should I check?"
- ⚡ "Station won't start, what's the checklist?"
- 🛠️ "How do I reset after an E-stop?"
- 📡 "Sensor keeps faulting, what could be wrong?"

#### Maintenance Questions
- 🔩 "What's the PM schedule for press stations?"
- 🧰 "How often should I lubricate bearings?"
- 📅 "When was last calibration for ST20?"
- 🧪 "How do I check hydraulic fluid levels?"

**How It Works:**
1. Click any suggestion button
2. Question automatically fills input field
3. Filters adjust if needed (e.g., safety question → Safety topic filter)
4. Chat sends question immediately
5. Response appears in chat area

**Customization:**
Suggestions update based on:
- Current shift (morning, afternoon, night)
- Production line selected in filters
- Recent frequently asked questions
- Trending issues (from diagnostics)

---

### 4. Chat Area

**Design:**
- **User Messages:**
  - Background: `bg-blue-600`
  - Text: `text-white`
  - Border radius: `rounded-2xl`
  - Shadow: `shadow-lg`
  - Aligned right
  - Padding: `p-4`
  
- **Assistant Messages:**
  - Background: `bg-white`
  - Border: `border-2 border-gray-200`
  - Text: `text-gray-900`
  - Aligned left
  - Padding: `p-4`
  - Markdown rendered for formatting

[📸 SCREENSHOT PLACEHOLDER]
**File:** `screenshots/operator-qna-chat.png`
**Caption:** Chat area showing user and assistant messages
**Instructions:**
1. Ask a question and get a response
2. Capture at least 2 exchanges (4 messages total)
3. Show blue user messages on right, white assistant messages on left

**Text Styling:**
- **Before (v0.3.0):** `text-sm` (14px) - too small
- **After (v0.3.1):** `text-base` (16px) with `leading-relaxed` - comfortable reading

**Markdown Support:**
- **Bold:** `**important**` → **important**
- **Italic:** `*emphasis*` → *emphasis*
- **Lists:** Bullet points and numbered lists
- **Code:** Inline `code` and code blocks
- **Links:** `[text](url)` → clickable links
- **Tables:** Formatted data tables

**Example Chat Exchange:**

**User (You):**
> How do I troubleshoot a slow motor on ST20?

**Assistant (Copilot):**
> For a motor running slow on Station ST20, follow this troubleshooting checklist:
> 
> **Immediate Checks:**
> 1. Verify motor is receiving correct voltage (should be 480V ±5%)
> 2. Check drive display for fault codes
> 3. Inspect encoder cable connections
> 4. Measure actual RPM vs setpoint
> 
> **Common Causes:**
> - **Drive parameter issue:** Speed setpoint may be configured incorrectly
> - **Encoder problem:** Position feedback failure causes speed reduction
> - **Mechanical binding:** Check for obstructions on motor shaft
> - **Thermal overload:** Motor may be in temperature protection mode
> 
> **Detailed Procedure:**
> See **WI-23: Motor Troubleshooting** (Section 4.2) for complete step-by-step instructions.
> 
> **Safety Note:**
> Always follow lockout/tagout procedures before inspecting motor components. See **SP-LOTO-001**.
> 
> Would you like me to provide more details on any of these steps?

---

### 5. Citations Section

**Design:**
- Appears below assistant messages
- Gradient backgrounds based on document type:
  - Work Instructions: `bg-gradient-to-r from-blue-50 to-blue-100`
  - SOPs: `bg-gradient-to-r from-green-50 to-green-100`
  - Safety: `bg-gradient-to-r from-red-50 to-red-100`
  - Quality: `bg-gradient-to-r from-purple-50 to-purple-100`
- Book emoji (📚) for source label
- Document ID in bold dark text
- Relevance score as percentage in blue
- Page numbers in dark grey
- Increased gap between citations: `gap-3`

[📸 SCREENSHOT PLACEHOLDER]
**File:** `screenshots/operator-qna-citations.png`
**Caption:** Citation cards with colored gradient backgrounds
**Instructions:**
1. Ask a question that returns multiple citations
2. Capture at least 3 citation cards
3. Show gradient backgrounds and relevance scores

**Citation Card Layout:**
```
┌────────────────────────────────────────────────┐
│ 📚 Source: Work Instruction                    │
│                                                 │
│ WI-23: Motor Troubleshooting                   │
│ Relevance: 94%                                  │
│ Pages: 12-15                                    │
│                                                 │
│ [View Full Document] button                     │
└────────────────────────────────────────────────┘
```

**Recent Improvements (v0.3.1):**
- ✅ Gradient backgrounds for visual appeal
- ✅ Document ID in `font-bold text-gray-900`
- ✅ Relevance score shown as percentage with blue color
- ✅ Better border and rounded corners
- ✅ Pages info in `text-gray-800` for readability

**Interpreting Relevance Scores:**
- **90-100%:** Highly relevant - primary source for answer
- **80-89%:** Very relevant - supporting information
- **70-79%:** Moderately relevant - related context
- **60-69%:** Somewhat relevant - tangential info
- **< 60%:** Low relevance - may not be directly useful

**Why Citations Matter:**
1. **Traceability:** Know where answer came from
2. **Verification:** Operator can check source document
3. **Compliance:** Audit trail for quality standards
4. **Trust:** Not AI invention - real documentation
5. **Learning:** Read full document for deeper understanding

---

### 6. Input Area

**Design:**
- Modern white card with blue border: `border-2 border-blue-300`
- Better placeholder text with emoji: "💬 Ask a question..."
- Proper textarea styling with 3 rows
- Large send button:
  - Background: `bg-blue-600`
  - Text: `text-white`
  - Hover: `bg-blue-700`
  - Icon: send (arrow)
- Disabled state when sending (prevents double-send)

[📸 SCREENSHOT PLACEHOLDER]
**File:** `screenshots/operator-qna-input.png`
**Caption:** Input area with textarea and send button
**Instructions:**
1. Show input area at bottom of screen
2. Type a sample question (don't send)
3. Capture modern styling with blue accents

**Recent Improvements (v0.3.1):**
- ✅ White card background for contrast
- ✅ Blue border for visual emphasis
- ✅ Larger send button for easier clicking
- ✅ Better placeholder text
- ✅ Disabled state feedback during processing

**Keyboard Shortcuts:**
- **Enter:** Send message (if single line)
- **Shift + Enter:** New line (if multi-line enabled)
- **Ctrl + K:** Clear chat
- **Ctrl + F:** Focus on input field

---

## How RAG Works (Behind the Scenes)

### The RAG Pipeline

```
┌─────────────────────────────────────────────────────────┐
│ 1. User Question                                         │
│    "How do I calibrate the torque wrench for ST18?"     │
└─────────────┬───────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Semantic Search (ChromaDB)                           │
│    - Convert question to vector embedding               │
│    - Search for similar documents in vector database    │
│    - Apply filters (station type, document type, topic) │
│    - Return top 5 most relevant chunks                  │
└─────────────┬───────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│ 3. Context Assembly                                      │
│    - Combine top 5 document chunks                       │
│    - Add metadata (document ID, section, page)          │
│    - Format for LLM consumption                          │
└─────────────┬───────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│ 4. LLM Generation (Ollama)                              │
│    - Send question + context to llama3.2                │
│    - Apply prompt template (answer from context only)   │
│    - Generate human-readable answer                      │
│    - Include citations to source documents              │
└─────────────┬───────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│ 5. Response Display                                      │
│    - Show answer in chat area                            │
│    - Display citation cards below answer                 │
│    - Render markdown formatting                          │
│    - Allow follow-up questions                           │
└─────────────────────────────────────────────────────────┘
```

### Key Concepts

#### 1. Vector Embeddings
- Each document is converted to a mathematical vector (list of numbers)
- Similar content has similar vectors
- Enables semantic search (meaning-based, not keyword matching)

**Example:**
```
Question: "How do I fix a jammed conveyor?"
Matches:
✅ "Clearing material blockages in transport systems" (semantic match)
✅ "Conveyor belt obstruction removal procedure" (keyword + semantic)
❌ "Jam storage container procedures" (keyword only - not relevant)
```

#### 2. Context Window
- LLM can only process limited text at once (~8000 tokens = ~6000 words)
- RAG retrieves only relevant chunks (not entire document library)
- Fits context within LLM limits while maximizing relevance

#### 3. Grounding
- LLM answer must come from retrieved context only
- Cannot invent information not in documents
- If no relevant context found, LLM says "I don't have information on that"

**Example of Grounding:**

**Question:** "What's the procedure for changing hydraulic fluid?"

**Scenario A - Context Found:**
> Based on **MP-HYD-005**, hydraulic fluid change procedure:
> 1. Shut down press and lockout
> 2. Drain reservoir using pump (takes ~15 minutes)
> 3. Replace filter element
> 4. Refill with ISO VG 46 fluid
> 5. Bleed air from system
> 
> See complete procedure in **MP-HYD-005, Section 3**.

**Scenario B - No Context Found:**
> I don't have specific information about hydraulic fluid change procedures in the knowledge base. 
> 
> Please contact maintenance supervisor or refer to equipment manufacturer's manual.
> 
> For general assistance, contact: maintenance@company.com

---

## Common Use Cases

### Use Case 1: Safety Procedure Lookup

**Scenario:** Operator needs lockout/tagout procedure

**Steps:**
1. Click suggestion: "What are the lockout/tagout procedures?"
2. System filters to Topic: Safety, Document Type: Safety Procedures
3. Retrieves SP-LOTO-001 from knowledge base
4. LLM generates step-by-step instructions with safety warnings
5. Operator follows procedure with confidence

**Expected Answer:**
> Lockout/Tagout (LOTO) procedure for Station ST18:
> 
> **Required PPE:**
> - Safety glasses
> - Lock and personal tag
> 
> **Steps:**
> 1. Notify affected personnel
> 2. Shut down equipment using normal stop procedure
> 3. Isolate all energy sources (electrical, pneumatic, hydraulic)
> 4. Apply personal lock to each energy isolation point
> 5. Attach personal tag with name and date
> 6. Attempt to restart (should not start - verify lockout)
> 7. Release stored energy (pneumatic pressure, hydraulic pressure)
> 8. Verify zero energy state with test equipment
> 
> **Removal:**
> Only the person who applied lock may remove it.
> 
> See **SP-LOTO-001** for complete procedure and exceptions.

---

### Use Case 2: Quality Standard Verification

**Scenario:** Operator unsure about torque specification

**Steps:**
1. Type: "What's the torque spec for M8 bolts on ST20?"
2. Filter: Station Type → Assembly, Document Type → Quality Standards
3. System retrieves QS-TORQUE-002
4. Answer includes torque value, tool calibration requirement, and verification method

**Expected Answer:**
> Torque specification for M8 bolts on Station ST20 (Motor Assembly):
> 
> **Specification:**
> - **Torque Value:** 25 Nm ± 2 Nm
> - **Tightening Sequence:** Star pattern (cross-wise)
> - **Thread Condition:** Clean, dry, no lubricant
> 
> **Tool Requirements:**
> - Calibrated torque wrench (range 10-50 Nm)
> - Last calibration: Check tool ID label (must be < 6 months)
> - Calibration record: See **CAL-T-203-Torque-Wrench**
> 
> **Verification:**
> - 100% inspection (every bolt)
> - Record torque value on traveler sheet
> - Flag any out-of-spec values to quality supervisor
> 
> Source: **QS-TORQUE-002, Section 4.3**

---

### Use Case 3: Troubleshooting Assistance

**Scenario:** Equipment fault, operator needs quick guidance

**Steps:**
1. Type: "ST15 showing fault code E-207, what does this mean?"
2. Filter: Station Type → Welding, Topic → Troubleshooting
3. System retrieves TSG-WELD-001
4. Answer explains fault code and resolution steps

**Expected Answer:**
> Fault Code E-207 on Station ST15 (Welding):
> 
> **Meaning:** Wire feed motor overcurrent
> 
> **Possible Causes:**
> 1. Wire spool tangled or jammed
> 2. Drive rolls need cleaning
> 3. Contact tip clogged
> 4. Liner blockage
> 5. Motor bearing failure (rare)
> 
> **Resolution Steps:**
> 1. **Acknowledge fault** and put station in safe mode
> 2. **Inspect wire path** from spool to gun
> 3. **Check wire spool** for tangles or binding
> 4. **Clean drive rolls** and check tension setting
> 5. **Replace contact tip** if clogged
> 6. **Clear liner** or replace if blocked
> 7. **Reset fault** and test
> 
> **If unresolved after these steps:**
> Contact maintenance - may require motor replacement.
> 
> **Safety:**
> Always lockout power before inspecting wire feed mechanism.
> 
> See **TSG-WELD-001, Section 7.4** for detailed troubleshooting.

---

### Use Case 4: Training & Onboarding

**Scenario:** New operator learning station operation

**Steps:**
1. Type: "How do I operate the press station for the first time?"
2. Filter: Station Type → Press, Document Type → Training Materials
3. System retrieves TM-PRESS-101
4. Answer provides step-by-step startup guide

**Expected Answer:**
> First-time operation of Press Station (ST10-ST13):
> 
> **Prerequisites:**
> - Completed safety training (ST-SAF-001)
> - Authorized operator badge
> - Supervisor signoff
> 
> **Startup Procedure:**
> 1. **Visual Inspection:**
>    - Check for obstacles under press
>    - Verify light curtain is clean
>    - Ensure E-stop not engaged
> 
> 2. **Power Up:**
>    - Turn key switch to ON position
>    - Wait for system self-test (30 seconds)
>    - Verify green "READY" indicator
> 
> 3. **Load Part:**
>    - Place part in fixture
>    - Verify correct orientation (datum mark aligned)
>    - Ensure all clamping pins engaged
> 
> 4. **Cycle Start:**
>    - Press green START button
>    - Keep hands clear (light curtain active)
>    - Wait for cycle completion (5-7 seconds)
> 
> 5. **Unload Part:**
>    - Wait for ram to fully retract
>    - Release clamps
>    - Remove part and inspect
> 
> **First-Day Guidelines:**
> - Run supervised for first 10 cycles
> - Ask questions immediately - no "dumb questions"
> - Review **TM-PRESS-101** training material
> - Practice E-stop procedure
> 
> **Emergency Contacts:**
> - Supervisor: Ext. 5555
> - Maintenance: Ext. 6666
> - Safety: Ext. 7777

---

## Best Practices

### For Operators

#### 1. Ask Specific Questions
**Bad:** "Tell me about welding"  
**Good:** "How do I adjust wire feed speed on ST15?"

**Why:** Specific questions return more actionable answers

---

#### 2. Use Filters Effectively
**Example:**
- If asking about safety → Set Topic filter to "Safety"
- If asking about specific station type → Set Station Type filter
- Filters reduce noise and improve answer relevance

---

#### 3. Read Citations
**Always check source documents for:**
- Complete procedure details
- Safety warnings
- Revision history (is it current?)
- Related procedures

---

#### 4. Follow Up with Questions
**Example Chat:**
> **You:** "How do I calibrate the torque wrench?"
> 
> **Copilot:** [Provides calibration procedure]
> 
> **You:** "What if I don't have the calibration fixture?"
> 
> **Copilot:** [Provides alternative or escalation path]

---

#### 5. Provide Feedback
If answer is:
- **Incomplete:** Ask follow-up question
- **Incorrect:** Report to supervisor (knowledge base may need update)
- **Outdated:** Check citation for revision date

---

### For Administrators

#### 1. Keep Knowledge Base Current
- Update documents when procedures change
- Remove obsolete procedures
- Add new equipment work instructions
- Review quarterly for accuracy

---

#### 2. Monitor Common Questions
- Track frequently asked questions
- Create quick suggestion buttons for common topics
- Identify training gaps (many questions on same topic)
- Update documentation if operators consistently confused

---

#### 3. Maintain Document Metadata
Each document in knowledge base should have:
- **Document ID:** Unique identifier (e.g., WI-23)
- **Title:** Clear, descriptive name
- **Station Type:** Applicable station types (tags)
- **Document Type:** WI, SOP, TSG, etc.
- **Topic:** Safety, Quality, Maintenance, etc.
- **Revision Date:** When last updated
- **Author:** Who created/maintains it
- **Pages:** Page count for citation reference

---

#### 4. Test Before Deploying
Before adding new documents:
1. Upload to test environment
2. Ask sample questions
3. Verify answers are accurate
4. Check citations point to correct pages
5. Deploy to production only after validation

---

## Troubleshooting

### Problem: Answer Not Relevant

**Possible Causes:**
1. Question too vague
2. Filters too restrictive
3. Content not in knowledge base
4. Poor document metadata

**Solutions:**
1. **Rephrase Question:** Be more specific
2. **Adjust Filters:** Remove restrictive filters
3. **Check Knowledge Base:** Verify document exists
4. **Review Metadata:** Ensure document is properly tagged

---

### Problem: No Answer Returned

**Possible Causes:**
1. No relevant documents found
2. ChromaDB service down
3. Network connectivity issue
4. Ollama LLM not responding

**Solutions:**
1. **Simplify Question:** Use simpler terms
2. **Check Services:** `docker ps` - verify all running
3. **Check Network:** Can you access other tabs?
4. **Restart Services:** `docker compose restart core-api ollama chroma`

---

### Problem: Slow Response Time

**Possible Causes:**
1. LLM inference is slow (10-30 seconds normal)
2. ChromaDB query is slow (large knowledge base)
3. Server CPU/memory saturated

**Solutions:**
1. **Be Patient:** Initial response can take 30 seconds
2. **Optimize Knowledge Base:** Remove unused documents
3. **Upgrade Hardware:** More CPU cores help LLM inference
4. **Use Faster LLM:** llama3.2-3B instead of llama3.2-8B (less accurate but faster)

---

### Problem: Citations Missing

**Possible Causes:**
1. LLM didn't cite sources (prompt issue)
2. Metadata missing from retrieved chunks
3. Answer came from LLM's training data (not RAG)

**Solutions:**
1. **Rephrase Question:** Be more specific to force RAG retrieval
2. **Check Prompt Template:** Verify citations required in system prompt
3. **Review Knowledge Base:** Ensure documents have proper metadata

---

## Advanced Topics

### Customizing Suggestions

Edit suggestion list in `operator_qna_interactive.py`:

```python
QUICK_QUESTIONS = [
    {
        "icon": "build",
        "label": "Motor Troubleshooting",
        "question": "How do I troubleshoot a motor running slow?",
        "filters": {"station_type": "Assembly", "topic": "Troubleshooting"}
    },
    {
        "icon": "security",
        "label": "LOTO Procedure",
        "question": "What are the lockout/tagout procedures?",
        "filters": {"document_type": "Safety Procedures", "topic": "Safety"}
    },
    # Add more suggestions...
]
```

---

### Adding New Document Types

1. **Update Filter Dropdown:**
```python
document_types = {
    "all": "All Document Types",
    "WI": "Work Instructions",
    "SOP": "Standard Operating Procedures",
    "NEW_TYPE": "New Document Type",  # Add this
    # ...
}
```

2. **Tag Documents in Knowledge Base:**
   - Add `document_type: NEW_TYPE` metadata when ingesting
   - Reindex existing documents if needed

3. **Update Citation Card Styling:**
```python
def get_citation_color(doc_type):
    colors = {
        "WI": "from-blue-50 to-blue-100",
        "SOP": "from-green-50 to-green-100",
        "NEW_TYPE": "from-purple-50 to-purple-100",  # Add this
        # ...
    }
    return colors.get(doc_type, "from-gray-50 to-gray-100")
```

---

### Improving Answer Quality

**Strategies:**

1. **Better Document Structure:**
   - Use clear headings
   - Number steps
   - Include examples
   - Add cross-references

2. **Richer Metadata:**
   - Add topic tags
   - Include equipment IDs
   - Tag by skill level
   - Add keywords

3. **Prompt Engineering:**
   - Refine system prompt for clarity
   - Add examples of good answers
   - Specify tone and format
   - Require citations

4. **Fine-Tuning LLM:**
   - Collect high-quality Q&A pairs
   - Fine-tune on domain-specific data
   - Balance general knowledge with specificity

---

## Summary

The **Operator Q&A** feature provides a modern, intelligent interface for accessing organizational knowledge:

- ✅ **Complete redesign (v0.3.1):** Modern chat interface with gradient cards
- ✅ **RAG-powered:** Answers grounded in actual documentation
- ✅ **Filtered search:** Narrow by station type, document type, topic
- ✅ **Citations:** Always shows source documents with relevance scores
- ✅ **Accessible:** WCAG AA compliant with clear contrast
- ✅ **Quick suggestions:** Common questions one-click away
- ✅ **Markdown support:** Rich formatting for clear answers

**Key Benefits:**
- **Faster answers:** No need to search through document library
- **Accurate information:** Grounded in approved procedures
- **Audit trail:** Citations provide traceability
- **Training tool:** New operators learn procedures quickly
- **Knowledge democratization:** Everyone has access to expertise

---

**Next Chapter:** [Shift Handover Guide →](10-shift-handover.md)

**Related Chapters:**
- [AI Diagnostics](07-ai-diagnostics.md) - Equipment-specific troubleshooting
- [Best Practices](15-best-practices.md) - Workflow optimization
- [Troubleshooting](12-troubleshooting.md) - Fix common issues
