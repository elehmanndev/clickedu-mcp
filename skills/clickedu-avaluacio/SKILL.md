---
name: clickedu-avaluacio
allowed-tools: [mcp__clickedu__get_subjects_and_rosters, mcp__clickedu__get_evaluation]
description: >-
  Consultar l'avaluació d'una assignatura a Clickedu: apartats, activitats,
  percentatges i notes posades. Usa-la quan el profe digui "les notes de",
  "quines notes té", "consultar l'avaluació", "els apartats i percentatges",
  "evaluar / avaluar", "notas de la 1ª evaluación", "qui no té nota de".
---

# Avaluació (només lectura)

1. `get_subjects_and_rosters` → la teva assignatura amb el seu `subject_id`
   (p. ex. Llengua castellana de 4t → `3376`).
2. `get_evaluation(subject_id, term_id)`:
   - `items`: els **apartats** (`level="section"`, amb `weight_percent` sobre la
     nota final) i les **activitats** (`level="activity"`, amb `parent_id` de
     l'apartat i `weight_percent` dins de l'apartat). Cada un té `code` (EE, BT...)
     i `name`.
   - `grades`: per alumne, les notes posades per activitat o apartat (clau =
     `code`). `final` és la nota final de l'avaluació si està guardada.
   - `term_ids` llista les avaluacions; sense `term_id` surt l'actual.
   - `grades_entered` compta les notes que realment hi ha.

**Aquesta skill no escriu notes ni crea apartats o activitats.** Per posar o
corregir notes, el profe ho fa a la pàgina «Avaluar» de Clickedu. Una nota final
que Clickedu calcula a la pàgina no queda guardada fins que el profe desa, així
que pot sortir buida aquí.
