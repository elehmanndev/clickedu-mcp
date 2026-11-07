"""Clickedu personal MCP server (stdio). Read tools + per-action-gated write tools.

Runs locally on the teacher's own machine against their own staff account.
No student impersonation. Every write requires an explicit confirm=True after a
preview; no bulk writes, no loops, no autonomous runs.
"""
from __future__ import annotations

import json
import os
import re
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


_LIST_KEYS = ("events", "sessions", "students", "subjects", "messages", "entries",
              "contacts", "documents", "items", "recipients", "incidents",
              "evaluations")


def _read(path: str, parser, post: list | None = None) -> str:
    """Fetch a page and parse it, tagging the result with a status so the agent
    can tell 'nothing there' from 'could not read the page':
    status = "ok" (has data), "empty" (page read fine, no rows) or "error".
    If post is given, the page is requested with that form data (read-only
    search/filter forms only, never a save action)."""
    try:
        html = _s().post(path, data=post) if post is not None else _s().get(path)
    except LoginError as e:
        return _ok({"status": "error", "error": f"login: {e}"})
    err = parse.page_error(html)
    if err:
        return _ok({"status": "error", "error": f"Clickedu said: {err}", "page": path})
    try:
        data = parser(html)
    except Exception as e:  # noqa: BLE001 - surface parser breakage, don't hide it
        return _ok({"status": "error", "error": f"could not parse the page: {e}", "page": path})
    lists = [data[k] for k in _LIST_KEYS if isinstance(data.get(k), list)]
    data["status"] = "empty" if lists and not any(lists) else "ok"
    return _ok(data)


# =====================================================================
# READ TOOLS
# =====================================================================
@mcp.tool()
def get_schedule() -> str:
    """Your weekly teaching timetable: each class session with day, time, subject,
    group, room, co-teachers, and a link to the session detail."""
    return _read("assignatures/el_meu_horari.php", parse.parse_schedule)


@mcp.tool()
def get_calendar(view: str = "week", date: str = "") -> str:
    """Your Clickedu calendar events, each with date (YYYY-MM-DD), time, title,
    owner and event_id. view is "week" (default) or "month"; date (YYYY-MM-DD)
    picks the week/month to show, default today."""
    if view not in ("week", "month"):
        return _err('view must be "week" or "month".')
    q = f"calendari/index.php?view={view}"
    if date:
        d = date.replace("-", "")
        if not re.fullmatch(r"\d{8}", d):
            return _err("date must be YYYY-MM-DD.")
        q += f"&date={d}"
    return _read(q, parse.parse_calendar)


@mcp.tool()
def get_subjects_and_rosters() -> str:
    """Your subjects and class groups, with the class_id for each so you can pull a
    roster with get_roster, plus your tutor/course tool links."""
    return _read("go/Index.php?ctr=Subjects/Subjects", parse.parse_subjects)


@mcp.tool()
def get_roster(class_id: str) -> str:
    """The student roster for one class group. class_id comes from
    get_subjects_and_rosters (the Classes/Students id)."""
    cid = str(class_id).strip()
    if not cid.isdigit():
        return _err("class_id must be numeric.")
    return _read(f"go/Index.php?ctr=Classes/Students&id={cid}", parse.parse_roster)


@mcp.tool()
def get_session_detail(assig: str, sessio: str) -> str:
    """Detail for one class session (content, valoracio fields, attendance link).
    assig and sessio come from a session_link in get_schedule."""
    a, se = str(assig).strip(), str(sessio).strip()
    if not (a.isdigit() and se.isdigit()):
        return _err("assig and sessio must be numeric.")
    return _read(f"assignatures/sessio.php?assig={a}&sessio={se}", parse.parse_session)


