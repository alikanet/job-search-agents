"""
demo_data.py

Made-up applications and interviews for `dashboard.py --demo`, so you can see
what the dashboard does before your own tracker has much in it. Every company
and person is fictional, and the dates are relative to today.
"""

import os
import random
import re
from datetime import date, timedelta

import jobdb

STORIES = {
    1: "Warehouse system migration",
    2: "Rescuing a stalled CRM rollout",
    3: "Building a delivery office from scratch",
    4: "Pushing back on a go-live date",
    5: "Leading a remote team through a merger",
    6: "A vendor contract that went wrong",
    7: "Halving customer onboarding time",
    8: "Winning over a sceptical finance director",
}

# Each question with the stories that could answer it. Story 6 is the one
# that keeps landing badly, so the demo has something to advise on.
QUESTIONS = [
    ("Tell me about a project that was failing and what you did", [2, 1]),
    ("How do you handle a stakeholder who disagrees with your plan?", [8, 4]),
    ("Walk me through how you build a delivery plan", [1, 3]),
    ("Tell me about a time something did not go to plan", [6, 6, 4]),
    ("How do you prioritise competing requests?", [3, 7]),
    ("What would success look like in your first 90 days?", []),
    ("Describe a time you led without formal authority", [5, 8]),
    ("How do you manage risk on a large programme?", [1, 6]),
    ("Why do you want to work here?", []),
    ("Tell me about a process you improved", [7, 3]),
]

COMPANIES = [
    "Northwind Traders", "Tailspin Toys", "Woodgrove Bank", "Litware", "Adventure Works", "Proseware",
    "Wide World Importers", "Alpine Ski House", "Coho Winery", "Fourth Coffee", "Lamna Healthcare",
    "Trey Research", "Wingtip Toys", "Blue Yonder Airlines", "Humongous Insurance", "Lucerne Publishing",
]
ROLES = ["Programme Manager", "Senior Delivery Manager", "Implementation Lead", "Head of PMO", "Senior Project Manager"]
SOURCES = ["LinkedIn", "LinkedIn", "LinkedIn", "Referral", "Recruiter", "Recruiter", "Company site", "Company site", "Indeed"]
PEOPLE = [
    ("Priya Shah", "Head of Delivery"), ("Tom Becker", "Talent Partner"), ("Ana Ruiz", "COO"),
    ("Sam Okafor", "Engineering Director"), ("Lena Fischer", "Recruiter"), ("Marcus Lee", "VP Operations"),
    ("Hannah Cole", "PMO Lead"), ("Ravi Menon", "CFO"),
]


def slug(text):
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")


def day(d):
    return d.isoformat()


