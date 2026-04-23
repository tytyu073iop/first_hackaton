# Fog of War — MTBank

## Dev Commands

### Docker (recommended)
```bash
docker-compose up --build
```
Frontend: http://localhost:5173 | Backend: http://localhost:8000

### Without Docker (two terminals)
```bash
# Terminal 1
cd backend && pip install -r requirements.txt && uvicorn main:app --reload

# Terminal 2
cd frontend && npm install && npm run dev
```

### Windows quick-start
`start.bat` or `start.ps1` — installs deps and opens both services + browser.

## Architecture

- **Frontend**: React 18 + Vite + MapLibre GL (`react-map-gl`), ESM (`"type": "module"`)
- **Backend**: FastAPI + SQLAlchemy 2.0 + SQLite (`game.db`)
- **Database**: SQLite at `backend/game.db`, auto-created on startup (`init_db()`). Do NOT commit this file.
- **Map**: Pointy-top hex grid centered on Minsk (53.9045, 27.5615). `seed_data.py` seeds partner locations.

## Startup Behavior

`main.py` runs `init_db()` then `seed_partners()` on every startup:
- Checks for `backend/partners_osm.json` first (real OSM data)
- Falls back to `PARTNERS_DATA` built-in list
- Partners are deduped, so restarting is safe

## API Keys

- Backend CORS whitelist: `http://localhost:5173`, `http://127.0.0.1:5173` only
- Frontend API URL: `VITE_API_URL` env var (default `http://localhost:8000`)
- Demo player: `demo_player_001`

## Important Files

| File | Purpose |
|------|---------|
| `backend/models.py` | SQLAlchemy models (Partner, PlayerProgress, Quest, Achievement, etc.) |
| `backend/seed_data.py` | Hex grid math, partner seed data, `hex_id_for_point()` |
| `backend/main.py` | FastAPI app, startup hooks, CORS config |
| `frontend/src/api/client.js` | All API calls, player storage in localStorage (`fow_player`) |
| `backend/achievement_engine.py` | Achievement logic |

## Gotchas

- `game.db` is gitignored — no migration system, schema is created fresh via `Base.metadata.create_all()`
- No tests exist in this repo
- `backend/venv/` is checked in (Python venv with installed packages) — do not use it; install fresh via `requirements.txt`
- `frontend/.env` sets `VITE_API_URL` for dev — never prefix Vite env vars with `VITE_` when reading them