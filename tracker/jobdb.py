r"""
jobdb.py

A small local database of your job applications and interviews, shared by
both agents. It lives in job_search.db next to this file, is created the
first time it is used, and needs nothing beyond Python itself.

The CV and cover letter agent records an application each time it saves a
draft. The interview prep agent's /prep and /debrief skills record
interviews, interviewers and the questions you were asked, and check which
stories an interviewer has already heard.

HOW TO RUN (from the repo folder; use python3 instead of python on Mac or
Linux):
    python tracker/jobdb.py list
    python tracker/jobdb.py show --company "Example Co"
    python tracker/jobdb.py status 3 applied
    python tracker/jobdb.py --help
"""

import argparse
import os
import sqlite3
import sys
from datetime import date, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
DEFAULT_DB = os.path.join(HERE, "job_search.db")
SCHEMA_PATH = os.path.join(HERE, "schema.sql")

# Keep these in step with the CHECK constraints in schema.sql.
STATUSES = ["drafting", "applied", "interviewing", "offer", "rejected", "withdrawn", "ghosted"]
STAGES = ["recruiter_screen", "hiring_manager", "panel", "case_study", "final"]
OUTCOMES = ["pending", "progressed", "rejected", "withdrew", "offer"]
LANDED = ["good", "ok", "weak"]

# An interview outcome that ends the application also sets its status.
OUTCOME_TO_STATUS = {"offer": "offer", "rejected": "rejected", "withdrew": "withdrawn"}

APPLICATION_QUERY = """
    SELECT a.*, c.name AS company, c.website
    FROM applications a JOIN companies c ON c.id = a.company_id
"""


# ---------------------------------------------------------------------------
# Connection and shared helpers
# ---------------------------------------------------------------------------

def connect(path=DEFAULT_DB):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    return conn


def repo_path(path):
    """Store paths inside the repo folder relative to it, so the database
    still makes sense if the whole folder is moved. Paths outside it are
    stored in full."""
    if not path:
        return path
    full = os.path.abspath(path)
    try:
        relative = os.path.relpath(full, REPO_ROOT)
    except ValueError:  # on a different drive from the repo, on Windows
        return full
    return full if relative.startswith("..") else relative.replace(os.sep, "/")


def require(conn, table, row_id):
    row = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (row_id,)).fetchone()
    if row is None:
        raise SystemExit(f"ERROR: there is no {table[:-1]} #{row_id}. Run 'list' or 'show' to find the right number.")
    return row


def update_row(conn, table, row_id, values):
    values = {k: v for k, v in values.items() if v is not None}
    if values:
        assignments = ", ".join(f"{column} = ?" for column in values)
        conn.execute(f"UPDATE {table} SET {assignments} WHERE id = ?", (*values.values(), row_id))


def get_or_create_company(conn, name, website=None):
    row = conn.execute("SELECT id, website FROM companies WHERE name = ?", (name,)).fetchone()
    if row is None:
        return conn.execute("INSERT INTO companies (name, website) VALUES (?, ?)", (name, website)).lastrowid
    if website and not row["website"]:
        conn.execute("UPDATE companies SET website = ? WHERE id = ?", (website, row["id"]))
    return row["id"]


def add_interviewers(conn, interview_id, people):
    """Link interviewers to an interview. Each person is "Name" or
    "Name, Title". Interviewers are shared across a company's interviews."""
    company_id = conn.execute(
        "SELECT a.company_id FROM interviews i JOIN applications a ON a.id = i.application_id WHERE i.id = ?",
        (interview_id,),
    ).fetchone()["company_id"]
    for person in people:
        name, _, title = (part.strip() for part in person.partition(","))
        if not name:
            continue
        row = conn.execute(
            "SELECT id, title FROM interviewers WHERE company_id = ? AND name = ?", (company_id, name)
        ).fetchone()
        if row is None:
            interviewer_id = conn.execute(
                "INSERT INTO interviewers (company_id, name, title) VALUES (?, ?, ?)",
                (company_id, name, title or None),
            ).lastrowid
        else:
            interviewer_id = row["id"]
            if title and not row["title"]:
                conn.execute("UPDATE interviewers SET title = ? WHERE id = ?", (title, interviewer_id))
        conn.execute("INSERT OR IGNORE INTO interview_interviewers VALUES (?, ?)", (interview_id, interviewer_id))


