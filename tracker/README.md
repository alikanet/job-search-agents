# Job search tracker

A small database of every application and interview: where you applied, the status, who interviewed you, what they asked, which stories you told and how they landed. Both agents use it, and you can use it yourself from the terminal.

It is one file, `tracker/job_search.db`, created automatically the first time anything uses it. It needs only Python, with no extra packages. It stays on your computer and is in `.gitignore`, because it holds interviewers' names and the job specs you applied to. When an agent reads it, what it reads is sent to Claude like the rest of your files.

The copy-and-paste prompts in `prompts/` do not use it.

## The dashboard

The easiest way to see and change everything is the dashboard, which opens in your web browser. Open the `start` folder in the repo and double-click **Dashboard (Windows).bat** or **Dashboard (Mac).command**, or the **Dashboard demo** version to look around with made-up data first. [Use the dashboard](../docs/05-use-the-dashboard.md) is a step-by-step guide for first-timers.

From a terminal in the repo folder instead (use `python3` on Mac or Linux):

```
python tracker/dashboard.py
python tracker/dashboard.py --demo
```

Leave the window open while you use it, and close it (or press Ctrl+C) to stop. It needs only Python and works without an internet connection.

| Page | What it gives you |
|---|---|
| Today | What to do next, most urgent first: interviews to prepare for or debrief, applications to follow up or give up on, drafts sitting unsent, stories that keep landing badly. Plus upcoming interviews, your key numbers and recent changes. |
| Applications | Every application as a table or a board. Search, filter by status, change any status (one at a time, several at once, or by dragging a card), and add new ones. |
| An application's page | Its status and history, how it compares with the rest of your search, its interviews (with interviewers, questions, stories used and outcomes, all editable), links to your CV, cover letter, prep sheets and debriefs, and buttons to mark it sent, reapply, edit or delete. |
| What's working | The funnel from sent to offer, which kinds of application get more interviews (source, tailored CV, advertised salary, how quickly you sent it), reply times, pass rates by interview stage, which stories land, and which questions you are asked most. |
| Compare | Pick two applications and see why one got further, with how much each difference has mattered across your whole search. |
| Help | What the statuses and numbers mean and where each piece of advice comes from. |

Patterns are only reported once each group has at least 3 sent applications, and small numbers are labelled as early signals, so a lucky week is not presented as a rule.

The dashboard only listens on your own computer, and each run uses a fresh secret that the page sends with every request, so other websites open in your browser cannot read or change your tracker. **Download as spreadsheet (CSV)** in the sidebar exports every application.

## How it fills itself in

| When | What is recorded | By |
|---|---|---|
| The CV agent saves your documents | The application, with the job spec and where the drafts are | `tailor_application.py` |
| You send the application | Status `applied` and the date | You (see below) |
| You run `/prep` | The interview: stage, format, length, interviewers and the prep sheet | The `/prep` skill |
| You run `/debrief` after the interview | Questions asked, stories used, how they landed, how it felt, the outcome | The `/debrief` skill |

`/prep` uses it to avoid telling an interviewer a story they have already heard.

## Using it from the terminal

Everything the dashboard does is also available as commands, which is also how Claude Code reads and updates the tracker. Open a terminal in the repo folder. On Mac or Linux, use `python3` instead of `python`.

```
python tracker/jobdb.py list                          all applications, newest first
python tracker/jobdb.py list --status interviewing    only those at one status
python tracker/jobdb.py show 3                        one application with its interviews
python tracker/jobdb.py show --company "Example"      everything at one company
python tracker/jobdb.py status 3 applied              mark application 3 as sent today
python tracker/jobdb.py reapply 3                     start a new application for the same role
python tracker/jobdb.py delete 3 --yes                delete application 3 and its interviews
python tracker/jobdb.py stories-told --company "Example"
python tracker/jobdb.py --help                        every command
```

Statuses are `drafting`, `applied`, `interviewing`, `offer`, `rejected`, `withdrawn` and `ghosted`. Adding an interview moves a `drafting` or `applied` application to `interviewing`. An interview outcome of `offer`, `rejected` or `withdrew` sets the application's status to match.

To record an application you made without the CV agent:

```
python tracker/jobdb.py add-application --company "Example Co" --role "Programme Manager" --status applied --job-url https://www.examplecompany.com/jobs/123
```

For anything else, `sql` runs a read-only query. For example, how many applications are at each status:

```
python tracker/jobdb.py sql "SELECT status, COUNT(*) AS n FROM applications GROUP BY status"
```

The tables are described in [`schema.sql`](schema.sql).

## Backing up

Copy `job_search.db` somewhere safe now and then. Deleting it starts the tracker afresh. Your documents, prep sheets and debrief files are separate files and are not affected.
