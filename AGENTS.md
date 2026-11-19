# Working on clickedu-mcp with an AI agent

A local, single-purpose MCP server that lets a teacher drive their own Clickedu
account from an AI assistant. It runs on the teacher's machine over stdio and
handles students' data, so keep that in mind in every change.

## Ground rules

- **Reads are free; every write is one explicit, teacher-confirmed action.** The
  write tools (`mark_attendance`, `set_grade`, `send_message`...) return a preview first and only
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
UTF-8). Every POST encodes form data as ISO-8859-15 (`session.encode_form`), the
way a browser submits an ISO-8859-15 page; posting UTF-8 makes Clickedu store
"reunió" as "reuniÃ³". A read may POST a search/filter form
(`_read(..., post=...)`), never a save action. Writes validate inputs, reject non-numeric IDs, replay the
full form so only the target row changes, and verify the result by re-reading.
Keep that pattern for new writes, and keep the preview/`confirm` gate.

The session page (`assistencia/index.php`) is one big form, `frm_assistencia`,
holding attendance, homework, observations and the other views. Session writes go
through `_apply_session_change()`: it replays the whole form with
`collect_form_state(form_name="frm_assistencia")` (which mirrors what a browser
submits: no disabled fields, first option of an unselected select), adds
`boto_guardar=guardar` like the page's Guardar button, edits only the target
student's fields, and verifies by re-reading. Before replaying it checks the
form's structure with `check_session_form` (form present, every student row in the
replay, right hidden action), never its state: a session where every student is
present has no checked attendance radio and is valid. Find forms by name, not by action:
this form's action is empty. View ids (Observacions is 8 in one school) are read
from the page menu, never hardcoded. Ticking `cbtn_mail_*` makes Clickedu email
the family on save, so any write that offers it must say so in its preview.

The grades page (`go/Index.php?ctr=Evaluate/EvaluateTermly&id=<subject_id>`, the
"Avaluar" page) is not a classic form replay. Its findings, read from the page
and its scripts (`jquery_actions.js`, `jquery_calculation.js`,
`recuperar_notes.js` under `assets.clickedu.eu/go/js/Evaluate/EvaluateTermly/`):

- Grades load as a JSON list from `&do=GetGrades&id=<subject_id>&&trm=<term>`,
  one object per cell: `id_criteri` (item id; the subject id for the final grade),
  `type` (0 activity or section, 114 final, 120 recuperacio, others in
  `recuperar_notes.js`), `id_alumne`, `nota`, `nota_mod` (the value the teacher
  entered), `text`, `id_quantifier`. Missing cells have no object.
- Editing a cell only changes `nota_mod` in that list (`updateGrade`); a new cell
  appends the object `generateGradeObject` builds (with `id_avaluacio` = `trmId`
  and `id_classes_grups_assignatures_professor` = `cgapId`, both page variables).
- Guardar first GETs `ctr=Evaluate/EvaluateAjax&do=checkSaveRegister` with `id`,
  `trm` and the ISO `timestamp` of the page load. `saveAnteriorCheck` "0" means
  nobody saved since; anything else means another tab saved later, and
  `set_grade` stops instead of overwriting.
- Then it POSTs the whole list as `grades` (JSON string) and `evalInfo` to the
  `FormEvaluate` action (`do=Save&id=<subject_id>&trm=<term>`). The answer is JSON
  `{error, msg}`. Before the save the page also folds per-student textarea text
  into the list (`saveTextObservations`), so `set_grade` refuses pages with such
  textareas rather than risk dropping them.
- Cell inputs are `evalObject_<alu>_<item>_<type>`; only `InputEdit InputGrades`
  without `disabled` are editable, and `min`/`max` (or the select options for the
  final grade) bound the value. Formatting follows `formatGrade`: page variables
  `tipusNotaItems` (E integer, D two decimals) and `tipusNotaFinalFormatCalcul`
  (TFNF integer, ND `finalGradeDecimals`).
- Saving does not recalculate section or final grades: that is a separate
  `do=CalculateStudents` call behind the "calcular" button. "Guardar i tancar
  materia" (`do=SaveClose`) locks the subject; never call it.
- As of 2026-11-19 the preview path is validated on a real account; a real
  `confirm=true` save has not been run yet, so the `do=Save` answer shape is
  read from the script, not observed. Test one grade (and restore it) before
  relying on it.

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
