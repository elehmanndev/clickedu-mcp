"""Authenticated Clickedu session: two-step login, cookie reuse, ISO-8859-15 decode."""
from __future__ import annotations

import os
import re
import threading
from pathlib import Path

from curl_cffi import CurlMime
from curl_cffi import requests as cffi

from .config import config_dir, load_env

load_env()

ENCODING = "iso-8859-15"
# Markers that mean "you are not logged in and looking at the login/pass-file page".
_LOGIN_MARKERS = (
    "action=doLogin",
    "action=controlArxiuPas",
    'name="password"',
)


class LoginError(RuntimeError):
    pass


def _env(name: str, required: bool = True) -> str:
    val = os.environ.get(name, "").strip()
    if required and not val:
        raise LoginError(f"Missing {name} in environment (.env). See .env.example.")
    return val


class ClickeduSession:
    """One live session. Thread-safe enough for the single-flight MCP stdio loop."""

    def __init__(self) -> None:
        self.base = _env("CLICKEDU_BASE_URL").rstrip("/")
        self._user = _env("CLICKEDU_USERNAME")
        self._pw = _env("CLICKEDU_PASSWORD")
        self._id_usuari = _env("CLICKEDU_ID_USUARI", required=False)
        self._passfile = Path(_env("CLICKEDU_PASSFILE")).expanduser()
        self._cookie_path = Path(
            os.environ.get("CLICKEDU_COOKIE_PATH") or (config_dir() / "cookies.jar")
        ).expanduser()
        self._cookie_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._s = self._new_client()

    # --- low level ---------------------------------------------------------
    def _new_client(self) -> cffi.Session:
        s = cffi.Session(impersonate="chrome", timeout=30)
        if self._cookie_path.exists():
            try:
                s.cookies.update(_load_jar(self._cookie_path))
            except Exception:
                pass
        return s

    def _save_cookies(self) -> None:
        try:
            _dump_jar(self._s.cookies, self._cookie_path)
        except Exception:
            pass

    def _url(self, path: str) -> str:
        if path.startswith("http"):
            return path
        return f"{self.base}/{path.lstrip('/')}"

    @staticmethod
    def _text(resp) -> str:
        """Decode with the charset the response declares. Most Clickedu pages are
        ISO-8859-15, but some AJAX endpoints answer in UTF-8."""
        raw = resp.content
        ctype = (resp.headers.get("content-type") or "").lower()
        m = re.search(r"charset=([\w-]+)", ctype)
        if not m:
            m = re.search(rb'charset=["\']?([\w-]+)', raw[:2048])
            charset = m.group(1).decode("ascii", "ignore").lower() if m else ""
        else:
            charset = m.group(1)
        if charset.replace("-", "") == "utf8":
            return raw.decode("utf-8", errors="replace")
        if not charset:
            try:
                return raw.decode("utf-8")
            except UnicodeDecodeError:
                pass
        return raw.decode(ENCODING, errors="replace")

    def _looks_logged_out(self, html: str) -> bool:
        head = html[:4000]
        return any(m in head for m in _LOGIN_MARKERS) and "doLogin" in html

    # --- auth --------------------------------------------------------------
    def login(self) -> None:
        """Run the full two-step login and persist cookies."""
        with self._lock:
            self._s = self._new_client()
            # Step 1: username + password.
            r1 = self._s.post(
                self._url("user.php?action=doLogin"),
                data={"username": self._user, "password": self._pw},
                allow_redirects=True,
            )
            html1 = self._text(r1)
            if self._id_usuari == "":
                self._id_usuari = _scrape_id_usuari(html1)
            if self._id_usuari == "":
                raise LoginError(
                    "Login step 1 did not yield id_usuari. Set CLICKEDU_ID_USUARI in .env."
                )
            if not self._passfile.exists():
                raise LoginError(f"Pass file not found at {self._passfile}")

            # Step 2: upload the pass file as multipart/form-data (curl_cffi CurlMime).
            mp = CurlMime()
            mp.addpart(name="MAX_FILE_SIZE", data="100000")
            mp.addpart(name="id_usuari", data=str(self._id_usuari))
            mp.addpart(
                name="userfile",
                filename=self._passfile.name,
                local_path=str(self._passfile),
                content_type="application/octet-stream",
            )
            try:
                r2 = self._s.post(
                    self._url("user.php?action=controlArxiuPas"),
                    multipart=mp,
                    allow_redirects=True,
                )
                html2 = self._text(r2)
            finally:
                mp.close()
            ok = ("sumari/index.php" in (r2.url or "")) or ("sumari/index.php" in html2) or (
                not self._looks_logged_out(html2)
            )
            if not ok or self._looks_logged_out(html2):
                raise LoginError(
                    "Login step 2 failed (pass file rejected or session not established)."
                )
            self._save_cookies()

    def get(self, path: str, **kw) -> str:
        """GET a page, auto re-login once if the session has expired. Returns decoded HTML."""
        with self._lock:
            r = self._s.get(self._url(path), allow_redirects=True, **kw)
            html = self._text(r)
        if self._looks_logged_out(html):
            self.login()
            with self._lock:
                r = self._s.get(self._url(path), allow_redirects=True, **kw)
                html = self._text(r)
        return html

    def post(self, path: str, *, data=None, files=None, **kw) -> str:
        """POST (for write tools). Re-login once if expired, then retry the POST.

        Form data is encoded as ISO-8859-15, like a browser does on Clickedu's
        ISO-8859-15 pages. Encoding it as UTF-8 (curl_cffi's default) makes
        Clickedu store 'reunió' as 'reuniÃ³'."""
        if data is not None and files is None and not isinstance(data, (str, bytes)):
            data = encode_form(data)
            hdrs = dict(kw.pop("headers", None) or {})
            hdrs.setdefault("Content-Type", "application/x-www-form-urlencoded")
            kw["headers"] = hdrs
        with self._lock:
            r = self._s.post(self._url(path), data=data, files=files, allow_redirects=True, **kw)
            html = self._text(r)
            self._save_cookies()
        if self._looks_logged_out(html):
            self.login()
            with self._lock:
                r = self._s.post(
                    self._url(path), data=data, files=files, allow_redirects=True, **kw
                )
                html = self._text(r)
                self._save_cookies()
        return html

    @property
    def id_usuari(self) -> str:
        return self._id_usuari


