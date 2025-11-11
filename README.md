# Welcome to Flask

A tiny GitHub space for learning by doing. The root of this repository holds the
smallest possible Flask app, while the `examples/` directory collects focused
recipes that show how to combine Flask with popular options (databases, env
management, etc.).

## Quick start (core demo)

1. Create a virtual environment (optional but recommended).
2. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the demo app:

   ```bash
   python app.py
   ```

4. Open <http://127.0.0.1:5000/> to see the familiar "Hello, World!" greeting.

This tiny app is intentionally bare-bones so you can copy it as the clean slate
for your own projects.

## Working with examples

Each subdirectory under `examples/` is a standalone Flask project with its own
dependencies. The general workflow is:

1. `cd examples/<name>`
2. `python -m venv .venv && .\.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (macOS/Linux)
3. `pip install -r requirements.txt`
4. Create a `.env` file if the example ships with `.env.example`
5. `python app.py`

### Example: Flask + HTML templates

Location: `examples/html-basic`

What it shows:

- Rendering HTML via `render_template`
- Passing Python data into Jinja2 loops and expressions
- Keeping markup inside `templates/` plus custom CSS/JS in `static/`

How to try it:

1. ```bash
   cd examples/html-basic
   pip install -r requirements.txt
   python app.py
   ```
2. Open <http://127.0.0.1:5000/> and tweak `templates/index.html` to see live updates.

### Example: Flask + PostgreSQL

Location: `examples/postgresql`

What it shows:

- Loading environment variables with `python-dotenv`
- Connecting to PostgreSQL with `psycopg2`
- Creating a table, inserting rows, and listing them through HTTP endpoints

#### Prepare PostgreSQL (optional but recommended)

If you want a dedicated database/user for the sample, run the following SQL in `psql`
or your favorite admin tool:

```sql
CREATE DATABASE flask_demo;
CREATE USER flask_user WITH PASSWORD 'change_me';
GRANT ALL PRIVILEGES ON DATABASE flask_demo TO flask_user;
```

Explanation:

- `CREATE DATABASE` makes an empty database the app can own.
- `CREATE USER` provisions a login for the app.
- `GRANT ALL PRIVILEGES` lets that user create tables and modify data inside the new database.

Update `DATABASE_URL` in `.env` so it points to this user/database combination, for example
`postgresql://flask_user:change_me@localhost:5432/flask_demo`.

#### SQL essentials for PostgreSQL beginners

Below is a mini cheat sheet so you can get comfortable with SQL even if you are new
to databases. You can run these commands inside `psql` (the PostgreSQL shell) after
connecting to the database you created.

```sql
-- 1. Create a table to store data
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    value NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Insert sample rows
INSERT INTO items (name, value) VALUES ('Desk', 120.00);
INSERT INTO items (name, value) VALUES ('Chair', 49.99), ('Lamp', 30.50);

-- 3. Query the data
SELECT id, name, value FROM items;
SELECT * FROM items WHERE value > 50 ORDER BY value DESC;

-- 4. Update and delete
UPDATE items SET value = 44.99 WHERE name = 'Chair';
DELETE FROM items WHERE name = 'Lamp';

-- 5. Alter the table (for example, add a new column)
ALTER TABLE items ADD COLUMN in_stock BOOLEAN DEFAULT TRUE;

-- 6. Create an index to speed up lookups
CREATE INDEX idx_items_name ON items(name);

-- 7. Drop objects when you no longer need them
DROP INDEX idx_items_name;
DROP TABLE items;
```

Understanding the statements:

