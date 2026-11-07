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
| `get_session_notes(cgap, sessio)` | `assistencia/index.php` (homework, observation and other per-student views of a session) |
| `get_monthly_attendance(class_id, months)` | `go/Index.php?ctr=Classes/Attendance&do=MonthlyAccumulated` (A / AJ / R / RJ per student and month) |
| `get_student_daily(alu_id, class_id, date_from, date_to)` | student file "Dia a dia" (each absence, late, homework, observation by date) |
| `get_class_behaviour(class_id, date_from, date_to)` | `go/Index.php?ctr=Classes/Behaviour` (incidents and merits) |
| `get_evaluation(subject_id, term_id)` | `go/Index.php?ctr=Evaluate/EvaluateTermly` (sections, activities, weights, grades) |
| `list_message_recipients(query)` | compose directory (read-only) |

Every read answers with a `status`: `ok` (has data), `empty` (read fine, nothing
there) or `error` (could not read: login, a Clickedu alert such as "No disposeu de
permisos", or a parsing problem). An error never looks like an empty list.

Write (gated — preview first, then `confirm=true`):

| Tool | Action |
| --- | --- |
| `mark_attendance(cgap, sessio, alu_id, status, reason_code, justified, confirm)` | set one student `absent`, `late` or `present` for one session |
| `add_observation(cgap, sessio, alu_id, text, notify_family, confirm)` | write one student's observation for one session; optionally tick "Enviar correu electrònic" (emails the family) |
| `mark_homework(cgap, sessio, alu_id, status, note, notify_family, confirm)` | set one student's homework `fets` / `no fets` / `no demanats` for one session |
| `add_tutor_conversation(alu_id, title, text, participants, confirm)` | record one interview summary in a tutored student's file (Converses del tutor); participants ticked, never notified |
| `justify_absences(alu_id, date_from, date_to, keys, include_not_taken, note, confirm)` | justify one tutored student's absences/lates in a date range (Justificar en bloc); optionally also sessions where the register was not taken |
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
automatically when the session expires. Each page is decoded with the charset it
declares (most Clickedu pages are ISO-8859-15, some AJAX answers are UTF-8).

## Notes

- Parsers were validated against one school's Clickedu instance. The login flow and
  page structure are shared across Clickedu, but if a page parses empty on your school,
  open an issue with the (redacted) HTML and it can be adjusted.
- `get_inbox` / `get_chat_contacts` may add a `note` when a module is a broadcast hub
  or a JSON SPA with nothing to show for your account.
- `get_class_behaviour` was only validated on a class with nothing recorded; filled
  reports are read generically from their table headers. Report any odd output.
- Grades are read-only. Writing grades, creating sections/activities, and family
  history/attachments are not implemented yet.
- `add_observation`, `mark_homework` and `mark_attendance` save the whole session
  form the way the page's Guardar button does, replaying every other student
  unchanged. With `notify_family`, Clickedu itself sends the email on save; the page
  does not confirm delivery.

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
| `clickedu-observacions` | posa una observació · avisa la família · pon una observación | one student's session observation, optional family email (preview → confirm) |
| `clickedu-converses` | anota l'entrevista · resum de l'entrevista · conversa del tutor | one interview summary in a tutored student's file (preview → confirm) |
| `clickedu-justificar` | justifica les faltes de · justificar en bloc · justificar faltas | one tutored student's absences/lates in a date range (preview → confirm) |
| `clickedu-deures` | no ha fet els deures · falta de deberes · marca deures | one student's homework for a session (preview → confirm) |
| `clickedu-tutoria` | resum mensual acumulat · quants retards porta el grup · incidències del grup | class monthly A/AJ/R/RJ and behaviour (read-only) |
| `clickedu-alumne` | seguiment de l'alumne · dia a dia · quines faltes té · ha fet els deures | one student's day-by-day log (read-only) |
| `clickedu-avaluacio` | les notes de · apartats i percentatges · notas de la 1ª evaluación | sections, activities, weights and grades (read-only) |

Write skills (`clickedu-assistencia`, `clickedu-retards`, `clickedu-observacions`, `clickedu-deures`, `clickedu-converses`, `clickedu-justificar`, `clickedu-missatges`)
encode the per-action preview-then-confirm and the no-bulk / no-impersonation rules.

## Contributing

PRs welcome, with one rule: you are the author of what you submit and can explain and
have run it. Keep secrets out of code, tests and fixtures. Do not add bulk writes,
autonomous runs, or impersonation. See [AGENTS.md](AGENTS.md) for the tool and skill
conventions.

## License

MIT — see [LICENSE](LICENSE).
