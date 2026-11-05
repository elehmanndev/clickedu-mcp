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
        entry = {"name": name, "class_id": rid, "links": links[:6]}
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


def collect_form_state(html: str, form_action_contains: str) -> dict:
    """Collect every current form field value, to replay a form safely."""
    soup = _soup(html)
    form = None
    for f in soup.find_all("form"):
        if form_action_contains in (f.get("action") or ""):
            form = f
            break
    if form is None:
        return {}
    data: dict[str, str] = {}
    for inp in form.find_all("input"):
        nm = inp.get("name")
        if not nm:
            continue
        typ = (inp.get("type") or "text").lower()
        if typ in ("checkbox", "radio"):
            if inp.has_attr("checked"):
                data[nm] = inp.get("value", "on")
        elif typ not in ("submit", "button", "file", "image"):
            data[nm] = inp.get("value", "")
    for sel in form.find_all("select"):
        nm = sel.get("name")
        if not nm:
            continue
        opt = sel.select_one("option[selected]")
        data[nm] = (opt.get("value") if opt else "") or ""
    for ta in form.find_all("textarea"):
        nm = ta.get("name")
        if nm:
            data[nm] = ta.get_text()
    return data


# --- generic list pages (calendar, inbox, chat, documents, files) ----------
def parse_calendar(html: str) -> dict:
    soup = _soup(html)
    events = []
    for ev in soup.select('[class*="event"], .fc-event, li[class*="esdeveniment"]'):
        t = _clean(ev.get_text(" "))
        if t:
            events.append({"text": t[:200]})
    return {"events": events[:100], "count": len(events)}


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
