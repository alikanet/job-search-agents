# Use the dashboard

The dashboard shows your whole job search in your web browser: what to do next, where every application stands, and what is working. You can also change anything from it, such as marking an application as sent or recording how an interview went.

It runs on your own computer. You do not need an internet connection, and you do not need to type any commands if you use the double-click files below.

## Before you start

You only need Python. If you have not installed it yet, follow step 2 of [Install the prerequisites](01-install-prerequisites.md). You do not need Claude Code or a Claude plan to use the dashboard on its own.

## Open the dashboard

Open the repo folder (the one you unzipped), then open the folder called **start** inside it.

### Windows

1. Double-click **Dashboard (Windows).bat**.
2. The first time, Windows may show **"Windows protected your PC"**. This is normal for files downloaded from the internet. Click **More info**, then **Run anyway**.
3. A black window opens, and a moment later the dashboard opens in your web browser.

### Mac

1. Double-click **Dashboard (Mac).command**.
2. The first time, your Mac may say it cannot check the file for malicious software, because it was downloaded from the internet. Click **Done** (or **Cancel**), then open **System Settings**, go to **Privacy & Security**, scroll down, and click **Open Anyway** next to the message about the file. On older Macs, right-click (or Control-click) the file and choose **Open** instead.
3. A Terminal window opens, and a moment later the dashboard opens in your web browser.

### Keep the window open

The black window (Windows) or Terminal window (Mac) is what runs the dashboard. **Leave it open while you use the dashboard.** When you are finished, close that window. Next time, double-click the same file again.

If you prefer typing commands, open a terminal in the repo folder and run `python tracker/dashboard.py` (Windows) or `python3 tracker/dashboard.py` (Mac).

## Try it with made-up data first

Double-click **Dashboard demo (Windows).bat** or **Dashboard demo (Mac).command**. You get the same dashboard filled with a made-up job search, so you can click around and see what everything does. Nothing you do in the demo touches your real tracker. Close the window when you are done.

## The pages

| Page | Use it to |
|---|---|
| **Today** | See what to do next, most urgent first. Start here each time. |
| **Applications** | See every application, search them, and change their status. Switch between **Table** and **Board** at the top. |
| An application's page | Click any application to see its details, history and interviews, and change any of them. |
| **What's working** | See which kinds of application get you interviews, how long replies take, and which interview stories land. |
| **Compare** | Pick two applications and see why one got further than the other. |
| **Help** | What the statuses and numbers mean. |

## Everyday tasks

**Record an application you sent.** If you used the CV agent, the application is already there as a draft: open it and click **Mark as sent today**. If you applied some other way, click **Add application** in the sidebar, fill in the company and role, leave the status as Applied, and click **Add application**.

**Change an application's status.** On the Applications page, pick the new status from the drop-down in its row. Or switch to **Board** and drag its card to another column. A message appears at the bottom right with an **Undo** button if you change your mind.

**Change several at once.** On the Applications page, tick the boxes next to the applications, choose a status in the bar that appears above the table, and click **Apply**.

**Record an interview.** Open the application and click **Add interview**. If you use the interview prep agent, `/prep` does this for you.

**Record how an interview went.** Open the application. For each interview you can set the outcome, how it felt, the interviewers, and each question you were asked with the story you used and how it landed. If you use the interview prep agent, `/debrief` does this for you.

**Apply again after a rejection.** Open the old application and click **Reapply**. This starts a new application linked to the old one, so each attempt keeps its own history.

**Remove an application.** If you just want it out of the way, set its status to **Withdrawn** or **Ghosted**. **Delete** removes it and its interviews for good.

**Get a spreadsheet.** Click **Download as spreadsheet (CSV)** in the sidebar. It opens in Excel, Numbers or Google Sheets.

## A simple routine

1. Open the dashboard and go to **Today**.
2. Work down the list from the top. Each item says what to do and why, and many have a button that does it for you.
3. When you send an application, mark it as sent straight away. The date you send it is what reply times are measured from.
4. After each interview, record how it went the same day, while you remember the questions.
5. Once a week, look at **What's working** to see where your interviews are coming from.

## If something goes wrong

- **The window flashes and disappears, or says Python was not found.** Python is not installed, or Windows cannot find it. Follow step 2 of [Install the prerequisites](01-install-prerequisites.md). On Windows, make sure you tick **Add python.exe to PATH** in the installer.
- **The browser does not open.** Look in the black or Terminal window for a line starting `Job search dashboard: http://127.0.0.1:`. Copy that address into your browser.
- **The page says "This site can't be reached".** The window that runs the dashboard was closed. Double-click the file in **start** again.
- **The page says the dashboard was restarted.** Reload the page (press F5 on Windows, or Cmd + R on Mac).
- **You see made-up companies.** You opened the demo. Close it and use the file without "demo" in its name.
- **Your applications are missing.** Make sure you are using the copy of the folder you have been working in. Your data lives in one file, `tracker/job_search.db`, inside that folder.
- **Anything else.** Copy the message from the black or Terminal window into any AI chat, say you are using Windows or Mac, and ask what to do.

## Keep a backup

Everything the dashboard shows is stored in `tracker/job_search.db`. Copy that file somewhere safe (a USB stick or cloud folder) every so often. To restore it, copy it back into the `tracker` folder.
