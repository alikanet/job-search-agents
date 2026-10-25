r"""
dashboard.py

Your job search tracker in a web browser: where every application stands,
what to do next, what seems to be working, and controls to update any of it.
It reads and writes tracker/job_search.db and needs nothing beyond Python.

It only listens on your own computer (127.0.0.1). Each run makes a fresh
secret that the page sends with every request, so other websites open in
your browser cannot read or change your tracker.

HOW TO RUN (from the repo folder; use python3 instead of python on Mac or
Linux):
    python tracker/dashboard.py           open the dashboard in your browser
    python tracker/dashboard.py --demo    try it first with made-up data

Press Ctrl+C in the terminal to stop it.
"""

import argparse
import csv
import io
import json
import os
import re
import secrets
import sqlite3
import sys
import tempfile
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # the tracker modules live next to this file

import insights
import jobdb

WEB_DIR = os.path.join(HERE, "web")
DEFAULT_PORT = 8765
STATIC_FILES = {"app.js": "text/javascript; charset=utf-8", "style.css": "text/css; charset=utf-8"}

# The only kinds of file the dashboard will open, and only when the tracker
# points at them, so a link can never reach anything else on your computer.
FILE_TYPES = {
    ".pdf": ("application/pdf", "inline"),
    ".md": ("text/plain; charset=utf-8", "inline"),
    ".txt": ("text/plain; charset=utf-8", "inline"),
    ".docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "attachment"),
}

PAGE_SECURITY = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
    "object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
)


class ApiError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


# ---------------------------------------------------------------------------
# Input checking
# ---------------------------------------------------------------------------

APPLICATION_FIELDS = {
    "role_title": "text", "job_url": "text", "job_spec": "text", "source": "text", "status": jobdb.STATUSES,
    "applied_on": "date", "salary_min": "int", "salary_max": "int", "salary_currency": "text", "notes": "text",
}
INTERVIEW_FIELDS = {
    "stage": jobdb.STAGES, "format": "text", "length_minutes": "int", "scheduled_at": "datetime",
    "outcome": jobdb.OUTCOMES, "feeling": "feeling",
}
QUESTION_FIELDS = {"question": "text", "story_number": "int", "landed": jobdb.LANDED, "on_prep_sheet": "bool"}


def clean(body, fields, required=()):
    """Check the fields a request sent against fields, returning column
    values. An empty value means "clear it" and becomes None."""
    if not isinstance(body, dict):
        raise ApiError(400, "Expected a JSON object.")
    values = {}
    for key, kind in fields.items():
        if key not in body:
            continue
        value = body[key]
        if isinstance(value, str):
            value = value.strip()
        if value in ("", None):
            values[key] = None
            continue
        try:
            if kind == "text":
                value = str(value)
            elif kind == "int":
                value = int(value)
            elif kind == "feeling":
                value = int(value)
                if not 1 <= value <= 5:
                    raise ValueError
            elif kind == "bool":
                value = 1 if value in (True, 1, "1", "true", "on") else 0
            elif kind == "date":
                value = datetime.fromisoformat(str(value)).date().isoformat()
            elif kind == "datetime":
                value = str(value).replace("T", " ")[:16]
                datetime.fromisoformat(value)
            elif value not in kind:
                raise ValueError
        except (TypeError, ValueError):
            raise ApiError(400, f"{key.replace('_', ' ').capitalize()} has a value that is not allowed: {body[key]!r}.")
        values[key] = value
    for key in required:
        if not values.get(key):
            raise ApiError(400, f"{key.replace('_', ' ').capitalize()} is required.")
    return values


def people(body):
    """Interviewers as a list of "Name, Title" strings, from a list or from
    text with one person per line."""
    value = body.get("interviewers") or []
    if isinstance(value, str):
        value = value.splitlines()
    return [str(p).strip() for p in value if str(p).strip()]


def must_exist(conn, table, row_id):
    row = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (row_id,)).fetchone()
    if row is None:
        raise ApiError(404, f"There is no {table[:-1]} #{row_id}. It may have been deleted.")
    return row


# ---------------------------------------------------------------------------
# API handlers: each takes (conn, body, query, *ids) and returns JSON data
# ---------------------------------------------------------------------------

def api_summary(conn, body, query):
    return insights.summary(conn)


def api_applications(conn, body, query):
    return insights.application_rows(conn)


