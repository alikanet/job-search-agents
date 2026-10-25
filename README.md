# Job Search Agents

Two AI agents that help you apply for jobs and prepare for interviews. Download them, fill in your own career details, and run them on your own computer.

| Agent | What it does | Runs with |
|---|---|---|
| **CV and cover letter agent** (`cv-cover-letter-agent/`) | Reads a job spec, researches the company, and drafts a tailored CV and one-page cover letter as Word documents | Python script (uses Claude) |
| **Interview prep agent** (`interview-prep-agent/`) | Produces a 1 to 2 page PDF cheat sheet for a specific interview: matched stories, likely questions, company snapshot, salary benchmarks, questions to ask | Claude Code |

**Not using Claude?** You can run both agents in ChatGPT, Gemini, Copilot or any other AI chat using the copy-and-paste prompts in `prompts/`. See [Use any AI chat](docs/04-use-any-ai-chat.md).

> **Important: this repo contains no career data.** It ships templates only. The agents are only as good as the information you give them, so **you must create your own knowledge files** (your career history, your story bank, your voice and style rules). Steps 3 to 5 below walk you through this, including how to get an AI to interview you to build them.

> **These are drafting tools.** You are responsible for checking every claim, figure and date before you send an application or walk into an interview. Never let an AI put anything on your CV that you cannot defend in person.

---

## New to this? Read this first