@mcp.tool()
def get_attendance(cgap: str, sessio: str, n: int = 0) -> str:
    """Read the CURRENT attendance state for one session: each student with their
    status (present / absent / late), reason, and justified flag. cgap and
    sessio come from the attendance_link in get_session_detail
    (assistencia/index.php?cgap=...&sessio=...&n=...). Read-only."""
    c, se = str(cgap).strip(), str(sessio).strip()
    if not (c.isdigit() and se.isdigit()):
        return _err("cgap and sessio must be numeric.")
    q = f"assistencia/index.php?cgap={c}&sessio={se}"
    if n:
        q += f"&n={int(n)}"
    return _read(q, parse.parse_attendance_state)


@mcp.tool()
def get_inbox() -> str:
    """Your communications inbox (Communication module)."""
    return _read("go/Index.php?ctr=Communication/Communication", parse.parse_messages)


@mcp.tool()
def get_chat_contacts() -> str:
    """Your chat contacts (Messaging/Chat)."""
    return _read("go/Index.php?ctr=Messaging/Chat", parse.parse_chat_contacts)


@mcp.tool()
def get_documents() -> str:
    """Your most recent documents (Documents registry)."""
    return _read("go/Index.php?ctr=Documents/DocumentsRegistry&do=Last", parse.parse_documents)


@mcp.tool()
def get_files() -> str:
    """Your files area (files/index.php)."""
    return _read("files/index.php", parse.parse_files)


@mcp.tool()
def get_student_daily(
    alu_id: str, class_id: str, date_from: str = "", date_to: str = ""
) -> str:
    """Day-by-day log of ONE student ('Dia a dia' in the student file): every
    recorded absence, justified absence, late, justified late, homework done/not
    done, work and behaviour item and teacher observation, each with date, time,
    subject and result, plus a count summary.

    alu_id comes from get_roster, class_id from get_subjects_and_rosters.
    date_from / date_to are YYYY-MM-DD; default is the whole current school year.
    Read-only."""
    alu, cid = str(alu_id).strip(), str(class_id).strip()
    if not (alu.isdigit() and cid.isdigit()):
        return _err("alu_id and class_id must be numeric.")
    dates = []
    for d in (date_from, date_to):
        if d and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
            return _err("dates must be YYYY-MM-DD.")
        dates.append(d.replace("-", "/") if d else "")
    # The school-year id (ce) is the selected option of the student file.
    try:
        fitxa = _s().get(f"assignatures/fitxa_alumne.php?alum={alu}&p=diaadia")
    except LoginError as e:
        return _ok({"status": "error", "error": f"login: {e}"})
    err = parse.page_error(fitxa)
    if err:
        return _ok({"status": "error", "error": f"Clickedu said: {err}"})
    m = re.search(rf'value="(\d+)_{cid}"', fitxa)
    if not m:
        return _ok({"status": "error",
                    "error": f"student {alu} has no school year in class {cid}"})
    ce = m.group(1)
    start = dates[0] or ""
    end = dates[1] or ""
    form = [
        ("ajax", "continc_detalls"), ("id_usuari", alu),
        ("data_inicial", start), ("data_final", end),
        ("tipus_assistencia", "sessio"), ("materia_actual", ""),
        ("numero_avaluacio", ""), ("total_avaluacions_alumne", "3"),
        ("id_classe", cid), ("ce", ce), ("mostrartot", "true"),
        ("datainitriada", start), ("datafitriada", end),
    ] + [("array_tipus_parametres_mostrar[]", x) for x in ("4", "4", "1", "2", "4", "3")]
    return _read("includes/include_fitxa_alumne/diaadia_ajax.php",
                 parse.parse_student_daily, post=form)


