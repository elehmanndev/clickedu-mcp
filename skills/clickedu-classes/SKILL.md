---
name: clickedu-classes
description: >-
  Les meves classes i alumnes a Clickedu. Usa-la quan el profe digui "les meves
  classes / mis clases", "els meus alumnes / mis alumnos", "llista de classe /
  lista de clase", "qui hi ha a 4t ESO / quién está en", "la meva tutoria".
---

# Classes i alumnes

1. `get_subjects_and_rosters` → les assignatures i grups del profe, cadascun amb
   el seu `class_id`, més els enllaços d'eines de tutoria/curs.
2. `get_roster(class_id)` → la llista d'alumnes d'aquell grup (`alu_id`, `name`).

Per veure el contingut d'una sessió concreta, usa `clickedu-sessio`. L'entrada de
notes/qualificacions viu a les pàgines d'avaluació de Clickedu (enllaços
`avaluacions` / `avaluar per alumne` que surten a `get_subjects_and_rosters`); no
hi ha eina d'escriptura de notes aquí, així que remet a aquests enllaços.
