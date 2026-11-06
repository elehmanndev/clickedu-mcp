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

Aquests mòduls poden tornar un `note` quan estan buits per aquest compte (la
comunicació és sobretot per enviar trameses, i el xat és una SPA JSON). Si surt el
`note`, digues-ho clarament en comptes de fer veure que no hi ha res a mostrar.

Per **enviar** un missatge nou, usa `clickedu-missatges`.
