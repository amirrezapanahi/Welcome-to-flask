import os

import psycopg2
from dotenv import load_dotenv
from flask import Flask, Response, request

"""
Minimal Flask + PostgreSQL example.

Endpoints
---------
GET /init
    Create the demo table if it does not exist.
GET /add?name=foo&value=1.23
    Insert a row using query parameters.
GET /list
    Return the stored rows in a tab-separated plain-text payload.

All connection details and runtime options are configured by environment
variables so you can point the app at any PostgreSQL instance without editing
this file.
"""

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/demo",
)
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("FLASK_DEBUG", "false").lower() in {"1", "true", "yes"}

app = Flask(__name__)


def get_conn() -> psycopg2.extensions.connection:
    """Return a new psycopg2 connection using DATABASE_URL."""
    return psycopg2.connect(DATABASE_URL)


@app.get("/init")
def init_db():
    """Create the items table if it does not yet exist."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                value DOUBLE PRECISION NOT NULL
            )
            """
        )
    return "ok: table ready\n"


@app.get("/add")
def add_item():
    """Insert a new row using query parameters (e.g. ?name=foo&value=42)."""
    name = (request.args.get("name") or "").strip()
    value = request.args.get("value")
    if not name or value is None:
        return "error: need ?name=...&value=...\n", 400
    try:
        numeric_value = float(value)
    except ValueError:
        return "error: value must be number\n", 400
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO items(name, value) VALUES (%s, %s)",
            (name, numeric_value),
        )
    return "ok: inserted\n"


@app.get("/list")
def list_items():
    """Return the stored items in a tab-separated plain-text response."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, name, value FROM items ORDER BY id")
        rows = cur.fetchall()
    lines = ["id\tname\tvalue"] + [f"{row[0]}\t{row[1]}\t{row[2]}" for row in rows]
    return Response("\n".join(lines) + "\n", mimetype="text/plain")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=DEBUG)