def record_draft(conn, company, role, website, job_spec, output_dir):
    """Used by the CV agent when it saves a draft. Updates the open
    application for this company and role if there is one, otherwise starts a
    new one. Returns (application id, created)."""
    with conn:
        company_id = get_or_create_company(conn, company, website)
        # A finished application is left alone; applying again starts afresh.
        row = conn.execute(
            "SELECT id FROM applications WHERE company_id = ? AND role_title = ? "
            "AND status NOT IN ('rejected', 'withdrawn', 'ghosted') ORDER BY id DESC LIMIT 1",
            (company_id, role),
        ).fetchone()
        if row:
            update_row(conn, "applications", row["id"], {"job_spec": job_spec, "output_dir": repo_path(output_dir)})
            return row["id"], False
        app_id = conn.execute(
            "INSERT INTO applications (company_id, role_title, job_spec, output_dir) VALUES (?, ?, ?, ?)",
            (company_id, role, job_spec, repo_path(output_dir)),
        ).lastrowid
        return app_id, True


def print_table(rows):
    if not rows:
        print("(nothing found)")
        return
    headers = list(rows[0].keys())
    cells = [["" if row[h] is None else str(row[h]) for h in headers] for row in rows]
    widths = [max(len(h), *(len(c[i]) for c in cells)) for i, h in enumerate(headers)]
    print("  ".join(h.ljust(w) for h, w in zip(headers, widths)).rstrip())
    for c in cells:
        print("  ".join(v.ljust(w) for v, w in zip(c, widths)).rstrip())


def print_application(conn, app):
    applied = f", applied {app['applied_on']}" if app["applied_on"] else ""
    print(f"Application #{app['id']}: {app['role_title']} at {app['company']} ({app['status']}{applied})")
    salary = None
    if app["salary_min"] is not None or app["salary_max"] is not None:
        salary = f"{app['salary_min'] or '?'} to {app['salary_max'] or '?'} {app['salary_currency'] or ''}".strip()
    details = [
        ("Website", app["website"]),
        ("Job posting", app["job_url"]),
        ("Job spec", f"saved ({len(app['job_spec'])} characters)" if app["job_spec"] else None),
        ("Source", app["source"]),
        ("Advertised salary", salary),
        ("Drafts", app["output_dir"]),
        ("Notes", app["notes"]),
    ]
    for label, value in details:
        if value:
            print(f"  {label}: {value}")

    interviews = conn.execute(
        "SELECT * FROM interviews WHERE application_id = ? ORDER BY scheduled_at IS NULL, scheduled_at, id",
        (app["id"],),
    ).fetchall()
    for iv in interviews:
        parts = [
            iv["stage"],
            iv["format"],
            f"{iv['length_minutes']} min" if iv["length_minutes"] else None,
            iv["scheduled_at"],
            f"outcome {iv['outcome']}" if iv["outcome"] else None,
            f"feeling {iv['feeling']}/5" if iv["feeling"] else None,
        ]
        print(f"  Interview #{iv['id']}: {', '.join(p for p in parts if p)}")
        people = conn.execute(
            "SELECT v.name, v.title FROM interview_interviewers ii JOIN interviewers v ON v.id = ii.interviewer_id "
            "WHERE ii.interview_id = ? ORDER BY v.name",
            (iv["id"],),
        ).fetchall()
        if people:
            names = [f"{p['name']} ({p['title']})" if p["title"] else p["name"] for p in people]
            print(f"    Interviewers: {'; '.join(names)}")
        for label, value in (("Prep sheet", iv["prep_sheet"]), ("Debrief", iv["debrief"])):
            if value:
                print(f"    {label}: {value}")
        questions = conn.execute(
            "SELECT * FROM interview_questions WHERE interview_id = ? ORDER BY id", (iv["id"],)
        ).fetchall()
        for q in questions:
            tags = [
                f"story {q['story_number']}" if q["story_number"] is not None else None,
                q["landed"],
                "on prep sheet" if q["on_prep_sheet"] else "not on prep sheet",
            ]
            print(f"    Q: {q['question']} [{', '.join(t for t in tags if t)}]")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def application_values(args):
    return {
        "role_title": args.role,
        "job_url": args.job_url,
        "job_spec": read_text(args.job_spec_file),
        "source": args.source,
        "status": args.status,
        "applied_on": args.applied_on,
        "salary_min": args.salary_min,
        "salary_max": args.salary_max,
        "salary_currency": args.currency,
        "notes": args.notes,
    }


def cmd_add_application(conn, args):
    values = application_values(args)
    if values["status"] == "applied" and not values["applied_on"]:
        values["applied_on"] = date.today().isoformat()
    values = {k: v for k, v in values.items() if v is not None}
    with conn:
        values["company_id"] = get_or_create_company(conn, args.company, args.website)
        app_id = conn.execute(
            f"INSERT INTO applications ({', '.join(values)}) VALUES ({', '.join('?' * len(values))})",
            tuple(values.values()),
        ).lastrowid
    print(f"Application #{app_id}: {args.role} at {args.company}")


