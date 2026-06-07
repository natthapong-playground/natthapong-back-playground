# Project guidance for Claude Code

## Canonical structure — `structures.txt`
`structures.txt` (repo root) is the **authoritative blueprint** for this
project's file/folder layout and naming. Treat it as the source of truth.

When creating, moving, or naming files:
- Place each file in the layer/folder defined in `structures.txt`
  (`app/api/controllers`, `app/core`, `app/models`, `app/schemas`,
  `app/services`, `app/websockets`, `tests/test_controllers`,
  `tests/test_websockets`, etc.).
- Follow the existing naming conventions (`*_routes.py`, `*_model.py`,
  `*_schema.py`, `*_service.py`, `test_*.py`).
- If a needed file/folder is described in `structures.txt` but does not exist
  yet, create it in the documented location rather than inventing a new path.
- If a task genuinely does not fit the blueprint, surface the mismatch and
  propose where it should live instead of silently deviating.

Keep `structures.txt` updated when the architecture intentionally changes, so
it stays the source of truth.

## Layering (per structures.txt)
- **controllers** = routing/endpoints only.
- **services** = business logic ("the brains"); domain logic lives here, not in
  controllers.
- **models** = database entities (SQLAlchemy).
- **schemas** = Pydantic validation / serialization (request vs response).
- **core** = config + security (env parsing, hashing, JWT).

## Living documentation — `codebase-docs/`
`codebase-docs/` holds one plain-text `.txt` doc per source file, written for
both engineers and non-engineers. **ALWAYS read `codebase-docs/_INDEX.txt`
first** — it is the head of that folder and defines the maintenance protocol,
the doc template, and the file map.

This is a hard rule: whenever you create, modify, move, rename, or delete a file
under `app/` or `tests/`, **update its matching `codebase-docs/*.txt` doc in the
same change** (create/edit/delete to mirror the source, and refresh the
doc's `LAST-SYNCED` date). Keep the `[ PLAIN ENGLISH ]` and `[ TECHNICAL ]`
sections consistent with each other and with the code. A doc that describes
behavior the code no longer has is a defect — fix it as part of the work.
