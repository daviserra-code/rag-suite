import os
import time
import asyncio
from typing import Dict, Any, Optional
from .db import get_conn

HISTORIAN_ENABLED = os.getenv("HISTORIAN_ENABLED", "true").lower() in ("1","true","yes","on")
INTERVAL_S = float(os.getenv("HISTORIAN_INTERVAL_S", "5"))

class Historian:
    def __init__(self):
        self.last_write_ts: Optional[float] = None
        self.enabled = HISTORIAN_ENABLED
        self.interval_s = INTERVAL_S

    def write_snapshot(self, snapshot: Dict[str, Any]) -> None:
        if not self.enabled:
            return
        data = snapshot.get("data") or {}
        plant = data.get("plant", "PLANT")
        lines = data.get("lines", {})

        now = time.time()
        with get_conn() as conn:
            with conn.cursor() as cur:
                for line_id, line in lines.items():
                    cur.execute(
                        """INSERT INTO opc_kpi_samples(ts, plant, line, oee, availability, performance, quality, status)
                           VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s)""",
                        (plant, line_id, float(line.get("oee",0)), float(line.get("availability",0)),
                         float(line.get("performance",0)), float(line.get("quality",0)), str(line.get("status","")))
                    )
                    for st_id, st in (line.get("stations") or {}).items():
                        cur.execute(
                            """INSERT INTO opc_station_samples(ts, plant, line, station, state, cycle_time_s, good_count, scrap_count, alarms)
                               VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s, %s)""",
                            (plant, line_id, st_id, str(st.get("state","")), float(st.get("cycle_time_s",0)),
                             int(st.get("good_count",0)), int(st.get("scrap_count",0)), st.get("alarms", []))
                        )
            conn.commit()
        self.last_write_ts = now

    def write_event(self, plant: str, line: str, station: str, event_type: str, payload: Dict[str, Any]) -> None:
        if not self.enabled:
            return
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO opc_events(ts, plant, line, station, event_type, payload)
                       VALUES (NOW(), %s, %s, %s, %s, %s)""",
                    (plant, line, station, event_type, payload)
                )
            conn.commit()

    async def loop(self, snapshot_fn):
        if not self.enabled:
            return
        while True:
            try:
                snap = snapshot_fn()
                # run blocking db writes in thread to keep event loop healthy
                await asyncio.to_thread(self.write_snapshot, snap)
            except Exception:
                # Keep v0 robust; add logging later
                pass
            await asyncio.sleep(self.interval_s)
