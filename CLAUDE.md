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
