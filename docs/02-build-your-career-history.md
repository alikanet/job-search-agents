# Build your career history with AI

The agents write only from facts you give them. A strong career history is what makes the output specific and believable, and a thin one produces generic CVs. Writing it from a blank page is hard, so let an AI interview you instead.

**This works in any AI chat** (ChatGPT, Claude, Gemini, Copilot and others).

## How it works

1. You paste an interviewer prompt into an AI chat.
2. The AI asks you questions one at a time about each role, starting with your most recent.
3. You answer in rough, plain language. Speaking your answers with voice dictation works well.
4. The AI turns your answers into your career history, in the exact format the agents need.
5. You check every fact, then save it into your CV style guide.

## Step by step

### 1. Gather material (optional but helpful)

Open a new chat and have ready, if you have them: your current CV, your LinkedIn profile text, old performance reviews, job descriptions for your past roles, and any numbers you remember (team sizes, budgets, revenue, customers, timelines).

### 2. Paste the interviewer prompt

Copy the whole prompt from [`prompts/career-history-interview.md`](../prompts/career-history-interview.md) into a new chat. If you have a CV, paste it after the prompt.

### 3. Answer honestly and specifically

For each achievement the AI will ask:

- **What was the situation?** What was broken, missing or at stake?
- **What exactly did you do?** Your own actions, not the team's.
- **How did you do it?** The method, the steps, the decisions you made.
- **What was the result?** Numbers wherever you have them: percentages, money, time saved, sites, customers, people.
- **How big was it?** Team size, budget, number of locations, number of stakeholders.
- **What was your authority?** Did you manage the people, or influence without formal authority?

Tips:

- **Rough is fine.** The AI will tidy the wording. Accuracy matters more than polish.
- **Say "I don't know" when you do not.** The AI should mark that detail `[TO ADD]` and move on. Never guess a number.
- **Give the true size of your role.** If you led a project but did not manage the team, say so. The agents use these limits to stop you overclaiming.
- **Aim for 10 to 15 minutes per role.**

### 4. Review each role as it is written

After each role the AI will show you a draft. Read it line by line and fix anything that is inaccurate, inflated or something you could not explain to an interviewer. If a figure came from memory, check it against a document if you can.

### 5. Save the result

When the AI has covered all your roles, ask it for the final version. Paste it into the **Career History** section of `cv-cover-letter-agent/knowledge/cv_style_guide.md`, replacing the template content.

Also fill in the other sections of that file: the roles to include per CV, tools you have genuinely used, qualifications and headline stats. Ask the AI to help, using the same chat.

### 6. Build your story bank (for interview prep)

If you will use the interview prep agent, continue in the same chat with this prompt:

```
Now turn my career history into a story bank for interview preparation. Choose
the 8 to 15 strongest achievements. For each, write: a short title, the
employer and role, a one-sentence headline with the key figure, the
situation, the action, the result, the hardest moment, anything still
missing marked [TO ADD], and guardrails (what I must not claim or exaggerate).
Number the stories. Then add an index table mapping common interview question
types (leading a team, recovering a failing project, influencing senior
stakeholders, handling failure, and so on) to story numbers. Use only facts I
have given you.
```

Save the result as `interview-prep-agent/story_bank.md`.

### 7. Keep it up to date

After every new job or major achievement, run the interviewer prompt again for just that role and add it.

## Rules the AI must follow

The interviewer prompt tells the AI to never invent facts, to challenge vague answers, and to mark gaps. Check that it does. If it adds a number you did not give it, delete it and tell the AI off. The agents treat everything in your career history as true.
