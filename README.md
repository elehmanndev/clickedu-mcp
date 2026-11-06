# clickedu-mcp

A local [MCP](https://modelcontextprotocol.io) server that lets a teacher run their
**Clickedu** daily workflow from an AI assistant (Claude Desktop, Claude Code, or any
MCP client): read your schedule, rosters, calendar, session detail, attendance,
messages and files — and take single, confirmed write actions (mark one student's
attendance, send one message).

[Clickedu](https://clickedu.eu) is a school management platform used by many schools,
each on its own subdomain (`https://yourschool.clickedu.eu`). This talks to **your own
staff account** over the same two-step login the website uses.

It is built to run **on your own machine**. It handles your students' data, so it runs
locally over stdio and keeps your credentials, pass file and session cookie on your own
disk — nothing is sent anywhere except Clickedu itself.

## Ethics and scope

- Use it only with **your own** account and the access your school already grants you.
- Every write is **one explicit action you confirm in the moment**. There is no bulk
  mode, no loop over a class, and no scheduled/autonomous run.
- Student impersonation (Clickedu's `popup_suplantar_alu`) is **not implemented** and
  will not be accepted as a contribution.
- You are responsible for complying with your school's and your country's data rules.

## Quick start (runs on your laptop)

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

## Notes

- Parsers were validated against one school's Clickedu instance. The login flow and
  page structure are shared across Clickedu, but if a page parses empty on your school,
  open an issue with the (redacted) HTML and it can be adjusted.
- `get_inbox` / `get_chat_contacts` / `get_documents` return a status `note` when a
  module is a broadcast hub or a JSON SPA with nothing to show for your account.

## Agent skills

`skills/` ships one Agent Skill per teacher task, so the assistant is triggered by
what a teacher actually says (in Catalan and Spanish) and knows the right tool
chain and guardrails. Clients that support skills (Claude Code, Codex, Cursor)
pick them up from the repo.

| Skill | Teacher says | Covers |
| --- | --- | --- |
| `clickedu-assistencia` | passar llista · pasar lista · marcar falta · qui ha faltat | read attendance + mark absent/present (preview → confirm) |
| `clickedu-retards` | posar un retard · marcar retraso/tardanza · ha arribat tard | mark late (preview → confirm) |
| `clickedu-horari` | el meu horari · mi horario · què tinc avui | the weekly schedule |
| `clickedu-classes` | les meves classes · mis alumnos · llista de classe | subjects and class rosters |
| `clickedu-sessio` | la sessió de · què toca · contingut de la sessió | one session's detail |
| `clickedu-missatges` | enviar missatge a família · avisar a | send one message (preview → confirm) |
| `clickedu-safata` | missatges rebuts · mi bandeja · xat | read inbox and chat contacts |
| `clickedu-calendari` | calendari · eventos | calendar events |
| `clickedu-documents` | documents · arxius · ficheros | documents and files |

Write skills (`clickedu-assistencia`, `clickedu-retards`, `clickedu-missatges`)
encode the per-action preview-then-confirm and the no-bulk / no-impersonation rules.

## Contributing

PRs welcome, with one rule: you are the author of what you submit and can explain and
have run it. Keep secrets out of code, tests and fixtures. Do not add bulk writes,
autonomous runs, or impersonation. See [AGENTS.md](AGENTS.md) for the tool and skill
conventions.

## License

MIT — see [LICENSE](LICENSE).
