# Schema Visualizer

A lightweight, local-first web tool to connect to your databases, visualize table relationships as ER diagrams, and export schemas in multiple formats.

No cloud. No npm. Runs entirely on your machine.

## Features

- **ER Diagram** — Interactive, zoomable, dark/light theme with right-angle relation lines (like dbdiagram.io)
- **Multi-DB support** — PostgreSQL, MySQL/MariaDB, MongoDB, Redis
- **Schema export** — SQL DDL, DBML, Markdown, JSON
- **Connection manager** — Save, edit, and delete connections (stored locally in SQLite)
- **Inferred relations** — Automatically detects NoSQL field patterns (e.g. `user_id` → `users`)

## Supported Databases

| Database      | Adapter      | Schema Introspection                  |
|---------------|--------------|---------------------------------------|
| PostgreSQL    | psycopg2     | information_schema + pg_catalog       |
| MySQL         | mysql-connector | information_schema                 |
| MariaDB       | mysql-connector | Same as MySQL                      |
| MongoDB       | pymongo      | Sample docs, inferred relations       |
| Redis         | redis-py     | Key pattern scan (limited to 500)     |

## Quick Start

```bash
git clone https://github.com/<your-username>/schema-visualizer.git
cd schema-visualizer
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn pydantic psycopg2-binary mysql-connector-python pymongo redis
```

Run the app:

```bash
./start.sh
```

Or manually:

```bash
uvicorn main:app --host 127.0.0.1 --port 8080
```

Open **http://127.0.0.1:8080** in your browser.

## Usage

1. Select your database type from the dropdown
2. Fill in host, port, user, password, and database/schema name
3. Click **Connect**
4. Pick a database from the sidebar
5. Explore the ER diagram — hover to highlight relations, click to pin
6. Switch to **Details** tab for column-level info
7. Export via **Export** tab (SQL, DBML, Markdown, JSON)

## Project Structure

```
schema-visualizer/
├── main.py              # FastAPI app + API routes
├── models.py            # Pydantic models
├── connections.py       # Local SQLite connection store
├── exporters.py         # Format converters (SQL, DBML, MD, JSON)
├── db/
│   ├── base.py          # Abstract adapter interface
│   ├── postgres.py      # PostgreSQL adapter
│   ├── mysql.py         # MySQL/MariaDB adapter
│   ├── mongodb.py       # MongoDB adapter
│   └── redis.py         # Redis adapter
├── static/
│   └── index.html       # Single-page dark/light theme UI
├── start.sh             # Launch script
└── venv/                # Python virtual environment (gitignored)
```

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, uvicorn, Pydantic v2
- **Frontend:** Vanilla JS, D3.js v7, dagre (ER layout)
- **Storage:** SQLite (local connection configs only)

## License

MIT — do whatever you want with it.
