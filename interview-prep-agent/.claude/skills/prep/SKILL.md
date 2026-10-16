---
name: prep
description: Prepare the user's interview prep cheat sheet as a 1 to 2 page PDF. Use when they ask to prep for an interview and give a company URL, a job spec, and the interview stage, type and length.
---

# Interview prep

Details for this interview: $ARGUMENTS

First read the knowledge files listed in CLAUDE.md, including any relevant files in `debriefs/`. Then follow the steps below and save the PDF to `output/`.

## Inputs

The user will give you:

1. Company URL
2. Job spec (pasted text or a URL)
3. Interview stage (e.g. recruiter screen, hiring manager, panel, case study, final round)
4. Interview type and length (e.g. video, in person, 30 minutes, 90 minutes)
5. Optional: their salary target, as a single line

If 1 to 4 are missing from the details above, ask for them before doing any work. Do not guess the stage. Do not ask for anything else.

---

## Research (web search)

Beyond the company URL and job spec, search for:

- Recent news (last 12 months), funding, acquisitions, leadership changes
- Main competitors and how the company positions itself against them
- Employee and customer reviews (treat as directional only, never quote them as fact)
- Salary benchmarks for the role, level and location

Rules:

- Prefer primary sources (company site, press releases, filings) over aggregators.
- Any company fact or salary figure you cannot verify from a reasonable source must be marked **[unverified]** on the sheet. Do not omit it and do not stop to ask.
- Do not put anything on the sheet that you have not sourced or that is not in the knowledge folder.
- Do not research or list interviewers unless the user supplies names.
- If a job spec URL will not load with normal fetching, use the Playwright browser tools to open the page and read it.

---

## Output: the cheat sheet

**Format:** PDF, maximum 2 pages, saved to `output/` as `[Company]_[Role]_[Stage]_[YYYY-MM-DD].pdf`.

**Look:** clean white background, matching the user's CV. Calibri (or the closest available metric-compatible font), body text about 9.5pt in near black (#222222), name and section headings in navy (#1F3864) in capitals with a thin rule, plain single column, no gradients, icons or decorative graphics. Print friendly. Use A4 or US Letter according to where the user will print it [SET IN CLAUDE.md]. Keep the body no smaller than 9pt.

**How to build it:** Write the sheet as HTML or use a Python PDF library, whichever renders reliably. If a needed tool is not installed, tell the user what to install rather than switching to a worse route. After creating the PDF, check the page count, convert each page to an image and look at it to confirm nothing is cut off, overlapping or too small to read.

**Header:** company, role, stage, type and length, date.

### Section order (fixed)

1. **Story matching**
2. **Likely questions with scripted openers**
3. **Role and company snapshot**
4. **Salary benchmarks**
5. **Questions to ask them**

### Section rules

**1. Story matching**
- Exactly 3 stories from the story bank and CV.
- Each story is mapped to a specific requirement in the job spec (quote or closely paraphrase the requirement).
- Each has a headline metric from the fact sheet.
- One or two lines per story: the requirement, the story, the result. Add a short reminder of the story bank entry to open with.
- Choose the three that best cover the role's most important requirements. Do not repeat the same employer three times unless the spec demands it.

**2. Likely questions with scripted openers**
- 5 to 6 questions the interviewer is most likely to ask at this stage, based on the job spec, the company and the stage.
- For each: the question, then a short scripted opener (2 to 3 sentences) the user can use to start their answer, plus a prompt for which story or proof point to follow with.
- If a question about leaving the last role is likely to come up, include it and use only the wording in `exit_answer.md`, including its follow-up line if pressed. Do not paraphrase, improve or add a pivot to it.
- Openers follow the voice rules in CLAUDE.md.

**3. Role and company snapshot**
- Bullets only. What the company does, size and stage, recent news, competitors, and what the role is really for (read between the lines of the job spec).
- End with one line on how the role fits the user's direction, worded to mirror the job spec's own language.
- Include anything the user should be able to say back to show they have done their homework, and the company mission or achievement they can reference for "why us".

**4. Salary benchmarks**
- Market range for the role, level and location, with source and date for each figure.
- If the user supplied a target, set the benchmarks against it in one line. If not, show benchmarks only.
- Mark thin or conflicting data as [unverified].
- If CLAUDE.md records a private salary floor, show in one line where the benchmark and any advertised range sit against it. If the advertised or benchmark range is below the floor, flag that clearly at the top of the section.
- Add one suggested spoken answer to "what are your salary expectations?" anchored on the benchmark range for the role (aim at the middle to upper part, never at the floor), phrased as a range and open to discussion.
- The salary rule in the CV and cover letter style guides applies to those documents only.

**5. Questions to ask them**
- Tailored to the stage. For each question, add a one line reason for asking it.
- Number depends on stage and length: fewer for a short recruiter call, more for hiring manager and final rounds.
- Use the standing questions in `story_bank.md` only where they fit the role.

### Reweighting by stage and length

The section order never changes, but emphasis and space do.

| Stage | Emphasis |
|---|---|
| Recruiter screen | More space to salary benchmarks, logistics (use the standard screening answers in CLAUDE.md) and the 60 second "tell me about yourself" from `story_bank.md`. Shorter story lines. Fewer questions to ask. |
| Hiring manager | Most space to story matching and likely questions. Questions to ask focus on team, delivery challenges and success at six months. |
| Panel | Map stories to different stakeholder concerns. Questions to ask suited to each function present. |
| Case study or presentation | Add a short "approach and structure" prompt inside the likely questions section. Keep the rest tight. |
| Final round or exec | More space to company snapshot, strategy and commercial awareness. Questions to ask are strategic. |

For interviews of 30 minutes or less, cut to the highest value content. For 90 minutes or more, the sheet can use its full two pages.

If the sheet exceeds 2 pages, cut content, never shrink text below a readable size.

---

## Before you finish

1. Check every number against the fact sheet in CLAUDE.md.
2. Check every company fact has a source or is marked [unverified].
3. Check openers contain no em dashes or en dashes, no hedging language, and none of the items CLAUDE.md says to keep out of openers.
4. Check the PDF is 2 pages or fewer and readable at normal print size. If a salary floor exists, check the salary section flags anything below it and that the floor appears only as a private comparison note, never inside the suggested spoken answer.
5. Reply with the file path, a one line list of anything marked [unverified], and any weak story fits from the honesty rules in CLAUDE.md.
