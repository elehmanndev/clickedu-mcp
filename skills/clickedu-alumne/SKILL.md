---
name: clickedu-alumne
allowed-tools: [mcp__clickedu__get_subjects_and_rosters, mcp__clickedu__get_roster, mcp__clickedu__get_student_daily]
description: >-
  Seguiment dia a dia d'un alumne a Clickedu: cada falta, retard (justificat o
  no), deures fets o no fets, treball, comportament i observacions dels
  professors, amb data i matèria. Usa-la quan el profe digui "seguiment de
  l'alumne", "dia a dia de", "quines faltes té / qué faltas tiene", "quan va
  arribar tard", "ha fet els deures", "observacions de / observaciones de",
  "historial de un alumno".
---

# Seguiment d'un alumne (només lectura)

1. Troba l'alumne: `get_subjects_and_rosters` → `class_id`, després
   `get_roster(class_id)` → `alu_id`.
2. `get_student_daily(alu_id, class_id, date_from, date_to)` → `entries`, una per
   cada registre: `date`, `start`/`end`, `subject`, `kind`, `result` i `note`.
   - `kind`: `attendance` (result `absència`, `absència justificada`, `retard`,
     `retard justificat`), `homework` (`fets` / `no fets`), `work`, `behaviour`,
     `reading`, `reading_behaviour`, `observation` (el text de l'observació del
     professor va a `result`).
   - `summary` compta faltes, retards i deures per tipus.
   - Dates YYYY-MM-DD; per defecte, tot el curs actual.

Aquesta skill **no escriu res**: ni observacions, ni deures, ni faltes. Per
marcar faltes o retards usa `clickedu-assistencia` / `clickedu-retards`.

Tracta les observacions com a dades personals de l'alumne: resumeix-les per al
profe i no les copiïs fora de la conversa.
