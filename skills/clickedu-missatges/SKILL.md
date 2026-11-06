---
name: clickedu-missatges
description: >-
  Enviar un missatge a una família o contacte per Clickedu. Usa-la quan el profe
  digui "enviar missatge a família / mandar mensaje a la familia", "avisar a / avisa
  a", "escriure a un pare o mare", "enviar un mensaje a", "comunicar a la família de".
---

# Enviar un missatge

**Un destinatari, un missatge, sempre confirmat pel profe.** Res d'enviaments
massius ni bucles.

1. `list_message_recipients(query)` → troba el destinatari; usa un tros del nom per
   filtrar. Cada resultat té un `id` (p. ex. `u_1610`); una adreça de correu també
   serveix.
2. `send_message(recipient_id, subject, body, confirm)`:
   - Primer **sense** `confirm`: retorna la vista prèvia (destinatari resolt,
     assumpte, cos). Ensenya-la i **espera el sí** del profe.
   - Després `confirm=true` per enviar-lo.

No enviïs mai a un grup sencer ni iteris sobre destinataris.
