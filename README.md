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
- **Dashboard** (`/`) — the home page for the active campaign: a metric row up top (current session,
  open threads, active clocks) over a grid of cards — recent faction moves, clocks nearing completion,
  open threads across your sessions, and the last session's summary — so you can see where the campaign
  stands at a glance before you start prepping. A card that can't render shows a quiet placeholder
  instead of breaking the page.
- **Sessions** (`/sessions`) — a numbered log of your games, one active at a time:
  - a **timestamped log** you type into during play, each line tagged combat / roleplay / loot /
    thread, newest first;
  - **threads** — tag a line as a thread and resolve or reopen it later as loose ends get tied up;
  - a per-session **summary** you write up after the fact;
  - **compile recap** turns the tags you pick into a markdown write-up you can drop straight into the
    summary instead of writing it from scratch.
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
  - cross-entity `[[wikilinks]]` — write `[[Name]]` inline and it links to a wiki page, NPC, or faction
    with that name (matched in that order); a name that doesn't exist yet renders as an amber "create it"
    link instead of a dead link;
  - a **backlinks** panel on every page showing what links to it;
  - **categories and tags** for organizing and filtering the page list, with quick add/remove of tags;
  - **search** across page titles and bodies;
  - pages, NPCs, and factions are all reachable from the **command palette** (Ctrl-K).
- **Combat Tracker** (`/combat`) — run encounters scoped to the active campaign:
  - build an encounter and add combatants by hand or **from an existing NPC** (pulling its name, and
    its HP/AC when the statblock is structured);
  - order the initiative list and **drag to reorder**, then run the fight: apply **damage/heal** with an
    HP bar that shades green→amber→red, edit AC, toggle **conditions** (the standard set plus your own
    custom ones) and a **concentration** flag;
  - a round counter and an active-combatant marker with **Next turn**, which advances the turn and bumps
    the round on wrap;
  - changes **sync live** — open the tracker in a second window (e.g. on another screen) and it mirrors
    the first as you play.
- **Maps** (`/map`) — a tactical battle map, the centrepiece of the toolkit:
  - upload a map image and lay a **square grid** over it — configurable square size, offset (to line the
    grid up with art that already has one), feet per square, and a show/hide toggle;
  - drop **tokens** (a coloured disc or uploaded art), size them in squares, rename, recolour, give them
    HP, and **drag them around** with optional snap-to-grid;
  - a **ruler** for measuring range: click to lay out a path with as many waypoints as you like and read
    the running total in feet. Each map picks its own **diagonal rule** — Chebyshev (5e), the 5-10-5
    variant, Euclidean, or Manhattan — and switching it changes what the ruler reports;
  - **fog of war**: reveal by rectangle or freehand brush, re-hide areas, or reveal/hide the whole map.
    The DM sees through the fog at half opacity while the table sees it solid;
  - a **DM layer** for secret tokens, plus a per-token "visible to players" switch — hidden things stay
    hidden;
  - **Push to players** shares the map with the player screen (and **Stop sharing** takes it back).
- **Player Screen** (`/player`) — a read-only second view for a TV or second monitor. Click **Open
  player screen** in the top bar to launch it, then present what you want the table to see:
  - set an encounter active and it mirrors the fight **live** — initiative order, names, whose turn it
    is, and a color-banded health indicator per combatant;
  - push a map and it mirrors that too, **live**: tokens move as you drag them and fog clears as you
    reveal it.
  - It deliberately shows **no hidden information** — no HP numbers, no AC, no conditions, no DM
    controls, no secret tokens, and nothing on the DM layer — so the table sees only what you choose to
    present. HP is shown only as a colour band, and only for tokens you explicitly share it for. When
    nothing is being shared it simply says so.

## Tech stack

- **Backend:** FastAPI + Uvicorn (async, native WebSockets, single process)
- **Data:** SQLAlchemy 2.x + SQLite, with Alembic migrations
- **Frontend:** Jinja2 server-rendered fragments + HTMX + Alpine.js (minimal custom JS)
- **Rich UI:** Vue 3 single-file components (TypeScript, bundled by Vite) mounted as *islands* onto the
  server-rendered pages — an additive layer for component-heavy UI; HTMX/Alpine still drive everything
  else. The runtime is unchanged (one Python process serving the built assets); Vite is a build-time tool
- **Map canvas:** Konva.js (layered 2D rendering), vendored locally — like every other front-end
  dependency, so the app runs fully offline
- **Images:** Pillow (reads the dimensions of uploaded maps and tokens)
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

Then open <http://localhost:8000> for the DM interface, and use the **Open player screen** button (or
open <http://localhost:8000/player>) in a second window for the read-only table view. Your data is stored
under `data/` (the SQLite database and uploaded media), which stays on your machine and out of version
control.

### Frontend (Vue islands)

Rich UI is built with Vue 3 single-file components, bundled by Vite, and mounted as islands onto the
server-rendered pages. Node 20+ is needed for the frontend build (not for the Python app itself).

First-time setup (from the repo root):

```bash
npm install
```

For a production-style run, build the assets once and let uvicorn serve them from `/static/dist`:

```bash
npm run build
.venv/Scripts/uvicorn main:app --port 8000
```

For frontend development, run the Vite dev server (hot-reload) alongside uvicorn:

```bash
npm run dev                                                      # Vite on :5173
HEXFORGE_VITE_DEV=1 .venv/Scripts/uvicorn main:app --reload --port 8000
```

Editing a `.vue` component then hot-updates the browser without a full reload.

## Tests

```bash
npm run lint                         # frontend lint (eslint)
npm run format:check                 # frontend format check (prettier)
npm run build                        # typecheck + bundle the Vue islands
.venv/Scripts/ruff check .           # lint
.venv/Scripts/ruff format --check .  # format check
.venv/Scripts/pytest                 # tests
```
