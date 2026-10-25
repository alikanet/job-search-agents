"""
insights.py

The numbers behind the dashboard: stats, the application funnel, what seems
to be working, interview and story performance, advice on what to do next,
and side-by-side comparisons. Everything is computed from the tracker
database on request, so it always reflects the latest data.

Rates are only compared when each group has at least MIN_GROUP applications,
and every figure carries its sample size, so small numbers are never
presented as a pattern.
"""

import os
import re
import statistics
from datetime import date

import jobdb

STAGE_LABELS = {
    "recruiter_screen": "recruiter screen",
    "hiring_manager": "hiring manager",
    "panel": "panel",
    "case_study": "case study",
    "final": "final round",
}
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

ACTIVE_STATUSES = ("drafting", "applied", "interviewing")
SUBMITTED_STATUSES = ("applied", "interviewing", "offer", "rejected", "ghosted")
RESPONSE_STATUSES = ("interviewing", "rejected", "offer")

MIN_GROUP = 3           # smallest group whose rate is compared with another
NOTABLE_GAP = 0.2       # a 20 point difference in interview rate is worth a mention
DEFAULT_FOLLOW_UP_DAYS = 7
DEFAULT_GHOST_DAYS = 30
DRAFT_STALE_DAYS = 5
STORY_BANK = os.path.join(jobdb.REPO_ROOT, "interview-prep-agent", "story_bank.md")


# ---------------------------------------------------------------------------
# Loading and per-application facts
# ---------------------------------------------------------------------------

def parse_day(text):
    try:
        return date.fromisoformat(text[:10]) if text else None
    except ValueError:
        return None


def rate(part, whole):
    return round(part / whole, 3) if whole else None