- `CREATE TABLE` defines the table structure. `SERIAL` auto-increments integers, `PRIMARY KEY` uniquely identifies rows, `TEXT` stores arbitrary strings, `NUMERIC(10, 2)` stores up to 10 digits with 2 decimal places, and `TIMESTAMPTZ` is a timestamp with timezone. `DEFAULT NOW()` fills a column automatically when a row is inserted.
- `INSERT INTO ... VALUES` adds new rows. Listing multiple sets of parentheses inserts multiple rows in one go.
- `SELECT` reads data. `WHERE` filters rows, `ORDER BY` sorts results, and `*` means "all columns".
- `UPDATE ... SET ... WHERE` changes data. Always include a `WHERE` clause so you do not accidentally update every row.
- `DELETE FROM ... WHERE` removes rows. Again, `WHERE` limits the deletion scope.
- `ALTER TABLE ... ADD COLUMN` modifies existing structures without recreating the table.
- `CREATE INDEX` adds a lookup helper so queries by indexed columns are faster. Later, `DROP INDEX` removes it.
- `DROP TABLE` deletes the table definition and its data. Use with caution.

Common SQL keywords you will see often:

- `NULL` - represents missing/unknown values. `NOT NULL` ensures data must be provided.
- `UNIQUE` - enforces that a column cannot contain duplicate values.
- `CHECK` - adds a constraint, for example `CHECK (value > 0)`.
- `REFERENCES` - declares a foreign key relationship to another table.
- `CASCADE` - when used with `DROP` or foreign keys, instructs PostgreSQL to apply the operation to related objects.
- `LIMIT` - returns only the first N rows of a query, useful for pagination or quick looks.
- `OFFSET` - skips a number of rows before returning results (often paired with `LIMIT`).

Additional helpful `psql` meta commands (type them without the trailing semicolon):

- `\l` lists databases.
- `\c flask_demo` connects to a database.
- `\dt` lists tables in the current database.
- `\d items` shows the schema of a table (`\d+ items` includes indexes and comments).
- `\x` toggles expanded output which is useful for wide tables.
- `\q` quits `psql`.

Practice these steps a few times and you will have the foundation needed for most Flask + PostgreSQL projects.

How to try it:

1. Copy the sample environment file:

   ```bash
   cd examples/postgresql
   cp .env.example .env  # or use copy .env.example .env on Windows
   ```

2. Adjust `DATABASE_URL` inside `.env` so it points to a PostgreSQL instance you
   can reach.
3. Install dependencies and run the app:

   ```bash
   pip install -r requirements.txt
   python app.py
   ```

4. Hit the endpoints highlighted below to explore the SQL lifecycle.

#### HTTP endpoints cheat sheet

| Method + Path | What it demonstrates |
| --- | --- |
| `GET /health` | Quick connection/latency test (`SELECT NOW()` from PostgreSQL). |
| `GET /init` | Idempotent table + index creation so you always start from a known schema. |
| `POST /reset` | Drops and recreates the schema to illustrate destructive DDL. |
| `POST /seed` | Bulk inserts with optional `replace=true` and UPSERT logic on `name`. |
| `GET /items` | Lists all rows as JSON, including timestamps. |
| `POST /items` | JSON create endpoint (`name`, `value`, optional `note`). |
| `GET /items/<id>` | Fetch a single row; returns `404` when it does not exist. |
| `PUT /items/<id>` | Replace the full row while keeping constraint checks (`UNIQUE`, `CHECK`). |
| `PATCH /items/<id>` | Partial updates (`name`, `value`, `note`) with automatic `updated_at`. |
| `DELETE /items/<id>` | Hard-delete rows and confirm the affected id. |
| `GET /search` | Filter by partial name plus optional `min_value`, `max_value`, `limit`. |
| `GET /stats` | Aggregate functions (`COUNT`, `SUM`, `MIN`, `MAX`, `AVG`). |
| `GET /schema` | Introspect the table via `information_schema.columns`. |
| `GET /add?name=Chair&value=49.99` | Legacy query-parameter insert for quick browser testing. |
| `GET /list` | Tab-separated export for copy/paste into spreadsheets or the shell. |

Feel free to duplicate this folder as a template for other database backends or
deployment targets.

## Contributing new examples

1. Create a new folder inside `examples/`
2. Keep the example self-contained (its own `requirements.txt`, optional `.env.example`)
3. Document the idea briefly inside the top-level README or in a per-example
   README so others know how to run it

Open a pull request with the new example and a short description of what it
teaches - simple and useful wins every time. Happy hacking!
