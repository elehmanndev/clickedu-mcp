---
name: clickedu-horari
allowed-tools: [mcp__clickedu__get_schedule]
description: >-
  El meu horari de classes a Clickedu. Usa-la quan el profe digui "el meu horari",
  "mi horario", "què tinc avui / qué clases tengo hoy", "a quina hora tinc",
  "quin dia faig", "quines classes tinc aquesta setmana".
---

# El meu horari

`get_schedule` retorna l'horari setmanal: cada sessió amb dia, hora d'inici i fi,
assignatura, grup/classe, aula, altres professors, i un `session_link`
(`sessio.php?assig=...&sessio=...`) per veure'n el detall.

- Per "què tinc avui", filtra les sessions del dia actual i resumeix-les en ordre
  d'hora.
- Si el profe vol entrar a una sessió (contingut, passar llista), passa'n l'`assig`
  i el `sessio` a les skills `clickedu-sessio` o `clickedu-passar-llista`.
