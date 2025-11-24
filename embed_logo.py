import base64
import os

logo_path = r"C:\Users\davis\.gemini\antigravity\brain\b2b79e02-facf-4af4-aaca-5fcd88485e4b\shopfloor_copilot_logo_v1_fixed_1763849277783.png"
ui_path = r"c:\Users\davis\Documents\Visual Studio 2022\rag-suite\rag-suite\apps\shopfloor_copilot\ui.py"

with open(logo_path, "rb") as f:
    logo_data = f.read()
    logo_b64 = base64.b64encode(logo_data).decode("utf-8")

with open(ui_path, "r") as f:
    content = f.read()

# Construct the replacement line
new_line = f"                ui.image('data:image/png;base64,{logo_b64}').classes('h-12 w-auto').props('fit=scale-down')"

# Find the line to replace (it contains ui.image and /static/logo.png)
lines = content.splitlines()
new_lines = []
for line in lines:
    if "ui.image" in line and "/static/logo.png" in line:
        new_lines.append(new_line)
    else:
        new_lines.append(line)

with open(ui_path, "w") as f:
    f.write("\n".join(new_lines))

print("Successfully embedded logo base64 in ui.py")