@mcp.tool()
def get_class_behaviour(class_id: str, date_from: str = "", date_to: str = "") -> str:
    """Behaviour record ('Comportament': incidències and mèrits) of one class
    group for a date range, as Clickedu's reports. status "empty" means the page
    was read and there is nothing recorded in that range. Read-only: it never
    creates or changes an incident or sanction.

    class_id from get_subjects_and_rosters; dates YYYY-MM-DD, default the current
    school year. For one student's day-by-day items (behaviour notes included)
    use get_student_daily."""
    cid = str(class_id).strip()
    if not cid.isdigit():
        return _err("class_id must be numeric.")
    form = []
    for name, d in (("dataIni", date_from), ("dataFi", date_to)):
        if d:
            m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", d)
            if not m:
                return _err("dates must be YYYY-MM-DD.")
            form.append((name, f"{m.group(3)}/{m.group(2)}/{m.group(1)}"))
    path = f"go/Index.php?ctr=Classes/Behaviour&do=Index&id={cid}"
    return _read(path, parse.parse_class_behaviour, post=form or None)


@mcp.tool()
def get_evaluation(subject_id: str, term_id: str = "") -> str:
    """Read the 'Avaluar' page of one subject for one term: its sections and
    activities with their weights (%), and every grade already entered, per
    student and activity. Read-only; it never saves anything.

    subject_id is the assignatura id (the number in the 'EvaluateTermly&id='
    link that get_subjects_and_rosters returns, e.g. 3376). term_id picks the
    term (ids are listed in the answer as term_ids); omit it for the current one.
    Grades come from Clickedu as entered; a final grade that Clickedu computes in
    the page is not stored until the teacher saves, so it may be missing here."""
    sid, trm = str(subject_id).strip(), str(term_id).strip()
    if not sid.isdigit() or (trm and not trm.isdigit()):
        return _err("subject_id and term_id must be numeric.")
    q = f"go/Index.php?ctr=Evaluate/EvaluateTermly&id={sid}" + (f"&trm={trm}" if trm else "")
    try:
        page = _s().get(q)
        grades_raw = _s().get(f"go/Index.php?ctr=Evaluate/EvaluateTermly&do=GetGrades&id={sid}&&trm={trm}")
    except LoginError as e:
        return _ok({"status": "error", "error": f"login: {e}"})
    err = parse.page_error(page)
    if err:
        return _ok({"status": "error", "error": f"Clickedu said: {err}", "page": q})
    try:
        data = parse.parse_evaluation_structure(page)
        grades = json.loads(grades_raw or "[]")
    except Exception as e:  # noqa: BLE001
        return _ok({"status": "error", "error": f"could not parse the evaluation: {e}"})
    names = {i["item_id"]: (i["code"] or i["name"]) for i in data["items"]}
    names[sid] = "final"  # the subject-level grade is keyed by the subject id
    by_student: dict[str, dict] = {s["alu_id"]: {"name": s["name"], "grades": {}}
                                   for s in data["students"]}
    for g in grades if isinstance(grades, list) else []:
        alu = str(g.get("id_alumne"))
        item = str(g.get("id_criteri"))
        val = g.get("nota_mod") if g.get("nota_mod") is not None else g.get("nota")
        if val is None and g.get("text"):
            val = g.get("text")
        rec = by_student.setdefault(alu, {"name": "", "grades": {}})
        rec["grades"][names.get(item, item)] = val
    data["grades"] = [{"alu_id": k, **v} for k, v in by_student.items()]
    data["grades_entered"] = sum(
        1 for v in by_student.values() for g in v["grades"].values() if g is not None
    )
    data["status"] = "ok" if data["items"] else "empty"
    return _ok(data)


