import time
from typing import Dict, Any
from .plant_model import load_model

class PlantState:
    """In-memory plant state for simulator + UA variables."""

    def __init__(self):
        self.model = load_model()
        self.started_at = time.time()
        self.data: Dict[str, Any] = {"plant": self.model.get("plant","PLANT"), "lines": {}}

        for line in self.model.get("lines", []):
            lid = line["id"]
            self.data["lines"][lid] = {
                "status": "RUNNING",
                "oee": 0.82,
                "availability": 0.90,
                "performance": 0.88,
                "quality": 0.93,
                "stations": { st["id"]: {
                    "state": "RUNNING",
                    "cycle_time_s": 42.0,
                    "good_count": 0,
                    "scrap_count": 0,
                    "alarms": []
                } for st in line.get("stations", [])}
            }

    def apply_scenario(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        line = payload.get("line", "A01")
        station = payload.get("station", "ST17")
        event = payload.get("event", "MaterialShortage")
        duration_min = float(payload.get("duration_min", 15))
        impact = payload.get("impact", {}) or {}

        ln = self.data["lines"].get(line)
        if not ln:
            return {"ok": False, "error": f"Unknown line '{line}'"}
        st = ln["stations"].get(station)
        if not st:
            return {"ok": False, "error": f"Unknown station '{station}'"}

        # Apply impacts (v0)
        if "availability" in impact:
            ln["availability"] = max(0.0, min(1.0, float(ln["availability"]) + float(impact["availability"])))
        if "performance" in impact:
            ln["performance"] = max(0.0, min(1.0, float(ln["performance"]) + float(impact["performance"])))
        if "quality" in impact:
            ln["quality"] = max(0.0, min(1.0, float(ln["quality"]) + float(impact["quality"])))
        ln["oee"] = round(ln["availability"] * ln["performance"] * ln["quality"], 4)

        alarms = impact.get("alarms", [])
        for a in alarms:
            if a not in st["alarms"]:
                st["alarms"].append(a)

        if event.lower() in ("materialshortage", "fault", "blocked", "starved"):
            st["state"] = "FAULTED" if event.lower() == "fault" else event.upper()

        return {"ok": True, "applied": {"line": line, "station": station, "event": event, "duration_min": duration_min, "impact": impact}}

    def snapshot(self) -> Dict[str, Any]:
        return {"ok": True, "data": self.data}
