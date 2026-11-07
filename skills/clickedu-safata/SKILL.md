---
name: clickedu-safata
allowed-tools: [mcp__clickedu__get_inbox, mcp__clickedu__get_chat_contacts]
description: >-
  Veure els missatges rebuts i els contactes de xat a Clickedu. Usa-la quan el
  profe digui "missatges rebuts / mensajes recibidos", "la meva safata / mi
  bandeja", "comunicacions / comunicaciones", "xat / chat", "tinc missatges nous /
  tengo mensajes nuevos".
---

# Safata i xat (llegir)

- `get_inbox` → el mòdul de comunicacions (Communication).
- `get_chat_contacts` → els contactes de xat (Messaging).

Mira el `status`: `"ok"` hi ha dades, `"empty"` la pàgina s'ha llegit i no hi ha
res, `"error"` no s'ha pogut llegir. Si surt un `note`, explica què vol dir (la
comunicació és sobretot per enviar trameses, i el xat és una SPA JSON que pot no
mostrar res aquí). Un error no és una safata buida: digues-ho clarament.

Per **enviar** un missatge nou, usa `clickedu-missatges`.