@mcp.tool()
def get_monthly_attendance(class_id: str, months: list[str] | None = None) -> str:
    """'Resum mensual acumulat' for one class group: every student on the list
    (also those with no incidents), per month and in total, with A (unjustified
    absences), AJ (justified absences), R (unjustified lates), RJ (justified
    lates) and number of sessions, plus percentages. R and RJ are separate.

    class_id comes from get_subjects_and_rosters. months is a list of two-digit
    month numbers ("09", "10", ...); omit it to get Clickedu's default selection.
    To get the whole school year so far, pass every month from "09" to the current
    one. Read-only."""
    cid = str(class_id).strip()
    if not cid.isdigit():
        return _err("class_id must be numeric.")
    path = f"go/Index.php?ctr=Classes/Attendance&do=MonthlyAccumulated&id={cid}"
    if not months:
        return _read(path, parse.parse_monthly_accumulated)
    ms = [str(m).strip().zfill(2) for m in months]
    if not all(re.fullmatch(r"(0[1-9]|1[0-2])", m) for m in ms):
        return _err('months must be two-digit month numbers, e.g. ["09","10","11"].')
    form = [("mesos[]", m) for m in ms] + [("export", "0")]
    return _read(path, parse.parse_monthly_accumulated, post=form)


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

    # Full current form state of the attendance form, then flip only this student.
    data = parse.collect_form_state(html, form_name="frm_assistencia")
    problem = parse.check_session_form(html, data)
    if problem:
        return _err(f"Could not read the attendance form ({problem}); nothing was changed.")
    data["action"] = "guardar_assistencies"
    data["boto_guardar"] = "guardar"  # what the page's Guardar button adds
    data["menu_triat"] = ""  # main Assistència view
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
def get_session_notes(cgap: str, sessio: str) -> str:
    """Read, for one class session, the per-student items besides attendance:
    homework (fets / no fets / no demanats) and its note, the free-text
    observation, and the other views the school has (Treball, Comportament,
    mobile use, reading...), with their available options. Also each student's
    "Enviar correu electrònic" (notify family) checkbox state. Read-only.

    cgap and sessio come from the attendance_link of get_session_detail. View ids
    are read from the page, so use the ids this tool returns."""
    c, se = str(cgap).strip(), str(sessio).strip()
    if not (c.isdigit() and se.isdigit()):
        return _err("cgap and sessio must be numeric.")
    return _read(f"assistencia/index.php?cgap={c}&sessio={se}", parse.parse_session_views)


def _apply_session_change(c: str, se: str, alu: str, apply, describe: dict,
                          notify_family: bool, confirm: bool, verify) -> str:
    """Shared preview/confirm/verify flow for one student's session change.

    apply(data, page) edits the replayed form in place and returns the list of
    fields it changed. verify(student_after) returns True if the re-read matches.
    """
    s = _s()
    q = f"assistencia/index.php?cgap={c}&sessio={se}"
    try:
        html = s.get(q)
    except LoginError as e:
        return _err(str(e))
    err = parse.page_error(html)
    if err:
        return _err(f"Clickedu said: {err}")
    page = parse.parse_session_views(html)
    student = next((x for x in page["students"] if x["alu_id"] == alu), None)
    if student is None:
        return _err(f"Student {alu} not found in this session. Available: "
                    + ", ".join(f'{x["alu_id"]}={x["name"]}' for x in page["students"][:40]))
    data = parse.collect_form_state(html, form_name="frm_assistencia")
    problem = parse.check_session_form(html, data)
    if problem:
        return _err(f"Could not read the session form ({problem}); nothing was changed.")
    data["action"] = "guardar_assistencies"
    data["boto_guardar"] = "guardar"
    data["menu_triat"] = ""
    try:
        changed = apply(data, page, student)
    except ValueError as e:
        return _err(str(e))
    if notify_family:
        if not student.get("email_field"):
            return _err("This student has no 'Enviar correu electrònic' checkbox here.")
        data[student["email_field"]] = "1"
        changed.append(student["email_field"])
    preview = {
        "student": {"alu_id": alu, "name": student["name"]},
        "session": {"cgap": c, "sessio": se},
        **describe,
        "notify_family_by_email": bool(notify_family),
        "fields_changed": changed,
    }
    if notify_family:
        preview["warning"] = (
            "Saving with notify_family sends a real email to this student's "
            "family from Clickedu."
        )
    if not confirm:
        preview["note"] = "PREVIEW only. Nothing saved or sent. Call again with confirm=true to apply."
        return _ok(preview)
    try:
        s.post(q, data=data)
    except LoginError as e:
        return _err(str(e))
    after = parse.parse_session_views(s.get(q))
    now = next((x for x in after["students"] if x["alu_id"] == alu), None)
    verified = bool(now and verify(now))
    preview.update({
        "applied": True,
        "verified": verified,
        "current_state": now,
        "note": None if verified else "Sent, but the re-read did not show the change. Check it in Clickedu.",
    })
    if notify_family:
        preview["email_note"] = (
            "Clickedu sends the email on save; the page does not confirm delivery. "
            "Check Clickedu's sent messages if needed."
        )
    return _ok(preview)


