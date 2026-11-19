---
name: clickedu-avaluacio
allowed-tools: [mcp__clickedu__get_subjects_and_rosters, mcp__clickedu__get_evaluation, mcp__clickedu__set_grade]
description: >-
  Consultar i posar notes a l'avaluació d'una assignatura a Clickedu: apartats,
  activitats, percentatges, notes posades i posar o corregir una nota. Usa-la
  quan el profe digui "les notes de", "quines notes té", "consultar l'avaluació",
  "els apartats i percentatges", "posa-li un 7 a", "corregeix la nota de",
  "avaluar", "notas de la 1ª evaluación", "ponle un 7 en", "cambia la nota de",
  "qui no té nota de".
---

# Avaluació

## Consultar

1. `get_subjects_and_rosters` → la teva assignatura amb el seu `subject_id`
   (p. ex. Llengua castellana de 1r A → `3135`).
2. `get_evaluation(subject_id, term_id)`:
   - `items`: els **apartats** (`level="section"`, amb `weight_percent` sobre la
     nota final) i les **activitats** (`level="activity"`, amb `parent_id` de
     l'apartat i `weight_percent` dins de l'apartat). Cada un té `item_id`,
     `code` (EE, UL...) i `name`.
   - `grades`: per alumne (`alu_id`), les notes posades (clau = `code`). `final`
     és la nota final si està guardada.
   - `term_ids` llista les avaluacions; sense `term_id` surt l'actual.

## Posar o corregir una nota (una sola, amb confirmació)

1. Treu `alu_id` i l'`item_id` (o el `code`) de `get_evaluation`.
2. `set_grade(subject_id, alu_id, item, grade, term_id)` sense `confirm` →
   **previsualització**: alumne, activitat, nota d'abans i de després. No canvia res.
3. Ensenya-la al profe. Només si diu que sí, torna a cridar amb `confirm=true`.
   La resposta diu `verified: true` si la nota rellegida és la nova.

Regles:

- **Una nota per acció i per confirmació.** Mai un bucle sobre la classe ni
  diverses notes amb un sol "sí". Si el profe en vol posar deu, són deu
  previsualitzacions i deu confirmacions, o millor que les posi a Clickedu.
- `item="final"` és la nota final; `grade=""` esborra la nota.
- La nota ha de ser dins del rang de la casella (normalment 0-10); la final
  només admet els valors del desplegable.
- **No recalcula** les notes d'apartat ni la final (el botó «calcular» de
  Clickedu); digues-ho al profe si canvia una activitat.
- No fa «Guardar i tancar matèria». Si algú ha desat la pàgina entre la lectura
  i l'escriptura, no escriu res: torna a començar.
