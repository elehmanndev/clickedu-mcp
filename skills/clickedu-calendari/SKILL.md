---
name: clickedu-calendari
allowed-tools: [mcp__clickedu__get_calendar]
description: >-
  El calendari de Clickedu. Usa-la quan el profe digui "calendari / calendario",
  "esdeveniments / eventos", "què hi ha al calendari / qué hay en el calendario",
  "què hi ha aquesta setmana / aquest mes al calendari", "reunions de la setmana".
---

# Calendari

`get_calendar(view, date)` retorna els esdeveniments amb `date` (YYYY-MM-DD),
`time`, `title`, `full_title` (amb el lloc), `owner` i `event_id`.

- `view="week"` (per defecte) o `"month"`; `date` tria la setmana o el mes
  (per defecte, avui).
- Resumeix-los en ordre de data i hora. Per un dia concret, filtra pel `date`.
- `status`: `"ok"` hi ha esdeveniments, `"empty"` la pàgina s'ha llegit i no n'hi
  ha, `"error"` no s'ha pogut llegir (digues-ho tal qual, no ho presentis com a
  calendari buit).

Per l'horari de classes (no el calendari d'esdeveniments) usa `clickedu-horari`.
