from fastapi import FastAPI
from pydantic import BaseModel
from .state import PlantState
from .historian import Historian

def build_api(state: PlantState, historian: Historian) -> FastAPI:
    app = FastAPI(title="OPC Studio API", version="0.2.0")

    class ScenarioReq(BaseModel):
        line: str = "A01"
        station: str = "ST17"
        event: str = "MaterialShortage"
        duration_min: float = 15
        impact: dict | None = None

    @app.get("/health")
    def health():
        return {"ok": True, "service": "opc-studio", "version": "0.2.0"}

    @app.get("/snapshot")
    def snapshot():
        return state.snapshot()

    @app.get("/historian/status")
    def hist_status():
        return {
            "ok": True,
            "enabled": historian.enabled,
            "interval_s": historian.interval_s,
            "last_write_ts": historian.last_write_ts,
        }

    @app.post("/scenario/apply")
    def apply_scenario(req: ScenarioReq):
        res = state.apply_scenario(req.model_dump())
        # Log event to DB (non-blocking best effort)
        if res.get("ok"):
            plant = state.data.get("plant", "PLANT")
            payload = req.model_dump()
            historian.write_event(plant, payload.get("line",""), payload.get("station",""), payload.get("event","Scenario"), payload)
        return res

    return app
