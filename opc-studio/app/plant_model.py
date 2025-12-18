import json
import os
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
    """Load plant model from JSON file.
    
    Supports two formats:
    1. Single-plant (legacy): {"plant": "TORINO", "lines": [...]}
    2. Multi-plant (new): {"plants": [{"id": "TORINO", "lines": [...]}, ...]}
    
    For multi-plant, returns the plant specified by ACTIVE_PLANT env var or first plant.
    """
    p = Path(models_dir) / "plant_model.json"
    if not p.exists():
        return DEFAULT_MODEL
    
    data = json.loads(p.read_text(encoding="utf-8"))
    
    # Multi-plant format
    if "plants" in data:
        active_plant_id = os.getenv("ACTIVE_PLANT", "").strip()
        plants = data["plants"]
        
        # Find active plant or use first
        selected = None
        if active_plant_id:
            for p in plants:
                if p.get("id", "").upper() == active_plant_id.upper():
                    selected = p
                    break
        
        if not selected and plants:
            selected = plants[0]
        
        if selected:
            return {
                "plant": selected.get("id", "PLANT"),
                "plant_name": selected.get("name", ""),
                "location": selected.get("location", ""),
                "lines": selected.get("lines", [])
            }
    
    # Single-plant format (legacy)
    return data