def api_create_application(conn, body, query):
    values = clean(body, APPLICATION_FIELDS, required=("role_title",))
    company = str(body.get("company") or "").strip()
    if not company:
        raise ApiError(400, "Company is required.")
    app_id = jobdb.create_application(conn, company, values, (body.get("website") or "").strip() or None)
    return {"id": app_id}


def file_entry(label, path):
    if not path:
        return None
    full = path if os.path.isabs(path) else os.path.join(jobdb.REPO_ROOT, path)
    return {"label": label, "path": path, "exists": os.path.isfile(full)}


def api_application(conn, body, query, app_id):
    detail = insights.application_detail(conn, int(app_id))
    if detail is None:
        raise ApiError(404, f"There is no application #{app_id}. It may have been deleted.")
    a = detail["app"]
    files = []
    if a["output_dir"]:
        folder = a["output_dir"] if os.path.isabs(a["output_dir"]) else os.path.join(jobdb.REPO_ROOT, a["output_dir"])
        if os.path.isdir(folder):
            for name in sorted(os.listdir(folder)):
                if os.path.splitext(name)[1].lower() in FILE_TYPES:
                    files.append(file_entry(name, f"{a['output_dir']}/{name}"))
    for iv in a["interviews"]:
        stage = insights.STAGE_LABELS[iv["stage"]]
        iv["files"] = [f for f in (file_entry(f"Prep sheet ({stage})", iv["prep_sheet"]),
                                   file_entry(f"Debrief ({stage})", iv["debrief"])) if f]
    detail["files"] = files
    return detail


def api_update_application(conn, body, query, app_id):
    must_exist(conn, "applications", app_id)
    values = clean(body, APPLICATION_FIELDS)
    if "role_title" in values and not values["role_title"]:
        raise ApiError(400, "Role is required.")
    jobdb.edit_application(conn, int(app_id), values, (body.get("website") or "").strip() or None, skip_none=False)
    return {"id": int(app_id)}


def api_set_status(conn, body, query, app_id):
    must_exist(conn, "applications", app_id)
    values = clean(body, {"status": jobdb.STATUSES, "date": "date"}, required=("status",))
    with conn:
        jobdb.set_status(conn, int(app_id), values["status"], values.get("date"))
    return {"id": int(app_id), "status": values["status"]}


def api_reapply(conn, body, query, app_id):
    must_exist(conn, "applications", app_id)
    return {"id": jobdb.reapply(conn, int(app_id))}


def api_delete_application(conn, body, query, app_id):
    must_exist(conn, "applications", app_id)
    with conn:
        conn.execute("DELETE FROM applications WHERE id = ?", (int(app_id),))
    return {"deleted": int(app_id)}


def api_create_interview(conn, body, query, app_id):
    must_exist(conn, "applications", app_id)
    values = clean(body, INTERVIEW_FIELDS, required=("stage",))
    outcome = values.pop("outcome", None)
    interview_id = jobdb.create_interview(conn, int(app_id), values, people(body))
    if outcome:
        jobdb.edit_interview(conn, interview_id, {"outcome": outcome})
    return {"id": interview_id}


def api_update_interview(conn, body, query, interview_id):
    must_exist(conn, "interviews", interview_id)
    values = clean(body, INTERVIEW_FIELDS)
    if "stage" in values and not values["stage"]:
        raise ApiError(400, "Stage is required.")
    jobdb.edit_interview(conn, int(interview_id), values, people(body), skip_none=False)
    return {"id": int(interview_id)}


def api_delete_interview(conn, body, query, interview_id):
    must_exist(conn, "interviews", interview_id)
    with conn:
        conn.execute("DELETE FROM interviews WHERE id = ?", (int(interview_id),))
    return {"deleted": int(interview_id)}


def api_remove_interviewer(conn, body, query, interview_id, interviewer_id):
    with conn:
        conn.execute(
            "DELETE FROM interview_interviewers WHERE interview_id = ? AND interviewer_id = ?",
            (int(interview_id), int(interviewer_id)),
        )
    return {"id": int(interview_id)}


def api_create_question(conn, body, query, interview_id):
    must_exist(conn, "interviews", interview_id)
    values = clean(body, QUESTION_FIELDS, required=("question",))
    values["interview_id"] = int(interview_id)
    with conn:
        question_id = jobdb.insert_row(conn, "interview_questions", values)
    return {"id": question_id}


