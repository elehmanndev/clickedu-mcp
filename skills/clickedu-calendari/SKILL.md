---
name: clickedu-calendari
allowed-tools: [mcp__clickedu__get_calendar]
description: >-
  El calendari de Clickedu. Usa-la quan el profe digui "calendari / calendario",
  "esdeveniments / eventos", "què hi ha al calendari / qué hay en el calendario",
  "què hi ha aquesta setmana al calendari".
---

# Calendari

`get_calendar` retorna els esdeveniments i entrades del calendari de Clickedu.
Resumeix-los (propers primer) i, si el profe pregunta per un dia o setmana
concreta, filtra per aquesta data.

Per l'horari de classes (no el calendari d'esdeveniments) usa `clickedu-horari`.
