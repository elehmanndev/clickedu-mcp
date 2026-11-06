---
name: clickedu-assistencia
description: >-
  Passar llista i marcar faltes a Clickedu. Usa-la quan el profe digui "passar
  llista", "pasar lista", "marcar falta", "posar absent / poner ausente", "qui ha
  faltat / quién ha faltado", "assistència / asistencia d'avui". Per arribades
  tard, usa clickedu-retards.
---

# Assistència (passar llista, faltes)

Llegir és lliure; **marcar és sempre una acció que el profe confirma al moment.**
Un alumne cada cop, mai tota la classe de cop, mai suplantar ningú.

Encadena els IDs, no te'ls inventis:

1. `get_schedule` → la sessió d'avui; agafa el `session_link`
   (`sessio.php?assig=<assig>&sessio=<sessio>`).
2. `get_session_detail(assig, sessio)` → l'`attendance_link`
   (`assistencia/index.php?cgap=<cgap>&sessio=<sessio>&n=<n>`).
3. `get_attendance(cgap, sessio, n)` → estat actual: cada alumne amb `alu_id`,
   `name`, `status` (present / absent / late), motiu i justificat.
4. `mark_attendance(cgap, sessio, alu_id, status, reason_code, justified, confirm)`
   — **un alumne cada cop**:
   - Primer **sense** `confirm`: retorna la vista prèvia (abans → després), no
     escriu res. Ensenya-la i **espera el sí** del profe.
   - Després `confirm=true`; rellegeix i informa de `verified`.
   - Faltes: `status="absent"` (o `"present"` per treure-la). `reason_code`:
     `10` MALALT, `11` METGE, `12` GESTIONS. `justified=true` la justifica.

Per marcar un **retard** usa `status="late"` — ho cobreix la skill
`clickedu-retards`. Si demanen "marca tota la classe", nega el bulk.
