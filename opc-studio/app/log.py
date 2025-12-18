import os
import logging

def get_logger(name: str = "opc-studio"):
    level = os.getenv("LOG_LEVEL", "info").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s"
    )
    return logging.getLogger(name)
