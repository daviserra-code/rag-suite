# Shopfloor Copilot - UI Style Guide
## Sprint 4 Enhancement - Dark Theme & Accessibility

### 🎨 Design Principles

1. **Dark-First Design**: All UIs use a consistent dark theme optimized for industrial environments
2. **High Contrast**: Text must be easily readable at a distance on industrial displays
3. **WCAG AA Compliant**: Minimum 4.5:1 contrast ratio for normal text
4. **Consistent Branding**: Teal accent colors maintain brand identity

---

## Color Palette

### Background Colors
```python
# Primary backgrounds
BG_PRIMARY = "bg-slate-900"      # #0f172a - Main background
BG_CARD = "bg-slate-800"          # #1e293b - Card/panel background
BG_ELEVATED = "bg-slate-700"      # #334155 - Hover states, elevated elements

# Never use these in dark theme:
❌ bg-white
❌ bg-gray-50
❌ bg-gray-100
```

### Text Colors (USE THESE!)
```python
# Import from theme.py
from apps.shopfloor_copilot.theme import TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED

TEXT_PRIMARY = "text-slate-900 dark:text-slate-100"      # #f8fafc - Headers, important text
TEXT_SECONDARY = "text-slate-700 dark:text-slate-300"    # #cbd5e0 - Body text, labels
TEXT_MUTED = "text-slate-600 dark:text-slate-400"        # #94a3b8 - Timestamps, metadata
TEXT_DISABLED = "text-slate-400 dark:text-slate-600"     # Disabled states only

# NEVER use these (poor contrast in dark theme):
❌ text-gray-400   # Too light/dark depending on theme
❌ text-gray-500   # Unreadable
❌ text-gray-600   # Marginal contrast
❌ text-grey-6     # NiceGUI grey variants are theme-unaware
❌ text-grey-7
```

### Brand Colors
```python
# Teal (primary brand)
"bg-teal-600"      # #0891b2 - Primary buttons, highlights
"text-teal-400"    # #2dd4bf - Interactive elements, links
"border-teal-500"  # Dividers, accents

# Status colors
"text-green-400"   # Success, online status
"text-red-400"     # Errors, offline status  
"text-yellow-400"  # Warnings, cautions
"text-blue-400"    # Information, notes
```

---

## Component Patterns

### ✅ Cards & Containers
```python
# Good - High contrast dark card
with ui.card().classes('bg-slate-800 border-slate-700'):
    ui.label('Card Title').classes('text-slate-100 text-lg font-semibold')
    ui.label('Card content goes here').classes('text-slate-300')

# Bad - Low contrast
with ui.card().classes('bg-gray-50'):  # ❌ Light background in dark theme
    ui.label('Title').classes('text-gray-600')  # ❌ Unreadable
```

### ✅ Data Tables
```python
# Good - Readable table headers and data
ui.label('Station').classes('text-slate-100 font-semibold')  # Header
ui.label('WS-101').classes('text-slate-300')                  # Data
ui.label('Updated 5 min ago').classes('text-slate-400 text-xs')  # Metadata

# Bad
ui.label('Station').classes('text-gray-600')  # ❌ Too dim
```

### ✅ Forms & Inputs
```python
# Labels should be clearly visible
ui.label('Station Name:').classes('text-slate-300 font-medium mb-1')
ui.input(placeholder='Enter name').classes('w-full')

# Bad
ui.label('Station Name:').classes('text-gray-500')  # ❌ Hard to read
```

### ✅ Status Indicators
```python
# Use semantic colors for status
ui.badge('Online', color='green').classes('text-green-100')
ui.badge('Warning', color='yellow').classes('text-yellow-100') 
ui.badge('Error', color='red').classes('text-red-100')

# For text status
ui.label('● Online').classes('text-green-400')
ui.label('● Warning').classes('text-yellow-400')
```

### ✅ Metrics & KPIs
```python
# Large numbers should be very bright
with ui.column().classes('bg-slate-800 p-4 rounded-lg'):
    ui.label('OEE').classes('text-slate-400 text-sm')
    ui.label('87.5%').classes('text-slate-100 text-3xl font-bold')
    ui.label('↑ 2.3% from last week').classes('text-green-400 text-xs')

# Bad
ui.label('87.5%').classes('text-gray-700')  # ❌ Not prominent enough
```

---

