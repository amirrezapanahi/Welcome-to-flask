import os
from decimal import Decimal
from typing import Any, Mapping, Sequence

import psycopg2
from psycopg2 import IntegrityError
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request

"""
Flask + PostgreSQL learning lab.

This single file now demonstrates every foundational database task you encounter
in CRUD apps:

- /init       – create the table and helper indexes
- /reset      – drop and recreate the schema (danger zone, but educational)
- /seed       – insert sample rows with optional UPSERT behavior
- /health     – verify the database connection
- /items      – list items as JSON
- /items/<id> – read/update/delete individual rows (JSON payloads)
- /add        – legacy query-param insert for quick URL experiments
- /search     – filter by name/value plus pagination
- /stats      – aggregate queries (min/max/avg)
- /schema     – inspect the table definition using information_schema
- /list       – tab-separated export for spreadsheets/CLI work

Connection details stay in environment variables so you can point the app at any
database without editing code.
"""

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/demo",
)
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("FLASK_DEBUG", "false").lower() in {"1", "true", "yes"}
TRUE_VALUES = {"1", "true", "yes", "on"}
SELECT_COLUMNS = "id, name, value, note, created_at, updated_at"

SEED_ITEMS = [
    {"name": "Desk", "value": 199.99, "note": "Spacious work surface"},
    {"name": "Chair", "value": 89.5, "note": "Ergonomic and adjustable"},
    {"name": "Lamp", "value": 35.0, "note": "LED task lighting"},
    {"name": "Notebook", "value": 6.25, "note": "Grid-paper notebook"},
    {"name": "Plant", "value": 18.75, "note": "Adds a splash of green"},
]

app = Flask(__name__)


def get_conn() -> psycopg2.extensions.connection:
    """Return a new psycopg2 connection using DATABASE_URL."""
    return psycopg2.connect(DATABASE_URL)


def create_items_table(drop_existing: bool = False) -> None:
    """(Re)create the demo table and the indexes we rely on."""
    with get_conn() as conn, conn.cursor() as cur:
        if drop_existing:
            cur.execute("DROP TABLE IF EXISTS items")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                value DOUBLE PRECISION NOT NULL CHECK (value >= 0),
                note TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_items_value ON items (value)")
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_items_created_at ON items (created_at)"
        )


def _floatify(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _serialize_item(row: Mapping[str, Any]) -> dict[str, Any]:
    """Convert psycopg2 rows into JSON-friendly data."""
    return {
        "id": row["id"],
        "name": row["name"],
        "value": _floatify(row.get("value")),
        "note": row.get("note") or "",
        "created_at": row.get("created_at").isoformat()
        if row.get("created_at")
        else None,
        "updated_at": row.get("updated_at").isoformat()
        if row.get("updated_at")
        else None,
    }


def _run_select(sql: str, params: Sequence[Any] | None = None) -> list[dict[str, Any]]:
    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params or ())
        rows = cur.fetchall()
    return [_serialize_item(row) for row in rows]


def _select_one(sql: str, params: Sequence[Any] | None = None) -> dict[str, Any] | None:
    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params or ())
        row = cur.fetchone()
    return _serialize_item(row) if row else None


def _coerce_name(raw: Any) -> str:
    name = str(raw or "").strip()
    if not name:
        raise ValueError("name is required")
    return name


def _coerce_value(raw: Any) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise ValueError("value must be a number")
    if value < 0:
        raise ValueError("value must be >= 0")
    return value


def _coerce_note(raw: Any) -> str:
    return str(raw or "").strip()


def _parse_create_payload(data: Mapping[str, Any]) -> tuple[str, float, str]:
    return (
        _coerce_name(data.get("name")),
        _coerce_value(data.get("value")),
        _coerce_note(data.get("note")),
    )


