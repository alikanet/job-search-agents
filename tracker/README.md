# Job search tracker

A small database of every application and interview: where you applied, the status, who interviewed you, what they asked, which stories you told and how they landed. Both agents use it, and you can use it yourself from the terminal.

It is one file, `tracker/job_search.db`, created automatically the first time anything uses it. It needs only Python, with no extra packages. It stays on your computer and is in `.gitignore`, because it holds interviewers' names and the job specs you applied to. When an agent reads it, what it reads is sent to Claude like the rest of your files.

The copy-and-paste prompts in `prompts/` do not use it.

## How it fills itself in

| When | What is recorded | By |
|---|---|---|
| The CV agent saves your documents | The application, with the job spec and where the drafts are | `tailor_application.py` |
| You send the application | Status `applied` and the date | You (see below) |
| You run `/prep` | The interview: stage, format, length, interviewers and the prep sheet | The `/prep` skill |
| You run `/debrief` after the interview | Questions asked, stories used, how they landed, how it felt, the outcome | The `/debrief` skill |

`/prep` uses it to avoid telling an interviewer a story they have already heard.

## Using it yourself

Open a terminal in the repo folder. On Mac or Linux, use `python3` instead of `python`.

```
python tracker/jobdb.py list                          all applications, newest first
python tracker/jobdb.py list --status interviewing    only those at one status
python tracker/jobdb.py show 3                        one application with its interviews
python tracker/jobdb.py show --company "Example"      everything at one company
python tracker/jobdb.py status 3 applied              mark application 3 as sent today
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