You do not need to be technical. Every step has copy-and-paste instructions for Windows and Mac, the install guide assumes you have never used a terminal, and once you are set up you start everything by double-clicking a file. Unfamiliar words are explained in [Words you will see](#words-you-will-see) at the end.

**What you need**

- A Windows or Mac computer.
- About an hour for the first setup. Most of it is answering questions while an AI builds your career history with you.
- For the full route, a paid Claude plan (Pro or above), which Claude Code needs. For the simple route, any AI chat, including free ones.

**Pick your route**

| | Simple route | Full route |
|---|---|---|
| What you install | Nothing (or just Python, if you want the dashboard) | Python and Claude Code |
| How it works | You paste a prompt and your files into ChatGPT, Gemini, Claude or another chat, then copy the result into Word | The agents research the company, write the Word documents and PDFs for you, and keep track of every application and interview |
| Start with | [Use any AI chat](docs/04-use-any-ai-chat.md), after Steps 1 and 3 to 5 below | Step 1 below |

If you are not sure, start with the simple route. Both use the same files, so you can switch later.

---

## Quick start

### Step 1: Download this repo

Click the green **Code** button at the top of this page, then **Download ZIP**, and unzip it somewhere easy to find (for example your Documents folder). The folder will be called `job-search-agents-main`. You can rename it if you like; the guides work whatever it is called. If you use Git, you can clone it instead.

### Step 2: Install what you need

Follow [Install the prerequisites](docs/01-install-prerequisites.md). It covers Python, Claude Code and the Python packages, for Windows and Mac, with copy-and-paste commands. If you plan to use ChatGPT or another chat tool instead, you can skip this step.

### Step 3: Create your own files from the templates

Every file ending in `.example` is a template. Copy it, remove `.example` from the name, and fill it in. Open a terminal in the repo folder (instructions in the install guide), then run the commands for your system.

**Windows (PowerShell):**

```powershell
cd cv-cover-letter-agent
Copy-Item profile.example.json profile.json
Copy-Item knowledge\cv_style_guide.example.md knowledge\cv_style_guide.md
Copy-Item knowledge\cover_letter_style_guide.example.md knowledge\cover_letter_style_guide.md
cd ..
```

**Mac or Linux (Terminal):**

```bash
cd cv-cover-letter-agent
cp profile.example.json profile.json
cp knowledge/cv_style_guide.example.md knowledge/cv_style_guide.md
cp knowledge/cover_letter_style_guide.example.md knowledge/cover_letter_style_guide.md
cd ..
```

Then open `profile.json` in any text editor and replace John Smith's details with yours.

### Step 4: Build your career history with AI

Your career history is the most important file. It is the only source of facts the agents are allowed to use. Follow [Build your career history](docs/02-build-your-career-history.md): you paste a prompt into any AI chat, and it interviews you one question at a time, then writes up your history in the right format.

### Step 5: Set your voice and style

The templates come with default choices for tone, sentence style, punctuation and cover letter structure. They will not suit everyone. Follow [Set your voice and style](docs/03-set-your-voice-and-style.md) to review and change every one of them before you generate anything.

### Step 6: Run an agent

The easiest way: open the **start** folder inside the repo and double-click **CV and cover letter agent** or **Interview prep agent** (the Windows or Mac version). The first time, your computer may warn you about a file downloaded from the internet; [here is what to do](docs/05-use-the-dashboard.md#open-the-dashboard).

Each agent's README explains what it will ask you and what you get back, with the commands if you prefer typing them:

- [CV and cover letter agent](cv-cover-letter-agent/README.md)
- [Interview prep agent](interview-prep-agent/README.md)

### Step 7: Follow your search in the dashboard

In the **start** folder, double-click **Dashboard demo** to look around with made-up data, then **Dashboard** for your own search. It opens in your web browser and shows what to do next, where every application stands, and what is working. [Use the dashboard](docs/05-use-the-dashboard.md) walks you through it.

---

## What to do for each job

1. **Find a job** you want and copy the full job description.
2. **Make your CV and cover letter.** Run the CV and cover letter agent, paste in the job description, answer its questions, and type `approved` when you are happy. It saves two Word documents and adds the application to your tracker as a draft.
3. **Check and send.** Read every line, fix anything that is not right, and send your application. Then open the dashboard and click **Mark as sent today** on that application.
4. **Prepare for the interview.** When an interview is booked, run the interview prep agent and type `/prep` with the company website, the job description and the type of interview. You get a one or two page cheat sheet as a PDF.
5. **Debrief.** After the interview, type `/debrief` in the interview prep agent with rough notes on what they asked and how it went. It saves your notes and records them in the tracker.
6. **Record the result** in the dashboard when you hear back.
7. **Check the Today page** in the dashboard every day or two. It tells you who to follow up with, what to prepare next, and which drafts you have not sent.

## If you get stuck

- Each guide ends with common problems and fixes: [installing](docs/01-install-prerequisites.md#if-something-goes-wrong), the [CV agent](cv-cover-letter-agent/README.md#troubleshooting), the [interview prep agent](interview-prep-agent/README.md#troubleshooting) and the [dashboard](docs/05-use-the-dashboard.md#if-something-goes-wrong).
- Copy the exact error message into any AI chat, say whether you use Windows or Mac, and ask what it means and what to do.

---

## What is in this repo

```
README.md                       You are here
start/                          Double-click files that start the agents and the dashboard (Windows and Mac)
docs/
  01-install-prerequisites.md   Install Python, Claude Code and packages (Windows and Mac)
  02-build-your-career-history.md   Use AI to interview you and build your career history
  03-set-your-voice-and-style.md    Review tone, sentence style, punctuation, cover letter structure
  04-use-any-ai-chat.md         Run the agents in ChatGPT, Gemini, Copilot or any chat tool
  05-use-the-dashboard.md       Open and use the dashboard, step by step
prompts/                        Copy-and-paste prompts that work in any AI chat
cv-cover-letter-agent/          The CV and cover letter agent (Python script plus templates)
interview-prep-agent/           The interview prep agent (Claude Code project plus templates)
tracker/                        Database of your applications and interviews, shared by both agents
```

## Tracking applications and interviews

Both agents record what they do in a small database on your computer (`tracker/job_search.db`): each application and its status, each interview, who interviewed you, what they asked, and which stories you told. The interview prep agent uses it so it never tells an interviewer the same story twice.

To see it all in your web browser, with what to do next, what is working, and controls to change any application, double-click **Dashboard** in the **start** folder (see [Use the dashboard](docs/05-use-the-dashboard.md)), or run `python tracker/dashboard.py` from the repo folder (`python3` on Mac or Linux). See the [tracker README](tracker/README.md) for everything else it can do.

## Privacy

Your files are stored on your computer: your career history, profile, story bank, generated documents and tracker. Keeping them in the folder does not upload them anywhere.

When an agent works, it sends what it needs to the AI behind it so the AI can read it: Claude (made by Anthropic) for the CV and interview prep agents, or whichever chat tool you paste into on the simple route. That includes your career history and anything the agent reads from the tracker, such as interviewers' names. If that matters to you, check your AI provider's privacy and data settings. The dashboard itself runs only on your computer and sends nothing anywhere.

If you publish your own copy of this repo, the included `.gitignore` keeps your personal files out of Git, but check before you push.

## Words you will see

| Word | What it means |
|---|---|
| Repo | This collection of files and folders. You downloaded it as a ZIP. |
| Terminal | A window where you type commands: PowerShell on Windows, Terminal on Mac. The install guide shows you how to open one. |
| Command | A line of text you paste into the terminal and run by pressing Enter. |
| Folder path | Where a folder is on your computer, for example `Documents\job-search-agents-main`. |
| Python | A free program that runs the CV agent, the tracker and the dashboard. |
| Claude Code | Anthropic's app for using Claude from a terminal. It runs the interview prep agent and signs the CV agent in to Claude. |
| Template | A file ending in `.example` that you copy and fill in with your own details. |
| Job spec | The job description or advert. |
| Tracker | The file that remembers your applications and interviews, `tracker/job_search.db`. The dashboard shows what is in it. |

## Licence

MIT. See `LICENSE`.