def api_update_question(conn, body, query, question_id):
    must_exist(conn, "interview_questions", question_id)
    values = clean(body, QUESTION_FIELDS)
    if "question" in values and not values["question"]:
        raise ApiError(400, "Question is required.")
    with conn:
        jobdb.update_row(conn, "interview_questions", int(question_id), values, skip_none=False)
    return {"id": int(question_id)}


def api_delete_question(conn, body, query, question_id):
    with conn:
        conn.execute("DELETE FROM interview_questions WHERE id = ?", (int(question_id),))
    return {"deleted": int(question_id)}


def api_analytics(conn, body, query):
    return insights.analytics(conn)


def api_compare(conn, body, query):
    try:
        a, b = int(query["a"][0]), int(query["b"][0])
    except (KeyError, ValueError):
        raise ApiError(400, "Choose two applications to compare.")
    result = insights.compare(conn, a, b)
    if result is None:
        raise ApiError(404, "One of those applications no longer exists.")
    return result


ROUTES = [
    ("GET", r"/api/summary", api_summary),
    ("GET", r"/api/applications", api_applications),
    ("POST", r"/api/applications", api_create_application),
    ("GET", r"/api/applications/(\d+)", api_application),
    ("PATCH", r"/api/applications/(\d+)", api_update_application),
    ("DELETE", r"/api/applications/(\d+)", api_delete_application),
    ("POST", r"/api/applications/(\d+)/status", api_set_status),
    ("POST", r"/api/applications/(\d+)/reapply", api_reapply),
    ("POST", r"/api/applications/(\d+)/interviews", api_create_interview),
    ("PATCH", r"/api/interviews/(\d+)", api_update_interview),
    ("DELETE", r"/api/interviews/(\d+)", api_delete_interview),
    ("DELETE", r"/api/interviews/(\d+)/interviewers/(\d+)", api_remove_interviewer),
    ("POST", r"/api/interviews/(\d+)/questions", api_create_question),
    ("PATCH", r"/api/questions/(\d+)", api_update_question),
    ("DELETE", r"/api/questions/(\d+)", api_delete_question),
    ("GET", r"/api/analytics", api_analytics),
    ("GET", r"/api/compare", api_compare),
]


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    server_version = "JobSearchTracker"

    def log_message(self, fmt, *args):
        pass  # keep the terminal quiet; errors are shown in the page

    def do_GET(self):
        self.dispatch("GET")

    def do_POST(self):
        self.dispatch("POST")

    def do_PATCH(self):
        self.dispatch("PATCH")

    def do_DELETE(self):
        self.dispatch("DELETE")

    def send(self, status, body, content_type, headers=()):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        for name, value in headers:
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status, data):
        self.send(status, json.dumps(data, default=str).encode("utf-8"), "application/json; charset=utf-8")

    def token_ok(self, supplied):
        return secrets.compare_digest(supplied or "", self.server.token)

    def dispatch(self, method):
        # Only answer requests addressed to this server by name, which stops a
        # malicious page from reaching it through a look-alike domain.
        if self.headers.get("Host") not in self.server.allowed_hosts:
            return self.send(403, b"Unknown host", "text/plain; charset=utf-8")
        url = urlparse(self.path)
        query = parse_qs(url.query)

        if method == "GET" and url.path == "/":
            with open(os.path.join(WEB_DIR, "index.html"), "r", encoding="utf-8") as f:
                page = f.read().replace("{{TOKEN}}", self.server.token)
            return self.send(200, page.encode("utf-8"), "text/html; charset=utf-8",
                             [("Content-Security-Policy", PAGE_SECURITY), ("Referrer-Policy", "no-referrer")])
        if method == "GET" and url.path.startswith("/static/"):
            name = url.path[len("/static/"):]
            if name not in STATIC_FILES:
                return self.send(404, b"Not found", "text/plain; charset=utf-8")
            with open(os.path.join(WEB_DIR, name), "rb") as f:
                return self.send(200, f.read(), STATIC_FILES[name])
        if method == "GET" and url.path in ("/files", "/export.csv"):
            if not self.token_ok(query.get("t", [""])[0]):
                return self.send(403, b"This link has expired. Reload the dashboard.", "text/plain; charset=utf-8")
            return self.send_file(query) if url.path == "/files" else self.send_csv()
        if not url.path.startswith("/api/"):
            return self.send(404, b"Not found", "text/plain; charset=utf-8")
        if not self.token_ok(self.headers.get("X-Tracker-Token")):
            return self.send_json(403, {"error": "The dashboard was restarted. Reload the page."})
        if method == "GET" and url.path == "/api/meta":
            return self.send_json(200, {"demo": self.server.demo, "db": self.server.db_label})

        for route_method, pattern, handler in ROUTES:
            match = re.fullmatch(pattern, url.path)
            if route_method == method and match:
                break
        else:
            return self.send_json(404, {"error": "Unknown request."})

        try:
            body = self.read_json() if method in ("POST", "PATCH") else {}
            conn = jobdb.connect(self.server.db_path)
            try:
                result = handler(conn, body, query, *match.groups())
            finally:
                conn.close()
        except ApiError as e:
            return self.send_json(e.status, {"error": str(e)})
        except sqlite3.IntegrityError as e:
            return self.send_json(400, {"error": f"That change breaks a rule in the tracker ({e})."})
        return self.send_json(200, result)

    def read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length > 2_000_000:
            raise ApiError(413, "That is too much text to save at once.")
        try:
            return json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            raise ApiError(400, "The request was not valid JSON.")

    def send_file(self, query):
        wanted = query.get("path", [""])[0]
        conn = jobdb.connect(self.server.db_path)
        try:
            known = {r[0] for r in conn.execute(
                "SELECT prep_sheet FROM interviews WHERE prep_sheet IS NOT NULL "
                "UNION SELECT debrief FROM interviews WHERE debrief IS NOT NULL")}
            folders = {r[0] for r in conn.execute("SELECT output_dir FROM applications WHERE output_dir IS NOT NULL")}
        finally:
            conn.close()
        allowed = wanted in known or os.path.dirname(wanted) in folders
        kind = FILE_TYPES.get(os.path.splitext(wanted)[1].lower())
        full = os.path.realpath(wanted if os.path.isabs(wanted) else os.path.join(jobdb.REPO_ROOT, wanted))
        if not (allowed and kind and os.path.isfile(full)):
            return self.send(404, b"That file is not in the tracker, or it has been moved.", "text/plain; charset=utf-8")
        with open(full, "rb") as f:
            data = f.read()
        name = os.path.basename(full).replace('"', "")
        self.send(200, data, kind[0], [("Content-Disposition", f'{kind[1]}; filename="{name}"')])

    def send_csv(self):
        conn = jobdb.connect(self.server.db_path)
        try:
            rows = insights.application_rows(conn)
        finally:
            conn.close()
        out = io.StringIO()
        if rows:
            writer = csv.DictWriter(out, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        self.send(200, out.getvalue().encode("utf-8-sig"), "text/csv; charset=utf-8",
                  [("Content-Disposition", 'attachment; filename="job_search_applications.csv"')])


def make_server(db_path, port, demo=False):
    """Bind to the first free port from port upwards, on this computer only."""
    for candidate in range(port, port + 20):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", candidate), Handler)
            break
        except OSError:
            continue
    else:
        raise SystemExit(f"ERROR: ports {port} to {port + 19} are all in use. Try --port with another number.")
    actual = server.server_address[1]
    server.allowed_hosts = {f"127.0.0.1:{actual}", f"localhost:{actual}"}
    server.token = secrets.token_urlsafe(32)
    server.db_path = db_path
    server.demo = demo
    server.db_label = "demo data (not saved)" if demo else jobdb.repo_path(db_path)
    return server


def main(argv=None):
    parser = argparse.ArgumentParser(description="Open your job search tracker in a web browser.")
    parser.add_argument("--db", default=jobdb.DEFAULT_DB, help="database file (default: tracker/job_search.db)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"port to use (default: {DEFAULT_PORT})")
    parser.add_argument("--demo", action="store_true", help="try the dashboard with made-up data; nothing is saved")
    parser.add_argument("--no-browser", action="store_true", help="do not open a browser window")
    args = parser.parse_args(argv)

    db_path = args.db
    if args.demo:
        import demo_data
        folder = tempfile.mkdtemp(prefix="job-tracker-demo-")
        db_path = os.path.join(folder, "demo.db")
        insights.STORY_BANK = demo_data.seed(db_path, folder)
    jobdb.connect(db_path).close()  # create the database now, so a problem shows here, not in the page

    server = make_server(db_path, args.port, args.demo)
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print(f"Job search dashboard: {url}")
    print("Demo mode: made-up data, nothing is saved to your tracker." if args.demo else f"Using {jobdb.repo_path(db_path)}")
    print("Press Ctrl+C to stop.")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