@mcp.tool()
def add_observation(
    cgap: str,
    sessio: str,
    alu_id: str,
    text: str,
    notify_family: bool = False,
    confirm: bool = False,
) -> str:
    """Write ONE student's free-text observation ('Observacions') for ONE
    session, optionally ticking "Enviar correu electrònic" so Clickedu emails the
    family. Single action only.

    Without confirm=True it returns a PREVIEW (session, student, the current and
    new text, whether the family gets an email) and changes nothing. Call again
    with confirm=True only after the teacher approves. Every other student's
    attendance, homework and observations are replayed unchanged.

    The text replaces this student's observation for this session; to add to an
    existing one, include the existing text (shown in the preview)."""
    c, se, alu = str(cgap).strip(), str(sessio).strip(), str(alu_id).strip()
    if not (c.isdigit() and se.isdigit() and alu.isdigit()):
        return _err("cgap, sessio and alu_id must be numeric.")
    text = (text or "").strip()
    if not text:
        return _err("text is required.")
    holder = {}

    def apply(data, page, student):
        view = next((v for v in page["views"] if v["kind"] == "text"), None)
        if view is None:
            raise ValueError("This session page has no free-text observation view.")
        field = f'param_{view["id"]}_{alu}'
        if field not in data:
            raise ValueError(f"Observation field {field} not found for this student.")
        holder["view"], holder["before"] = view, data[field]
        data[field] = text
        return [field]

    # apply() runs inside the shared flow, so view and 'before' text are known
    # only after it returns; they are added to the answer here.
    result = _apply_session_change(
        c, se, alu, apply, {}, notify_family, confirm,
        verify=lambda now: (now["views"].get(holder["view"]["id"]) or "").strip() == text,
    )
    out = json.loads(result)
    if "error" not in out:
        out = {"action": "add_observation",
               "view": holder["view"]["name"],
               "observation": {"before": holder["before"], "after": text},
               **out}
    return _ok(out)


@mcp.tool()
def mark_homework(
    cgap: str,
    sessio: str,
    alu_id: str,
    status: str = "no fets",
    note: str = "",
    notify_family: bool = False,
    confirm: bool = False,
) -> str:
    """Set ONE student's homework ('Deures') for ONE session: "fets", "no fets"
    or "no demanats", with an optional homework note, and optionally tick
    "Enviar correu electrònic" so Clickedu emails the family. Single action only.

    Without confirm=True it returns a PREVIEW and changes nothing; call again
    with confirm=True only after the teacher approves. Every other student's data
    is replayed unchanged. An empty note keeps the existing homework note."""
    c, se, alu = str(cgap).strip(), str(sessio).strip(), str(alu_id).strip()
    if not (c.isdigit() and se.isdigit() and alu.isdigit()):
        return _err("cgap, sessio and alu_id must be numeric.")
    wanted = (status or "").strip().lower()
    value = next((k for k, v in parse.HOMEWORK.items() if v == wanted), None)
    if value is None:
        return _err('status must be "fets", "no fets" or "no demanats".')
    holder = {}

    def apply(data, page, student):
        if not any(v["id"] == "deures" for v in page["views"]):
            raise ValueError("This session page has no Deures view.")
        field = f"deures_{alu}"
        holder["before"] = {"status": student.get("homework"), "note": student.get("homework_note")}
        data[field] = value
        changed = [field]
        # The note textarea is disabled until a homework option is ticked; once
        # ticked the browser sends it, so send the new note or the existing one.
        new_note = note.strip() or (student.get("homework_note") or "")
        data[f"deures_{alu}_obs"] = new_note
        if note.strip():
            changed.append(f"deures_{alu}_obs")
        return changed

    result = _apply_session_change(
        c, se, alu, apply, {}, notify_family, confirm,
        verify=lambda now: now.get("homework") == wanted,
    )
    out = json.loads(result)
    if "error" not in out:
        out = {"action": "mark_homework",
               "homework": {"before": holder["before"],
                            "after": {"status": wanted, "note": note.strip() or holder["before"]["note"]}},
               **out}
    return _ok(out)


