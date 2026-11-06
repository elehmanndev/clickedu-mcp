# Sending a message

## Steps

1. `list_message_recipients(query)` → find the recipient. Use a name substring to
   narrow the directory. Each result has an `id` (e.g. `u_1610`). A plain email
   address also works as the recipient.
2. `send_message(recipient_id, subject, body, confirm)`.

## Preview-then-confirm protocol (mandatory)

- Call `send_message` first **without** `confirm` (or `confirm=false`): it returns
  a preview (resolved recipient, subject, body) and sends nothing.
- Show the preview to the teacher and **wait for an explicit yes**.
- Only then call again with `confirm=true` to send.

## Rules

- One recipient, one message. Never send to a whole group, never loop over
  recipients.
- If the teacher wants to reach several families, send one confirmed message at a
  time, or ask them to confirm each.
