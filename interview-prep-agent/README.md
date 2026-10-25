# Interview Prep Agent

A Claude Code project that produces a 1 to 2 page PDF cheat sheet for a specific interview, tailored to the role, the company and the interview stage. Each sheet has: three matched stories from your own story bank, likely questions with scripted openers, a company snapshot, salary benchmarks, and questions to ask.

It runs in Claude Code. If you want to use ChatGPT, Gemini or another AI instead, use the copy-and-paste prompt in [`../prompts/interview-prep-agent.md`](../prompts/interview-prep-agent.md) (see [Use any AI chat](../docs/04-use-any-ai-chat.md)).

> **This is a drafting tool.** Check every figure and claim before you rely on it in an interview.

## Before you start

You need to have done these (see the main [README](../README.md)):

1. Installed Claude Code and logged in: [install guide](../docs/01-install-prerequisites.md)
2. Built your career history and style guides in `../cv-cover-letter-agent/knowledge/`: [career history guide](../docs/02-build-your-career-history.md) and [voice and style guide](../docs/03-set-your-voice-and-style.md)

**This agent has no data of its own.** It works only from the files you create below. If they are thin, the sheets will be generic.

## Step 1: Create your files

Open a terminal in the repo folder and run the commands for your system. They create your personal files from the templates.

**Windows (PowerShell):**

```powershell
cd interview-prep-agent
Copy-Item CLAUDE.example.md CLAUDE.md
Copy-Item story_bank.example.md story_bank.md
Copy-Item exit_answer.example.md exit_answer.md
Copy-Item .mcp.example.json .mcp.json
New-Item -ItemType Directory -Force knowledge, debriefs, output
Copy-Item ..\cv-cover-letter-agent\knowledge\cv_style_guide.md knowledge\cv_style_guide.md
Copy-Item ..\cv-cover-letter-agent\knowledge\cover_letter_style_guide.md knowledge\cover_letter_style_guide.md
```

**Mac or Linux:**

```bash
cd interview-prep-agent
cp CLAUDE.example.md CLAUDE.md
cp story_bank.example.md story_bank.md
cp exit_answer.example.md exit_answer.md
cp .mcp.example.json .mcp.json
mkdir -p knowledge debriefs output
cp ../cv-cover-letter-agent/knowledge/cv_style_guide.md knowledge/cv_style_guide.md
cp ../cv-cover-letter-agent/knowledge/cover_letter_style_guide.md knowledge/cover_letter_style_guide.md
```

(The last two commands assume you have already created and finished your own style guides in the CV agent folder. If you have not, do that first.)

| File | What it is |
|---|---|
| `CLAUDE.md` | The agent's standing instructions: your roles and dates, key numbers, experience framing, screening answers, voice rules, honesty rules and known weak spots. Fill in every `[PLACEHOLDER]`. |
| `story_bank.md` | Your achievements written as stories (situation, action, result), plus an index of which story answers which question. Build it with the prompt in the [career history guide](../docs/02-build-your-career-history.md). |
| `exit_answer.md` | Optional. Your agreed wording if you will be asked why you left your last role. Delete the file, and its row in `CLAUDE.md`, if you do not need it. |
| `.mcp.json` | Optional. Registers a Playwright browser tool so the agent can open job pages it cannot otherwise read. Needs Node.js. Delete it if you do not want it. |
| `knowledge/cv_master.md` | **You must create this.** A plain text copy of your current CV. It is the source of truth for dates and headline achievements. |
| `knowledge/cv_style_guide.md` and `knowledge/cover_letter_style_guide.md` | Your finished guides, copied by the commands above. |
| `debriefs/` | Empty folder. After each interview, save a filled-in copy of `debrief_template.md` here. The agent reads these before every new prep. |
| `output/` | Where finished PDFs are saved. |

To create `knowledge/cv_master.md`, paste your career history into any AI chat and ask: *"Turn this into a one-page CV in plain text, using only these facts, and do not invent anything."* Check it carefully, then save it as `knowledge/cv_master.md`.