def story_titles():
    """Story numbers and titles from story_bank.md ("## 3. Title"), so the
    dashboard can name stories rather than number them."""
    try:
        with open(STORY_BANK, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return {}
    return {
        int(number): title.strip()
        for number, title in re.findall(r"^##\s+(\d+)\.\s+(.+)$", text, re.MULTILINE)
        if "[" not in title
    }


def load(conn, today=None):
    """Every application with its interviews, questions, interviewers and
    status history, plus the derived facts the stats are built from."""
    today = today or date.today()
    apps = [dict(row) for row in conn.execute(jobdb.APPLICATION_QUERY + " ORDER BY a.id")]
    by_id = {a["id"]: a for a in apps}
    for a in apps:
        a["interviews"], a["history"] = [], []

    interviews = {}
    for row in conn.execute("SELECT * FROM interviews ORDER BY scheduled_at IS NULL, scheduled_at, id"):
        iv = dict(row, questions=[], interviewers=[])
        interviews[iv["id"]] = iv
        by_id[iv["application_id"]]["interviews"].append(iv)
    for row in conn.execute("SELECT * FROM interview_questions ORDER BY id"):
        interviews[row["interview_id"]]["questions"].append(dict(row))
    for row in conn.execute(
        "SELECT ii.interview_id, v.id, v.name, v.title FROM interview_interviewers ii "
        "JOIN interviewers v ON v.id = ii.interviewer_id ORDER BY v.name"
    ):
        interviews[row["interview_id"]]["interviewers"].append({"id": row["id"], "name": row["name"], "title": row["title"]})
    for row in conn.execute("SELECT * FROM status_history ORDER BY changed_on, id"):
        by_id[row["application_id"]]["history"].append(dict(row))

    for a in apps:
        derive(a, today)
    return apps


def derive(a, today):
    ivs = a["interviews"]
    outcomes = {iv["outcome"] for iv in ivs}
    a["interviewed"] = bool(ivs)
    a["submitted"] = bool(a["applied_on"] or ivs or a["status"] in SUBMITTED_STATUSES)
    a["responded"] = bool(ivs) or a["status"] in ("rejected", "offer")
    a["offer"] = a["status"] == "offer" or "offer" in outcomes
    a["progressed"] = a["offer"] or "progressed" in outcomes
    a["tailored"] = bool(a["output_dir"])
    a["salary_listed"] = a["salary_min"] is not None or a["salary_max"] is not None
    stages = [iv["stage"] for iv in ivs]
    a["furthest_stage"] = max(stages, key=jobdb.STAGES.index) if stages else None
    a["progress"] = 4 if a["offer"] else 3 if a["progressed"] else 2 if a["interviewed"] else 1 if a["responded"] else 0

    applied = parse_day(a["applied_on"])
    response = next((parse_day(h["changed_on"]) for h in a["history"] if h["status"] in RESPONSE_STATUSES), None)
    if response is None and ivs:
        response = parse_day(ivs[0]["scheduled_at"])
    a["response_on"] = response.isoformat() if response else None
    a["days_to_response"] = (response - applied).days if applied and response and response >= applied else None
    a["days_since_applied"] = (today - applied).days if applied else None
    created = parse_day(a["created_on"])
    a["days_draft_to_send"] = (applied - created).days if applied and created and applied >= created else None

    since = next((parse_day(h["changed_on"]) for h in reversed(a["history"]) if h["status"] == a["status"]), None)
    since = since or (applied if a["status"] == "applied" else None) or created
    a["status_since"] = since.isoformat() if since else None
    a["days_in_status"] = (today - since).days if since else None

    upcoming = [iv for iv in ivs if parse_day(iv["scheduled_at"]) and parse_day(iv["scheduled_at"]) >= today]
    a["next_interview"] = upcoming[0]["scheduled_at"] if upcoming else None
    questions = [q for iv in ivs for q in iv["questions"]]
    a["stories"] = sorted({q["story_number"] for q in questions if q["story_number"] is not None})
    a["landed"] = {k: sum(q["landed"] == k for q in questions) for k in jobdb.LANDED}
    feelings = [iv["feeling"] for iv in ivs if iv["feeling"]]
    a["feeling"] = round(statistics.mean(feelings), 1) if feelings else None


def label(a):
    return f"{a['role_title']} at {a['company']}"


def follow_up_thresholds(apps):
    """When to follow up and when to give up, learned from how long your
    replies have actually taken once there are enough of them."""
    days = sorted(a["days_to_response"] for a in apps if a["days_to_response"] is not None)
    if len(days) < 5:
        return {"follow_up_days": DEFAULT_FOLLOW_UP_DAYS, "ghost_days": DEFAULT_GHOST_DAYS, "based_on": 0}
    p80 = days[min(len(days) - 1, int(len(days) * 0.8))]
    return {
        "follow_up_days": max(5, round(statistics.median(days))),
        "ghost_days": max(21, p80 * 2),
        "based_on": len(days),
    }


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------

def kpis(apps, today):
    submitted = [a for a in apps if a["submitted"]]
    days = [a["days_to_response"] for a in submitted if a["days_to_response"] is not None]

    def sent_within(n):
        return sum(1 for a in submitted if a["days_since_applied"] is not None and a["days_since_applied"] < n)

    return {
        "total": len(apps),
        "active": sum(a["status"] in ACTIVE_STATUSES for a in apps),
        "submitted": len(submitted),
        "responded": sum(a["responded"] for a in submitted),
        "interviewed": sum(a["interviewed"] for a in submitted),
        "offers": sum(a["offer"] for a in submitted),
        "response_rate": rate(sum(a["responded"] for a in submitted), len(submitted)),
        "interview_rate": rate(sum(a["interviewed"] for a in submitted), len(submitted)),
        "offer_rate": rate(sum(a["offer"] for a in submitted), len(submitted)),
        "median_days_to_response": statistics.median(days) if days else None,
        "responses_timed": len(days),
        "submitted_last_7": sent_within(7),
        "submitted_last_30": sent_within(30),
    }


def weekly(apps, today, weeks=12):
    """Applications sent per week (weeks start on Monday), oldest first."""
    monday = today.toordinal() - today.weekday()
    starts = [date.fromordinal(monday - 7 * i) for i in range(weeks - 1, -1, -1)]
    counts = {s: 0 for s in starts}
    for a in apps:
        applied = parse_day(a["applied_on"])
        if applied:
            start = date.fromordinal(applied.toordinal() - applied.weekday())
            if start in counts:
                counts[start] += 1
    return [{"week_start": s.isoformat(), "count": counts[s]} for s in starts]


def summary(conn, today=None):
    today = today or date.today()
    apps = load(conn, today)
    upcoming = sorted(
        (
            {
                "interview_id": iv["id"], "app_id": a["id"], "company": a["company"], "role": a["role_title"],
                "stage": iv["stage"], "format": iv["format"], "length_minutes": iv["length_minutes"],
                "scheduled_at": iv["scheduled_at"], "has_prep": bool(iv["prep_sheet"]),
                "interviewers": [p["name"] for p in iv["interviewers"]],
            }
            for a in apps for iv in a["interviews"]
            if parse_day(iv["scheduled_at"]) and parse_day(iv["scheduled_at"]) >= today
        ),
        key=lambda u: u["scheduled_at"],
    )
    activity = sorted(
        (
            {"app_id": a["id"], "company": a["company"], "role": a["role_title"], "status": h["status"], "on": h["changed_on"]}
            for a in apps for h in a["history"]
        ),
        key=lambda e: e["on"],
        reverse=True,
    )[:12]
    return {
        "today": today.isoformat(),
        "kpis": kpis(apps, today),
        "status_counts": {s: sum(a["status"] == s for a in apps) for s in jobdb.STATUSES},
        "advice": advice(apps, today),
        "upcoming": upcoming,
        "activity": activity,
        "weekly": weekly(apps, today),
        "thresholds": follow_up_thresholds(apps),
    }


def application_rows(conn, today=None):
    today = today or date.today()
    keys = [
        "id", "company", "role_title", "status", "source", "created_on", "applied_on", "status_since",
        "days_in_status", "furthest_stage", "next_interview", "responded", "tailored", "reapplied_from",
        "salary_min", "salary_max", "salary_currency", "job_url", "notes",
    ]
    rows = []
    for a in load(conn, today):
        row = {k: a[k] for k in keys}
        row["interviews"] = len(a["interviews"])
        rows.append(row)
    return sorted(rows, key=lambda r: r["id"], reverse=True)


# ---------------------------------------------------------------------------
# Advice
# ---------------------------------------------------------------------------

def advice(apps, today):
    """What to do next, most urgent first. Every item names the application
    it is about and, where it helps, an action the dashboard can take."""
    items = []
    thresholds = follow_up_thresholds(apps)
    learned = (
        f" Most of your replies have come within {thresholds['follow_up_days']} days."
        if thresholds["based_on"] else ""
    )

    def add(priority, kind, a, title, detail, actions=(), apps_listed=()):
        items.append({
            "priority": priority, "kind": kind, "app_id": a["id"] if a else None,
            "title": title, "detail": detail, "actions": list(actions),
            "apps": [{"id": x["id"], "label": label(x)} for x in apps_listed],
        })

    ghosts = []
    for a in apps:
        for iv in a["interviews"]:
            day = parse_day(iv["scheduled_at"])
            stage = STAGE_LABELS[iv["stage"]]
            if day and today <= day <= date.fromordinal(today.toordinal() + 7) and not iv["prep_sheet"]:
                when = "today" if day == today else f"on {WEEKDAYS[day.weekday()]} {day.day} {day.strftime('%B')}"
                add(1, "prep", a, f"Prepare for your {stage} interview at {a['company']} {when}",
                    "Run /prep in the interview-prep-agent folder to get a cheat sheet with matched stories, "
                    "likely questions and salary benchmarks.")
            if day and day < today and not iv["debrief"] and not iv["questions"]:
                age = (today - day).days
                add(1 if age <= 3 else 2, "debrief", a, f"Debrief your {stage} interview at {a['company']}",
                    f"It was {age} day{'s' if age != 1 else ''} ago. Run /debrief with rough notes while you still "
                    f"remember the questions, or add them on the application page. Debriefs make the next prep sharper.")
            if day and (today - day).days > 7 and iv["outcome"] in (None, "pending") and a["status"] == "interviewing":
                add(2, "chase", a, f"Chase {a['company']} for a decision",
                    f"Your {stage} interview was {(today - day).days} days ago with no outcome recorded. "
                    f"A short note asking about timing is normal. Record the result when you hear.")

        if a["status"] == "offer":
            add(1, "offer", a, f"You have an offer from {a['company']}",
                "Check it against your private salary floor and the benchmarks on your prep sheet before you answer. "
                "It is normal to ask for a few days and for the offer in writing.")
        if a["status"] == "drafting" and a["days_in_status"] is not None and a["days_in_status"] >= DRAFT_STALE_DAYS:
            add(2, "draft", a, f"Send or drop your draft for {label(a)}",
                f"It has been a draft for {a['days_in_status']} days. Postings close, and early applications "
                f"are read first.",
                [{"label": "Mark as sent today", "status": "applied"}, {"label": "Withdraw", "status": "withdrawn"}])
        if a["status"] == "applied" and a["days_since_applied"] is not None:
            waited = a["days_since_applied"]
            if waited >= thresholds["ghost_days"]:
                ghosts.append(a)
            elif waited >= thresholds["follow_up_days"]:
                add(2, "follow_up", a, f"Follow up on {label(a)}",
                    f"You applied {waited} days ago and have not heard back. A two-line note to the recruiter or "
                    f"hiring manager restating your fit is worth sending once." + learned)

    if ghosts:
        ghosts.sort(key=lambda a: -a["days_since_applied"])
        single = len(ghosts) == 1
        add(3, "ghost", ghosts[0] if single else None,
            f"No reply from {ghosts[0]['company']} after {ghosts[0]['days_since_applied']} days" if single
            else f"{len(ghosts)} applications have had no reply for over {thresholds['ghost_days']} days",
            "Replies this late are rare. Marking them as ghosted keeps your pipeline honest, and you can "
            "reopen any of them if they get in touch." + learned,
            [{"label": "Mark as ghosted" if single else f"Mark all {len(ghosts)} as ghosted",
              "status": "ghosted", "app_ids": [a["id"] for a in ghosts]}],
            [] if single else ghosts)

    stories = story_stats(apps)
    for s in stories:
        if s["weak"] >= 2 and s["weak"] >= s["good"]:
            add(2, "story", None, f"Rework story {s['number']}" + (f": {s['title']}" if s["title"] else ""),
                f"It landed weak {s['weak']} of {s['uses']} times. Tighten the result and the number, "
                f"or swap in a stronger story for the questions it has been answering.")

    q = question_stats(apps)
    if q["total"] >= 6 and q["predicted_rate"] is not None and q["predicted_rate"] < 0.5:
        add(3, "prep_quality", None, "Your prep sheets are missing most questions",
            f"Only {q['predicted']} of {q['total']} recorded questions were on the prep sheet. Recording "
            f"questions with /debrief after every interview is what teaches /prep what to expect.")

    in_play = sum(a["status"] in ("applied", "interviewing") for a in apps)
    sent_this_week = sum(1 for a in apps if a["days_since_applied"] is not None and a["days_since_applied"] < 7)
    if apps and in_play < 5 and sent_this_week == 0:
        add(3, "momentum", None, "Your pipeline is thin",
            f"You have {in_play} application{'s' if in_play != 1 else ''} waiting on a reply and none sent in the "
            f"last week. Most searches need a steady flow, because most applications do not get a reply.")

    return sorted(items, key=lambda i: i["priority"])


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

def funnel(apps):
    submitted = [a for a in apps if a["submitted"]]
    steps = [
        ("submitted", "Sent", len(submitted)),
        ("responded", "Got a reply", sum(a["responded"] for a in submitted)),
        ("interviewed", "Interviewed", sum(a["interviewed"] for a in submitted)),
        ("progressed", "Got past a round", sum(a["progressed"] for a in submitted)),
        ("offer", "Offer", sum(a["offer"] for a in submitted)),
    ]
    return [{"key": k, "label": lbl, "count": n, "rate": rate(n, len(submitted))} for k, lbl, n in steps]


def factor_values(a):
    """The things the tracker knows about an application that might explain
    how it did. Only applications that were sent are compared."""
    sent_after = a["days_draft_to_send"]
    return {
        "Where you found it": a["source"] or "Source not recorded",
        "CV and cover letter": "Tailored with the CV agent" if a["tailored"] else "Not tailored with the CV agent",
        "Advertised salary": "Salary in the posting" if a["salary_listed"] else "No salary in the posting",
        "First try or reapplication": "Reapplication" if a["reapplied_from"] else "First application",
        "Time from draft to sending": (
            None if sent_after is None else "Sent within 2 days of drafting" if sent_after <= 2 else "Sent 3 or more days after drafting"
        ),
    }


def factors(apps):
    submitted = [a for a in apps if a["submitted"]]
    results = []
    names = list(factor_values(submitted[0]).keys()) if submitted else []
    for name in names:
        groups = {}
        for a in submitted:
            value = factor_values(a)[name]
            if value is not None:
                groups.setdefault(value, []).append(a)
        rows = [
            {
                "label": value, "n": len(members),
                "responded": sum(m["responded"] for m in members),
                "interviewed": sum(m["interviewed"] for m in members),
                "offers": sum(m["offer"] for m in members),
                "response_rate": rate(sum(m["responded"] for m in members), len(members)),
                "interview_rate": rate(sum(m["interviewed"] for m in members), len(members)),
                "offer_rate": rate(sum(m["offer"] for m in members), len(members)),
            }
            for value, members in groups.items()
        ]
        rows.sort(key=lambda r: (-(r["interview_rate"] or 0), -r["n"]))
        results.append({"name": name, "groups": rows})
    return results


def factor_insights(factor_list):
    """Plain-language notes on the biggest differences in interview rate,
    only where both groups are big enough to compare."""
    notes = []
    for factor in factor_list:
        comparable = [g for g in factor["groups"] if g["n"] >= MIN_GROUP]
        if len(comparable) < 2:
            continue
        best, worst = comparable[0], comparable[-1]
        gap = (best["interview_rate"] or 0) - (worst["interview_rate"] or 0)
        if gap < NOTABLE_GAP:
            continue
        small = best["n"] + worst["n"] < 15
        notes.append({
            "factor": factor["name"],
            "gap": round(gap, 3),
            "strength": "early signal" if small else "pattern",
            "text": (
                f"{best['label']}: interviews from {best['interviewed']} of {best['n']} "
                f"({round(100 * best['interview_rate'])}%). {worst['label']}: {worst['interviewed']} of {worst['n']} "
                f"({round(100 * (worst['interview_rate'] or 0))}%)."
            ),
        })
    return sorted(notes, key=lambda n: -n["gap"])


def stage_stats(apps):
    rows = []
    for stage in jobdb.STAGES:
        ivs = [iv for a in apps for iv in a["interviews"] if iv["stage"] == stage]
        if not ivs:
            continue
        passed = sum(iv["outcome"] in ("progressed", "offer") for iv in ivs)
        failed = sum(iv["outcome"] in ("rejected", "withdrew") for iv in ivs)
        rows.append({
            "stage": stage, "label": STAGE_LABELS[stage], "total": len(ivs), "passed": passed, "failed": failed,
            "pending": len(ivs) - passed - failed, "pass_rate": rate(passed, passed + failed),
        })
    return rows


def story_stats(apps):
    titles = story_titles()
    stats = {}
    for a in apps:
        for iv in a["interviews"]:
            for q in iv["questions"]:
                n = q["story_number"]
                if n is None:
                    continue
                s = stats.setdefault(n, {
                    "number": n, "title": titles.get(n), "uses": 0, "good": 0, "ok": 0, "weak": 0,
                    "unrated": 0, "companies": set(), "last_used": None,
                })
                s["uses"] += 1
                s[q["landed"] or "unrated"] += 1
                s["companies"].add(a["company"])
                if iv["scheduled_at"] and (s["last_used"] is None or iv["scheduled_at"] > s["last_used"]):
                    s["last_used"] = iv["scheduled_at"][:10]
    rows = []
    for s in stats.values():
        rated = s["good"] + s["ok"] + s["weak"]
        rows.append(dict(s, companies=sorted(s["companies"]), good_rate=rate(s["good"], rated)))
    unused = sorted(set(titles) - set(stats))
    return sorted(rows, key=lambda r: (-r["uses"], r["number"])) + [
        {"number": n, "title": titles[n], "uses": 0, "good": 0, "ok": 0, "weak": 0, "unrated": 0,
         "companies": [], "last_used": None, "good_rate": None}
        for n in unused
    ]


def question_stats(apps):
    questions = [(a, iv, q) for a in apps for iv in a["interviews"] for q in iv["questions"]]
    common = {}
    for a, iv, q in questions:
        key = re.sub(r"[^a-z0-9 ]", "", q["question"].lower()).strip()
        entry = common.setdefault(key, {"question": q["question"], "count": 0, "weak": 0, "companies": set()})
        entry["count"] += 1
        entry["weak"] += q["landed"] == "weak"
        entry["companies"].add(a["company"])
    common_rows = sorted(
        (dict(e, companies=sorted(e["companies"])) for e in common.values()),
        key=lambda e: (-e["count"], -e["weak"]),
    )
    hardest = [
        {"question": q["question"], "company": a["company"], "stage": iv["stage"], "app_id": a["id"]}
        for a, iv, q in questions if q["landed"] == "weak"
    ]
    predicted = sum(q["on_prep_sheet"] for _, _, q in questions)
    return {
        "total": len(questions),
        "predicted": predicted,
        "predicted_rate": rate(predicted, len(questions)),
        "common": common_rows[:15],
        "hardest": hardest[:15],
    }


def feeling_stats(apps):
    def mean_of(outcomes):
        values = [iv["feeling"] for a in apps for iv in a["interviews"] if iv["feeling"] and iv["outcome"] in outcomes]
        return {"average": round(statistics.mean(values), 1) if values else None, "n": len(values)}
    return {"went_well": mean_of(("progressed", "offer")), "went_badly": mean_of(("rejected",))}


def response_times(apps):
    days = sorted(a["days_to_response"] for a in apps if a["days_to_response"] is not None)
    buckets = [("0 to 3 days", 0, 3), ("4 to 7", 4, 7), ("8 to 14", 8, 14), ("15 to 30", 15, 30), ("Over 30", 31, None)]
    return {
        "n": len(days),
        "median": statistics.median(days) if days else None,
        "buckets": [
            {"label": lbl, "count": sum(1 for d in days if d >= lo and (hi is None or d <= hi))}
            for lbl, lo, hi in buckets
        ],
    }


def analytics(conn, today=None):
    today = today or date.today()
    apps = load(conn, today)
    factor_list = factors(apps)
    return {
        "today": today.isoformat(),
        "kpis": kpis(apps, today),
        "funnel": funnel(apps),
        "factors": factor_list,
        "insights": factor_insights(factor_list),
        "weekly": weekly(apps, today, weeks=26),
        "response_times": response_times(apps),
        "stages": stage_stats(apps),
        "stories": story_stats(apps),
        "questions": question_stats(apps),
        "feeling": feeling_stats(apps),
        "status_counts": {s: sum(a["status"] == s for a in apps) for s in jobdb.STATUSES},
        "min_group": MIN_GROUP,
    }


# ---------------------------------------------------------------------------
# One application, and comparing two
# ---------------------------------------------------------------------------

PROGRESS_LABELS = ["No reply yet", "Got a reply", "Interviewed", "Got past a round", "Offer"]


def group_rate(factor_list, factor_name, value):
    for factor in factor_list:
        if factor["name"] == factor_name:
            for g in factor["groups"]:
                if g["label"] == value:
                    return g
    return None


def application_context(apps, a, factor_list, thresholds):
    """How this application compares with the rest of your search."""
    notes = []
    if a["status"] == "applied" and a["days_since_applied"] is not None:
        notes.append(
            f"Sent {a['days_since_applied']} days ago. You usually follow up after {thresholds['follow_up_days']} days "
            f"and treat it as ghosted after {thresholds['ghost_days']}."
        )
    if a["days_to_response"] is not None:
        others = [o["days_to_response"] for o in apps if o["days_to_response"] is not None and o["id"] != a["id"]]
        if others:
            median = statistics.median(others)
            notes.append(f"They replied in {a['days_to_response']} days; your other replies took {median:g} days (median).")
    if a["submitted"]:
        for name, value in factor_values(a).items():
            g = group_rate(factor_list, name, value)
            if value and g and g["n"] >= MIN_GROUP:
                notes.append(
                    f"{value}: {g['interviewed']} of {g['n']} such applications got an interview "
                    f"({round(100 * (g['interview_rate'] or 0))}%)."
                )
    return notes


def application_detail(conn, app_id, today=None):
    today = today or date.today()
    apps = load(conn, today)
    a = next((x for x in apps if x["id"] == app_id), None)
    if a is None:
        return None
    factor_list = factors(apps)
    thresholds = follow_up_thresholds(apps)
    return {
        "app": a,
        "progress_label": PROGRESS_LABELS[a["progress"]],
        "context": application_context(apps, a, factor_list, thresholds),
        "advice": [i for i in advice(apps, today) if i["app_id"] == app_id],
        "reapplications": [x["id"] for x in apps if x["reapplied_from"] == app_id],
        "story_titles": story_titles(),
    }


def compare(conn, a_id, b_id, today=None):
    today = today or date.today()
    apps = load(conn, today)
    by_id = {a["id"]: a for a in apps}
    a, b = by_id.get(a_id), by_id.get(b_id)
    if a is None or b is None:
        return None
    factor_list = factors(apps)

    def landed(x):
        rated = sum(x["landed"].values())
        return f"{x['landed']['good']} good, {x['landed']['ok']} ok, {x['landed']['weak']} weak" if rated else "None recorded"

    def prep(x):
        if not x["interviews"]:
            return "No interviews"
        return f"{sum(bool(iv['prep_sheet']) for iv in x['interviews'])} of {len(x['interviews'])} interviews"

    def sent(x):
        d = parse_day(x["applied_on"])
        return f"{d.day} {d.strftime('%b %Y')}" if d else "Not sent"

    def waited(x):
        return "No reply" if x["days_to_response"] is None else f"{x['days_to_response']} days"

    def furthest(x):
        return STAGE_LABELS[x["furthest_stage"]].capitalize() if x["furthest_stage"] else "None"

    rows = [
        ("Where it got to", PROGRESS_LABELS[a["progress"]], PROGRESS_LABELS[b["progress"]]),
        ("Status", a["status"].capitalize(), b["status"].capitalize()),
        ("Sent", sent(a), sent(b)),
        ("Time to a reply", waited(a), waited(b)),
        ("Furthest interview", furthest(a), furthest(b)),
        ("Prep sheet used", prep(a), prep(b)),
        ("How answers landed", landed(a), landed(b)),
        ("Stories told", ", ".join(map(str, a["stories"])) or "None", ", ".join(map(str, b["stories"])) or "None"),
        ("How it felt", f"{a['feeling']} of 5" if a["feeling"] else "Not recorded", f"{b['feeling']} of 5" if b["feeling"] else "Not recorded"),
    ]
    va, vb = factor_values(a), factor_values(b)
    rows += [(name, va[name] or "Unknown", vb[name] or "Unknown") for name in va]

    if a["progress"] == b["progress"]:
        leader, trailer = None, None
    else:
        leader, trailer = (a, b) if a["progress"] > b["progress"] else (b, a)

    reasons = []
    if leader:
        reasons.append(
            f"{label(leader)} got further ({PROGRESS_LABELS[leader['progress']].lower()}) than "
            f"{label(trailer)} ({PROGRESS_LABELS[trailer['progress']].lower()})."
        )
        lv, tv = factor_values(leader), factor_values(trailer)
        for name in lv:
            if lv[name] and tv[name] and lv[name] != tv[name]:
                lg, tg = group_rate(factor_list, name, lv[name]), group_rate(factor_list, name, tv[name])
                if lg and tg and lg["n"] >= MIN_GROUP and tg["n"] >= MIN_GROUP:
                    if (lg["interview_rate"] or 0) > (tg["interview_rate"] or 0):
                        reasons.append(
                            f"{name}: {lv[name]} versus {tv[name]}. Across your search, the first gets interviews "
                            f"{round(100 * lg['interview_rate'])}% of the time ({lg['n']} applications), "
                            f"the second {round(100 * (tg['interview_rate'] or 0))}% ({tg['n']})."
                        )
                else:
                    reasons.append(f"{name}: {lv[name]} versus {tv[name]} (too few applications to say whether it matters).")
        if leader["interviews"] and trailer["interviews"]:
            if leader["landed"]["good"] > trailer["landed"]["good"] or trailer["landed"]["weak"] > leader["landed"]["weak"]:
                reasons.append(f"Answers landed better at {leader['company']} ({landed(leader)}) than at {trailer['company']} ({landed(trailer)}).")
            if leader["feeling"] and trailer["feeling"] and leader["feeling"] != trailer["feeling"]:
                reasons.append(f"You rated the {leader['company']} interviews {leader['feeling']} of 5 and the {trailer['company']} ones {trailer['feeling']}.")
    return {
        "a": {"id": a["id"], "label": label(a), "status": a["status"]},
        "b": {"id": b["id"], "label": label(b), "status": b["status"]},
        "leader": None if leader is None else ("a" if leader is a else "b"),
        "rows": [{"label": r[0], "a": r[1], "b": r[2]} for r in rows],
        "reasons": reasons,
        "caveat": (
            "These are clues, not causes. Two applications can differ for reasons the tracker cannot see, such as "
            "the number of applicants, an internal candidate or a hiring freeze."
        ),
    }
