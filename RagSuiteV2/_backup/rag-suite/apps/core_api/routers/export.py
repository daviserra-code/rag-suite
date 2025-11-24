from fastapi import APIRouter
from pydantic import BaseModel
from weasyprint import HTML
from jinja2 import Template
import base64

router = APIRouter(tags=["export"])

class ChecklistReq(BaseModel):
    title: str
    steps: list[dict]

@router.post("/export/checklist")
def export_checklist(req: ChecklistReq):
    html = Template("""
    <html><body>
      <h1>{{ title }}</h1>
      <ol>
      {% for s in steps %}
        <li><strong>{{ s.id }}</strong> – {{ s.text }} {% if s.ref %}<em>({{ s.ref }})</em>{% endif %}</li>
      {% endfor %}
      </ol>
    </body></html>""").render(title=req.title, steps=req.steps)
    pdf_bytes = HTML(string=html).write_pdf()
    return {"ok": True, "pdf_base64": base64.b64encode(pdf_bytes).decode("utf-8")}