When you have filled in `CLAUDE.md`, delete `(TEMPLATE)` from its title. Then start Claude Code (Step 2) and ask:

```
Check CLAUDE.md and story_bank.md for any remaining [PLACEHOLDER], [TO ADD] or template text, and list what I still need to fill in.
```

## Step 2: Start Claude Code in this folder

In the terminal, inside the `interview-prep-agent` folder:

```
claude
```

Type `/context` and check that `CLAUDE.md` appears in the list. If it does not, you are in the wrong folder.

## Step 3: Prepare for an interview

Type `/prep` followed by the company website, the job spec, and the stage, format and length of the interview. Copy one of these and replace the details.

**If you saved the job spec as a text file in this folder (called `job_spec.txt`):**

```
/prep https://www.examplecompany.com job_spec.txt hiring manager interview, video, 45 minutes
```

**If you want to paste the job spec:**

```
/prep https://www.examplecompany.com Hiring manager interview, video, 45 minutes. Job spec: [paste the full job spec here]
```

**If you have a salary target (optional):** add `Salary target: £70,000.` at the end.

Interview stages the agent understands: recruiter screen, hiring manager, panel, case study or presentation, final or executive round. The sheet changes emphasis for each.

The agent will research the company, then write a PDF into `output/` named like `Company_Role_Stage_2026-01-15.pdf`. If it asks to install a tool to make PDFs, allow it. It will tell you which facts it could not verify (marked `[unverified]`) and which story fits are weak.

It also records the interview in the [job search tracker](../tracker/README.md) and checks which stories this company's interviewers have already heard. The first time, Claude Code asks permission to run `jobdb.py`. Allow it.

## Step 4: After the interview

Within 24 hours, while it is fresh, start Claude Code in this folder and type `/debrief` followed by rough notes: who interviewed you, what they asked, which stories you used, how each landed, and what happens next. For example:

```
/debrief ExampleCo hiring manager interview on 2026-01-15 with Jane Smith (Head of Delivery). Asked about a failing project, I used the warehouse story and it landed well. Asked about a stakeholder conflict, my answer was weak. Overall 4 out of 5. Next round expected in a week.
```

The agent writes a debrief file into `debriefs/` following `debrief_template.md`, and records the questions, stories, interviewers and how it felt in the tracker. If you would rather fill in the template yourself, copy `debrief_template.md` into `debriefs/`, rename it with the date, company and stage (for example `2026-01-15_ExampleCo_HiringManager.md`), fill it in, then run `/debrief debriefs/2026-01-15_ExampleCo_HiringManager.md` to record it.

When you hear the result, tell Claude Code (for example "ExampleCo offered me the job, update the tracker"), or run `python ../tracker/jobdb.py update-interview <interview number> --outcome offer` yourself (`progressed`, `rejected` and `withdrew` also work).

`/prep` reads every debrief for the same company and all from the last 90 days, and checks the tracker, so it can avoid repeating a story with the same interviewer and follow up on feedback.

## Keeping it current

When your CV changes, update `knowledge/cv_master.md`, the fact sheet in `CLAUDE.md`, and the numbers in `story_bank.md`.

## Troubleshooting

- **`/prep` not recognised:** you are not inside the `interview-prep-agent` folder. Close Claude Code, `cd` into the folder, and run `claude` again.
- **The agent says a knowledge file is missing:** check `knowledge/cv_master.md`, `knowledge/cv_style_guide.md` and `knowledge/cover_letter_style_guide.md` exist.
- **The agent cannot read a job page:** save the job spec as a text file, or paste it into the command.
- **Playwright errors:** install Node.js (see the install guide), or delete `.mcp.json`.
- **The agent cannot run `jobdb.py`:** install Python (see the install guide). Prep sheets still work without the tracker; the agent just cannot record interviews or check which stories an interviewer has heard.
