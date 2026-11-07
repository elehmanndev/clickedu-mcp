---
name: clickedu-tutoria
allowed-tools: [mcp__clickedu__get_subjects_and_rosters, mcp__clickedu__get_monthly_attendance, mcp__clickedu__get_class_behaviour]
description: >-
  Resum de tutoria d'un grup a Clickedu: faltes i retards acumulats per mes o de
  tot el curs, i el registre de comportament. Usa-la quan el profe digui "resum
  mensual acumulat", "resumen de faltas/retrasos", "quants retards porta el
  grup", "acumulat del curs", "qui passa de 5 retards", "incidències del grup /
  conductes de la classe", "informe de tutoria".
---

# Resum de tutoria (només lectura)

Aquesta skill **no escriu res**. No decideix ni registra sancions: només llegeix
i resumeix perquè el profe decideixi.

## Faltes i retards acumulats

`get_monthly_attendance(class_id, months)` és el «Resum mensual acumulat»:

- Inclou **tots** els alumnes, també els que no tenen cap incidència.
- Per alumne i per mes: `A` (faltes sense justificar), `AJ` (justificades),
  `R` (retards sense justificar), `RJ` (retards justificats) i `sessions`; més
  `totals` i `percentages`. Fila de grup a `class_total`.
- **`R` i `RJ` van separats: no els sumis** per comparar amb llindars de
  retards (els llindars de retards sense justificar es comproven només amb `R`).
- `months`: llista de mesos de dos dígits. Per l'acumulat de tot el curs, passa
  tots els mesos des de `"09"` fins a l'actual (p. ex. `["09","10","11"]`). Sense
  `months`, surt la selecció per defecte de Clickedu, que pot no ser tot el curs.
- El `class_id` surt de `get_subjects_and_rosters` (`clickedu-classes`).

## Comportament del grup

`get_class_behaviour(class_id, date_from, date_to)` retorna els informes de
«Comportament» (incidències i mèrits) del grup per a un rang de dates
(YYYY-MM-DD; per defecte, el curs actual). `status="empty"` vol dir que la
pàgina s'ha llegit i no hi ha res registrat.

Per l'historial dia a dia d'un sol alumne (dates exactes de cada falta, retard,
deures i observacions) usa `clickedu-alumne`.
