---
name: clickedu
description: >-
  Drive the daily Clickedu teaching workflow through the clickedu MCP tools:
  take attendance for a class session, look up rosters / sessions / per-student
  info, and message a family. Use when the teacher asks to pass/take attendance
  ("pasar lista", "marcar falta/retard", "quién ha faltado"), to look up a class
  list, a student or a session ("mi clase", "alumnos de", "la sesión de"), or to
  send a message to a family/contact ("manda un mensaje a", "avisa a la familia").
---

# Clickedu teacher workflow

These tools talk to the teacher's own Clickedu account. Reads are free; **every
write is one explicit action the teacher confirms in the moment.** Never do bulk
writes, never loop over a class, never impersonate a student.

Tool names below are the MCP tools (`get_schedule`, `mark_attendance`, ...). If a
read returns an `error`, relay it; if it returns a `note`, that module is empty
for this account, say so plainly.

## Taking attendance (pasar lista)

Chain the IDs, do not guess them:

1. `get_schedule` → find today's session; take its `session_link`
   (`sessio.php?assig=<assig>&sessio=<sessio>`).
2. `get_session_detail(assig, sessio)` → read its `attendance_link`
   (`assistencia/index.php?cgap=<cgap>&sessio=<sessio>&n=<n>`).
3. `get_attendance(cgap, sessio, n)` → the current state: each student with
   `alu_id`, `name`, `status` (present / absent / late), reason, justified.
4. `mark_attendance(cgap, sessio, alu_id, status, reason_code, justified, confirm)`
   — **one student at a time.**
   - Call it first **without** `confirm` (or `confirm=false`): it returns a
     preview of the exact change (before → after) and writes nothing.
   - Show that preview to the teacher and **wait for an explicit yes**.
   - Only then call again with `confirm=true`. It re-reads the page and reports
     `verified`.
   - `status` is `"absent"`, `"late"` (retard), or `"present"` (clears any
     absence/late). `reason_code` for absent/late: `10` = MALALT (ill),
     `11` = METGE (doctor), `12` = GESTIONS. `justified=true` marks it justified.

If the teacher says "mark the whole class / everyone absent", refuse the bulk
action and do them one confirmed student at a time, or ask them to name the
students.

## Rosters, sessions and per-student info (rúbricas/notas)

- `get_subjects_and_rosters` → the teacher's subjects and class groups, each with
  a `class_id`, plus tutor/course tool links.
- `get_roster(class_id)` → the student list for that class (`alu_id`, `name`).
- `get_session_detail(assig, sessio)` → one session's content and valoració
  fields.

These tools read structure and session content. Full grade entry / rubric
editing lives in Clickedu's own evaluation pages (the `avaluacions` /
`avaluar per alumne` links surfaced in `get_subjects_and_rosters`); there is no
write tool for grades here, so point the teacher to those links rather than
inventing one.

## Messaging a family / contact (mensajes a familias)

1. `list_message_recipients(query)` → find the recipient; use a name substring to
   narrow it. Each result has an `id` (e.g. `u_1610`); a plain email also works.
2. `send_message(recipient_id, subject, body, confirm)` — **one recipient.**
   - First call without `confirm`: returns a preview (resolved recipient,
     subject, body). Show it and **wait for the teacher's yes**.
   - Then call with `confirm=true` to send.

Never send to a whole group or loop over recipients. One message, one recipient,
one confirmation.

## Guardrails

- Confirm every attendance change, grade-adjacent action, and family message
  before it is sent — the teacher reviews each one.
- Prefer reading and summarizing; only write when asked, and always one action
  at a time.
- This runs on the teacher's own machine; keep student data in the conversation,
  do not send it anywhere else.
