# Screenshots Directory
**Shopfloor Copilot & OPC Studio Documentation**  
**Version:** 0.3.1  
**Date:** December 26, 2025

## Purpose

This directory contains all official screenshots for the Shopfloor Copilot and OPC Studio user & functional manual. Screenshots follow strict naming conventions and capture specifications to ensure:

- Visual consistency across documentation
- Domain correctness (aerospace_defence primary)
- Enterprise-grade documentation quality
- Zero redundant or placeholder images

---

## Directory Contents

### Required Screenshots (16 total)

| # | Filename | Section | Description |
|---|----------|---------|-------------|
| 01 | `manual_01_landing_overview.png` | Landing | Landing page with tiles and navigation |
| 02 | `manual_02_opc_studio_overview.png` | Landing | OPC Studio main dashboard |
| 03 | `manual_03_profile_selector.png` | Profiles | Domain profile selection (A&D selected) |
| 04 | `manual_05_semantic_snapshot.png` | Semantic | Runtime snapshot showing ST18 state |
| 05 | `manual_06_material_context_present.png` | Material | Material evidence present (ST10) |
| 06 | `manual_07_missing_material_evidence_ad.png` | Material | **CRITICAL** - Missing material evidence (ST18) |
| 07 | `manual_08_diagnostics_blocking_ad.png` | Diagnostics | BLOCKING status with A&D violations |
| 08 | `manual_09_violations_list.png` | Violations | Violations overview list |
| 09 | `manual_10_violation_timeline.png` | Violations | Violation lifecycle timeline |
| 10 | `manual_11_rag_citations.png` | RAG | AI explanation with citations |
| 11 | `manual_13_opc_browsing.png` | OPC Studio | OPC namespace browsing |
| 12 | `manual_14_custom_tags.png` | OPC Studio | Custom tag configuration |
| 13 | `manual_15_simulation.png` | OPC Studio | OPC simulation running |
| 14 | `manual_16_demo_ad_blocking.png` | Demo | A&D blocking scenario (ST18) |
| 15 | `manual_17_demo_pharma_blocking.png` | Demo | Pharma blocking scenario (ST25) |
| 16 | `manual_18_demo_happy_path.png` | Demo | Happy path scenario (ST10) |

---

## Naming Convention

All screenshots MUST follow this format:

```
manual_<section><feature><profile>.png
```

**Examples:**
- `manual_07_missing_material_evidence_ad.png`
  - `manual_` = prefix
  - `07` = screenshot number (sequential)
  - `missing_material_evidence` = feature description
  - `ad` = aerospace_defence profile (optional suffix)
  - `.png` = file format

**Rules:**
- Use underscores (not spaces or hyphens)
- Lowercase only
- Two-digit numbers (01, 02, ..., 16)
- PNG format only
- Profile suffix only when profile-specific (ad, pharma, auto)

---

## Capture Standards

### Technical Requirements
- **Resolution:** 1920x1080 minimum (or maximized browser window)
- **Format:** PNG (lossless)
- **File Size:** 50KB - 2MB (compress if needed)
- **Browser Zoom:** 100% (Ctrl+0)
- **Theme:** Dark mode (mandatory)

### Content Requirements
- **Profile:** aerospace_defence (primary), pharma_process for ST25 only
- **Stations:** ST18 (A&D blocking), ST25 (Pharma blocking), ST10 (happy path)
- **Data:** Demo seed data only (no production data)
- **UI:** Full window capture (no cropped panels)
- **State:** Application must be in specified state per CAPTURE_CHECKLIST.md

### Quality Standards
- ✅ Text readable (no blur, no artifacts)
- ✅ Dark theme consistent
- ✅ No loading spinners or intermediate states
- ✅ No personal/sensitive data visible
- ✅ No browser UI clutter (tabs, bookmarks, dev tools)
- ✅ Professional appearance

---

## Capture Process

### 1. Preparation
1. Start Shopfloor Copilot: `docker-compose up -d`
2. Access UI: http://localhost:8010
3. Load demo seed data (if not present)
4. Verify dark theme enabled
5. Set browser zoom to 100%

### 2. Capture
1. Open `CAPTURE_CHECKLIST.md`
2. Follow each screenshot specification exactly
3. Use Windows Snipping Tool (Win+Shift+S) or ShareX
4. Save with exact filename to this directory
5. Check off item in checklist

### 3. Verification
```powershell
# Run verification script
.\verify_screenshots.ps1

# Expected output: 16/16 screenshots found
```

