import os
import asyncio
from asyncua import Server
from .state import PlantState

class UAServer:
    def __init__(self, state: PlantState):
        self.state = state
        self.server = Server()
        self.endpoint = os.getenv("OPC_ENDPOINT", "opc.tcp://0.0.0.0:4840/shopfloor/opc-studio")
        self._nodes = {}

    async def start(self):
        await self.server.init()
        self.server.set_endpoint(self.endpoint)
        self.server.set_server_name("OPC Studio (Shopfloor-Copilot)")

        uri = "urn:shopfloor:opc-studio"
        idx = await self.server.register_namespace(uri)

        objects = self.server.nodes.objects
        plant_obj = await objects.add_object(idx, f"Plant_{self.state.data['plant']}")

        for line_id, line in self.state.data["lines"].items():
            line_obj = await plant_obj.add_object(idx, f"Line_{line_id}")
            self._nodes[(line_id, "Status")] = await line_obj.add_variable(idx, "Status", line["status"])
            self._nodes[(line_id, "OEE")] = await line_obj.add_variable(idx, "OEE", float(line["oee"]))
            self._nodes[(line_id, "Availability")] = await line_obj.add_variable(idx, "Availability", float(line["availability"]))
            self._nodes[(line_id, "Performance")] = await line_obj.add_variable(idx, "Performance", float(line["performance"]))
            self._nodes[(line_id, "Quality")] = await line_obj.add_variable(idx, "Quality", float(line["quality"]))

            stations_obj = await line_obj.add_object(idx, "Stations")
            for st_id, st in line["stations"].items():
                st_obj = await stations_obj.add_object(idx, f"Station_{st_id}")
                self._nodes[(line_id, st_id, "State")] = await st_obj.add_variable(idx, "State", st["state"])
                self._nodes[(line_id, st_id, "CycleTime_s")] = await st_obj.add_variable(idx, "CycleTime_s", float(st["cycle_time_s"]))
                self._nodes[(line_id, st_id, "GoodCount")] = await st_obj.add_variable(idx, "GoodCount", int(st["good_count"]))
                self._nodes[(line_id, st_id, "ScrapCount")] = await st_obj.add_variable(idx, "ScrapCount", int(st["scrap_count"]))

        for n in self._nodes.values():
            await n.set_writable()

        await self.server.start()
        asyncio.create_task(self._sync_loop())

    async def _sync_loop(self):
        while True:
            try:
                for line_id, line in self.state.data["lines"].items():
                    await self._nodes[(line_id, "Status")].write_value(line["status"])
                    await self._nodes[(line_id, "OEE")].write_value(float(line["oee"]))
                    await self._nodes[(line_id, "Availability")].write_value(float(line["availability"]))
                    await self._nodes[(line_id, "Performance")].write_value(float(line["performance"]))
                    await self._nodes[(line_id, "Quality")].write_value(float(line["quality"]))
                    for st_id, st in line["stations"].items():
                        await self._nodes[(line_id, st_id, "State")].write_value(st["state"])
                        await self._nodes[(line_id, st_id, "CycleTime_s")].write_value(float(st["cycle_time_s"]))
                        await self._nodes[(line_id, st_id, "GoodCount")].write_value(int(st["good_count"]))
                        await self._nodes[(line_id, st_id, "ScrapCount")].write_value(int(st["scrap_count"]))
            except Exception:
                pass
            await asyncio.sleep(1.0)

    async def stop(self):
        await self.server.stop()
