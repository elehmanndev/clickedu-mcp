"""HTML -> clean dicts for each Clickedu page. All input is already decoded text."""
from __future__ import annotations

import re
from bs4 import BeautifulSoup

DAY_STARTS = [140, 280, 420, 560, 700]


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def _clean(s: str | None) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def _num(style: str, key: str) -> float:
    m = re.search(rf"{key}:\s*([\d.]+)", style or "")
    return float(m.group(1)) if m else 0.0


# --- schedule --------------------------------------------------------------
def parse_schedule(html: str) -> dict:
    soup = _soup(html)
    days = []
    for d in soup.select("#horari_titols .titol_dia, .titol_dia"):
        txt = _clean(d.get_text())
        m = re.match(r"(.+?)\s*\((\d{2}/\d{2}/\d{4})\)", txt)
        days.append(
            {"name": m.group(1) if m else txt, "date": m.group(2) if m else None}
        )
        if len(days) == 5:
            break
    zone = soup.find(id="horari_zona")
    blocks = []
    for b in zone.select(".bloc_colocable") if zone else []:
        style = b.get("style", "")
        left = _num(style, "left")
        di = min(range(len(DAY_STARTS)), key=lambda i: abs(left - DAY_STARTS[i]))

        def field(cls, strip_label=None):
            el = b.select_one("." + cls)
            if not el:
                return None
            t = _clean(el.get_text(" "))
            if strip_label:
                t = re.sub(rf"^{strip_label}\s*:?\s*", "", t)
            return t

        link_el = b.select_one(".bc_vincle a[href]")
        hrs = field("bc_hores") or ""
        hm = re.search(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", hrs)
        blocks.append(
            {
                "day": days[di]["name"] if di < len(days) else None,
                "date": days[di]["date"] if di < len(days) else None,
                "start": hm.group(1) if hm else None,
                "end": hm.group(2) if hm else None,
                "subject": field("bc_assig"),
                "group": field("bc_classesgrups", "Grups i/o classes"),
                "teachers": field("bc_profes", "Professors"),
                "room": field("bc_aula", "Aula"),
                "date_range": field("bc_dates"),
                "session_link": link_el.get("href") if link_el else None,
                "_top": _num(style, "top"),
            }
        )
    blocks.sort(key=lambda x: (x["date"] or "", x["_top"]))
    for b in blocks:
        b.pop("_top", None)
    return {"days": days, "sessions": blocks, "count": len(blocks)}


# --- subjects + rosters ----------------------------------------------------
def parse_subjects(html: str) -> dict:
    soup = _soup(html)
    subjects, tools = [], []
    for p in soup.select(".panel"):
        head = p.select_one(".panel-heading")
        name = _clean(head.get_text(" ")) if head else ""
        if not name:
            continue
        roster = p.select_one('a[href*="Classes/Students"]')
        rid = None
        if roster:
            m = re.search(r"id=(\d+)", roster.get("href", ""))
            rid = m.group(1) if m else None
        links = [
            {"label": _clean(a.get_text()), "href": a.get("href")}
            for a in p.select("a[href]")
            if _clean(a.get_text())
        ]
        subj = None
        ev = p.select_one('a[href*="EvaluateTermly&id="], a[href*="Subject&do=Index&id="]')
        if ev:
            m = re.search(r"[?&]id=(\d+)", ev.get("href", ""))
            subj = m.group(1) if m else None
        entry = {"name": name, "class_id": rid, "subject_id": subj, "links": links[:6]}
        # Subject cards name a course + group (e.g. "... Primer d'ESO-A"); tool
        # cards are single words like "avaluacions". Heuristic: a subject card
        # has a group token (A-D suffix) or a roster link.
        if rid or re.search(r"d'ESO|Batx|Primer|Segon|Tercer|Quart|-[A-D]\b", name):
            subjects.append(entry)
        else:
            tools.append({"name": name, "links": links[:4]})
    return {"subjects": subjects, "tools": tools}


def parse_roster(html: str) -> dict:
    soup = _soup(html)
    students = []
    seen = set()
    for a in soup.select('a[href*="fitxa_alumne"]'):
        m = re.search(r"alum=(\d+)", a.get("href", ""))
        if not m:
            continue
        alu = m.group(1)
        row = a.find_parent("tr")
        name = ""
        if row:
            for td in row.find_all("td"):
                t = _clean(td.get_text(" "))
                if t and not t.isdigit() and "," in t:
                    name = t
                    break
        if alu not in seen:
            seen.add(alu)
            students.append({"alu_id": alu, "name": name})
    return {"students": students, "count": len(students)}


# --- session detail --------------------------------------------------------
def parse_session(html: str) -> dict:
    soup = _soup(html)
    title = _clean(soup.title.get_text()) if soup.title else None
    # content / valoracio textarea + fields
    content = {}
    for ta in soup.find_all("textarea"):
        nm = ta.get("name")
        if nm and nm != "selector_idioma":
            content[nm] = _clean(ta.get_text())
    # attendance link for this session
    att = re.search(r'(assistencia/index\.php\?[^"\']+)', html)
    headings = [_clean(h.get_text()) for h in soup.select("h1,h2,h3")][:6]
    return {
        "title": title,
        "headings": [h for h in headings if h],
        "content_fields": content,
        "attendance_link": att.group(1) if att else None,
    }


# --- attendance (read current state from assistencia page) -----------------
HOMEWORK = {"1": "fets", "2": "no fets", "3": "no demanats"}


def parse_session_views(html: str) -> dict:
    """The per-student views of a session page besides attendance: the menu of
    views (Deures, Observacions, Treball, Comportament...) with their ids, and
    for each student the current homework value, homework note, and the value of
    every param_<view>_<alu> field (free text for Observacions, a select or radio
    for the others). Also the name and state of each student's email checkbox.

    View ids come from the page menu, never hardcoded: they can differ per school."""
    soup = _soup(html)
    views = {}
    for li in soup.find_all("li", attrs={"name": "vista"}):
        vid = li.get("id")
        if vid and vid not in ("0",):
            views[vid] = _clean(li.get_text(" "))
    # options for select/radio views, so a teacher's words can map to a value
    view_options: dict[str, list] = {}
    students: dict[str, dict] = {}

    def st(alu):
        return students.setdefault(alu, {"alu_id": alu, "name": "", "views": {}})

    for vid in views:
        box = soup.find(id=f"vista_param_{vid}")
        if box is None:
            continue
        for el in box.find_all(["input", "select", "textarea"]):
            name = el.get("name") or ""
            if vid == "deures":
                m = re.fullmatch(r"deures_(\d+)(_obs)?", name)
                if not m:
                    continue
                s = st(m.group(1))
                if m.group(2):
                    s["homework_note"] = el.get_text()
                elif el.has_attr("checked"):
                    s["homework"] = HOMEWORK.get(el.get("value"), el.get("value"))
                s.setdefault("homework", None)
                continue
            m = re.fullmatch(rf"param_{re.escape(vid)}_(\d+)", name)
            if not m:
                continue
            s = st(m.group(1))
            if el.name == "textarea":
                s["views"][vid] = el.get_text()
                view_options.setdefault(vid, "text")
            elif el.name == "select":
                opt = el.select_one("option[selected]")
                s["views"][vid] = _clean(opt.get_text()) if opt and opt.get("value") else None
                if vid not in view_options:
                    view_options[vid] = [
                        {"value": o.get("value"), "label": _clean(o.get_text())}
                        for o in el.find_all("option") if o.get("value")
                    ]
            elif el.get("type") == "radio":
                if el.has_attr("checked"):
                    s["views"][vid] = el.get("value")
                s["views"].setdefault(vid, None)
                opts = view_options.setdefault(vid, [])
                if isinstance(opts, list) and not any(o["value"] == el.get("value") for o in opts):
                    opts.append({"value": el.get("value"), "label": el.get("value")})
    # names and email checkboxes from the main attendance view
    main = soup.find(id="vista_param_0")
    if main:
        for cb in main.find_all("input", attrs={"name": re.compile(r"^cbtn_mail_")}):
            alu = cb.get("name").split("_")[-1]
            s = st(alu)
            s["email_field"] = cb.get("name")
            s["email_checked"] = cb.has_attr("checked")
            row = cb.find_parent("tr")
            if row and not s["name"]:
                for td in row.find_all("td"):
                    t = _clean(td.get_text(" "))
                    if "," in t and not t[:1].isdigit():
                        s["name"] = t
                        break
    return {
        "views": [{"id": k, "name": v,
                   "kind": ("text" if view_options.get(k) == "text"
                            else "homework" if k == "deures" else "choice"),
                   "options": (view_options.get(k) if isinstance(view_options.get(k), list)
                               else [{"value": v2, "label": l} for v2, l in HOMEWORK.items()]
                               if k == "deures" else None)}
                  for k, v in views.items()],
        "students": sorted(students.values(), key=lambda x: x["name"]),
    }


def parse_attendance_state(html: str) -> dict:
    """Parse the per-student attendance controls into a reviewable list.

    Each student has a radio group ``rbtn_ar_<rec>_<alu>`` with value 1 = absent,
    value 2 = late (retard); neither checked = present.
    """
    soup = _soup(html)
    groups: dict[str, list] = {}
    for inp in soup.select('input[name^="rbtn_ar_"]'):
        groups.setdefault(inp.get("name", ""), []).append(inp)

    status_map = {"1": "absent", "2": "late"}
    state = []
    for name, radios in groups.items():
        key = name[len("rbtn_ar_"):]  # <rec>_<alu>
        alu = key.split("_")[-1]
        checked = next((r for r in radios if r.has_attr("checked")), None)
        status = status_map.get(checked.get("value"), "present") if checked else "present"
        # Student name: the row holding this control, first cell with a comma.
        row = radios[0].find_parent("tr")
        nm = ""
        if row:
            for td in row.find_all("td"):
                t = _clean(td.get_text(" "))
                if "," in t and not t[0].isdigit():
                    nm = t
                    break
        reason_el = soup.select_one(f'select[name="cbtn_motiu_{key}"]')
        reason = None
        if reason_el:
            opt = reason_el.select_one("option[selected]")
            reason = _clean(opt.get_text()) if opt and opt.get("value") else None
        just = soup.select_one(f'input[name="cbtn_just_{key}"]')
        state.append(
            {
                "alu_id": alu,
                "name": nm,
                "key": key,
                "status": status,
                "absent": status == "absent",
                "reason": reason,
                "justified": bool(just and just.has_attr("checked")),
            }
        )
    state.sort(key=lambda x: x["name"])
    return {"students": state, "count": len(state)}


def collect_form_state(html: str, form_action_contains: str = "", form_name: str = "") -> dict:
    """Collect every current form field value, to replay a form safely.

    Prefer form_name: some Clickedu forms have an empty action (the attendance
    form posts to its own URL), and matching on action then picks the wrong form,
    such as the language selector, which would drop every other student's state.
    Returns {} when the form is not found; callers must treat that as an error."""
    soup = _soup(html)
    form = None
    if form_name:
        form = soup.find("form", attrs={"name": form_name})
    else:
        for f in soup.find_all("form"):
            if form_action_contains and form_action_contains in (f.get("action") or ""):
                form = f
                break
    if form is None:
        return {}
    # Reproduce what a browser submits: disabled controls are not sent, and a
    # select with no option marked selected sends its first option.
    data: dict[str, str] = {}
    for inp in form.find_all("input"):
        nm = inp.get("name")
        if not nm or inp.has_attr("disabled"):
            continue
        typ = (inp.get("type") or "text").lower()
        if typ in ("checkbox", "radio"):
            if inp.has_attr("checked"):
                data[nm] = inp.get("value", "on")
        elif typ not in ("submit", "button", "file", "image", "reset"):
            data[nm] = inp.get("value", "")
    for sel in form.find_all("select"):
        nm = sel.get("name")
        if not nm or sel.has_attr("disabled"):
            continue
        opt = sel.select_one("option[selected]") or sel.find("option")
        if opt is None:
            continue
        val = opt.get("value")
        data[nm] = val if val is not None else opt.get_text()
    for ta in form.find_all("textarea"):
        nm = ta.get("name")
        if nm and not ta.has_attr("disabled"):
            data[nm] = ta.get_text()
    return data


# --- generic list pages (calendar, inbox, chat, documents, files) ----------
def page_error(html: str) -> str | None:
    """Return Clickedu's own error message if the page is an error screen rather
    than real content (e.g. 'Dades incorrectes' shown in a bootbox alert)."""
    m = re.search(r"bootbox\.alert\(\{[^}]*?message\s*:\s*'([^']*)'", html, re.S)
    if m:
        msg = _clean(re.sub(r"<[^>]+>", " ", m.group(1)))
        return msg or "Clickedu returned an alert with no message"
    low = html[:5000].lower()
    for marker in ("no teniu permís", "no tiene permiso", "acceso denegado", "accés denegat"):
        if marker in low:
            return marker
    return None


_ACC_COLS = ("A", "AJ", "R", "RJ")


def _count(cell: str) -> int:
    cell = cell.strip()
    return int(cell) if cell.isdigit() else 0  # Clickedu prints "-" for zero


def parse_monthly_accumulated(html: str) -> dict:
    """'Resum mensual acumulat' for a class: per student, per month A / AJ / R / RJ
    and number of sessions, plus totals. R (unjustified late) and RJ (justified
    late) are kept separate on purpose. Every student on the class list is
    included, also those with no incidents."""
    soup = _soup(html)
    months_avail, months_sel = [], []
    sel = soup.find("select", attrs={"name": "mesos[]"})
    if sel:
        for o in sel.find_all("option"):
            item = {"value": o.get("value"), "label": _clean(o.get_text())}
            months_avail.append(item)
            if o.has_attr("selected"):
                months_sel.append(item)
    table = None
    for t in soup.find_all("table"):
        if "Alumne" in t.get_text()[:200]:
            table = t
            break
    if table is None:
        return {"months": months_sel, "available_months": months_avail, "students": []}
    rows = table.find_all("tr")
    # Header row 0: Alumne/a | <month> ... | Totals per alumne | Percentatges
    head = [_clean(c.get_text(" ")) for c in rows[0].find_all(["th", "td"])]
    month_labels = [h for h in head[1:] if not h.lower().startswith(("totals", "percent"))]
    students = []
    class_total = None
    for r in rows[2:]:
        cells = [_clean(c.get_text(" ")) for c in r.find_all(["th", "td"])]
        if len(cells) < 2 or not cells[0]:
            continue
        name, vals = cells[0], cells[1:]
        per_month, i = {}, 0
        for label in month_labels:
            chunk = vals[i:i + 5]
            i += 5
            if len(chunk) < 5:
                break
            per_month[label] = {**{k: _count(v) for k, v in zip(_ACC_COLS, chunk[:4])},
                                "sessions": _count(chunk[4])}
        tot = vals[i:i + 5]
        pct = vals[i + 5:i + 9]
        totals = ({**{k: _count(v) for k, v in zip(_ACC_COLS, tot[:4])},
                   "sessions": _count(tot[4]) if len(tot) > 4 else 0} if tot else {})
        row = {
            "name": name,
            "months": per_month,
            "totals": totals,
            "percentages": dict(zip(_ACC_COLS, pct)),
        }
        if name.lower() in ("total", "totals"):
            class_total = row
            continue
        students.append(row)
    return {
        "months": months_sel,
        "available_months": months_avail,
        "legend": {"A": "unjustified absences", "AJ": "justified absences",
                   "R": "unjustified lates", "RJ": "justified lates"},
        "students": students,
        "count": len(students),
        "class_total": class_total,
    }


_DAILY_KIND = {
    "assistència": "attendance",
    "deures": "homework",
    "treball": "work",
    "comportament": "behaviour",
    "comportament a lectura": "reading_behaviour",
    "llegeix?": "reading",
    "observacions": "observation",
}


def parse_student_daily(html: str) -> dict:
    """Day-by-day log of one student (the 'Dia a dia' details of the student
    file): one entry per recorded item with date, time, subject, kind
    (attendance / homework / work / behaviour / observation ...) and result.
    Attendance results distinguish 'absència', 'absència justificada', 'retard'
    and 'retard justificat'."""
    soup = _soup(html)
    period = None
    for el in soup.find_all(["h3", "h4", "strong", "b"]):
        t = _clean(el.get_text(" "))
        if t.lower().startswith("detalls"):
            period = t
            break
    table = soup.find("table")
    entries = []
    if table:
        for r in table.find_all("tr")[1:]:
            c = [_clean(x.get_text(" ")) for x in r.find_all("td")]
            if len(c) < 5:
                continue
            date, hour, subject, param, result = c[:5]
            obs = c[5] if len(c) > 5 and c[5] != "-" else None
            d = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", date)
            hm = re.findall(r"\d{1,2}:\d{2}", hour)
            entries.append({
                "date": f"{d.group(3)}-{d.group(2)}-{d.group(1)}" if d else date,
                "start": hm[0] if hm else None,
                "end": hm[1] if len(hm) > 1 else None,
                "subject": subject,
                "kind": _DAILY_KIND.get(param.lower(), param),
                "item": param,
                "result": result,
                "note": obs,
            })
    entries.sort(key=lambda e: (e["date"], e["start"] or ""))
    summary: dict[str, int] = {}
    for e in entries:
        if e["kind"] in ("attendance", "homework"):
            key = f'{e["kind"]}: {e["result"]}'
            summary[key] = summary.get(key, 0) + 1
    return {"period": period, "entries": entries, "count": len(entries), "summary": summary}


def parse_evaluation_structure(html: str) -> dict:
    """Structure of the 'Avaluar' page of one subject and term: the sections
    (level 0, with their weight in the final grade) and the activities inside
    them (level 1, with their weight inside the section), the students, and the
    available terms. Grades come separately as JSON (see parse_evaluation_grades)."""
    import html as _html

    soup = _soup(html)
    heads = [_clean(x.get_text(" ")) for x in soup.find_all(["h1", "h2", "h3", "h4"])]
    heads = [h for h in heads if h]
    # weights: input name percent_<parent>_<item>_<n>
    weights: dict[str, tuple[str, str]] = {}
    for inp in soup.select("input.InputPercent"):
        m = re.match(r"percent_(\d+)_(\d+)_\d+", inp.get("name", ""))
        if m:
            weights[m.group(2)] = (m.group(1), inp.get("value") or "")
    items = []
    for th in soup.select("th[attr-item]"):
        iid = th.get("attr-item")
        cls = " ".join(th.get("class") or [])
        level = 1 if "nivell-1" in cls else 0
        pop = BeautifulSoup(_html.unescape(th.get("data-content", "")), "lxml").get_text(" ", strip=True)
        a = th.find("a", class_="header-name")
        parent, w = weights.get(iid, (None, ""))
        items.append({
            "item_id": iid,
            "code": _clean(a.get_text()) if a else None,
            "name": _clean(pop) or None,
            "level": "section" if level == 0 else "activity",
            "parent_id": parent if level == 1 else None,
            "weight_percent": float(w) if re.fullmatch(r"\d+(\.\d+)?", w or "") else None,
            "has_children": th.get("attr-children") == "1",
        })
    students = {}
    for inp in soup.select("input[attr-student]"):
        sid = inp.get("attr-student")
        if sid and sid not in students:
            row = inp.find_parent("tr")
            name = ""
            if row:
                first = row.find(["th", "td"])
                name = re.sub(r"^\d+\s*\.\s*", "", _clean(first.get_text(" "))) if first else ""
            students[sid] = name
    terms = sorted(set(re.findall(r"trm=(\d+)(?![\dp])", html)))
    return {
        "subject": heads[0] if heads else None,
        "course": heads[1] if len(heads) > 1 else None,
        "term": heads[2] if len(heads) > 2 else None,
        "term_ids": terms,
        "items": items,
        "students": [{"alu_id": k, "name": v} for k, v in students.items()],
    }


def parse_class_behaviour(html: str) -> dict:
    """'Comportament' reports of a class group (incidències and mèrits). Each
    report panel is returned with its title and, when Clickedu shows a table,
    its rows as header->value dicts. Panels with no data are listed as empty.

    Note: only validated on a class with no incidents recorded; the row layout of
    a filled report is read generically from its table headers."""
    soup = _soup(html)
    dfrom = soup.find("input", attrs={"name": "dataIni"})
    dto = soup.find("input", attrs={"name": "dataFi"})
    reports = []
    for p in soup.select(".panel"):
        head = p.select_one(".panel-heading")
        body = p.select_one(".panel-body")
        if not head or not body:
            continue
        title = _clean(head.get_text(" "))
        if title.startswith("Paràmetres"):
            continue
        rows = []
        table = body.find("table")
        if table:
            trs = table.find_all("tr")
            headers = [_clean(c.get_text(" ")) for c in trs[0].find_all(["th", "td"])] if trs else []
            for tr in trs[1:]:
                cells = [_clean(c.get_text(" ")) for c in tr.find_all(["th", "td"])]
                if any(cells):
                    rows.append(dict(zip(headers, cells)) if headers else {"cells": cells})
        reports.append({"report": title, "rows": rows,
                        "has_data": bool(rows) or "No hi ha dades" not in body.get_text()})
    return {
        "date_from": dfrom.get("value") if dfrom else None,
        "date_to": dto.get("value") if dto else None,
        "reports": reports,
        "incidents": [r for r in reports if r["has_data"]],
    }


def _ymd(raw: str | None) -> str | None:
    if raw and re.fullmatch(r"\d{8}", raw):
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"
    return None


def parse_calendar(html: str) -> dict:
    """Events of the calendar view. Each event link carries its date in the href
    (date=YYYYMMDD); the time sits in the <i> just before it and the full title,
    place and owner are in the overlib tooltip."""
    soup = _soup(html)
    events = []
    for a in soup.select("a.event"):
        if "dayModLink" in (a.get("class") or []):
            continue  # "Nou esdeveniment" button, not an event
        href = a.get("href", "")
        m_date = re.search(r"[?&]date=(\d{8})", href)
        m_id = re.search(r"[?&]id=(\d+)", href)
        time = None
        prev = a.find_previous_sibling("i")
        if prev:
            time = _clean(prev.get_text())
        tip = a.get("onmouseover", "")
        m_cap = re.search(r"CAPTION,\s*'([^']*)'", tip)
        m_owner = re.search(r"Propietari:\s*([^&<]+)", tip)
        events.append(
            {
                "date": _ymd(m_date.group(1) if m_date else None),
                "time": time,
                "title": _clean(a.get_text()),
                "full_title": _clean(m_cap.group(1)) if m_cap else None,
                "owner": _clean(m_owner.group(1)) if m_owner else None,
                "event_id": m_id.group(1) if m_id else None,
            }
        )
    events.sort(key=lambda e: (e["date"] or "", e["time"] or ""))
    return {"events": events, "count": len(events)}


def parse_messages(html: str) -> dict:
    """The Communication module is a send/broadcast hub, not a received-mail inbox.
    Return the available sections and any message rows that are present."""
    soup = _soup(html)
    msgs = []
    for row in soup.select("table tr"):
        cells = [_clean(td.get_text(" ")) for td in row.find_all("td")]
        cells = [c for c in cells if c]
        link = row.select_one('a[href*="missatge"], a[href*="Message"], a[href*="conversa"]')
        if len(cells) >= 2:
            msgs.append({"cells": cells[:6], "link": link.get("href") if link else None})
    sections = []
    for a in soup.select("a[href]"):
        t = _clean(a.get_text())
        if t and any(k in t.lower() for k in ("tramesa", "correu", "històric", "directori", "missatge")):
            sections.append({"label": t[:60], "href": a.get("href")})
    out = {"messages": msgs[:100], "count": len(msgs), "sections": sections[:12]}
    if not msgs:
        out["note"] = (
            "Communication is a broadcast/mass-email hub; received personal messages "
            "live in the chat module (get_chat_contacts)."
        )
    return out


_CHAT_HINT_IDS = {
    "new-conversation-hint", "loading-conversations", "empty-archive-hint",
    "loading-contacts", "reload-contacts", "add-members-hint",
    "reload-group-contacts", "loading-details",
}


def parse_chat_contacts(html: str) -> dict:
    soup = _soup(html)
    contacts = []
    for item in soup.select(".list-group-item"):
        if (item.get("data-id") or item.get("id")) in _CHAT_HINT_IDS:
            continue
        name = _clean(item.get_text(" "))
        cls = " ".join(item.get("class", []))
        if name and "hidden" not in cls:
            contacts.append({"name": name[:80], "data_id": item.get("data-id")})
    out = {"contacts": contacts[:100], "count": len(contacts)}
    if not contacts:
        out["note"] = (
            "Chat conversations/contacts load from the Messaging JSON API and this "
            "account currently shows none. Use list_message_recipients to send a new "
            "message to anyone in your directory."
        )
    return out


def parse_documents(html: str) -> dict:
    soup = _soup(html)
    docs = []
    for a in soup.select('a[href]'):
        href = a.get("href", "")
        txt = _clean(a.get_text())
        if txt and any(k in href.lower() for k in ("doc", "file", "arxiu", "download", "baixar")):
            docs.append({"name": txt[:120], "href": href})
    out = {"documents": docs[:100], "count": len(docs)}
    if not docs:
        out["note"] = "No recent documents in the registry for this account."
    return out


def parse_files(html: str) -> dict:
    soup = _soup(html)
    items = []
    for el in soup.select(".llegenda_element, .tab-arxius a, a[href*='files']"):
        t = _clean(el.get_text(" "))
        href = el.get("href") if el.name == "a" else None
        if t:
            items.append({"name": t[:120], "href": href})
    return {"items": items[:100], "count": len(items)}


def parse_message_compose(html: str) -> dict:
    """Extract recipient directory + token from the compose page for send_message."""
    soup = _soup(html)
    recipients = []
    for sel in soup.select('select[name^="select_0_"]'):
        group = sel.get("name")
        for o in sel.find_all("option"):
            val = o.get("value")
            if val and val.startswith("u_"):
                recipients.append(
                    {"id": val, "name": _clean(o.get_text()), "group": group}
                )
    token_el = soup.select_one('input[name="token"]')
    return {
        "recipients": recipients,
        "token": token_el.get("value", "") if token_el else "",
    }