def cmd_update_application(conn, args):
    app = require(conn, "applications", args.id)
    with conn:
        update_row(conn, "applications", app["id"], application_values(args))
        if args.website:
            conn.execute("UPDATE companies SET website = ? WHERE id = ?", (args.website, app["company_id"]))
    print(f"Updated application #{app['id']}")


def cmd_status(conn, args):
    app = require(conn, "applications", args.id)
    values = {"status": args.status}
    if args.status == "applied":
        values["applied_on"] = args.date or app["applied_on"] or date.today().isoformat()
    with conn:
        update_row(conn, "applications", app["id"], values)
    print(f"Application #{app['id']} is now {args.status}")


def interview_values(args):
    return {
        "stage": args.stage,
        "format": args.format,
        "length_minutes": args.length,
        "scheduled_at": args.scheduled_at,
        "prep_sheet": repo_path(args.prep_sheet),
    }


def cmd_add_interview(conn, args):
    app = require(conn, "applications", args.application_id)
    values = {k: v for k, v in interview_values(args).items() if v is not None}
    values["application_id"] = app["id"]
    with conn:
        interview_id = conn.execute(
            f"INSERT INTO interviews ({', '.join(values)}) VALUES ({', '.join('?' * len(values))})",
            tuple(values.values()),
        ).lastrowid
        add_interviewers(conn, interview_id, args.interviewer)
        conn.execute(
            "UPDATE applications SET status = 'interviewing' WHERE id = ? AND status IN ('drafting', 'applied')",
            (app["id"],),
        )
    print(f"Interview #{interview_id} added to application #{app['id']}")


def cmd_update_interview(conn, args):
    interview = require(conn, "interviews", args.id)
    values = interview_values(args)
    values.update(debrief=repo_path(args.debrief), feeling=args.feeling, outcome=args.outcome)
    with conn:
        update_row(conn, "interviews", interview["id"], values)
        add_interviewers(conn, interview["id"], args.interviewer)
        if args.outcome in OUTCOME_TO_STATUS:
            update_row(conn, "applications", interview["application_id"], {"status": OUTCOME_TO_STATUS[args.outcome]})
    print(f"Updated interview #{interview['id']}")


def cmd_add_question(conn, args):
    interview = require(conn, "interviews", args.interview_id)
    with conn:
        question_id = conn.execute(
            "INSERT INTO interview_questions (interview_id, question, on_prep_sheet, story_number, landed) "
            "VALUES (?, ?, ?, ?, ?)",
            (interview["id"], args.question, int(args.on_sheet), args.story, args.landed),
        ).lastrowid
    print(f"Question #{question_id} added to interview #{interview['id']}")


def cmd_list(conn, args):
    where, params = ("WHERE a.status = ?", (args.status,)) if args.status else ("", ())
    rows = conn.execute(
        f"""
        SELECT a.id, c.name AS company, a.role_title AS role, a.status, a.applied_on AS applied,
               COUNT(i.id) AS interviews,
               (SELECT stage FROM interviews WHERE application_id = a.id
                ORDER BY scheduled_at IS NULL DESC, scheduled_at DESC, id DESC LIMIT 1) AS latest_stage
        FROM applications a
        JOIN companies c ON c.id = a.company_id
        LEFT JOIN interviews i ON i.application_id = a.id
        {where}
        GROUP BY a.id
        ORDER BY a.id DESC
        """,
        params,
    ).fetchall()
    print_table(rows)


def cmd_show(conn, args):
    if args.id is not None:
        apps = conn.execute(APPLICATION_QUERY + " WHERE a.id = ?", (args.id,)).fetchall()
    elif args.company:
        apps = conn.execute(APPLICATION_QUERY + " WHERE c.name LIKE ? ORDER BY a.id", (f"%{args.company}%",)).fetchall()
    else:
        raise SystemExit("ERROR: give an application number or --company.")
    if not apps:
        print("No matching applications.")
    for i, app in enumerate(apps):
        if i:
            print()
        print_application(conn, app)


def cmd_stories_told(conn, args):
    rows = conn.execute(
        """
        SELECT q.story_number AS story,
               COALESCE(GROUP_CONCAT(v.name, '; '), '(interviewers not recorded)') AS heard_by,
               i.scheduled_at AS date, i.stage, q.landed, a.role_title AS role
        FROM interview_questions q
        JOIN interviews i ON i.id = q.interview_id
        JOIN applications a ON a.id = i.application_id
        JOIN companies c ON c.id = a.company_id
        LEFT JOIN interview_interviewers ii ON ii.interview_id = i.id
        LEFT JOIN interviewers v ON v.id = ii.interviewer_id
        WHERE c.name LIKE ? AND q.story_number IS NOT NULL
        GROUP BY q.id
        ORDER BY q.story_number, i.scheduled_at IS NULL, i.scheduled_at
        """,
        (f"%{args.company}%",),
    ).fetchall()
    print_table(rows)


