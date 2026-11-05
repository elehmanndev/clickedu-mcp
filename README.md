# clickedu-mcp

A local [MCP](https://modelcontextprotocol.io) server that lets a teacher run their
**Clickedu** daily workflow from an AI assistant (Claude Desktop, Claude Code, or any
MCP client): read your schedule, rosters, calendar, session detail, attendance,
messages and files — and take single, confirmed write actions (mark one student's
attendance, send one message).

[Clickedu](https://clickedu.eu) is a school management platform used by many schools,
each on its own subdomain (`https://yourschool.clickedu.eu`). This talks to **your own
staff account** over the same two-step login the website uses.

It is built to run **on your own machine**. It handles your students' data, so by
default it runs locally over stdio and keeps your credentials, pass file and session
cookie on disk next to it. An optional HTTP transport is included if you know what you
are doing and put it behind your own authentication.

## Ethics and scope

- Use it only with **your own** account and the access your school already grants you.
- Every write is **one explicit action you confirm in the moment**. There is no bulk
  mode, no loop over a class, and no scheduled/autonomous run.
- Student impersonation (Clickedu's `popup_suplantar_alu`) is **not implemented** and
  will not be accepted as a contribution.
- You are responsible for complying with your school's and your country's data rules.

## Quick start (easiest — no Docker, no Cloudflare)

If you use **Codex CLI**, **Claude Code**, **Cursor**, or any tool that runs a local
MCP server, this is the whole setup. It runs on your own laptop; your students' data
never leaves your machine.

Install [uv](https://docs.astral.sh/uv/) (one line — see its site), then:

```sh
# 1) one-time: enter your school URL, login and pass file
uvx --from git+https://github.com/elehmanndev/clickedu-mcp clickedu-mcp setup

# 2) add it to Codex (one line)
codex mcp add clickedu -- uvx --from git+https://github.com/elehmanndev/clickedu-mcp clickedu-mcp
```

`setup` stores everything under `~/.clickedu-mcp/` and tests your login before you
finish. For Claude Code the second line is
`claude mcp add clickedu -- uvx --from git+https://github.com/elehmanndev/clickedu-mcp clickedu-mcp`.
For Claude Desktop / Cursor, use the same command/args in their MCP config.

> ChatGPT and the Codex cloud connector only accept *remote* MCP servers over OAuth,
> which cannot run locally like this. Local MCP (above) is the simple path; a remote
> deployment is far more involved and is out of scope for most teachers.

## Tools

Read (return clean JSON):

| Tool | Clickedu page |
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

Write (gated — preview first, then `confirm=true`):

| Tool | Action |
| --- | --- |
| `mark_attendance(cgap, sessio, alu_id, absent, reason_code, justified, confirm)` | mark one student present/absent for one session |
| `send_message(recipient_id, subject, body, confirm)` | send one message to one recipient |

`mark_attendance` re-reads the whole session form and flips only the one student, so
no one else's attendance is touched, then re-reads the page to verify the change.

## Requirements

- [uv](https://docs.astral.sh/uv/) (Python toolchain and runner).
- Your Clickedu **pass file** (the `arxiu de pas` your school issued you — the file you
  upload as the second login step).

## Setup

```sh
git clone https://github.com/elehmanndev/clickedu-mcp
cd clickedu-mcp
cp .env.example .env    # then edit .env
uv sync
```

Fill `.env` with your school URL, your login, and the absolute path to your pass file.
Leave `CLICKEDU_ID_USUARI` blank — it is scraped on first login and printed so you can
pin it. Confirm login works:

```sh
uv run python -c "from clickedu_mcp.session import get_session; get_session(); print('login ok')"
```

## Use it from your assistant

Register it as a stdio MCP server. Claude Code:

```sh
claude mcp add clickedu -- uv --directory /ABSOLUTE/PATH/TO/clickedu-mcp run clickedu-mcp
```

Claude Desktop / other MCP clients (`claude_desktop_config.json`):

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

The server reads `.env` from its own directory, performs the two-step login
(username/password, then pass-file upload), reuses the cookie jar, and re-logs in
automatically when the session expires. Clickedu pages are ISO-8859-15; they are
decoded before parsing.

## Optional: run over HTTP

If you want to reach it from a remote MCP gateway instead of stdio, set
`CLICKEDU_TRANSPORT=streamable-http` (see `.env.example`) and run it. It serves at
`/mcp`. A `Dockerfile` is included for this:

```sh
docker build -t clickedu-mcp .
docker run -d --name clickedu-mcp --restart unless-stopped \
  -p 127.0.0.1:8791:8791 \
  --env-file /path/to/clickedu.env \
  -v /path/to/arxiu_de_pas.txt:/secrets/passfile:ro \
  -v /path/to/cookiedir:/data \
  clickedu-mcp
```

This transport has **no authentication of its own** — it exposes your logged-in
session to anyone who can reach the port. Only run it bound to localhost or behind a
gateway that authenticates callers, never directly on the public internet.

## Notes

- Parsers were validated against one school's Clickedu instance. The login flow and
  page structure are shared across Clickedu, but if a page parses empty on your school,
  open an issue with the (redacted) HTML and it can be adjusted.
- `get_inbox` / `get_chat_contacts` / `get_documents` return a status `note` when a
  module is a broadcast hub or a JSON SPA with nothing to show for your account.

## Contributing

PRs welcome, with one rule: you are the author of what you submit and can explain and
have run it. Keep secrets out of code, tests and fixtures. Do not add bulk writes,
autonomous runs, or impersonation.

## License

MIT — see [LICENSE](LICENSE).