@mcp.tool()
def add_tutor_conversation(
    alu_id: str,
    title: str,
    text: str,
    participants: list[str] | None = None,
    confirm: bool = False,
) -> str:
    """Record ONE tutor conversation (an interview summary) in a student's file:
    'Comunicació > Converses del tutor > Nova', with a title and a message, and
    the participants ticked. Only the student's tutor can do this.

    The 'Notificar als participants' box is NEVER ticked: nobody is emailed.

    text may be Markdown (e.g. a Granola summary): it is converted to plain text,
    because Clickedu shows the message literally. Headings, paragraphs, line
    breaks and list items are kept; #, ** and other markers are removed. The
    preview shows the exact text that will be saved.

    participants: who took part, matched against the names or roles on the form
    ("alumne", "pare", "mare", or a name). Omit it to tick everyone listed (the
    student and every linked parent); the preview shows who is ticked.

    Without confirm=True it returns a PREVIEW (student, participants, title, text)
    and saves nothing. Call again with confirm=True only after the teacher
    approves. After saving it re-reads the new conversation and checks title,
    message (accents included) and participants. alu_id comes from get_roster of
    the tutor's class."""
    from .session import _to_latin9

    alu = str(alu_id).strip()
    if not alu.isdigit():
        return _err("alu_id must be numeric.")
    title = parse.markdown_to_plain(title or "").replace("\n", " ").strip()
    text = parse.markdown_to_plain(text or "")
    if not title or not text:
        return _err("title and text are both required.")
    if len(title) > 255:
        return _err("title is longer than 255 characters.")
    # What Clickedu can store (ISO-8859-15): curly quotes become straight ones,
    # unsupported symbols become '?'. Shown in the preview and used to verify.
    title, text = _to_latin9(title), _to_latin9(text)
    s = _s()
    form_path = f"assignatures/conversa_tutor.php?accio=crear&alum={alu}"
    try:
        html = s.get(form_path)
    except LoginError as e:
        return _err(str(e))
    err = parse.page_error(html)
    if err:
        return _err(f"Clickedu said: {err}")
    form = parse.parse_tutor_conversation_form(html)
    if not form.get("found") or not form.get("title_field") or not form.get("text_field"):
        return _err("The 'Nova conversa' form was not found for this student "
                    "(only the class tutor can add tutor conversations).")
    people = form["participants"]
    if not people:
        return _err("The form lists no participants for this student.")

    def matches(p, w):
        return (w in p["name"].lower() or w == p["role"].lower()
                or (w in ("alumne", "alumna", "alumno", "student") and p["is_student"]))

    if participants:
        wanted = [p.strip().lower() for p in participants if p and p.strip()]
        chosen = [p for p in people if any(matches(p, w) for w in wanted)]
        missing = [w for w in wanted if not any(matches(p, w) for p in people)]
        if missing:
            return _err(f"No participant matches {missing}. On the form: "
                        + ", ".join(f'{p["name"]} ({p["role"]})' for p in people))
    else:
        chosen = people
    data = dict(form["hidden"])
    for p in chosen:
        data[p["field"]] = "1"
    if form.get("notify_field"):
        data.pop(form["notify_field"], None)  # never ticked: nobody is emailed
    data[form["title_field"]] = title
    data[form["text_field"]] = text
    if form.get("submit"):
        data[form["submit"]["name"]] = form["submit"]["value"]
    preview = {
        "action": "add_tutor_conversation",
        "student_id": alu,
        "tutor": form.get("tutor"),
        "participants": [f'{p["name"]} ({p["role"]})' for p in chosen],
        "not_ticked": [f'{p["name"]} ({p["role"]})' for p in people if p not in chosen],
        "notify_participants": False,
        "notify_field_sent": bool(form.get("notify_field") and form["notify_field"] in data),
        "title": title,
        "text": text,
    }
    if not confirm:
        preview["note"] = "PREVIEW only. Nothing saved. Call again with confirm=true to save."
        return _ok(preview)
    action = form["action"] or ""
    if not action.startswith("conversa_tutor.php?accio=insert_bd"):
        return _err(f"Unexpected form action {action!r}; nothing was saved.")
    list_path = f"assignatures/fitxa_alumne.php?alum={alu}&p=comunicacio"
    try:
        before_ids = set(re.findall(r"conversa_tutor\.php\?accio=llegir&(?:amp;)?id=(\d+)", s.get(list_path)))
        s.post("assignatures/" + action, data=data)  # relative to assignatures/
        after_ids = set(re.findall(r"conversa_tutor\.php\?accio=llegir&(?:amp;)?id=(\d+)", s.get(list_path)))
        new_ids = sorted(after_ids - before_ids, key=int)
        saved = None
        if len(new_ids) == 1:
            saved = parse.parse_tutor_conversation(
                s.get(f"assignatures/conversa_tutor.php?accio=llegir&id={new_ids[0]}"))
    except LoginError as e:
        return _err(str(e))
    checks = {"created": len(new_ids) == 1}
    if saved and saved.get("found"):
        norm = lambda v: re.sub(r"\s+", " ", v or "").strip()
        checks["title_matches"] = norm(saved["title"]) == norm(title)
        checks["text_matches"] = bool(saved["messages"]) and norm(saved["messages"][0]) == norm(text)
        checks["no_mojibake"] = not re.search(r"Ã.|Â.", (saved["title"] or "") + "".join(saved["messages"]))
        want = sorted(p["name"] for p in chosen)
        got = sorted(saved["participants"])
        checks["participants_match"] = all(any(w in g or g in w for g in got) for w in want) and len(got) == len(want)
        preview["saved"] = {"conversation_id": new_ids[0], **saved}
    verified = all(checks.values()) and len(checks) > 1
    preview.update({
        "applied": True,
        "verified": verified,
        "checks": checks,
        "notify_note": ("Notificar als participants was not ticked in the request. "
                        "Clickedu does not show it on the saved conversation, so this is "
                        "checked on what was sent, not on the result."),
        "note": None if verified else (
            "Saved, but some checks failed (see checks). Review it in Clickedu."
            if checks.get("created") else
            "Sent, but no new conversation appeared in the student's file. Check it in Clickedu."),
    })
    return _ok(preview)


