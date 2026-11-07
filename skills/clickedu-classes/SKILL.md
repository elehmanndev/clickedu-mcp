---
name: clickedu-classes
allowed-tools: [mcp__clickedu__get_subjects_and_rosters, mcp__clickedu__get_roster]
description: >-
  Les meves classes i alumnes a Clickedu. Usa-la quan el profe digui "les meves
  classes / mis clases", "els meus alumnes / mis alumnos", "llista de classe /
  lista de clase", "qui hi ha a 4t ESO / quién está en", "la meva tutoria".
---

# Classes i alumnes

1. `get_subjects_and_rosters` → les assignatures i grups del profe. Cada entrada
   porta `class_id` (grup, per llistes, assistència i comportament) i/o
   `subject_id` (assignatura, per l'avaluació), més enllaços de tutoria i curs.
2. `get_roster(class_id)` → la llista d'alumnes del grup (`alu_id`, `name`).

Aquests ids alimenten les altres skills: `clickedu-tutoria` (resum d'assistència
i comportament del grup), `clickedu-alumne` (seguiment d'un alumne) i
`clickedu-avaluacio` (notes d'una assignatura). Per una sessió concreta, usa
`clickedu-sessio`.
