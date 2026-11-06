---
name: clickedu-assistencia
allowed-tools: [mcp__clickedu__get_schedule, mcp__clickedu__get_session_detail, mcp__clickedu__get_attendance, mcp__clickedu__mark_attendance]
description: >-
  Passar llista i marcar faltes a Clickedu. Usa-la quan el profe digui "passar
  llista", "pasar lista", "marcar falta", "posar absent / poner ausente", "qui ha
  faltat / quién ha faltado", "assistència / asistencia d'avui". Per arribades
  tard, usa clickedu-retards.
---

# Assistència (passar llista, faltes)

Llegir és lliure; **marcar és sempre una acció que el profe confirma al moment** —
un alumne cada cop, mai tota la classe de cop, mai suplantar ningú.

Flux: `get_schedule` → `get_session_detail` → `get_attendance` →
`mark_attendance` amb `status="absent"` (o `"present"` per treure la falta), en
**dos passos**: primer sense `confirm` (vista prèvia, ensenya-la i espera el sí
del profe), després `confirm=true`.

Si demanen "marca tota la classe", nega el bulk.

La cadena d'IDs exacta, els codis de motiu i el protocol de confirmació:
[`references/attendance.md`](references/attendance.md). Per retards, usa
`clickedu-retards`.
