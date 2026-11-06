# Attendance model and protocol

Shared by `clickedu-assistencia` (faltes) and `clickedu-retards` (retards). Both
use the same chain and the same `mark_attendance` tool; only the `status` differs.
For retards, use `status="late"`.

## ID chain (do not guess IDs)

1. `get_schedule` → today's session; take its `session_link`
   (`sessio.php?assig=<assig>&sessio=<sessio>`).
2. `get_session_detail(assig, sessio)` → its `attendance_link`
   (`assistencia/index.php?cgap=<cgap>&sessio=<sessio>&n=<n>`).
3. `get_attendance(cgap, sessio, n)` → current state: each student with `alu_id`,
   `name`, `status` (`present` / `absent` / `late`), `reason`, `justified`.
4. `mark_attendance(cgap, sessio, alu_id, status, reason_code, justified, confirm)`.

## mark_attendance parameters

- `status`: `"late"` (retard), `"absent"` (falta), or `"present"` (clears it).
- `reason_code` (optional for late): `10` = MALALT, `11` = METGE, `12` = GESTIONS.
- `justified`: `true` marks it justified.

## Preview-then-confirm protocol (mandatory)

- Call `mark_attendance` first **without** `confirm`: it returns a preview of the
  exact change (`before` → `after`) and writes nothing.
- Show that preview to the teacher and **wait for an explicit yes**.
- Only then call again with `confirm=true`. It re-reads and reports `verified`.

## Rules

- One student per call. Never loop over a class, never bulk-mark.
- Never impersonate a student. The server flips only the target student and
  replays everyone else unchanged.
