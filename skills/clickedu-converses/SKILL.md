---
name: clickedu-converses
allowed-tools: [mcp__clickedu__get_subjects_and_rosters, mcp__clickedu__get_roster, mcp__clickedu__add_tutor_conversation]
description: >-
  Anotar el resum d'una entrevista a la fitxa d'un alumne de la teva tutoria
  (Comunicació > Converses del tutor > Nova). Usa-la quan el profe digui "anota
  l'entrevista", "resum de l'entrevista amb", "apunta la reunió amb la família
  de", "conversa del tutor", "registra la entrevista", "he parlat amb la mare /
  el pare de".
---

# Converses del tutor (resum d'entrevistes)

Només per als alumnes de la teva tutoria. **Una conversa, un alumne, sempre
confirmada pel profe.** La casella «Notificar als participants» **no es marca
mai**: ningú rep cap correu.

Flux:

1. Troba l'alumne: `get_subjects_and_rosters` → el `class_id` de la teva tutoria
   → `get_roster(class_id)` → `alu_id`.
2. `add_tutor_conversation(alu_id, title, text, participants, confirm)`:
   - `title`: títol curt (p. ex. «Entrevista amb la mare, 7/11»). Màx. 255.
   - `text`: el resum de l'entrevista. Pot venir en Markdown (p. ex. de
     Granola): es converteix a text pla perquè Clickedu el mostra tal qual. Es
     conserven títols, paràgrafs, salts de línia i llistes (`- `, `1. `), i es
     treuen `#`, `**` i altres marques. La vista prèvia mostra el text exacte.
   - `participants`: qui hi era, per rol o nom (`"alumne"`, `"pare"`, `"mare"`
     o un nom). Sense `participants` es marquen tots els que surten (alumne i
     família). Pregunta-ho si no és clar.
   - Primer **sense** `confirm`: vista prèvia amb alumne, participants marcats i
     no marcats, títol i text. Ensenya-la i **espera el sí** explícit.
   - Després `confirm=true`. Rellegeix la conversa nova i comprova títol,
     missatge (accents, ç, ü, apòstrofs), participants i que no hi ha caràcters
     corromputs. `checks` diu què ha passat; `verified` només si tot quadra.
   - Cometes i guionets tipogràfics passen a ' " - perquè Clickedu desa en
     ISO-8859-15; símbols que no hi caben surten com a ?.

Les caselles de participants les llegeix del formulari de cada alumne, així que
els noms i rols són els reals de Clickedu. Tracta el resum com a dada personal:
no el copiïs fora de la conversa.