def _justify_url(alu: str, d_from: str, d_to: str) -> str:
    return (f"assignatures/assistencia.php?p=justificar_bloc&alum={alu}"
            f"&ini={d_from.replace('-', '')}&fi={d_to.replace('-', '')}"
            "&r=a&v=assignatures_at&mst=0")


@mcp.tool()
def justify_absences(
    alu_id: str,
    date_from: str,
    date_to: str = "",
    record_ids: list[str] | None = None,
    note: str = "",
    confirm: bool = False,
) -> str:
    """Justify ONE student's unjustified absences and lates in a date range, the
    way 'Detall d'assistència > Justificar en bloc' does in the student file.
    One student per call; never loops over a class.

    Without confirm=True it lists what is pending in the range (record_id, date,
    time, subject, absent/late) and which ones would be justified, and changes
    nothing. Call again with confirm=True only after the teacher approves.

    record_ids picks specific items from that list; omit it to justify every
    pending item in the range. note is the optional annotation text saved with the
    justification (e.g. "Visita mèdica"). The 'email me a copy' box is never ticked.
    Dates are YYYY-MM-DD; date_to defaults to date_from (one day). After saving it
    re-reads the range and checks that the chosen items are no longer pending."""
    from .session import _to_latin9

    alu = str(alu_id).strip()
    if not alu.isdigit():
        return _err("alu_id must be numeric.")
    d_to = date_to or date_from
    for d in (date_from, d_to):
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d or ""):
            return _err("date_from and date_to must be YYYY-MM-DD.")
    if d_to < date_from:
        return _err("date_to is before date_from.")
    s = _s()
    url = _justify_url(alu, date_from, d_to)
    try:
        html = s.get(url)
    except LoginError as e:
        return _err(str(e))
    err = parse.page_error(html)
    if err:
        return _err(f"Clickedu said: {err}")
    page = parse.parse_justify_bloc(html)
    if not page.get("found"):
        return _err("The 'Justificar en bloc' page was not found for this student "
                    "(only the class tutor can justify in bulk).")
    items = page["items"]
    if record_ids:
        wanted = {str(r).strip() for r in record_ids}
        chosen = [i for i in items if i["record_id"] in wanted]
        unknown = sorted(wanted - {i["record_id"] for i in items})
        if unknown:
            return _err(f"record_ids not pending in this range: {unknown}. "
                        f"Pending: {[i['record_id'] for i in items]}")
    else:
        chosen = list(items)
    note = _to_latin9(parse.markdown_to_plain(note or ""))
    preview = {
        "action": "justify_absences",
        "student": {"alu_id": alu, "name": page.get("student")},
        "range": {"from": date_from, "to": d_to},
        "pending": items,
        "to_justify": [f'{i["date"]} {i["start"] or ""} {i["subject"]} ({i["type"]})'.replace("  ", " ")
                       for i in chosen],
        "to_justify_ids": [i["record_id"] for i in chosen],
        "left_pending": [i["record_id"] for i in items if i not in chosen],
        "note": note or None,
        "email_copy": False,
    }
    if not items:
        preview["status"] = "empty"
        preview["message"] = "Nothing unjustified in this range; nothing to do."
        return _ok(preview)
    if not confirm:
        preview["status"] = "preview"
        preview["message"] = "PREVIEW only. Nothing justified. Call again with confirm=true to apply."
        return _ok(preview)
    save = page["save"]
    if not (save.get("action") and save["hidden"].get("p") == "justificar_bloc_bd"
            and save["hidden"].get("alum") == alu):
        return _err("The save form does not look as expected; nothing was changed.")
    form = []
    for i in items:  # every row's hidden fields, as the browser sends them
        n = i["index"]
        form += [(f"id_{n}", i["record_id"]), (f"id_sessio_{n}", i["session_id"] or ""),
                 (f"abs_ret_id_{n}", {"absent": "1", "late": "2"}.get(i["type"], ""))]
    form += [(i["checkbox"], "1") for i in chosen]
    form += list(save["hidden"].items())
    if save.get("note_field"):
        form.append((save["note_field"], note))
    if save.get("submit"):
        form.append(save["submit"])
    try:
        s.post(save["action"].lstrip("/"), data=form)
        after = parse.parse_justify_bloc(s.get(url))
    except LoginError as e:
        return _err(str(e))
    still = {i["record_id"] for i in after.get("items", [])}
    done = [r for r in preview["to_justify_ids"] if r not in still]
    untouched = [r for r in preview["left_pending"] if r in still]
    verified = len(done) == len(chosen) and len(untouched) == len(preview["left_pending"])
    preview.update({
        "status": "applied",
        "applied": True,
        "verified": verified,
        "justified_ids": done,
        "still_pending": sorted(still),
        "message": None if verified else "Sent, but the re-read does not match. Check it in Clickedu.",
    })
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
