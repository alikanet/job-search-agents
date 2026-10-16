# Use any AI chat (ChatGPT, Gemini, Copilot, Claude and others)

You do not need Claude Code or Python. Any AI chat tool that lets you paste long text, and ideally upload files, can run both agents. You do the copying and pasting yourself.

**What you lose compared with the automated route:** the Python script builds finished Word documents and the Claude Code project saves a PDF for you. In a chat tool you get text back, and you paste it into Word or Google Docs yourself. Web research only works if your chat tool can browse the web. If it cannot, paste the company information in yourself.

## Step 1: Create your files

Do Steps 3 to 5 of the main [README](../README.md): your career history, your story bank and your voice and style rules. These are plain text or Markdown files. You can write them in any text editor, or even in a Word document.

## Step 2: Set up a reusable assistant (recommended)

Most chat tools let you save instructions and files so you do not repeat yourself:

- **ChatGPT:** create a Project or a custom GPT, paste the prompt into its instructions, and upload your files.
- **Gemini:** create a Gem with the prompt as its instructions and add your files.
- **Claude:** create a Project, paste the prompt into the project instructions and add your files.
- **Microsoft Copilot and others:** look for an equivalent feature, or simply start every chat with the prompt and attach the files.

Feature names change, so check your tool's help pages if you cannot find these options.

## Step 3: Pick the prompt

| You want to... | Copy this prompt |
|---|---|
| Tailor a CV and cover letter | [`prompts/cv-cover-letter-agent.md`](../prompts/cv-cover-letter-agent.md) |
| Prepare for an interview | [`prompts/interview-prep-agent.md`](../prompts/interview-prep-agent.md) |

Paste the whole prompt as the instructions (or as the first message), then add your files:

- **CV and cover letter:** your CV style guide and cover letter style guide.
- **Interview prep:** your CV style guide (for the career history), your story bank, your cover letter style guide (for voice), and any exit answer and debriefs.

## Step 4: Give it each job

Send a message like this (replace the details):

```
Company website: https://www.examplecompany.com
Role title: Senior Programme Manager
Job spec:
[paste the full job spec here]
```

For interview prep, add the stage and format:

```
Interview stage: hiring manager interview
Format and length: video, 45 minutes
```

## Step 5: Review and approve

The assistant will research the company, check your experience against the job spec, flag gaps, and ask you questions. Answer them. When you are happy, tell it to produce the final version.

Copy the result into a Word or Google Docs file. For a CV, use a plain single-column layout, no tables or text boxes, so application tracking systems can read it.

## Using a coding assistant instead

Some command-line AI tools, such as OpenAI's Codex CLI or Google's Gemini CLI, read an instruction file from your project folder in the same way Claude Code reads `CLAUDE.md`. The file name differs by tool (check your tool's documentation). To use the interview prep agent this way, copy the contents of `interview-prep-agent/CLAUDE.md` and `.claude/skills/prep/SKILL.md` into your tool's instruction file or prompt. This is not tested here, so treat it as a starting point.
