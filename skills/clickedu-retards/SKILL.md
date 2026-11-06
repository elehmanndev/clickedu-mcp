---
name: clickedu-retards
description: >-
  Marcar retards (arribades tard) a Clickedu. Usa-la quan el profe digui "posar un
  retard", "marcar retard", "poner un retraso / una tardanza", "ha arribat tard /
  ha llegado tarde", "li poso retard". Per faltes/absències, usa
  clickedu-assistencia.
---

# Retards (arribades tard)

Mateixa mecànica que l'assistència, però marcant **retard** en comptes de falta.
**Sempre confirmat pel profe, un alumne cada cop, mai bulk.**

1. `get_schedule` → sessió d'avui → `session_link` (`assig`, `sessio`).
2. `get_session_detail(assig, sessio)` → `attendance_link` (`cgap`, `sessio`, `n`).
3. `get_attendance(cgap, sessio, n)` → troba l'alumne (`alu_id`, `name`, `status`).
4. `mark_attendance(cgap, sessio, alu_id, status="late", reason_code, justified, confirm)`:
   - Primer **sense** `confirm` → vista prèvia; ensenya-la i **espera el sí**.
   - Després `confirm=true`; rellegeix i comprova `verified`.
   - `reason_code` opcional (`10` MALALT, `11` METGE, `12` GESTIONS);
     `justified=true` el justifica. `status="present"` treu el retard.

Per faltes/absències (no retard) usa `clickedu-assistencia`.