### 4. Quality Check
- Manually review each screenshot
- Verify dark theme consistent
- Check text readability
- Confirm content matches specification

---

## Tools

### Recommended Capture Tools

**Windows:**
- **Snipping Tool** (Win+Shift+S) - Built-in, simple
- **ShareX** - Advanced, free - https://getsharex.com
  - Features: Auto-upload, annotations, hotkeys

**Browser Extensions:**
- Awesome Screenshot (Chrome/Firefox)
- Full Page Screen Capture

**Command Line:**
```powershell
# Compress all screenshots (if too large)
Get-ChildItem *.png | ForEach-Object {
    magick $_.Name -quality 85 $_.Name
}

# Resize to max width 1920px
Get-ChildItem *.png | ForEach-Object {
    magick $_.Name -resize 1920x1080\> $_.Name
}
```

### Verification Script
```powershell
# Check all screenshots present
.\verify_screenshots.ps1

# Output: Summary with found/missing counts
```

---

## Usage in Documentation

### Markdown Embedding

**Standard Format:**
```markdown
![Landing Page Overview](screenshots/manual_01_landing_overview.png)
*Figure 1.1: Shopfloor Copilot landing page with dashboard tiles*
```

**With Caption:**
```markdown
<figure>
  <img src="screenshots/manual_07_missing_material_evidence_ad.png" 
       alt="Missing Material Evidence">
  <figcaption>
    Figure 4.1: Missing material evidence warning for ST18 (A&D profile)
  </figcaption>
</figure>
```

**Before/After Comparison:**
```markdown
| Before | After |
|--------|-------|
| ![Before](screenshots/manual_16_demo_ad_blocking.png) | ![After](screenshots/manual_18_demo_happy_path.png) |
| ST18: BLOCKING | ST10: Normal Operation |
```

---

## Troubleshooting

### Problem: Screenshots too large (>2MB)
**Solution:**
```powershell
# Compress with ImageMagick
magick input.png -quality 85 -resize 1920x1080\> output.png

# Or use online tool: tinypng.com
```

### Problem: Dark theme not showing
**Solution:**
- Check Settings → Appearance → Theme: Dark
- Clear browser cache (Ctrl+Shift+Delete)
- Try incognito mode
- Check application CSS not overriding theme

### Problem: Text blurry in screenshot
**Solution:**
- Ensure browser zoom = 100% (Ctrl+0)
- Use PNG format (not JPG)
- Capture at higher resolution (4K display)
- Use ShareX with PNG optimization disabled

### Problem: Demo data not showing
**Solution:**
```bash
# Re-run seed script
python scripts/seed_demo_data.py

# Or restore from backup
docker-compose exec postgres psql -U shopfloor -d shopfloor_mes < backup.sql
```

---

## File Organization

```
screenshots/
├── README.md (this file)
├── CAPTURE_CHECKLIST.md (detailed capture instructions)
├── verify_screenshots.ps1 (verification script)
│
├── manual_01_landing_overview.png
├── manual_02_opc_studio_overview.png
├── manual_03_profile_selector.png
├── manual_05_semantic_snapshot.png
├── manual_06_material_context_present.png
├── manual_07_missing_material_evidence_ad.png (CRITICAL)
├── manual_08_diagnostics_blocking_ad.png
├── manual_09_violations_list.png
├── manual_10_violation_timeline.png
├── manual_11_rag_citations.png
├── manual_13_opc_browsing.png
├── manual_14_custom_tags.png
├── manual_15_simulation.png
├── manual_16_demo_ad_blocking.png
├── manual_17_demo_pharma_blocking.png
└── manual_18_demo_happy_path.png
```

---

## Next Steps

1. ✅ **Review `CAPTURE_CHECKLIST.md`** - Understand each screenshot requirement
2. ✅ **Prepare environment** - Start application, load demo data, enable dark theme
3. ✅ **Capture systematically** - Follow checklist order (1-16)
4. ✅ **Verify completeness** - Run `verify_screenshots.ps1`
5. ✅ **Quality check** - Review each screenshot manually
6. ✅ **Proceed to STEP C** - Use screenshots in manual assembly

**Estimated Time:** 45-60 minutes for all 16 screenshots

---

## Contact

For questions or issues with screenshot capture:
- Refer to `CAPTURE_CHECKLIST.md` for detailed instructions
- Check troubleshooting section above
- Review STEP B documentation guide

**Documentation Version:** 0.3.1  
**Last Updated:** December 26, 2025