def _parse_partial_payload(data: Mapping[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    if "name" in data:
        fields["name"] = _coerce_name(data.get("name"))
    if "value" in data:
        fields["value"] = _coerce_value(data.get("value"))
    if "note" in data:
        fields["note"] = _coerce_note(data.get("note"))
    if not fields:
        raise ValueError("provide at least one of name, value, or note")
    return fields


def _insert_item(name: str, value: float, note: str) -> dict[str, Any]:
    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            f"""
            INSERT INTO items (name, value, note)
            VALUES (%s, %s, %s)
            RETURNING {SELECT_COLUMNS}
            """,
            (name, value, note),
        )
        row = cur.fetchone()
    return _serialize_item(row)


def _update_item(item_id: int, fields: Mapping[str, Any]) -> dict[str, Any] | None:
    if not fields:
        return None
    assignments = ", ".join(f"{column} = %s" for column in fields)
    params = [*fields.values(), item_id]
    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            f"""
            UPDATE items
            SET {assignments}, updated_at = NOW()
            WHERE id = %s
            RETURNING {SELECT_COLUMNS}
            """,
            params,
        )
        row = cur.fetchone()
    return _serialize_item(row) if row else None


def _delete_item(item_id: int) -> bool:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM items WHERE id = %s", (item_id,))
        return cur.rowcount > 0


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in TRUE_VALUES


def _parse_limit(raw: Any, default: int = 20) -> int:
    try:
        limit = int(raw) if raw is not None else default
    except (TypeError, ValueError):
        limit = default
    return max(1, min(100, limit))


