---
name: debrief
description: Record how an interview went. Use after an interview when the user pastes rough notes or points to a filled-in debrief file. Writes the debrief into debriefs/ and records the questions, stories used, interviewers and outcome in the job search tracker.
---

# Interview debrief

Notes or file from the user: $ARGUMENTS

Below, `jobdb.py` is short for `python ../tracker/jobdb.py` run from this folder (`python3` on Mac or Linux).

## 1. Find the interview

Run `jobdb.py show --company "<Company>"` and find the interview these notes are about. If it is unclear which one, ask. If there is no matching interview, create the application and interview as step 3 and 4 of the Tracking section in `.claude/skills/prep/SKILL.md` describe.

## 2. Write the debrief file

- If the user pointed to a file in `debriefs/`, read it and do not change it.
- Otherwise write `debriefs/YYYY-MM-DD_Company_Stage.md` (the interview date, for example `debriefs/2026-10-08_Acme_HiringManager.md`), following the sections of `debrief_template.md`.
- Use only what the user told you. Leave a section empty when the notes do not cover it. Never invent questions, answers, reactions or names.

## 3. Record it in the tracker

- Run `jobdb.py update-interview <interview number> --debrief debriefs/<file name>.md`, adding `--feeling <1 to 5>` and `--outcome <pending|progressed|rejected|withdrew|offer>` when the notes give them, and one `--interviewer "Name, Title"` for each interviewer not already recorded. An outcome of offer, rejected or withdrew also updates the application's status.
- For each question asked, run `jobdb.py add-question <interview number> --question "<question>"`, adding `--story <number>` for the story from `story_bank.md` used in the answer, `--landed <good|ok|weak>` when known, and `--on-sheet` if the question was on the prep sheet.
- Match stories to their numbers in `story_bank.md` by content. If you cannot tell which story was used, leave `--story` off and say so.
- If `show` already lists questions for this interview, do not add them again.

## 4. Reply

Give the debrief file path, a one line summary of what was recorded, and any detail from the notes worth adding to `story_bank.md` (section 12 of the template). Do not edit `story_bank.md` yourself.
