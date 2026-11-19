---
name: clickedu-butlleti
allowed-tools: [mcp__clickedu__get_subjects_and_rosters, mcp__clickedu__get_evaluation, mcp__clickedu__set_subject_remark]
description: >-
  Escriure l'observació d'una matèria per al butlletí (o per al tutor) d'un
  alumne en una avaluació a Clickedu. Usa-la quan el profe digui "observació del
  butlletí", "comentari per al butlletí", "observacions de la matèria", "nota per
  al tutor", "aspectes acadèmics", "comentario del boletín", "observación para el
  boletín", "comentario para el tutor".
---

# Observacions de la matèria (butlletí i tutor)

No és l'observació d'una sessió (això és `clickedu-observacions`). Aquí és el
text de final d'avaluació per a una matèria.

1. `get_subjects_and_rosters` → `subject_id`; `get_evaluation` → `alu_id` i
   `term_ids`.
2. Redacta el text amb el profe. Si et demana que l'escriguis tu, basa't només en
   el que et digui i en les notes que surten a `get_evaluation`; no inventis fets.
3. `set_subject_remark(subject_id, alu_id, text, kind, block, term_id)` sense
   `confirm` → **previsualització** amb el text actual i el nou. No canvia res.
   - `kind`: `butlleti` (surt al butlletí que rep la família) o `tutor` (intern).
   - `block`: `observacions` (general de la matèria) o `aspectes` (aspectes
     acadèmics, personals i evolutius).
4. Ensenya el text exacte al profe. Només si diu que sí, torna a cridar amb
   `confirm=true`. La resposta diu `verified: true` si el text rellegit és el nou.

Regles:

- **Un text per alumne i per confirmació.** Mai un bucle sobre la classe ni
  diverses observacions amb un sol "sí", encara que el profe en demani moltes:
  són previsualitzacions i confirmacions separades.
- El text substitueix el que hi havia; `text=""` l'esborra. Avisa si ja n'hi
  havia un i se'n perdria el contingut.
- Recorda al profe que `butlleti` el llegeix la família.
