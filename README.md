# Hexforge

A local-first, offline desktop app for running tabletop RPG sessions — a Dungeon Master's toolkit.
One Python process serves a full **DM interface** and (by design) a read-only **player screen** for a
second monitor or TV, so what the table sees stays in sync with what the DM controls. No cloud, no
account: all data lives in a single SQLite file plus an image folder on your machine.

Hexforge is **modular** — each feature is a self-contained module that plugs into a thin core, so the
app grows one drop-in feature at a time.

## Status

Early and actively built. Working today:

- **App shell** — a persistent navigation rail, a campaign switcher (all data is scoped to the active
  campaign), a built-in design-system reference page, and a keyboard command palette (Ctrl-K) for quick
  search and navigation.
- **Dice Roller** (`/dice`) — roll standard dice notation and see a per-die breakdown:
  - terms and modifiers like `2d6+1d8+3`, keep/drop highest & lowest (`4d6kh3`, `2d20kl1`),
    advantage/disadvantage (`1d20adv` / `1d20dis`), exploding dice (`3d6!`), and reroll (`4d6r1`);
  - **saved rolls** — store frequently used rolls as one-click re-roll buttons;
  - a **history feed** that logs every roll and updates live.
- **Factions** (`/factions`) — a faction roster scoped to the active campaign:
  - a **5-point disposition badge** from hostile to allied, with create, edit, and delete;
  - Blades-style **progress clocks** — click a segment to fill up to it, click the current top segment
    again to unfill;
  - a **timestamped activity log** per faction, newest entries first.
- **NPCs** (`/npcs`) — an NPC roster scoped to the active campaign, grouped by faction (with a filter):
  - full CRUD with a portrait upload, motivation, secrets, voice notes, and a freeform statblock,
    alongside the same disposition badge used for factions;
  - a **relationships** page for linking NPCs to other NPCs or to factions with a free-text label
    (e.g. "rival of", "sworn to"), grouped by source and removable per edge;
  - a **random NPC generator** that pre-fills a name, motivation, and voice to speed up prep.
- **Wiki** (`/wiki`) — a markdown knowledge base scoped to the active campaign:
  - pages with a title, slug, category, and a markdown body rendered server-side;
  - cross-entity `[[wikilinks]]` — write `[[Page Title]]`, `[[npc:Name]]`, or `[[faction:Name]]` inline
    and it renders as a link to that page, NPC, or faction; links to something that doesn't exist yet
    render as an amber "create it" link instead of a dead link;
  - a **backlinks** panel on every page showing what links to it;
  - **categories and tags** for organizing and filtering the page list, with quick add/remove of tags;
  - **search** across page titles and bodies;
  - pages, NPCs, and factions are all reachable from the **command palette** (Ctrl-K).

The read-only player screen and further modules (combat tracker, maps with fog) are on the way.

## Tech stack

- **Backend:** FastAPI + Uvicorn (async, native WebSockets, single process)
- **Data:** SQLAlchemy 2.x + SQLite, with Alembic migrations
- **Frontend:** Jinja2 server-rendered fragments + HTMX + Alpine.js (minimal custom JS)
- **Desktop packaging:** pywebview + PyInstaller (added at the packaging stage; in dev you just run a
  local server and open it in a browser)

## Running it (development)

Requires Python 3.12. From the repo root:

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # POSIX: .venv/bin/pip
.venv/Scripts/alembic upgrade head              # creates the SQLite DB (required before first run)
.venv/Scripts/uvicorn main:app --reload --port 8000
```

Then open <http://localhost:8000> for the DM interface. Your data is stored under `data/` (the SQLite
database and uploaded media), which stays on your machine and out of version control.

## Tests

```bash
.venv/Scripts/ruff check .           # lint
.venv/Scripts/ruff format --check .  # format check
.venv/Scripts/pytest                 # tests
```