def cmd_sql(conn, args):
    conn.execute("PRAGMA query_only = ON")
    print_table(conn.execute(args.query).fetchall())


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def iso_date(text):
    try:
        datetime.fromisoformat(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"use YYYY-MM-DD or YYYY-MM-DD HH:MM, not {text!r}")
    return text


def read_text(path):
    """Read a job spec from a file, or from standard input when path is -."""
    if path is None:
        return None
    if path == "-":
        return sys.stdin.read()
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def add_application_options(parser, creating):
    parser.add_argument("--role", required=creating, help="role title")
    parser.add_argument("--website", help="company website")
    parser.add_argument("--job-url", help="link to the job posting")
    parser.add_argument("--job-spec-file", help="file holding the job spec text, or - to read it from standard input")
    parser.add_argument("--source", help="where you found it, e.g. LinkedIn, referral")
    parser.add_argument("--status", choices=STATUSES, default="drafting" if creating else None)
    parser.add_argument("--applied-on", type=iso_date, help="YYYY-MM-DD")
    parser.add_argument("--salary-min", type=int, help="bottom of the advertised range")
    parser.add_argument("--salary-max", type=int, help="top of the advertised range")
    parser.add_argument("--currency", help="e.g. GBP, USD")
    parser.add_argument("--notes")


def add_interview_options(parser, creating):
    parser.add_argument("--stage", choices=STAGES, required=creating)
    parser.add_argument("--format", help="video, in person, phone")
    parser.add_argument("--length", type=int, help="length in minutes")
    parser.add_argument("--scheduled-at", type=iso_date, help="YYYY-MM-DD or YYYY-MM-DD HH:MM")
    parser.add_argument("--prep-sheet", help="path to the prep sheet PDF")
    parser.add_argument(
        "--interviewer", action="append", default=[],
        help='"Name" or "Name, Title"; repeat for each interviewer',
    )


def build_parser():
    parser = argparse.ArgumentParser(description="Track your job applications and interviews.")
    parser.add_argument("--db", default=DEFAULT_DB, help="database file (default: tracker/job_search.db)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("list", help="list applications, newest first")
    p.add_argument("--status", choices=STATUSES)
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("show", help="show an application with its interviews and questions")
    p.add_argument("id", type=int, nargs="?", help="application number")
    p.add_argument("--company", help="show every application at companies matching this name")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("add-application", help="record an application")
    p.add_argument("--company", required=True)
    add_application_options(p, creating=True)
    p.set_defaults(func=cmd_add_application)

    p = sub.add_parser("update-application", help="change details of an application")
    p.add_argument("id", type=int)
    add_application_options(p, creating=False)
    p.set_defaults(func=cmd_update_application)

    p = sub.add_parser("status", help="set an application's status")
    p.add_argument("id", type=int)
    p.add_argument("status", choices=STATUSES)
    p.add_argument("--date", type=iso_date, help="date applied, if not today (only used for 'applied')")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("add-interview", help="record an interview for an application")
    p.add_argument("application_id", type=int)
    add_interview_options(p, creating=True)
    p.set_defaults(func=cmd_add_interview)

    p = sub.add_parser("update-interview", help="change details of an interview, or record how it went")
    p.add_argument("id", type=int)
    add_interview_options(p, creating=False)
    p.add_argument("--debrief", help="path to the debrief file")
    p.add_argument("--feeling", type=int, choices=range(1, 6), help="overall feeling, 1 to 5")
    p.add_argument("--outcome", choices=OUTCOMES)
    p.set_defaults(func=cmd_update_interview)

    p = sub.add_parser("add-question", help="record a question you were asked")
    p.add_argument("interview_id", type=int)
    p.add_argument("--question", required=True)
    p.add_argument("--story", type=int, help="story number from story_bank.md, if you used one")
    p.add_argument("--landed", choices=LANDED)
    p.add_argument("--on-sheet", action="store_true", help="the prep sheet predicted this question")
    p.set_defaults(func=cmd_add_question)

    p = sub.add_parser("stories-told", help="which stories each interviewer at a company has heard")
    p.add_argument("--company", required=True)
    p.set_defaults(func=cmd_stories_told)

    p = sub.add_parser("sql", help="run a read-only SQL query")
    p.add_argument("query")
    p.set_defaults(func=cmd_sql)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    conn = connect(args.db)
    try:
        args.func(conn, args)
    except sqlite3.Error as e:
        raise SystemExit(f"ERROR: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
