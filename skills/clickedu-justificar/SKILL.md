---
name: clickedu-justificar
allowed-tools: [mcp__clickedu__get_subjects_and_rosters, mcp__clickedu__get_roster, mcp__clickedu__justify_absences]
description: >-
  Justificar en bloc les faltes i retards d'un alumne de la teva tutoria a
  Clickedu. Usa-la quan el profe digui "justifica les faltes de", "justificar en
  bloc", "justifica l'absència d'ahir de", "la mare ha justificat", "justifica
  els retards de", "justificar faltas de", "justificar ausencias".
---

# Justificar faltes i retards (en bloc, d'un alumne)

Només per als alumnes de la teva tutoria. **Un alumne per crida, sempre
confirmat pel profe.** Mai es recorre tota la classe.

Flux:

1. Troba l'alumne: `get_subjects_and_rosters` → `class_id` de la tutoria →
   `get_roster(class_id)` → `alu_id`.
2. `justify_absences(alu_id, date_from, date_to, record_ids, note, confirm)`:
   - Dates YYYY-MM-DD. Sense `date_to`, només aquell dia («ahir» = la data
     d'ahir).
   - Primer **sense** `confirm`: llista les faltes i retards **sense justificar**
     del rang (`pending`, amb `record_id`, data, hora, matèria i tipus) i quines es
     justificarien (`to_justify`). Ensenya-ho i **espera el sí** explícit.
   - `record_ids` tria només algunes; sense, es justifiquen totes les pendents
     del rang. Si el profe només en vol algunes, passa els seus `record_id`.
   - `note`: text de l'anotació (p. ex. «Visita mèdica»). Opcional.
   - Després `confirm=true`. Rellegeix el rang i comprova que les triades ja no
     surten com a pendents i que les altres segueixen igual (`verified`).
   - `status="empty"` vol dir que no hi ha res pendent en aquell rang.

La casella «Envia'm per correu una còpia» no es marca mai.
