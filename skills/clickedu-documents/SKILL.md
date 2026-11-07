---
name: clickedu-documents
allowed-tools: [mcp__clickedu__get_documents, mcp__clickedu__get_files]
description: >-
  Documents i arxius a Clickedu. Usa-la quan el profe digui "documents /
  documentos", "arxius / archivos", "fitxers / ficheros", "els meus documents / mis
  documentos", "què tinc a arxius".
---

# Documents i arxius

- `get_documents` → els documents recents (registre de documents).
- `get_files` → l'àrea d'arxius (`files/index.php`).

Mira el `status`: `"ok"` hi ha dades, `"empty"` la pàgina s'ha llegit i no hi ha
res, `"error"` no s'ha pogut llegir (p. ex. «No disposeu de permisos» si el centre
no dona accés a aquest mòdul). Digues-ho tal qual; un error no és una llista buida.
