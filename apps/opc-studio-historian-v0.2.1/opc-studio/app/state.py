import time
from typing import Dict, Any, List
from .plant_model import load_model

def _normalize_id(s: str) -> str:
    return (s or "").strip()

class PlantState:
    """In-memory plant state for simulator + UA variables."""

    def __init__(self):
        self.model = load_model()
        self.started_at = time.time()
        self.data: Dict[str, Any] = {"plant": self.model.get("plant","PLANT"), "lines": {}}

        for line in self.model.get("lines", []):
            lid = _normalize_id(line["id"])
            self.data["lines"][lid] = {
                "status": "RUNNING",
                "oee": 0.82,
                "availability": 0.90,
                "performance": 0.88,
                "quality": 0.93,
                "stations": {}
            }
            for st in line.get("stations", []):
                sid = _normalize_id(st["id"])
                self.data["lines"][lid]["stations"][sid] = {
                    "state": "RUNNING",
                    "cycle_time_s": 42.0,
                    "good_count": 0,
                    "scrap_count": 0,
                    "alarms": []
                }

    def list_model(self) -> Dict[str, Any]:
        return {
            "plant": self.data.get("plant"),
            "lines": [
                {"id": lid, "stations": list(line["stations"].keys())}
                for lid, line in self.data.get("lines", {}).items()
            ]
        }

    def _resolve_line(self, line_id: str) -> str | None:
        want = _normalize_id(line_id)
        if want in self.data["lines"]:
            return want
        for k in self.data["lines"].keys():
            if k.lower() == want.lower():
                return k
        return None

    def _resolve_station(self, line_key: str, station_id: str) -> str | None:
        want = _normalize_id(station_id)
        stations = self.data["lines"][line_key]["stations"]
        if want in stations:
            return want
        for k in stations.keys():
            if k.lower() == want.lower():
                return k
        return None

    def apply_scenario(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        line_req = payload.get("line", "A01")
        station_req = payload.get("station", "ST17")
        event = payload.get("event", "MaterialShortage")
        duration_min = float(payload.get("duration_min", 15))
        impact = payload.get("impact", {}) or {}

        line_key = self._resolve_line(line_req)
        if not line_key:
            return {"ok": False, "error": f"Unknown line '{line_req}'. Available: {list(self.data['lines'].keys())}"}

        st_key = self._resolve_station(line_key, station_req)
        if not st_key:
            return {"ok": False, "error": f"Unknown station '{station_req}' for line '{line_key}'. Available: {list(self.data['lines'][line_key]['stations'].keys())}"}

        ln = self.data["lines"][line_key]
        st = ln["stations"][st_key]

        if "availability" in impact:
            ln["availability"] = max(0.0, min(1.0, float(ln["availability"]) + float(impact["availability"])))
        if "performance" in impact:
            ln["performance"] = max(0.0, min(1.0, float(ln["performance"]) + float(impact["performance"])))
        if "quality" in impact:
            ln["quality"] = max(0.0, min(1.0, float(ln["quality"]) + float(impact["quality"])))
        ln["oee"] = round(ln["availability"] * ln["performance"] * ln["quality"], 4)

        alarms: List[str] = impact.get("alarms", []) or []
        for a in alarms:
            if a not in st["alarms"]:
                st["alarms"].append(a)

        if event.lower() in ("materialshortage", "fault", "blocked", "starved"):
            st["state"] = "FAULTED" if event.lower() == "fault" else event.upper()

        return {"ok": True, "applied": {"line": line_key, "station": st_key, "event": event, "duration_min": duration_min, "impact": impact}}

    def snapshot(self) -> Dict[str, Any]:
        return {"ok": True, "data": self.data}
