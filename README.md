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

## Quick start

### Step 1: Download this repo

Click the green **Code** button at the top of this page, then **Download ZIP**, and unzip it somewhere easy to find (for example your Documents folder). If you use Git, you can clone it instead.

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

Each agent has its own README with exact commands:

- [CV and cover letter agent](cv-cover-letter-agent/README.md)
- [Interview prep agent](interview-prep-agent/README.md)

---

## What is in this repo

```
README.md                       You are here
docs/
  01-install-prerequisites.md   Install Python, Claude Code and packages (Windows and Mac)
  02-build-your-career-history.md   Use AI to interview you and build your career history
  03-set-your-voice-and-style.md    Review tone, sentence style, punctuation, cover letter structure
  04-use-any-ai-chat.md         Run the agents in ChatGPT, Gemini, Copilot or any chat tool
prompts/                        Copy-and-paste prompts that work in any AI chat
cv-cover-letter-agent/          The CV and cover letter agent (Python script plus templates)
interview-prep-agent/           The interview prep agent (Claude Code project plus templates)
tracker/                        Database of your applications and interviews, shared by both agents
```

## Tracking applications and interviews

Both agents record what they do in a small database on your computer (`tracker/job_search.db`): each application and its status, each interview, who interviewed you, what they asked, and which stories you told. The interview prep agent uses it so it never tells an interviewer the same story twice. See the [tracker README](tracker/README.md) to list your applications or update them yourself.

## Privacy

Everything runs on your own computer using the files you create. Your career history, profile and generated documents stay in your folder. If you publish your own copy of this repo, the included `.gitignore` keeps your personal files out of Git, but check before you push.

## Licence

MIT. See `LICENSE`.
