# Working on clickedu-mcp with an AI agent

A local, single-purpose MCP server that lets a teacher drive their own Clickedu
account from an AI assistant. It runs on the teacher's machine over stdio and
handles students' data, so keep that in mind in every change.

## Ground rules

- **Reads are free; every write is one explicit, teacher-confirmed action.** The
  write tools (`mark_attendance`, `send_message`) return a preview first and only
  POST when called again with `confirm=true`. Never add bulk writes, loops over a
  class, scheduled runs, or student impersonation (`popup_suplantar_alu`).
- **No credentials in code, tests, fixtures, logs, or commit messages.** Secrets
  live only in `~/.clickedu-mcp/` (or env vars); `.env`, `secrets/`, `.cookies/`
  are gitignored.
- **Local only.** The server is stdio. There is no HTTP transport, Docker, or
  remote deployment in this repo on purpose; a remote deployment is the owner's
  separate concern.
- Plain sentences, sentence case, no em dashes, in prose and messages.

## Layout

- `src/clickedu_mcp/`: `session.py` (two-step login, cookie reuse, ISO-8859-15
  decode), `parse.py` (HTML to clean dicts), `server.py` (FastMCP stdio, the tools),
  `config.py` (per-user `~/.clickedu-mcp/` config and the `setup` command).
- `skills/`: one Agent Skill per teacher task (see below).

## Tools

Defined in `server.py`, decorated with `@mcp.tool()`. Reads go through `_read()`,
which tags every answer with `status`: `"ok"` (has data), `"empty"` (the page was
read and has no rows) or `"error"` (login failed, Clickedu showed its own alert
such as "Dades incorrectes" / "No disposeu de permisos", or the parser broke).
Never let an unreadable page look like an empty one. Pages are decoded with the
charset each response declares (most are ISO-8859-15, some AJAX answers are
UTF-8). A read may POST a search/filter form (`_read(..., post=...)`), never a
save action. Writes validate inputs, reject non-numeric IDs, replay the
full form so only the target row changes, and verify the result by re-reading.
Keep that pattern for new writes, and keep the preview/`confirm` gate.

## Skills

Each skill is a directory under `skills/` with a `SKILL.md`. Conventions:

- **Named and triggered in the teacher's language** (Catalan and Spanish), by the
  task the teacher asks for, not by the API tool name: a teacher says "passar
  llista / pasar lista", not "attendance". Pack the natural phrases (ca and es)
  into the `description` so the skill triggers regardless of wording.
- **One skill per task.** Read+write of the same resource can share a skill; the
  two attendance states are split (`clickedu-assistencia` for faltes,
  `clickedu-retards` for retards) because teachers think of them separately.
- **Lean `SKILL.md`, detail offloaded to `references/`** only where there is bulky
  content worth deferring (the attendance id chain, reason codes, the
  preview-then-confirm protocol). Trivial one-tool read skills stay single-file;
  do not add empty `references/` as ceremony.
- **Self-containment beats DRY.** A skill must work when loaded alone, so some
  repetition across skills is intentional, not a smell to refactor away.
- **`allowed-tools`** scopes each skill to its MCP tools. It assumes the server is
  registered as `clickedu` (tool names `mcp__clickedu__<tool>`). If a client
  registers the server under another name, adjust or drop `allowed-tools`.
- Write skills must state the per-action confirm, one-at-a-time, and no-bulk rules.

## Build and check

```sh
uv sync
uv run python -c "import clickedu_mcp.server"   # imports clean
uvx --from . clickedu-mcp setup                 # the teacher onboarding path
```

The person who opens the pull request is the author: you must be able to explain
every line and have run it.
