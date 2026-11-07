---
name: clickedu-deures
allowed-tools: [mcp__clickedu__get_schedule, mcp__clickedu__get_session_detail, mcp__clickedu__get_session_notes, mcp__clickedu__mark_homework]
description: >-
  Marcar els deures d'un alumne en una sessió de Clickedu (fets, no fets, no
  demanats). Usa-la quan el profe digui "no ha fet els deures / no ha hecho los
  deberes", "deures no fets", "falta de deures / falta de deberes", "marca deures",
  "ha fet els deures", "qui no ha fet els deures".
---

# Deures d'una sessió

**Un alumne cada cop, sempre confirmat pel profe.** Mai tota la classe de cop.

Flux:

1. `get_schedule` → sessió → `get_session_detail(assig, sessio)` →
   `attendance_link` (`cgap`, `sessio`).
2. `get_session_notes(cgap, sessio)` → per alumne, `homework` actual (`fets`,
   `no fets`, `no demanats` o buit) i `homework_note`.
3. `mark_homework(cgap, sessio, alu_id, status, note, notify_family, confirm)`:
   - `status`: `"no fets"` (per defecte), `"fets"` o `"no demanats"`.
   - `note` opcional; buida conserva la nota que ja hi hagués.
   - Primer **sense** `confirm`: vista prèvia (abans i després). Espera el sí.
   - Després `confirm=true`; rellegeix i informa de `verified`.
   - `notify_family=true` marca «Enviar correu electrònic» i **Clickedu envia un
     correu real a la família**. Només si el profe ho demana.

Per consultar deures d'altres dies, usa `clickedu-alumne` (dia a dia).
