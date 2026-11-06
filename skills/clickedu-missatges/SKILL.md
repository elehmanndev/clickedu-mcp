---
name: clickedu-missatges
allowed-tools: [mcp__clickedu__list_message_recipients, mcp__clickedu__send_message]
description: >-
  Enviar un missatge a una família o contacte per Clickedu. Usa-la quan el profe
  digui "enviar missatge a família / mandar mensaje a la familia", "avisar a / avisa
  a", "escriure a un pare o mare", "enviar un mensaje a", "comunicar a la família de".
---

# Enviar un missatge

**Un destinatari, un missatge, sempre confirmat pel profe.** Res d'enviaments
massius ni bucles.

Flux: `list_message_recipients(query)` → tria el destinatari → `send_message`, en
**dos passos**: primer sense `confirm` (vista prèvia del destinatari/assumpte/cos,
ensenya-la i espera el sí), després `confirm=true`.

Detall (format del destinatari, protocol de confirmació):
[`references/messaging.md`](references/messaging.md).
