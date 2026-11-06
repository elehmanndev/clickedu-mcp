"""Clickedu personal MCP server (stdio). Read tools + per-action-gated write tools.

Runs locally on the teacher's own machine against their own staff account.
No student impersonation. Every write requires an explicit confirm=True after a
preview; no bulk writes, no loops, no autonomous runs.
"""
from __future__ import annotations

import json
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from . import parse
from .session import ClickeduSession, LoginError, get_session

mcp = FastMCP("clickedu")


def _ok(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _err(msg: str) -> str:
    return json.dumps({"error": msg}, ensure_ascii=False, indent=2)


def _s() -> ClickeduSession:
    return get_session()


# =====================================================================
# READ TOOLS
# =====================================================================
@mcp.tool()
def get_schedule() -> str:
    """Your weekly teaching timetable: each class session with day, time, subject,
    group, room, co-teachers, and a link to the session detail."""
    try:
        return _ok(parse.parse_schedule(_s().get("assignatures/el_meu_horari.php")))
    except LoginError as e:
        return _err(str(e))


@mcp.tool()
def get_calendar() -> str:
    """Your Clickedu calendar: upcoming events and entries."""
    try:
        return _ok(parse.parse_calendar(_s().get("calendari/index.php")))
    except LoginError as e:
        return _err(str(e))


@mcp.tool()
def get_subjects_and_rosters() -> str:
    """Your subjects and class groups, with the class_id for each so you can pull a
    roster with get_roster, plus your tutor/course tool links."""
    try:
        return _ok(parse.parse_subjects(_s().get("go/Index.php?ctr=Subjects/Subjects")))
    except LoginError as e:
        return _err(str(e))


@mcp.tool()
def get_roster(class_id: str) -> str:
    """The student roster for one class group. class_id comes from
    get_subjects_and_rosters (the Classes/Students id)."""
    cid = str(class_id).strip()
    if not cid.isdigit():
        return _err("class_id must be numeric.")
    try:
        html = _s().get(f"go/Index.php?ctr=Classes/Students&id={cid}")
        return _ok(parse.parse_roster(html))
    except LoginError as e:
        return _err(str(e))


@mcp.tool()
def get_session_detail(assig: str, sessio: str) -> str:
    """Detail for one class session (content, valoracio fields, attendance link).
    assig and sessio come from a session_link in get_schedule."""
    a, se = str(assig).strip(), str(sessio).strip()
    if not (a.isdigit() and se.isdigit()):
        return _err("assig and sessio must be numeric.")
    try:
        html = _s().get(f"assignatures/sessio.php?assig={a}&sessio={se}")
        return _ok(parse.parse_session(html))
    except LoginError as e:
        return _err(str(e))


@mcp.tool()
def get_attendance(cgap: str, sessio: str, n: int = 0) -> str:
    """Read the CURRENT attendance state for one session: each student with their
    status (present / absent / late), reason, and justified flag. cgap and
    sessio come from the attendance_link in get_session_detail
    (assistencia/index.php?cgap=...&sessio=...&n=...). Read-only."""
    c, se = str(cgap).strip(), str(sessio).strip()
    if not (c.isdigit() and se.isdigit()):
        return _err("cgap and sessio must be numeric.")
    try:
        q = f"assistencia/index.php?cgap={c}&sessio={se}"
        if n:
            q += f"&n={int(n)}"
        return _ok(parse.parse_attendance_state(_s().get(q)))
    except LoginError as e:
        return _err(str(e))


@mcp.tool()
def get_inbox() -> str:
    """Your communications inbox (Communication module)."""
    try:
        html = _s().get("go/Index.php?ctr=Communication/Communication")
        return _ok(parse.parse_messages(html))
    except LoginError as e:
        return _err(str(e))


@mcp.tool()
def get_chat_contacts() -> str:
    """Your chat contacts (Messaging/Chat)."""
    try:
        html = _s().get("go/Index.php?ctr=Messaging/Chat")
        return _ok(parse.parse_chat_contacts(html))
    except LoginError as e:
        return _err(str(e))


@mcp.tool()
def get_documents() -> str:
    """Your most recent documents (Documents registry)."""
    try:
        html = _s().get("go/Index.php?ctr=Documents/DocumentsRegistry&do=Last")
        return _ok(parse.parse_documents(html))
    except LoginError as e:
        return _err(str(e))


@mcp.tool()
def get_files() -> str:
    """Your files area (files/index.php)."""
    try:
        return _ok(parse.parse_files(_s().get("files/index.php")))
    except LoginError as e:
        return _err(str(e))


# =====================================================================
# WRITE TOOLS (gated: preview unless confirm=True; single action only)
# =====================================================================
@mcp.tool()
def mark_attendance(
    cgap: str,
    sessio: str,
    alu_id: str,
    status: str = "absent",
    reason_code: str = "",
    justified: bool = False,
    confirm: bool = False,
) -> str:
    """Set ONE student's attendance for ONE session. Single action only.

    Without confirm=True this returns a PREVIEW of the exact change and does not
    write anything. Call again with confirm=True only after the teacher approves.
    It replays every other student's current state unchanged and flips only this
    student, so no one else's attendance is touched.

    status is "absent", "late" (retard), or "present" (clears any absence/late).
    reason_code is the motive code for absent/late (e.g. 10=MALALT, 11=METGE,
    12=GESTIONS). justified marks an absent/late as justified.
    """
    c, se, alu = str(cgap).strip(), str(sessio).strip(), str(alu_id).strip()
    if not (c.isdigit() and se.isdigit() and alu.isdigit()):
        return _err("cgap, sessio and alu_id must be numeric.")
    status = status.strip().lower()
    _radio = {"absent": "1", "late": "2"}
    if status not in ("absent", "late", "present"):
        return _err('status must be "absent", "late" or "present".')
    s = _s()
    q = f"assistencia/index.php?cgap={c}&sessio={se}"
    try:
        html = s.get(q)
    except LoginError as e:
        return _err(str(e))

    state = parse.parse_attendance_state(html)
    target = next((st for st in state["students"] if st["alu_id"] == alu), None)
    if target is None:
        return _err(
            f"Student {alu} not found in this session. Available: "
            + ", ".join(f'{x["alu_id"]}={x["name"]}' for x in state["students"][:40])
        )
    key = target["key"]
    rbtn = f"rbtn_ar_{key}"
    motiu = f"cbtn_motiu_{key}"
    just = f"cbtn_just_{key}"

    # Full current form state, then flip only this student.
    data = parse.collect_form_state(html, "assistencia/index.php")
    data["action"] = "guardar_assistencies"
    before = {
        "status": target["status"],
        "reason": target["reason"],
        "justified": target["justified"],
    }
    val = _radio.get(status)  # "1" absent, "2" late, None present
    if val:
        data[rbtn] = val
        if reason_code:
            data[motiu] = str(reason_code)
        if justified:
            data[just] = "1"
        elif just in data:
            del data[just]
    else:
        data.pop(rbtn, None)
        data.pop(just, None)
        data[motiu] = ""

    preview = {
        "action": "mark_attendance",
        "student": {"alu_id": alu, "name": target["name"]},
        "session": {"cgap": c, "sessio": se},
        "change": {
            "before": before,
            "after": {
                "status": status,
                "reason_code": reason_code or None,
                "justified": justified if val else False,
            },
        },
        "endpoint": q,
        "fields_changed": [rbtn, motiu, just],
    }
    if not confirm:
        preview["note"] = "PREVIEW only. Nothing sent. Call again with confirm=true to apply."
        return _ok(preview)

    try:
        resp = s.post(q, data=data)
    except LoginError as e:
        return _err(str(e))
    # Verify by re-reading the state.
    after_state = parse.parse_attendance_state(s.get(q))
    now = next((st for st in after_state["students"] if st["alu_id"] == alu), None)
    verified = bool(now and now["status"] == status)
    preview.update(
        {
            "applied": True,
            "verified": verified,
            "current_state": now,
            "note": None if verified else "POST sent but re-read did not confirm the change.",
        }
    )
    return _ok(preview)


@mcp.tool()
def send_message(
    recipient_id: str,
    subject: str,
    body: str,
    confirm: bool = False,
) -> str:
    """Send ONE message to ONE recipient. Single action only.

    Without confirm=True this returns a PREVIEW (resolved recipient, subject, body)
    and sends nothing. Call again with confirm=True only after the teacher approves.
    recipient_id is a directory id like 'u_1610' from list_message_recipients, or a
    plain email address.
    """
    rid = str(recipient_id).strip()
    subject = subject.strip()
    if not rid or not subject or not body.strip():
        return _err("recipient_id, subject and body are all required.")
    s = _s()
    try:
        html = s.get("comunicacio/missatge.php")
    except LoginError as e:
        return _err(str(e))
    compose = parse.parse_message_compose(html)
    resolved = next((r for r in compose["recipients"] if r["id"] == rid), None)
    is_email = "@" in rid and rid.startswith("u_") is False
    if resolved is None and not is_email:
        return _err(
            f"Recipient '{rid}' not found in directory. Use list_message_recipients, "
            "or pass a plain email address."
        )

    data = parse.collect_form_state(html, "missatge.php")
    if is_email:
        data["per_a_manual"] = rid
        data["valor_0"] = data.get("valor_0", "")
    else:
        data["valor_0"] = rid
    data["v_assumpte"] = subject
    data["v_cos"] = body
    data["email"] = "1"
    data.setdefault("num_arxius", "0")
    data["accio"] = "missatge"

    preview = {
        "action": "send_message",
        "to": resolved or {"id": rid, "name": rid, "group": "manual_email"},
        "subject": subject,
        "body_preview": body[:500],
        "endpoint": "comunicacio/missatge.php",
    }
    if not confirm:
        preview["note"] = "PREVIEW only. Nothing sent. Call again with confirm=true to send."
        return _ok(preview)

    try:
        resp = s.post("comunicacio/missatge.php", data=data)
    except LoginError as e:
        return _err(str(e))
    sent_ok = ("missatge" in resp.lower()) and ("error" not in resp[:2000].lower())
    preview.update(
        {
            "applied": True,
            "verified": sent_ok,
            "note": None if sent_ok else "POST sent; could not confirm delivery from response.",
        }
    )
    return _ok(preview)


@mcp.tool()
def list_message_recipients(query: str = "") -> str:
    """List message recipients from the compose directory (teachers, admin, contacts).
    Optional query filters by name substring. Use to find a recipient_id for
    send_message. Read-only."""
    try:
        html = _s().get("comunicacio/missatge.php")
    except LoginError as e:
        return _err(str(e))
    recips = parse.parse_message_compose(html)["recipients"]
    if query:
        ql = query.lower()
        recips = [r for r in recips if ql in r["name"].lower()]
    return _ok({"recipients": recips[:200], "count": len(recips)})


def main() -> None:
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        from .config import setup

        raise SystemExit(setup())

    # If no credentials are configured yet, guide the user instead of crashing
    # cryptically when the MCP client launches us.
    if not os.environ.get("CLICKEDU_USERNAME"):
        from .config import config_env_path

        print(
            "clickedu-mcp is not configured yet.\n"
            "Run the one-time setup first:\n"
            "  clickedu-mcp setup\n"
            f"(it writes {config_env_path()})",
            file=sys.stderr,
        )
        raise SystemExit(2)

    # Local stdio server, launched by the MCP client (Codex, Claude Code, ...).
    mcp.run()


if __name__ == "__main__":
    main()
