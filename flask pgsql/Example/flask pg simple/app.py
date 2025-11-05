import os
import psycopg2
from flask import Flask, request, Response
from dotenv import load_dotenv

# بارگذاری env از فایل .env اگر وجود داشته باشد
load_dotenv()

# خواندن تنظیمات
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/demo")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")

app = Flask(__name__)

def get_conn():
    return psycopg2.connect(DATABASE_URL)

@app.get("/init")
def init_db():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS items(
              id SERIAL PRIMARY KEY,
              name TEXT NOT NULL,
              value DOUBLE PRECISION NOT NULL
            )
        """)
    return "ok: table ready\n"

@app.get("/add")
def add_item():
    name = (request.args.get("name") or "").strip()
    value = request.args.get("value")
    if not name or value is None:
        return "error: need ?name=...&value=...\n", 400
    try:
        v = float(value)
    except:
        return "error: value must be number\n", 400
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("INSERT INTO items(name, value) VALUES (%s, %s)", (name, v))
    return "ok: inserted\n"

@app.get("/list")
def list_items():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, name, value FROM items ORDER BY id")
        rows = cur.fetchall()
    lines = ["id\tname\tvalue"] + [f"{r[0]}\t{r[1]}\t{r[2]}" for r in rows]
    return Response("\n".join(lines) + "\n", mimetype="text/plain")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=DEBUG)
