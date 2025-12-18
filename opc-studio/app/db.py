import os
import psycopg
from contextlib import contextmanager

def _dsn() -> str:
    return os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/ragdb")

@contextmanager
def get_conn():
    conn = psycopg.connect(_dsn())
    try:
        yield conn
    finally:
        conn.close()
