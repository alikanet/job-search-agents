-- Job search database: applications, interviews, interviewers and the
-- questions you were asked. jobdb.py runs this file every time it opens the
-- database, so every statement must be safe to run again.
--
-- Career facts and stories stay in the Markdown knowledge files. This
-- database only records what happened, and points at files by their path
-- relative to the repo folder.

CREATE TABLE IF NOT EXISTS companies (
  id       INTEGER PRIMARY KEY,
  name     TEXT NOT NULL UNIQUE COLLATE NOCASE,
  website  TEXT
);

CREATE TABLE IF NOT EXISTS applications (
  id              INTEGER PRIMARY KEY,
  company_id      INTEGER NOT NULL REFERENCES companies(id),
  role_title      TEXT NOT NULL COLLATE NOCASE,
  job_url         TEXT,
  job_spec        TEXT,             -- full text, since postings disappear
  source          TEXT,             -- LinkedIn, referral, recruiter
  status          TEXT NOT NULL DEFAULT 'drafting' CHECK (status IN
                  ('drafting', 'applied', 'interviewing', 'offer', 'rejected', 'withdrawn', 'ghosted')),
  created_on      TEXT NOT NULL DEFAULT (date('now')),
  applied_on      TEXT,             -- YYYY-MM-DD
  salary_min      INTEGER,          -- advertised range, not your private floor
  salary_max      INTEGER,
  salary_currency TEXT,
  output_dir      TEXT,             -- where the CV agent saved the drafts
  notes           TEXT,
  reapplied_from  INTEGER REFERENCES applications(id) ON DELETE SET NULL
);

-- Every status change, with the date it happened, for the time-based stats
-- in the dashboard (how long replies take, how long things sit).
CREATE TABLE IF NOT EXISTS status_history (
  id              INTEGER PRIMARY KEY,
  application_id  INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
  status          TEXT NOT NULL,
  changed_on      TEXT NOT NULL     -- YYYY-MM-DD
);

CREATE TABLE IF NOT EXISTS interviews (
  id              INTEGER PRIMARY KEY,
  application_id  INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
  stage           TEXT NOT NULL CHECK (stage IN
                  ('recruiter_screen', 'hiring_manager', 'panel', 'case_study', 'final')),
  format          TEXT,             -- video, in person, phone
  length_minutes  INTEGER,
  scheduled_at    TEXT,             -- YYYY-MM-DD or YYYY-MM-DD HH:MM
  prep_sheet      TEXT,             -- path to the prep PDF
  debrief         TEXT,             -- path to the debrief .md
  feeling         INTEGER CHECK (feeling BETWEEN 1 AND 5),
  outcome         TEXT CHECK (outcome IN ('pending', 'progressed', 'rejected', 'withdrew', 'offer'))
);

CREATE TABLE IF NOT EXISTS interviewers (
  id          INTEGER PRIMARY KEY,
  company_id  INTEGER NOT NULL REFERENCES companies(id),
  name        TEXT NOT NULL COLLATE NOCASE,
  title       TEXT,
  UNIQUE (company_id, name)
);

CREATE TABLE IF NOT EXISTS interview_interviewers (
  interview_id   INTEGER NOT NULL REFERENCES interviews(id) ON DELETE CASCADE,
  interviewer_id INTEGER NOT NULL REFERENCES interviewers(id),
  PRIMARY KEY (interview_id, interviewer_id)
);

CREATE TABLE IF NOT EXISTS interview_questions (
  id             INTEGER PRIMARY KEY,
  interview_id   INTEGER NOT NULL REFERENCES interviews(id) ON DELETE CASCADE,
  question       TEXT NOT NULL,
  on_prep_sheet  INTEGER NOT NULL DEFAULT 0,  -- 1 if the prep sheet predicted it
  story_number   INTEGER,                     -- story number in story_bank.md
  landed         TEXT CHECK (landed IN ('good', 'ok', 'weak'))
);
