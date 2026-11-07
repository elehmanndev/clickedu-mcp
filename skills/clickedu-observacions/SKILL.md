---
name: clickedu-observacions
allowed-tools: [mcp__clickedu__get_schedule, mcp__clickedu__get_session_detail, mcp__clickedu__get_session_notes, mcp__clickedu__add_observation]
description: >-
  Posar una observació a un alumne en una sessió de Clickedu i, si cal, avisar la
  família per correu. Usa-la quan el profe digui "posa una observació", "pon una
  observación a", "apunta que", "anota a", "avisa a la família de / avisa a su
  familia", "envia un correu a la família", "observacions de la sessió".
---

# Observacions d'una sessió

**Una observació, un alumne, una sessió, sempre confirmada pel profe.** Si
`notify_family=true`, Clickedu **envia un correu de veritat a la família** en
desar: digues-ho clarament a la vista prèvia.

Flux:

1. `get_schedule` → sessió → `get_session_detail(assig, sessio)` → el seu
   `attendance_link` dona `cgap` i `sessio`.
2. `get_session_notes(cgap, sessio)` → alumnes (`alu_id`, `name`), l'observació
   actual de cadascun i la casella de correu.
3. `add_observation(cgap, sessio, alu_id, text, notify_family, confirm)`:
   - Primer **sense** `confirm`: vista prèvia amb sessió, alumne, text abans i
     després, i si s'avisa la família. Ensenya-la i **espera el sí** explícit.
   - Després `confirm=true`. Rellegeix la pàgina i informa de `verified`.
   - El text **substitueix** l'observació d'aquella sessió. Si ja n'hi havia una
     (surt a `before`), pregunta si cal afegir-hi o substituir-la.

L'enviament del correu no es pot confirmar des de la pàgina: si el profe vol
saber si ha arribat, que ho miri als missatges enviats de Clickedu.

Mai en bloc ni per a tota la classe. Per deures usa `clickedu-deures`; per
faltes i retards, `clickedu-assistencia` / `clickedu-retards`.
