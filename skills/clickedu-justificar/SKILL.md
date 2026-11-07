---
name: clickedu-justificar
allowed-tools: [mcp__clickedu__get_subjects_and_rosters, mcp__clickedu__get_roster, mcp__clickedu__justify_absences]
description: >-
  Justificar en bloc les faltes i retards d'un alumne de la teva tutoria a
  Clickedu, també les sessions on no es va passar llista. Usa-la quan el profe
  digui "justifica les faltes de", "justificar en bloc", "justifica
  l'absència d'ahir de", "la mare ha justificat", "justifica els retards de",
  "justificar faltas de", "justificar ausencias", "estava malalta / lesionada".
---

# Justificar faltes i retards (en bloc, d'un alumne)

Només per als alumnes de la teva tutoria. **Un alumne per crida, sempre
confirmat pel profe.** Mai es recorre tota la classe.

Detall de la pàgina, camps i errors coneguts:
[`references/justificar-bloc.md`](references/justificar-bloc.md).

## Pas a pas

1. **Troba l'alumne:** `get_subjects_and_rosters` → `class_id` de la tutoria →
   `get_roster(class_id)` → `alu_id`.

2. **Vista prèvia** (no escriu res):
   `justify_absences(alu_id, date_from, date_to, include_not_taken=…, note=…)`.
   - Dates YYYY-MM-DD. Sense `date_to`, només aquell dia («ahir» = la data
     d'ahir).
   - `items` llista el que es pot justificar al rang: `absent` (falta),
     `late` (retard) i, amb `include_not_taken=true`, `not_taken` (sessions on el
     professor **no va passar llista**, el que a Clickedu es veu amb l'ull
     «Mostrar totes les sessions»).
   - `to_justify` diu quines es justificarien. Les ja justificades i les
     presents no hi surten mai.

3. **Pregunta i ensenya-ho al profe abans de desar:**
   - Si hi ha sessions `not_taken`, pregunta si l'alumne **no hi va ser**.
     Justificar-les el deixa com a absència justificada en aquella sessió.
     Si hi va ser, no les incloguis.
   - Si només en vol algunes, passa'n les claus a `keys` (`key` de cada item:
     el número del registre o la clau de la sessió).
   - `note`: el text de l'anotació (p. ex. «Està lesionada i necessita
     repòs»). Opcional.
   - Ensenya alumne, dia, cada sessió que es justificarà i l'anotació, i
     **espera el sí** explícit.

4. **Desa** amb els mateixos paràmetres més `confirm=true`.

5. **Comprova el resultat:**
   - `results`: l'estat nou de cada sessió triada; ha de ser «absència
     justificada» o «retard justificat».
   - `others_unchanged`: `true` vol dir que les sessions que no has triat (p. ex.
     una de «Present») segueixen igual.
   - `verified: true` només si tot quadra. Si és `false`, digues al profe quines
     han fallat i que ho miri a Clickedu. **No tornis a enviar automàticament.**

La casella «Envia'm per correu una còpia» no es marca mai.
