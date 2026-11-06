---
name: clickedu-retards
allowed-tools: [mcp__clickedu__get_schedule, mcp__clickedu__get_session_detail, mcp__clickedu__get_attendance, mcp__clickedu__mark_attendance]
description: >-
  Marcar retards (arribades tard) a Clickedu. Usa-la quan el profe digui "posar un
  retard", "marcar retard", "poner un retraso / una tardanza", "ha arribat tard /
  ha llegado tarde", "li poso retard". Per faltes/absències, usa
  clickedu-assistencia.
---

# Retards (arribades tard)

Mateixa mecànica que l'assistència, però marcant **`status="late"`**.
**Sempre confirmat pel profe, un alumne cada cop, mai bulk, mai suplantar.**

Flux: `get_schedule` → `get_session_detail` → `get_attendance` →
`mark_attendance(..., status="late", confirm=...)`, en **dos passos**: primer
sense `confirm` (vista prèvia, espera el sí), després `confirm=true`.
`status="present"` treu el retard.

Cadena d'IDs, codis de motiu i protocol complet:
[`references/attendance.md`](references/attendance.md). Per faltes/absències, usa
`clickedu-assistencia`.