## Migration Guide

### Replacing Old Color Classes

| ❌ Old (Avoid) | ✅ New (Use Instead) | Context |
|----------------|----------------------|---------|
| `text-gray-400` | `text-slate-300` | Body text |
| `text-gray-500` | `text-slate-300` | Labels |
| `text-gray-600` | `text-slate-200` | Important labels |
| `text-gray-700` | `text-slate-100` | Headers |
| `text-gray-800` | `text-slate-100` | Strong emphasis |
| `text-gray-900` | `text-white` | Critical text |
| `text-grey-6` | `text-slate-300` | NiceGUI replacement |
| `text-grey-7` | `text-slate-200` | NiceGUI replacement |
| `bg-gray-50` | `bg-slate-800` | Card backgrounds |
| `bg-gray-100` | `bg-slate-700` | Elevated surfaces |
| `bg-white` | `bg-slate-800` | Never use white in dark theme |

### Quick Find & Replace Commands

```bash
# PowerShell commands to update color classes across files:

# Update text colors
Get-ChildItem -Path "apps/shopfloor_copilot" -Filter "*.py" -Recurse | 
    ForEach-Object {
        (Get-Content $_.FullName) `
            -replace 'text-gray-400', 'text-slate-300' `
            -replace 'text-gray-500', 'text-slate-300' `
            -replace 'text-gray-600', 'text-slate-200' `
            -replace 'text-gray-700', 'text-slate-100' `
            -replace 'text-grey-6', 'text-slate-300' `
            -replace 'text-grey-7', 'text-slate-200' |
        Set-Content $_.FullName
    }
```

---

## Component Examples

### Dashboard Card
```python
def create_kpi_card(title: str, value: str, trend: str = None):
    """Standard KPI card with proper contrast"""
    with ui.card().classes('bg-slate-800 border-slate-700 p-4'):
        ui.label(title).classes('text-slate-400 text-sm uppercase tracking-wide')
        ui.label(value).classes('text-slate-100 text-3xl font-bold mt-2')
        if trend:
            color = 'text-green-400' if '↑' in trend else 'text-red-400'
            ui.label(trend).classes(f'{color} text-sm mt-1')
```

### Data Table Row
```python
def create_table_row(station: str, status: str, value: str):
    """Table row with readable text"""
    with ui.row().classes('bg-slate-800 p-3 rounded-lg items-center gap-4'):
        ui.label(station).classes('text-slate-100 font-medium')
        
        status_color = 'text-green-400' if status == 'Online' else 'text-red-400'
        ui.label(f'● {status}').classes(status_color)
        
        ui.label(value).classes('text-slate-300')
```

### Section Header
```python
def create_section(title: str, description: str = None):
    """Section header with clear hierarchy"""
    ui.label(title).classes('text-slate-100 text-2xl font-bold mb-2')
    if description:
        ui.label(description).classes('text-slate-400 mb-4')
```

---

## Testing Checklist

Before committing UI changes, verify:

- [ ] All text is readable in dark theme
- [ ] No grey text on white/light backgrounds
- [ ] Status colors (green/red/yellow) are clearly visible
- [ ] KPI numbers use bright colors (slate-100 or white)
- [ ] Labels use medium contrast (slate-300 or slate-400)
- [ ] Hover states provide clear feedback
- [ ] Cards have visible borders (slate-700)
- [ ] No FOUC (Flash of Unstyled Content) on page load

---

## Tools & Resources

### Color Contrast Checker
Use online tools to verify WCAG compliance:
- https://contrast-ratio.com/
- https://webaim.org/resources/contrastchecker/

### Tailwind CSS Dark Mode
- Documentation: https://tailwindcss.com/docs/dark-mode
- Color reference: https://tailwindcss.com/docs/customizing-colors

### Development Tips
1. Use browser DevTools to inspect element colors
2. Test on different displays (bright office vs. dim shopfloor)
3. Review with actual users in target environment
4. Consider colorblind-friendly palettes for status indicators

---

## Sprint 4 Goals

1. ✅ Create unified dark theme system
2. ✅ Document color usage guidelines
3. 🔄 Migrate all pages to new color scheme
4. 🔄 Remove all grey-on-white instances
5. 🔄 Enhance visual hierarchy
6. 📝 Create reusable component library

---

*Last updated: Sprint 4 preparation - December 2025*
