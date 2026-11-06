---
name: clickedu-sessio
allowed-tools: [mcp__clickedu__get_schedule, mcp__clickedu__get_session_detail]
description: >-
  El detall d'una sessió de classe a Clickedu. Usa-la quan el profe digui "la
  sessió de / la sesión de", "què toca a / qué toca en", "el contingut de la
  sessió / el contenido de la sesión", "la valoració de la sessió".
---

# Detall d'una sessió

`get_session_detail(assig, sessio)` retorna el títol, el contingut, els camps de
valoració i l'enllaç d'assistència de la sessió.

- `assig` i `sessio` surten del `session_link` d'una sessió de `get_schedule`
  (`sessio.php?assig=...&sessio=...`). Si el profe no els dona, mira primer
  l'horari (`clickedu-horari`).
- Per passar llista d'aquesta sessió, passa a `clickedu-assistencia` /
  `clickedu-retards` amb l'`attendance_link` que retorna aquest detall.