class Demo:
    def __init__(self, conn, today):
        self.conn, self.today, self.rng = conn, today, random.Random(7)

    def application(self, company, role, source, created, tailored=True, salary=False, reapplied_from=None):
        values = {
            "company_id": jobdb.get_or_create_company(self.conn, company, f"https://www.{slug(company).lower()}.example"),
            "role_title": role, "source": source, "created_on": day(created), "status": "drafting",
            "job_url": f"https://careers.example.com/{slug(company).lower()}/{self.rng.randint(100, 999)}",
            "job_spec": f"{role} at {company}. Lead delivery of a multi-site change programme, own the plan and "
                        f"the risks, and bring finance, operations and IT together around it.",
            "output_dir": f"cv-cover-letter-agent/output/{slug(company)}_{slug(role)}" if tailored else None,
            "reapplied_from": reapplied_from,
        }
        if salary:
            low = self.rng.choice([55, 60, 65, 70, 75]) * 1000
            values.update(salary_min=low, salary_max=low + 15000, salary_currency="GBP")
        app_id = jobdb.insert_row(self.conn, "applications", values)
        jobdb.log_status(self.conn, app_id, "drafting", day(created))
        return app_id

    def status(self, app_id, status, on):
        jobdb.set_status(self.conn, app_id, status, day(min(on, self.today)))

    def interview(self, app_id, company, stage, when, outcome=None, prep=True, debrief=True,
                  questions=True, feeling=None, people=(), good_odds=0.5):
        values = {
            "application_id": app_id, "stage": stage,
            "format": "video" if stage in ("recruiter_screen", "hiring_manager") else self.rng.choice(["video", "in person"]),
            "length_minutes": {"recruiter_screen": 30, "hiring_manager": 45, "panel": 60, "case_study": 90, "final": 60}[stage],
            "scheduled_at": f"{day(when)} {self.rng.choice(['09:30', '11:00', '14:00', '15:30'])}",
            "outcome": outcome, "feeling": feeling,
            "prep_sheet": f"interview-prep-agent/output/{slug(company)}_{stage}_{day(when)}.pdf" if prep else None,
            "debrief": f"interview-prep-agent/debriefs/{day(when)}_{slug(company)}_{stage}.md" if debrief else None,
        }
        interview_id = jobdb.insert_row(self.conn, "interviews", values)
        jobdb.add_interviewers(self.conn, interview_id, [f"{n}, {t}" for n, t in people])
        good = 0
        if questions:
            for text, stories in self.rng.sample(QUESTIONS, self.rng.choice([3, 4, 4, 5])):
                story = self.rng.choice(stories) if stories else None
                odds = 0.15 if story == 6 else good_odds
                roll = self.rng.random()
                landed = "good" if roll < odds else "ok" if roll < odds + 0.3 else "weak"
                good += landed == "good"
                jobdb.insert_row(self.conn, "interview_questions", {
                    "interview_id": interview_id, "question": text, "story_number": story, "landed": landed,
                    "on_prep_sheet": int(prep and self.rng.random() < 0.6),
                })
        return interview_id, good

    def scripted(self):
        """A few situations every demo should show, whatever the random draw."""
        t, d = self.today, lambda n: self.today - timedelta(days=n)
        hm = [PEOPLE[0], PEOPLE[1]]

        # An interview in two days with no prep sheet yet.
        a = self.application("Contoso Logistics", "Programme Manager", "Referral", d(30), salary=True)
        self.status(a, "applied", d(28))
        self.status(a, "interviewing", d(20))
        self.interview(a, "Contoso Logistics", "recruiter_screen", d(16), "progressed", feeling=4, people=[PEOPLE[1]], good_odds=0.7)
        self.interview(a, "Contoso Logistics", "hiring_manager", t + timedelta(days=2), prep=False, debrief=False,
                       questions=False, people=hm)

        # An interview two days ago that has not been debriefed.
        b = self.application("Fabrikam Retail", "Senior Delivery Manager", "Recruiter", d(26))
        self.status(b, "applied", d(25))
        self.status(b, "interviewing", d(9))
        self.interview(b, "Fabrikam Retail", "recruiter_screen", d(2), debrief=False, questions=False, people=[PEOPLE[4]])

        # An offer after a full set of rounds.
        c = self.application("Graphic Design Institute", "Head of PMO", "Referral", d(70), salary=True)
        self.status(c, "applied", d(69))
        self.status(c, "interviewing", d(60))
        self.interview(c, "Graphic Design Institute", "recruiter_screen", d(56), "progressed", feeling=4, people=[PEOPLE[1]], good_odds=0.7)
        self.interview(c, "Graphic Design Institute", "hiring_manager", d(45), "progressed", feeling=5, people=[PEOPLE[6]], good_odds=0.7)
        self.interview(c, "Graphic Design Institute", "case_study", d(30), "progressed", feeling=4, people=[PEOPLE[6], PEOPLE[3]], good_odds=0.7)
        self.interview(c, "Graphic Design Institute", "final", d(12), "offer", feeling=5, people=[PEOPLE[2], PEOPLE[7]], good_odds=0.7)
        self.status(c, "offer", d(6))

        # Waiting on a reply long enough to follow up.
        e = self.application("Margie's Travel", "Implementation Lead", "LinkedIn", d(13), tailored=False)
        self.status(e, "applied", d(11))

        # A draft that has sat for a week.
        self.application("Trey Research", "Senior Project Manager", "Company site", d(7))

        # Rejected, then reapplied for the same role.
        f = self.application("Coho Vineyard", "Implementation Lead", "LinkedIn", d(95), tailored=False)
        self.status(f, "applied", d(94))
        self.status(f, "rejected", d(80))
        g = self.application("Coho Vineyard", "Implementation Lead", "Referral", d(6), reapplied_from=f)
        self.status(g, "applied", d(5))

    def random_application(self, company, created):
        rng = self.rng
        source = rng.choice(SOURCES)
        tailored = rng.random() < 0.6
        a = self.application(company, rng.choice(ROLES), source, created, tailored=tailored, salary=rng.random() < 0.5)
        sent = min(created + timedelta(days=rng.choice([0, 0, 1, 1, 2, 3, 5, 8])), self.today)
        self.status(a, "applied", sent)

        reply_odds = 0.18 + 0.4 * (source == "Referral") + 0.2 * tailored + 0.08 * (source == "Recruiter") - 0.08 * (source == "Indeed")
        reply = sent + timedelta(days=rng.randint(3, 16))
        if rng.random() > reply_odds or reply >= self.today:
            if (self.today - sent).days > 40 and rng.random() < 0.7:
                self.status(a, "ghosted", sent + timedelta(days=35))
            return
        if rng.random() < 0.3:
            self.status(a, "rejected", reply)
            return

        self.status(a, "interviewing", reply)
        when = reply + timedelta(days=rng.randint(2, 6))
        hiring_manager = rng.choice(PEOPLE)
        for stage in ["recruiter_screen", "hiring_manager", rng.choice(["panel", "case_study"]), "final"]:
            if when >= self.today:
                return
            people = [PEOPLE[1]] if stage == "recruiter_screen" else [hiring_manager] + ([rng.choice(PEOPLE)] if stage != "hiring_manager" else [])
            decided = when + timedelta(days=rng.randint(2, 7))
            if decided >= self.today:
                self.interview(a, company, stage, when, "pending", feeling=rng.choice([3, 4]), people=people)
                return
            good_odds = 0.55 if tailored else 0.4
            interview_id, good = self.interview(a, company, stage, when, people=people, good_odds=good_odds)
            passed = rng.random() < 0.35 + 0.1 * good + 0.1 * (source == "Referral")
            outcome = ("offer" if stage == "final" else "progressed") if passed else "rejected"
            jobdb.update_row(self.conn, "interviews", interview_id, {
                "outcome": outcome, "feeling": rng.choice([3, 4, 4, 5]) if passed else rng.choice([2, 3, 3, 4]),
            })
            if outcome != "progressed":
                self.status(a, "offer" if outcome == "offer" else "rejected", decided)
                return
            when = decided + timedelta(days=rng.randint(3, 8))


def seed(db_path, folder):
    """Fill a new database with the demo search and write a matching story
    bank. Returns the story bank's path."""
    today = date.today()
    conn = jobdb.connect(db_path)
    demo = Demo(conn, today)
    with conn:
        demo.scripted()
        for company, offset in zip(COMPANIES, sorted(demo.rng.sample(range(10, 110), len(COMPANIES)), reverse=True)):
            demo.random_application(company, today - timedelta(days=offset))
    conn.close()
    story_bank = os.path.join(folder, "story_bank.md")
    with open(story_bank, "w", encoding="utf-8") as f:
        f.write("# Story Bank (demo)\n\n" + "".join(f"## {n}. {title}\n\n" for n, title in STORIES.items()))
    return story_bank
