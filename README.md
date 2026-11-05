# clickedu-mcp

A personal, local stdio MCP server for one Clickedu teacher account
(`https://jpif.clickedu.eu`). It runs your daily read workflow from Claude and
lets you take single, confirmed write actions (attendance, messages).

It is built to run **on your own laptop**. It touches your students' data, so it
never belongs on a shared server. Keep `.env`, the pass file, and the cookie jar
on the machine you run it from.

## What it does

Read tools (return clean JSON):

| Tool | Page |
| --- | --- |
| `get_schedule` | `assignatures/el_meu_horari.php` |
| `get_calendar` | `calendari/index.php` |
| `get_subjects_and_rosters` | `go/Index.php?ctr=Subjects/Subjects` |
| `get_roster(class_id)` | `go/Index.php?ctr=Classes/Students&id=` |
| `get_session_detail(assig, sessio)` | `assignatures/sessio.php` |
| `get_attendance(cgap, sessio, n)` | `assistencia/index.php` (current state) |
| `get_inbox` | `go/Index.php?ctr=Communication/Communication` |
| `get_chat_contacts` | `go/Index.php?ctr=Messaging/Chat` |
| `get_documents` | `go/Index.php?ctr=Documents/DocumentsRegistry&do=Last` |
| `get_files` | `files/index.php` |
| `list_message_recipients(query)` | compose directory (read-only) |

Write tools (gated — one explicit action, previewed, then confirmed):

| Tool | Action |
| --- | --- |
| `mark_attendance(cgap, sessio, alu_id, absent, reason_code, justified, confirm)` | mark one student present/absent for one session |
| `send_message(recipient_id, subject, body, confirm)` | send one message to one recipient |

Both write tools return a **preview** and write nothing unless you call them
again with `confirm=true`. `mark_attendance` re-reads the whole session form and
flips only the one student, so no one else's attendance is touched; after the
POST it re-reads the page to verify. There is no bulk mode, no loop over a class,
no scheduled run, and no student impersonation.

## Setup (on your laptop)

Requires [uv](https://docs.astral.sh/uv/).

```sh
cd clickedu-mcp
cp .env.example .env     # then edit .env
```

Fill `.env`:

```
CLICKEDU_BASE_URL=https://jpif.clickedu.eu
CLICKEDU_USERNAME=your_user
CLICKEDU_PASSWORD=your_password
CLICKEDU_ID_USUARI=        # leave blank; scraped on first login
CLICKEDU_PASSFILE=/absolute/path/to/your/arxiu_de_pas.txt
CLICKEDU_COOKIE_PATH=.cookies/session.jar
```

Put your pass file (`arxiu de pas`) somewhere local and point `CLICKEDU_PASSFILE`
at it. Install and smoke-test login:

```sh
uv sync
uv run python -c "from clickedu_mcp.session import get_session; get_session(); print('login ok')"
```

## Run it from Claude

Register it as a stdio MCP server. For Claude Code:

```sh
claude mcp add clickedu -- uv --directory /ABSOLUTE/PATH/TO/clickedu-mcp run clickedu-mcp
```

Or in a `claude_desktop_config.json` / MCP client config:

```json
{
  "mcpServers": {
    "clickedu": {
      "command": "uv",
      "args": ["--directory", "/ABSOLUTE/PATH/TO/clickedu-mcp", "run", "clickedu-mcp"]
    }
  }
}
```

The server reads `.env` from its own directory on startup, logs in with the
two-step flow (username/password, then pass-file upload), reuses the cookie jar,
and re-logs in automatically when the session expires.

## Security model

- Credentials and the pass file live only in local `.env` / disk, never in code
  or git (`.gitignore` covers `.env`, `secrets/`, `.cookies/`).
- Pages are ISO-8859-15; they are decoded before parsing.
- Every write is a single action you confirm in the moment.
- `popup_suplantar_alu` (student impersonation) is not implemented and never will be.

## Status notes

- Read tools are validated end to end against the live site.
- `get_inbox`/`get_chat_contacts`/`get_documents` reflect that, for this account,
  Communication is a broadcast hub and the chat/document modules are JSON SPAs
  that are currently empty; each returns a clear `note`.
- Write tools are validated through their preview path against live data. The
  real POST for `send_message` (recipient packing + CSRF token) should be
  confirmed on a first send to yourself; adjust `accio`/recipient field if the
  server rejects it.