def _to_latin9(value: str) -> str:
    """Make a value representable in ISO-8859-15. Typographic characters that
    the charset lacks (curly quotes, dashes, ellipsis, bullets, nbsp) become their
    plain equivalents; anything else unrepresentable becomes '?' rather than
    being stored as garbage."""
    table = {
        "‘": "'", "’": "'", "‚": "'", "′": "'",
        "“": '"', "”": '"', "„": '"', "″": '"',
        "–": "-", "—": "-", "−": "-",
        "…": "...", "•": "-", " ": " ", " ": " ",
    }
    value = "".join(table.get(ch, ch) for ch in value)
    return value.encode(ENCODING, errors="replace").decode(ENCODING)


def encode_form(data) -> bytes:
    """URL-encode form fields as ISO-8859-15 bytes, the way a browser submits a
    form on an ISO-8859-15 page. Accepts a dict or a list of (name, value) pairs."""
    from urllib.parse import urlencode

    pairs = data.items() if isinstance(data, dict) else data
    clean = [(str(k), _to_latin9(str(v))) for k, v in pairs]
    return urlencode(clean, encoding=ENCODING).encode("ascii")


def _scrape_id_usuari(html: str) -> str:
    for pat in (
        r'name="id_usuari"[^>]*value="(\d+)"',
        r"id_usuari=(\d+)",
        r'"id_usuari"\s*:\s*"?(\d+)',
    ):
        m = re.search(pat, html)
        if m:
            return m.group(1)
    return ""


# Minimal cookie persistence (name=value per line, host-agnostic; curl_cffi re-scopes on use).
def _dump_jar(cookies, path: Path) -> None:
    lines = []
    for c in cookies.jar:
        lines.append(f"{c.domain}\t{c.path}\t{c.name}\t{c.value or ''}")
    path.write_text("\n".join(lines), encoding="utf-8")


def _load_jar(path: Path) -> dict:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) == 4:
            _, _, name, value = parts
            out[name] = value
    return out


_SESSION: ClickeduSession | None = None


def get_session() -> ClickeduSession:
    global _SESSION
    if _SESSION is None:
        _SESSION = ClickeduSession()
        _SESSION.login()
    return _SESSION