@app.get("/health")
def health_check():
    """Simple connection test that also returns the database server time."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT NOW()")
        (current_time,) = cur.fetchone()
    return jsonify({"status": "ok", "database_time": current_time.isoformat()})


@app.get("/init")
def init_db():
    """Create the items table if it does not yet exist."""
    create_items_table(drop_existing=False)
    return "ok: table ready\n"


@app.post("/reset")
def reset_db():
    """Drop the table and recreate it from scratch."""
    create_items_table(drop_existing=True)
    return jsonify({"status": "ok", "message": "table dropped and recreated"})


@app.post("/seed")
def seed_data():
    """
    Insert a batch of sample rows.

    Accepts JSON:
    {
        "replace": true,          # optional, truncate before inserting
        "items": [
            {"name": "...", "value": 1.23, "note": "..."},
            ...
        ]
    }
    """

    payload = request.get_json(silent=True) or {}
    replace = _as_bool(payload.get("replace") or request.args.get("replace"))
    dataset = payload.get("items") or SEED_ITEMS
    if not isinstance(dataset, list):
        return jsonify({"error": "items must be a JSON list"}), 400

    parsed_rows: list[tuple[str, float, str]] = []
    for entry in dataset:
        if not isinstance(entry, Mapping):
            return jsonify({"error": "each item must be an object"}), 400
        try:
            parsed_rows.append(_parse_create_payload(entry))
        except ValueError as exc:
            return jsonify({"error": f"invalid item: {exc}"}), 400

    if not parsed_rows:
        return jsonify({"error": "no items to insert"}), 400

    create_items_table(drop_existing=False)
    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        if replace:
            cur.execute("TRUNCATE TABLE items RESTART IDENTITY")
        cur.executemany(
            """
            INSERT INTO items (name, value, note)
            VALUES (%s, %s, %s)
            ON CONFLICT (name) DO UPDATE
            SET value = EXCLUDED.value,
                note = EXCLUDED.note,
                updated_at = NOW()
            """,
            parsed_rows,
        )
        cur.execute("SELECT COUNT(*) AS total FROM items")
        total = cur.fetchone()["total"]

    return jsonify(
        {
            "status": "ok",
            "processed": len(parsed_rows),
            "replace": replace,
            "total_rows": total,
        }
    )


@app.get("/items")
def list_items_json():
    """Return all rows as JSON."""
    rows = _run_select(f"SELECT {SELECT_COLUMNS} FROM items ORDER BY created_at")
    return jsonify({"count": len(rows), "items": rows})


@app.post("/items")
def create_item():
    """Create a row from a JSON payload."""
    data = request.get_json(silent=True) or {}
    try:
        name, value, note = _parse_create_payload(data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    try:
        item = _insert_item(name, value, note)
    except IntegrityError:
        return jsonify({"error": "name must be unique"}), 409
    return jsonify(item), 201


@app.get("/items/<int:item_id>")
def get_item(item_id: int):
    """Fetch a single row by ID."""
    row = _select_one(
        f"SELECT {SELECT_COLUMNS} FROM items WHERE id = %s", (item_id,)
    )
    if not row:
        return jsonify({"error": "item not found"}), 404
    return jsonify(row)


@app.put("/items/<int:item_id>")
def replace_item(item_id: int):
    """Replace an existing row (requires name + value)."""
    data = request.get_json(silent=True) or {}
    try:
        name, value, note = _parse_create_payload(data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    try:
        row = _update_item(item_id, {"name": name, "value": value, "note": note})
    except IntegrityError:
        return jsonify({"error": "name must be unique"}), 409
    if not row:
        return jsonify({"error": "item not found"}), 404
    return jsonify(row)


@app.patch("/items/<int:item_id>")
def update_item(item_id: int):
    """Partially update a row."""
    data = request.get_json(silent=True) or {}
    try:
        fields = _parse_partial_payload(data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    try:
        row = _update_item(item_id, fields)
    except IntegrityError:
        return jsonify({"error": "name must be unique"}), 409
    if not row:
        return jsonify({"error": "item not found"}), 404
    return jsonify(row)


@app.delete("/items/<int:item_id>")
def delete_item(item_id: int):
    """Remove a row permanently."""
    if not _delete_item(item_id):
        return jsonify({"error": "item not found"}), 404
    return jsonify({"status": "ok", "deleted_id": item_id})


@app.get("/search")
def search_items():
    """Filter by partial name and/or numeric ranges."""
    name_query = (request.args.get("q") or "").strip()
    min_value_raw = request.args.get("min_value")
    max_value_raw = request.args.get("max_value")
    limit = _parse_limit(request.args.get("limit"))

    try:
        min_value = _coerce_value(min_value_raw) if min_value_raw else None
        max_value = _coerce_value(max_value_raw) if max_value_raw else None
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    conditions = []
    params: list[Any] = []
    if name_query:
        conditions.append("name ILIKE %s")
        params.append(f"%{name_query}%")
    if min_value is not None:
        conditions.append("value >= %s")
        params.append(min_value)
    if max_value is not None:
        conditions.append("value <= %s")
        params.append(max_value)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(limit)

    sql = f"""
        SELECT {SELECT_COLUMNS}
        FROM items
        {where_clause}
        ORDER BY value DESC
        LIMIT %s
    """
    rows = _run_select(sql, params)
    return jsonify({"returned": len(rows), "items": rows})


@app.get("/stats")
def stats():
    """Aggregate information about the table."""
    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT
                COUNT(*) AS total_rows,
                COALESCE(SUM(value), 0) AS total_value,
                COALESCE(MIN(value), 0) AS min_value,
                COALESCE(MAX(value), 0) AS max_value,
                COALESCE(AVG(value), 0) AS avg_value
            FROM items
            """
        )
        row = cur.fetchone()

    return jsonify(
        {
            "total_rows": row["total_rows"],
            "total_value": _floatify(row["total_value"]),
            "min_value": _floatify(row["min_value"]),
            "max_value": _floatify(row["max_value"]),
            "avg_value": _floatify(row["avg_value"]),
        }
    )


@app.get("/schema")
def describe_schema():
    """Inspect the table definition via information_schema."""
    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'items'
            ORDER BY ordinal_position
            """
        )
        columns = cur.fetchall()
    return jsonify({"columns": columns})


@app.get("/add")
def add_item():
    """Insert a new row using query parameters (e.g. ?name=foo&value=42)."""
    data = {
        "name": request.args.get("name"),
        "value": request.args.get("value"),
        "note": request.args.get("note", ""),
    }
    try:
        name, value, note = _parse_create_payload(data)
    except ValueError as exc:
        return f"error: {exc}\n", 400
    try:
        item = _insert_item(name, value, note)
    except IntegrityError:
        return "error: name must be unique\n", 409
    return f"ok: inserted id={item['id']}\n"


@app.get("/list")
def list_items_text():
    """Return the stored items in a tab-separated plain-text response."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, name, value, note FROM items ORDER BY id")
        rows = cur.fetchall()
    lines = ["id\tname\tvalue\tnote"] + [
        f"{row[0]}\t{row[1]}\t{row[2]:.2f}\t{row[3]}" for row in rows
    ]
    return Response("\n".join(lines) + "\n", mimetype="text/plain")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=DEBUG)
