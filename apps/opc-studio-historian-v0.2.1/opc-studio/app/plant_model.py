import json
from pathlib import Path
from typing import Any, Dict

DEFAULT_MODEL = {
  "plant": "TORINO",
  "lines": [{
    "id": "A01",
    "stations": [{"id": "ST17"}, {"id": "ST18"}]
  }]
}

def load_model(models_dir: str = "/app/models") -> Dict[str, Any]:
    p = Path(models_dir) / "plant_model.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return DEFAULT_MODEL
