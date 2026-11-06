# Attendance model and protocol

Shared by `clickedu-assistencia` (faltes) and `clickedu-retards` (retards). Both
use the same chain and the same `mark_attendance` tool; only the `status` differs.

## ID chain (do not guess IDs)

1. `get_schedule` → today's session; take its `session_link`
   (`sessio.php?assig=<assig>&sessio=<sessio>`).
2. `get_session_detail(assig, sessio)` → its `attendance_link`
   (`assistencia/index.php?cgap=<cgap>&sessio=<sessio>&n=<n>`).
3. `get_attendance(cgap, sessio, n)` → current state: each student with `alu_id`,
   `name`, `status` (`present` / `absent` / `late`), `reason`, `justified`.
4. `mark_attendance(cgap, sessio, alu_id, status, reason_code, justified, confirm)`.

## mark_attendance parameters

- `status`: `"absent"` (falta), `"late"` (retard), or `"present"` (clears any
  absence/late).
- `reason_code` (for absent/late): `10` = MALALT (ill), `11` = METGE (doctor),
  `12` = GESTIONS.
- `justified`: `true` marks the absence/late as justified.

## Preview-then-confirm protocol (mandatory)

- Call `mark_attendance` first **without** `confirm` (or `confirm=false`): it
  returns a preview of the exact change (`before` → `after`) and writes nothing.
- Show that preview to the teacher and **wait for an explicit yes**.
- Only then call again with `confirm=true`. It re-reads the page and reports
  `verified` (true if the re-read matches).

## Rules

- One student per call. Never loop over a class, never bulk-mark.
- If asked to "mark the whole class", refuse the bulk action; do confirmed
  students one at a time, or ask which students.
- Never impersonate a student (`popup_suplantar_alu` is not available).
- The server replays every other student's current state unchanged and flips only
  the target, so no one else's attendance is touched.
