import os
import asyncio
import uvicorn

from .state import PlantState
from .api import build_api
from .ua_server import UAServer
from .historian import Historian

async def run():
    state = PlantState()

    ua = UAServer(state)
    await ua.start()

    historian = Historian()
    # start historian loop (writes to Postgres)
    asyncio.create_task(historian.loop(lambda: state.snapshot()))

    http_port = int(os.getenv("OPC_STUDIO_HTTP_PORT", "8040"))
    api = build_api(state, historian)

    config = uvicorn.Config(api, host="0.0.0.0", port=http_port, log_level="info")
    server = uvicorn.Server(config)

    try:
        await server.serve()
    finally:
        await ua.stop()

if __name__ == "__main__":
    asyncio.run(run())
