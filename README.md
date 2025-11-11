# Welcome to Flask

A tiny GitHub space for learning by doing. The root of this repository holds the
smallest possible Flask app, while the `examples/` directory collects focused
recipes that show how to combine Flask with popular options (databases, env
management, etc.).

```
.
|-- app.py                 # Hello, World! demo
|-- requirements.txt       # Dependencies for the root demo
`-- examples/
    `-- postgresql/        # Flask + PostgreSQL sample project
```

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

### Example: Flask + PostgreSQL

Location: `examples/postgresql`

What it shows:

- Loading environment variables with `python-dotenv`
- Connecting to PostgreSQL with `psycopg2`
- Creating a table, inserting rows, and listing them through HTTP endpoints

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

4. Hit the endpoints:

   - `GET /init` - create the `items` table
   - `GET /add?name=Chair&value=49.99` - insert a row
   - `GET /list` - print the stored rows in plain text

Feel free to duplicate this folder as a template for other database backends or
deployment targets.

## Contributing new examples

1. Create a new folder inside `examples/`
2. Keep the example self-contained (its own `requirements.txt`, optional `.env.example`)
3. Document the idea briefly inside the top-level README or in a per-example
   README so others know how to run it

Open a pull request with the new example and a short description of what it
teaches - simple and useful wins every time. Happy hacking!
