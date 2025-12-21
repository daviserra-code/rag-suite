from nicegui import ui

# Embedded CSS tokens (avoiding file I/O issues)
TOKENS_CSS = """:root{
  --brandTeal:#0F7C7C; --brandTealDark:#0B5D5D; --brandTealLight:#1FA3A3;
  --accentBlue:#0082C8; --accentGreen:#2EA44F;
  --danger:#D64545; --warning:#D39E00; --ok:#2CB34A;
  --ink:#1F2933; --inkMuted:#3E4C59;
  --border:#DDE2E8; --panel:#F5F7FA; --panelAlt:#EEF2F7;
  --canvas:#FFFFFF; --canvasMuted:#F7F9FB; --focus:#82D8D8;
  --r-sm:8px; --r-md:12px; --r-lg:16px; --r-xl:20px;
  --shadow-card:0 1px 2px rgba(0,0,0,0.06),0 1px 1px rgba(0,0,0,0.04);
  --shadow-modal:0 10px 25px rgba(0,0,0,0.20);
  --font-ui:Inter, Segoe UI, Roboto, Arial, sans-serif;
  --font-mono:JetBrains Mono, SFMono-Regular, Consolas, monospace;
}
:root.dark{
  --brandTeal:#1AA3A3; --brandTealDark:#0E7070; --brandTealLight:#2DC6C6;
  --accentBlue:#45A8E6; --accentGreen:#41C165;
  --danger:#F07B7B; --warning:#E6B54D; --ok:#44D168;
  --ink:#E6EDF5; --inkMuted:#B8C4CF;
  --border:#2A3540; --panel:#141A20; --panelAlt:#10161B;
  --canvas:#0B0F13; --canvasMuted:#0D1318; --focus:#30D0D0;
  --shadow-card:0 1px 2px rgba(0,0,0,0.35),0 1px 1px rgba(0,0,0,0.25);
  --shadow-modal:0 10px 25px rgba(0,0,0,0.55);
}
body{font-family:var(--font-ui); color:var(--ink); background:var(--canvasMuted);}
.sf-appbar{background:linear-gradient(180deg, var(--brandTealDark), var(--brandTeal)); color:#fff; padding:12px 20px; display:flex; align-items:center; gap:16px; box-shadow:var(--shadow-card); border-bottom:1px solid rgba(255,255,255,0.08);}
.sf-chip{background:#fff; border:1px solid var(--border); border-radius:999px; padding:6px 10px; color:var(--inkMuted);}
:root.dark .sf-chip{background:var(--panel); color:var(--ink); border-color:var(--border);}
.sf-badge{background:var(--brandTealLight); color:#fff; border-radius:8px; padding:4px 8px; font-weight:600;}
.sf-card{background:#fff; border:1px solid var(--border); border-radius:var(--r-lg); box-shadow:var(--shadow-card); padding:16px;}
:root.dark .sf-card{background:var(--panel);}
.sf-kpi{display:flex; flex-direction:column; gap:4px; background:var(--panel); border:1px solid var(--border); border-radius:var(--r-md); padding:16px;}
.sf-btn{background:var(--brandTeal); color:#fff; border:none; padding:10px 14px; border-radius:12px; font-weight:600; cursor:pointer;}
.sf-btn.secondary{background:#fff; color:var(--brandTealDark); border:1px solid var(--brandTealLight);}
:root.dark .sf-btn.secondary{background:transparent; color:var(--ink); border-color:var(--brandTealLight);}
.sf-btn.ghost{background:transparent; color:var(--brandTealDark); border:1px dashed var(--brandTealLight);}
.sf-table{width:100%; border-collapse:separate; border-spacing:0 8px;}
.sf-table tr{background:#fff; border:1px solid var(--border);}
:root.dark .sf-table tr{background:var(--panel);}
.sf-table td, .sf-table th{padding:10px 12px;}
.sf-table tr{border-radius:12px; overflow:hidden;}"""

def apply_shopfloor_theme(dark: bool | None = None):
    """Apply tokens and optionally set dark mode.
    dark=True  -> force dark
    dark=False -> force light
    dark=None  -> leave as-is (use NiceGUI default or system).
    """
    # Apply base theme tokens
    ui.add_head_html(f'<style>{TOKENS_CSS}</style>')
    
    # Apply global dark theme styles for industrial UI (always applied for consistency)
    ui.add_head_html('''
    <style>
        /* Global dark theme for all pages - loaded immediately to prevent FOUC */
        body {
            background: #0f172a !important;
            color: #e2e8f0 !important;
            transition: none !important; /* Prevent flash during navigation */
        }
        
        /* Dark theme for all cards */
        .nicegui-card, .q-card {
            background: #1e293b !important;
            border: 1px solid #334155 !important;
            color: #e2e8f0 !important;
        }
        
        /* Dark theme for inputs and selects */
        .q-field__control {
            background: #1e293b !important;
            color: #e2e8f0 !important;
        }
        
        .q-field__label, .q-field__native {
            color: #94a3b8 !important;
        }
        
        .q-field__input {
            color: #e2e8f0 !important;
        }
        
        /* Dark theme for tables */
        .q-table, .q-table__card {
            background: #1e293b !important;
            color: #e2e8f0 !important;
        }
        
        .q-table thead th {
            color: #f1f5f9 !important;
            background: #0f172a !important;
        }
        
        .q-table tbody td {
            color: #e2e8f0 !important;
            border-color: #334155 !important;
        }
        
        .q-table tbody tr:hover {
            background: #334155 !important;
        }
        
        /* Dark theme for buttons (non-colored) */
        .q-btn:not(.bg-primary):not(.bg-secondary):not(.bg-positive):not(.bg-negative):not(.bg-warning):not(.bg-blue):not(.bg-green):not(.bg-teal):not(.bg-purple):not(.bg-orange) {
            background: #334155 !important;
            color: #e2e8f0 !important;
        }
        
        /* Dark theme for dialogs and menus */
        .q-menu {
            background: #1e293b !important;
            border: 1px solid #334155 !important;
        }
        
        .q-menu .q-item {
            color: #e2e8f0 !important;
        }
        
        .q-menu .q-item:hover {
            background: #334155 !important;
        }
        
        .q-dialog__backdrop {
            background: rgba(15, 23, 42, 0.75) !important;
        }
        
        /* Dark theme for expansion panels */
        .q-expansion-item {
            background: #1e293b !important;
            color: #e2e8f0 !important;
        }
        
        /* Prevent any white flash during page transitions */
        .nicegui-content, .q-page {
            background: #0f172a !important;
            transition: none !important;
        }
    </style>
    ''')
    
    if dark is True:
        ui.dark_mode().enable()
        ui.add_head_html('<script>document.documentElement.classList.add("dark");</script>')
    elif dark is False:
        ui.dark_mode().disable()
        ui.add_head_html('<script>document.documentElement.classList.remove("dark");</script>')
