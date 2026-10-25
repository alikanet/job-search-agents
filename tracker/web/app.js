// Job search dashboard. Plain JavaScript, no build step and no internet
// needed. Every value from the tracker goes through esc() before it is put
// into the page, because job specs and notes are pasted from the web.
"use strict";

(() => {
  const TOKEN = document.querySelector('meta[name="tracker-token"]').content;
  const main = document.getElementById("main");
  const dialog = document.getElementById("dialog");
  const tooltip = document.getElementById("tooltip");

  const STATUSES = ["drafting", "applied", "interviewing", "offer", "rejected", "withdrawn", "ghosted"];
  const STATUS_LABEL = {
    drafting: "Drafting", applied: "Applied", interviewing: "Interviewing", offer: "Offer",
    rejected: "Rejected", withdrawn: "Withdrawn", ghosted: "Ghosted",
  };
  const STAGES = ["recruiter_screen", "hiring_manager", "panel", "case_study", "final"];
  const STAGE_LABEL = {
    recruiter_screen: "Recruiter screen", hiring_manager: "Hiring manager", panel: "Panel",
    case_study: "Case study", final: "Final round",
  };
  const OUTCOMES = ["pending", "progressed", "rejected", "withdrew", "offer"];
  const OUTCOME_LABEL = {
    pending: "Waiting to hear", progressed: "Went through", rejected: "Rejected", withdrew: "I withdrew", offer: "Offer",
  };
  const LANDED_LABEL = { good: "Landed well", ok: "Was ok", weak: "Landed badly" };
  const PRIORITY_LABEL = { 1: "Now", 2: "This week", 3: "When you can" };
  const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const LONG_MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  const DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

  const state = {
    meta: { demo: false, db: "" },
    rows: [],
    search: "",
    statusFilter: new Set(),
    sort: { key: "days_in_status", dir: 1 },  // most recently changed first
    selected: new Set(),
    mode: remember("appsMode") || "table",
  };

  // -------------------------------------------------------------------------
  // Small helpers
  // -------------------------------------------------------------------------

  function remember(key, value) {
    try {
      if (value === undefined) return localStorage.getItem(key);
      localStorage.setItem(key, value);
    } catch (e) { /* private windows can refuse storage; the default is fine */ }
    return null;
  }

  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const plural = (n, one, many) => `${n} ${n === 1 ? one : many || one + "s"}`;
  const pct = (r) => (r == null ? "No data yet" : `${Math.round(r * 100)}%`);

  function parseDay(s) {
    if (!s) return null;
    const [y, m, d] = s.slice(0, 10).split("-").map(Number);
    return new Date(y, m - 1, d);
  }
  function isoDay(d) {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  }
  const todayIso = () => isoDay(new Date());
  function fmtDay(s) {
    const d = parseDay(s);
    if (!d) return "";
    const year = d.getFullYear() === new Date().getFullYear() ? "" : ` ${d.getFullYear()}`;
    return `${d.getDate()} ${MONTHS[d.getMonth()]}${year}`;
  }
  function fmtWhen(s) {
    if (!s) return "Date not set";
    const d = parseDay(s);
    const time = s.length > 10 ? `, ${s.slice(11, 16)}` : "";
    return `${DAYS[d.getDay()].slice(0, 3)} ${fmtDay(s)}${time}`;
  }
  function daysBetween(a, b) {
    return Math.round((b - a) / 86400000);
  }
  function relative(s) {
    const d = parseDay(s);
    if (!d) return "";
    const today = parseDay(todayIso());
    const n = daysBetween(today, d);
    if (n === 0) return "today";
    if (n === 1) return "tomorrow";
    if (n === -1) return "yesterday";
    return n > 0 ? `in ${n} days` : `${-n} days ago`;
  }
  function money(n, currency) {
    if (n == null) return "?";
    const symbol = { GBP: "£", USD: "$", EUR: "€" }[currency] || "";
    return `${symbol}${Number(n).toLocaleString()}${symbol ? "" : currency ? " " + currency : ""}`;
  }
  const appLabel = (r) => `${r.role_title} at ${r.company}`;
  const statusChip = (s) => `<span class="chip ${esc(s)}">${esc(STATUS_LABEL[s] || s)}</span>`;
  const options = (values, labels, selected, blank) =>
    (blank !== undefined ? `<option value="">${esc(blank)}</option>` : "") +
    values.map((v) => `<option value="${esc(v)}"${String(v) === String(selected ?? "") ? " selected" : ""}>${esc(labels ? labels[v] : v)}</option>`).join("");

  async function api(method, path, body) {
    const headers = { "X-Tracker-Token": TOKEN };
    if (body !== undefined) headers["Content-Type"] = "application/json";
    const res = await fetch(path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
    let data = null;
    try { data = await res.json(); } catch (e) { /* not JSON */ }
    if (!res.ok) throw new Error((data && data.error) || `The dashboard could not do that (error ${res.status}).`);
    return data;
  }

  function toast(message, { error = false, undo = null } = {}) {
    const el = document.createElement("div");
    el.className = "toast" + (error ? " error" : "");
    el.setAttribute("role", error ? "alert" : "status");
    el.append(message);
    if (undo) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = "Undo";
      button.addEventListener("click", async () => { el.remove(); await undo(); });
      el.append(button);
    }
    document.getElementById("toasts").append(el);
    setTimeout(() => el.remove(), undo ? 8000 : 5000);
  }

  async function attempt(fn) {
    try {
      return await fn();
    } catch (e) {
      toast(e.message, { error: true });
      return undefined;
    }
  }

  // -------------------------------------------------------------------------
  // Charts: thin single-colour marks, hairline grid, a tooltip on every mark
  // and a table view under every chart.
  // -------------------------------------------------------------------------

  // Charts are built from HTML rather than scaled SVG, so their text stays
  // the same size however wide the column is.
  function niceMax(v) {
    if (v <= 5) return Math.max(1, Math.ceil(v));
    const p = 10 ** Math.floor(Math.log10(v));
    return [1, 2, 5, 10].map((m) => m * p).find((m) => m >= v);
  }

  // Vertical columns over time or buckets. points: [{label, value, tip, tick}]
  function columnChart(points, { title, valueName = "Count" } = {}) {
    const max = niceMax(Math.max(0, ...points.map((p) => p.value)));
    const ticks = max <= 5 ? Array.from({ length: max + 1 }, (_, i) => i) : [0, max / 2, max];
    const peak = points.reduce((best, p, i) => (p.value > points[best].value ? i : best), 0);
    const grid = ticks.map((t) => `<span class="cols-grid${t === 0 ? " base" : ""}" style="--at:${t / max}"><em>${t}</em></span>`).join("");
    const cols = points.map((p, i) => {
      const labelled = p.value > 0 && (i === peak || i === points.length - 1);
      return `<div class="col" tabindex="0" data-tip="${esc(p.tip || `${p.label}: ${p.value}`)}">` +
        (labelled ? `<span class="col-value">${p.value}</span>` : "") +
        (p.value > 0 ? `<span class="col-fill" style="--h:${p.value / max}"></span>` : "") + "</div>";
    }).join("");
    return `<figure class="cols" style="--n:${points.length}" aria-label="${esc(title)}">
        <div class="cols-plot">${grid}${cols}</div>
        <div class="cols-ticks">${points.map((p) => `<span>${esc(p.tick || "")}</span>`).join("")}</div>
      </figure>` + tableView([points.map((p) => [p.label, p.value])], ["", valueName]);
  }

  // Horizontal bars, labelled above each bar so long labels fit, with the
  // value at the bar's tip. rows: [{label, value, text, quiet, tip}]
  function barChart(rows, { title, max = 1, headers = ["", "Value"] } = {}) {
    const bars = rows.map((r) => {
      const share = max ? Math.max(0, Math.min(1, r.value / max)) : 0;
      return `<div class="hbar" tabindex="0" data-tip="${esc(r.tip || r.text)}">
        <div class="hbar-label${r.quiet ? " quiet" : ""}">${esc(r.label)}</div>
        <div class="hbar-area"><span class="hbar-fill${r.quiet ? " quiet" : ""}" style="--w:${share}"></span><span class="hbar-text">${esc(r.text)}</span></div>
      </div>`;
    }).join("");
    return `<figure class="hbars" aria-label="${esc(title)}">${bars}</figure>` + tableView([rows.map((r) => [r.label, r.text])], headers);
  }

  function tableView(groups, headers) {
    const rows = groups.flat();
    return `<details><summary>Show as a table</summary><div class="table-wrap"><table>
      <thead><tr>${headers.map((h) => `<th>${esc(h)}</th>`).join("")}</tr></thead>
      <tbody>${rows.map((r) => `<tr>${r.map((c, i) => `<td${i ? ' class="num"' : ""}>${esc(c)}</td>`).join("")}</tr>`).join("")}</tbody>
    </table></div></details>`;
  }

  function showTip(target, x, y) {
    tooltip.textContent = target.dataset.tip;
    tooltip.hidden = false;
    const box = tooltip.getBoundingClientRect();
    tooltip.style.left = `${Math.min(window.innerWidth - box.width - 8, x + 12)}px`;
    tooltip.style.top = `${Math.max(8, y - box.height - 10)}px`;
  }
  document.addEventListener("mousemove", (e) => {
    const t = e.target.closest?.("[data-tip]");
    if (t) showTip(t, e.clientX, e.clientY); else tooltip.hidden = true;
  });
  document.addEventListener("focusin", (e) => {
    const t = e.target.closest?.("[data-tip]");
    if (t) { const r = t.getBoundingClientRect(); showTip(t, r.left + r.width / 2, r.top); } else tooltip.hidden = true;
  });
  document.addEventListener("scroll", () => { tooltip.hidden = true; }, true);

  // -------------------------------------------------------------------------
  // Shared pieces
  // -------------------------------------------------------------------------

  function demoBanner() {
    return state.meta.demo
      ? `<p class="banner">You are looking at made-up demo data. Changes here are not saved to your tracker. Run <code>python tracker/dashboard.py</code> without <code>--demo</code> to see your own search.</p>`
      : "";
  }

  function adviceItem(item, { linkTitle = true } = {}) {
    const title = item.app_id && linkTitle ? `<a href="#/app/${item.app_id}">${esc(item.title)}</a>` : esc(item.title);
    const listed = item.apps?.length
      ? `<ul class="listed">${item.apps.map((x) => `<li><a href="#/app/${x.id}">${esc(x.label)}</a></li>`).join("")}</ul>`
      : "";
    const actions = item.actions.map((a) => {
      const ids = (a.app_ids || [item.app_id]).join(",");
      return `<button type="button" class="button" data-action="advice-status" data-status="${esc(a.status)}" data-ids="${esc(ids)}">${esc(a.label)}</button>`;
    }).join("");
    return `<li>
      <span class="when${item.priority === 1 ? " now" : ""}">${PRIORITY_LABEL[item.priority]}</span>
      <div><h3>${title}</h3><p>${esc(item.detail)}</p>${listed}${actions ? `<div class="actions">${actions}</div>` : ""}</div>
    </li>`;
  }

  async function changeStatus(ids, status, date, { quiet = false } = {}) {
    state.rows = await api("GET", "/api/applications");
    const before = new Map(state.rows.filter((r) => ids.includes(r.id) && r.status !== status).map((r) => [r.id, r.status]));
    for (const id of ids) await api("POST", `/api/applications/${id}/status`, { status, date: date || undefined });
    const what = ids.length === 1 ? "Status" : `${ids.length} applications`;
    if (!quiet) {
      toast(`${what} changed to ${STATUS_LABEL[status].toLowerCase()}.`, {
        undo: before.size ? async () => {
          await attempt(async () => {
            for (const [id, old] of before) await api("POST", `/api/applications/${id}/status`, { status: old });
            toast("Change undone.");
            await render();
          });
        } : null,
      });
    }
  }

  // -------------------------------------------------------------------------
  // Today
  // -------------------------------------------------------------------------

  async function pageOverview() {
    const s = await api("GET", "/api/summary");
    const k = s.kpis;
    const now = new Date();
    const things = s.advice.length;
    const docket = things
      ? `<ol class="docket">${s.advice.map((i) => adviceItem(i)).join("")}</ol>`
      : `<p class="empty-state">Nothing needs you right now. ${k.total ? "Keep sending applications, and check back after your next interview." : "Add your first application to get started."}</p>`;
    const upcoming = s.upcoming.length
      ? `<ul class="upcoming">${s.upcoming.map((u) => `<li>
          <div class="date">${esc(fmtWhen(u.scheduled_at))}</div>
          <div><a href="#/app/${u.app_id}">${esc(u.company)}</a>, ${esc(STAGE_LABEL[u.stage].toLowerCase())}${u.format ? `, ${esc(u.format)}` : ""}</div>
          <div class="small muted">${u.has_prep ? "Prep sheet ready" : "No prep sheet yet"}${u.interviewers.length ? `. With ${esc(u.interviewers.join(", "))}` : ""}</div>
        </li>`).join("")}</ul>`
      : `<p class="muted">No interviews booked.</p>`;
    const pipeline = STATUSES.filter((st) => s.status_counts[st]).map((st) =>
      `<a class="chip ${st}" href="#/applications?status=${st}">${esc(STATUS_LABEL[st])} ${s.status_counts[st]}</a>`).join("") ||
      `<span class="muted">No applications yet.</span>`;
    const hero = k.submitted
      ? `<div class="hero"><span class="figure">${pct(k.interview_rate)}</span><span class="caption">of the applications you sent led to an interview (${k.interviewed} of ${k.submitted}).</span></div>`
      : `<div class="hero"><span class="figure">0</span><span class="caption">applications sent so far. Mark a draft as sent and the numbers start here.</span></div>`;
    const tiles = `<div class="tiles">
      <div class="tile"><div class="label">Sent in the last 30 days</div><div class="value">${k.submitted_last_30}</div><div class="sub">${k.submitted_last_7} in the last week</div></div>
      <div class="tile"><div class="label">Got a reply</div><div class="value">${pct(k.response_rate)}</div><div class="sub">${k.responded} of ${k.submitted} sent</div></div>
      <div class="tile"><div class="label">Typical wait for a reply</div><div class="value">${k.median_days_to_response == null ? "No data yet" : plural(k.median_days_to_response, "day")}</div><div class="sub">median of ${plural(k.responses_timed, "reply", "replies")}</div></div>
      <div class="tile"><div class="label">Offers</div><div class="value">${k.offers}</div><div class="sub">${k.submitted ? pct(k.offer_rate) + " of sent" : ""}</div></div>
    </div>`;
    const weeks = s.weekly.map((w, i) => ({
      label: `Week of ${fmtDay(w.week_start)}`, value: w.count, tip: `Week of ${fmtDay(w.week_start)}: ${plural(w.count, "application")} sent`,
      tick: i % 3 === 0 ? fmtDay(w.week_start) : "",
    }));
    const feed = s.activity.length
      ? `<ul class="feed">${s.activity.map((e) => `<li><span class="on">${esc(fmtDay(e.on))}</span><span>${esc(STATUS_LABEL[e.status])}: <a href="#/app/${e.app_id}">${esc(e.role)} at ${esc(e.company)}</a></span></li>`).join("")}</ul>`
      : `<p class="muted">Nothing yet.</p>`;

    main.innerHTML = `${demoBanner()}
      <div class="page-head"><div>
        <h1>${DAYS[now.getDay()]} ${now.getDate()} ${LONG_MONTHS[now.getMonth()]}</h1>
        <p>${plural(k.active, "application")} in play. ${things ? `${plural(things, "thing")} to do, most urgent first.` : "Nothing needs you right now."}</p>
      </div></div>
      <div class="two-col">
        <section aria-labelledby="todo"><h2 id="todo" class="visually-hidden">What to do next</h2>${docket}</section>
        <aside>
          <section><h2>Coming up</h2>${upcoming}</section>
          <section><h2>Where things stand</h2><div class="pipeline">${pipeline}</div></section>
        </aside>
      </div>
      <section><h2>Your numbers</h2><p class="section-note">Counted from applications you have sent. <a href="#/analytics">See what is working</a>.</p>
        ${hero}${tiles}
        <div class="chart-block"><h3>Applications sent per week</h3><p class="note">The last 12 weeks.</p>${columnChart(weeks, { title: "Applications sent per week", valueName: "Sent" })}</div>
      </section>
      <section><h2>Recent changes</h2>${feed}</section>`;
  }

  // -------------------------------------------------------------------------
  // Applications: a table or a board, with filters and bulk changes
  // -------------------------------------------------------------------------

  const SORTS = {
    id: (r) => r.id, company: (r) => `${r.company} ${r.role_title}`.toLowerCase(), status: (r) => STATUSES.indexOf(r.status),
    applied_on: (r) => r.applied_on || "", days_in_status: (r) => r.days_in_status ?? -1, interviews: (r) => r.interviews,
    furthest_stage: (r) => STAGES.indexOf(r.furthest_stage), next_interview: (r) => r.next_interview || "~", source: (r) => (r.source || "~").toLowerCase(),
  };

  function visibleRows() {
    const q = state.search.trim().toLowerCase();
    const rows = state.rows.filter((r) =>
      (!state.statusFilter.size || state.statusFilter.has(r.status)) &&
      (!q || `${r.company} ${r.role_title} ${r.source || ""} ${r.notes || ""}`.toLowerCase().includes(q)));
    const key = SORTS[state.sort.key];
    return rows.sort((a, b) => (key(a) > key(b) ? 1 : key(a) < key(b) ? -1 : 0) * state.sort.dir);
  }

  async function pageApplications(r) {
    state.rows = await api("GET", "/api/applications");
    const preset = r.params.get("status");
    if (preset) state.statusFilter = new Set([preset]);
    state.selected.clear();
    main.innerHTML = `${demoBanner()}
      <div class="page-head"><div><h1>Applications</h1><p>${plural(state.rows.length, "application")}. Change a status from the list, or drag cards on the board.</p></div>
        <button type="button" class="button primary" data-action="new-application">Add application</button></div>
      <div class="toolbar">
        <input type="search" placeholder="Search company, role, source or notes" aria-label="Search applications" data-input="search" value="${esc(state.search)}">
        <div class="pipeline" role="group" aria-label="Filter by status">${STATUSES.map((s) =>
          `<button type="button" class="chip" data-action="filter-status" data-status="${s}" aria-pressed="${state.statusFilter.has(s)}">${esc(STATUS_LABEL[s])} ${state.rows.filter((x) => x.status === s).length}</button>`).join("")}</div>
        <div class="segmented" role="group" aria-label="Layout">
          <button type="button" data-action="mode" data-mode="table" aria-pressed="${state.mode === "table"}">Table</button>
          <button type="button" data-action="mode" data-mode="board" aria-pressed="${state.mode === "board"}">Board</button>
        </div>
      </div>
      <div id="apps-body"></div>`;
    renderAppsBody();
  }

  function renderAppsBody() {
    const body = document.getElementById("apps-body");
    if (!body) return;
    const rows = visibleRows();
    if (!state.rows.length) {
      body.innerHTML = `<p class="empty-state">No applications yet. Use <strong>Add application</strong>, or let the CV agent record one when it saves your documents.</p>`;
      return;
    }
    if (state.mode === "board") {
      body.innerHTML = `<div class="board">${STATUSES.map((s) => {
        const cards = rows.filter((r) => r.status === s);
        return `<div class="column" data-status="${s}"><h3><span>${esc(STATUS_LABEL[s])}</span><span class="muted">${cards.length}</span></h3>
          ${cards.map((r) => `<div class="card" draggable="true" data-id="${r.id}">
            <a href="#/app/${r.id}">${esc(r.company)}</a><div>${esc(r.role_title)}</div>
            <div class="meta">${r.next_interview ? `Interview ${esc(relative(r.next_interview))}` : r.applied_on ? `Sent ${esc(fmtDay(r.applied_on))}` : `Started ${esc(fmtDay(r.created_on))}`}</div>
            <select aria-label="Status of ${esc(appLabel(r))}" data-change="row-status" data-id="${r.id}">${options(STATUSES, STATUS_LABEL, r.status)}</select>
          </div>`).join("")}</div>`;
      }).join("")}</div>`;
      wireBoard(body.querySelector(".board"));
      return;
    }
    const th = (key, text, cls = "") => {
      const sorted = state.sort.key === key;
      return `<th class="${cls}"${sorted ? ` aria-sort="${state.sort.dir > 0 ? "ascending" : "descending"}"` : ""}><button type="button" data-action="sort" data-key="${key}">${esc(text)}${sorted ? (state.sort.dir > 0 ? " ▲" : " ▼") : ""}</button></th>`;
    };
    const bulk = state.selected.size
      ? `<form class="bulk toolbar" data-submit="bulk-status"><strong>${state.selected.size} selected.</strong>
          <label>Set status to <select name="status">${options(STATUSES, STATUS_LABEL, "applied")}</select></label>
          <button class="button primary" type="submit">Apply</button>
          <button class="button" type="button" data-action="clear-selection">Clear selection</button></form>`
      : "";
    body.innerHTML = `${bulk}<div class="table-wrap"><table>
      <thead><tr>
        <th><input type="checkbox" aria-label="Select all shown" data-change="select-all" ${rows.length && rows.every((r) => state.selected.has(r.id)) ? "checked" : ""}></th>
        ${th("company", "Application")}${th("status", "Status")}${th("applied_on", "Sent")}${th("days_in_status", "In this status", "num")}
        ${th("interviews", "Interviews", "num")}${th("furthest_stage", "Furthest stage")}${th("next_interview", "Next interview")}${th("source", "Source")}
      </tr></thead>
      <tbody>${rows.map((r) => `<tr>
        <td><input type="checkbox" aria-label="Select ${esc(appLabel(r))}" data-change="select-row" data-id="${r.id}" ${state.selected.has(r.id) ? "checked" : ""}></td>
        <td><a class="row-link" href="#/app/${r.id}"><span class="role">${esc(r.role_title)}</span><br>${esc(r.company)}</a></td>
        <td><select aria-label="Status of ${esc(appLabel(r))}" data-change="row-status" data-id="${r.id}">${options(STATUSES, STATUS_LABEL, r.status)}</select></td>
        <td>${r.applied_on ? esc(fmtDay(r.applied_on)) : '<span class="muted">Not sent</span>'}</td>
        <td class="num">${r.days_in_status == null ? "" : plural(r.days_in_status, "day")}</td>
        <td class="num">${r.interviews || ""}</td>
        <td>${r.furthest_stage ? esc(STAGE_LABEL[r.furthest_stage]) : ""}</td>
        <td>${r.next_interview ? `${esc(fmtWhen(r.next_interview))}` : ""}</td>
        <td>${esc(r.source || "")}</td>
      </tr>`).join("") || `<tr><td colspan="9" class="muted">No applications match. Clear the search or the status filter.</td></tr>`}</tbody>
    </table></div>`;
  }

  function wireBoard(board) {
    let dragging = null;
    board.addEventListener("dragstart", (e) => {
      const card = e.target.closest(".card");
      if (!card) return;
      dragging = Number(card.dataset.id);
      card.setAttribute("aria-grabbed", "true");
      e.dataTransfer.setData("text/plain", card.dataset.id);
      e.dataTransfer.effectAllowed = "move";
    });
    board.addEventListener("dragend", (e) => {
      e.target.closest(".card")?.removeAttribute("aria-grabbed");
      board.querySelectorAll(".drop-target").forEach((c) => c.classList.remove("drop-target"));
    });
    board.addEventListener("dragover", (e) => {
      const column = e.target.closest(".column");
      if (!column || dragging == null) return;
      e.preventDefault();
      board.querySelectorAll(".drop-target").forEach((c) => c !== column && c.classList.remove("drop-target"));
      column.classList.add("drop-target");
    });
    board.addEventListener("drop", async (e) => {
      const column = e.target.closest(".column");
      if (!column || dragging == null) return;
      e.preventDefault();
      const id = dragging;
      dragging = null;
      const row = state.rows.find((r) => r.id === id);
      if (row && row.status !== column.dataset.status) {
        await attempt(() => changeStatus([id], column.dataset.status));
        await render();
      }
    });
  }

  // -------------------------------------------------------------------------
  // One application
  // -------------------------------------------------------------------------

  async function pageApplication(r) {
    const d = await api("GET", `/api/applications/${r.id}`);
    const a = d.app;
    const titles = d.story_titles || {};
    const fileLink = (f) => f.exists
      ? `<a href="/files?path=${encodeURIComponent(f.path)}&t=${encodeURIComponent(TOKEN)}" target="_blank" rel="noopener">${esc(f.label)}</a>`
      : `<span class="muted" data-tip="${esc(f.path)}">${esc(f.label)} (file not found)</span>`;
    const salary = a.salary_min != null || a.salary_max != null ? `${money(a.salary_min, a.salary_currency)} to ${money(a.salary_max, a.salary_currency)}` : "";
    const facts = [
      ["Company", a.website ? `<a href="${esc(a.website)}" target="_blank" rel="noopener noreferrer">${esc(a.company)}</a>` : esc(a.company)],
      ["Where you found it", esc(a.source || "")],
      ["Started", esc(fmtDay(a.created_on))],
      ["Sent", a.applied_on ? esc(fmtDay(a.applied_on)) : "Not sent yet"],
      ["Reply", a.response_on ? `${esc(fmtDay(a.response_on))}${a.days_to_response != null ? `, after ${plural(a.days_to_response, "day")}` : ""}` : ""],
      ["Advertised salary", esc(salary)],
      ["Job posting", a.job_url ? `<a href="${esc(a.job_url)}" target="_blank" rel="noopener noreferrer">Open the posting</a>` : ""],
      ["Notes", esc(a.notes || "")],
      ["Earlier application", a.reapplied_from ? `<a href="#/app/${a.reapplied_from}">Application #${a.reapplied_from}</a>` : ""],
      ["Reapplied as", d.reapplications.map((id) => `<a href="#/app/${id}">Application #${id}</a>`).join(", ")],
    ].filter(([, v]) => v);
    const events = [
      ...a.history.map((h) => ({ on: h.changed_on, text: STATUS_LABEL[h.status] || h.status, key: ["applied", "offer", "rejected"].includes(h.status) })),
      ...a.interviews.filter((iv) => iv.scheduled_at).map((iv) => ({ on: iv.scheduled_at.slice(0, 10), text: `${STAGE_LABEL[iv.stage]} interview`, key: true })),
    ].sort((x, y) => (x.on > y.on ? 1 : x.on < y.on ? -1 : 0));
    const datalist = `<datalist id="stories">${Object.entries(titles).map(([n, t]) => `<option value="${esc(n)}">${esc(t)}</option>`).join("")}</datalist>`;
    const howItsGoing = [...d.advice.map((i) => adviceItem(i, { linkTitle: false }))].join("");

    main.innerHTML = `${demoBanner()}
      <div class="page-head"><div>
        <p class="small"><a href="#/applications">All applications</a></p>
        <h1>${esc(a.role_title)}</h1>
        <p>${esc(a.company)}. ${statusChip(a.status)} <span class="muted">${esc(d.progress_label)}${a.days_in_status != null ? `, ${plural(a.days_in_status, "day")} in this status` : ""}.</span></p>
        <form class="status-bar" data-submit="status" data-id="${a.id}">
          <label>Status <select name="status">${options(STATUSES, STATUS_LABEL, a.status)}</select></label>
          <label>Date it happened <input type="date" name="date" value="${todayIso()}" max="${todayIso()}"></label>
          <button class="button primary" type="submit">Change status</button>
        </form>
      </div>
      <div class="actions">
        ${a.status === "drafting" ? `<button type="button" class="button" data-action="quick-status" data-id="${a.id}" data-status="applied">Mark as sent today</button>` : ""}
        <button type="button" class="button" data-action="reapply" data-id="${a.id}">Reapply</button>
        <button type="button" class="button" data-action="edit-application" data-id="${a.id}">Edit details</button>
        <button type="button" class="button" data-action="compare-with" data-id="${a.id}">Compare</button>
        <button type="button" class="button danger" data-action="delete-application" data-id="${a.id}">Delete</button>
      </div></div>
      <section><h2>How it is going</h2>
        ${howItsGoing ? `<ol class="docket">${howItsGoing}</ol>` : ""}
        ${d.context.length ? `<ul class="notes-list">${d.context.map((c) => `<li>${esc(c)}</li>`).join("")}</ul>` : `<p class="muted">Nothing to compare yet. The more applications you track, the more this can tell you.</p>`}
      </section>
      <div class="two-col">
        <section>
          <div class="page-head"><h2>Interviews</h2><button type="button" class="button" data-action="new-interview" data-id="${a.id}">Add interview</button></div>
          ${a.interviews.length ? a.interviews.map((iv) => interviewBlock(iv, titles, fileLink)).join("") : `<p class="muted">No interviews yet. When one is booked, add it here or run <code>/prep</code> in Claude Code.</p>`}
          ${datalist}
        </section>
        <aside>
          <section><h2>Details</h2><dl class="facts">${facts.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${v}</dd>`).join("")}</dl></section>
          ${d.files.length ? `<section><h2>Your documents</h2><div class="files">${d.files.map(fileLink).join("")}</div></section>` : ""}
          <section><h2>Timeline</h2>${events.length ? `<ol class="timeline">${events.map((e) => `<li class="${e.key ? "key" : ""}"><span class="on">${esc(fmtDay(e.on))}</span>${esc(e.text)}</li>`).join("")}</ol>` : `<p class="muted">No changes recorded.</p>`}</section>
          ${a.job_spec ? `<section><details class="spec"><summary>Job spec</summary><pre>${esc(a.job_spec)}</pre></details></section>` : ""}
        </aside>
      </div>`;
  }

  function interviewBlock(iv, titles, fileLink) {
    const meta = [iv.format, iv.length_minutes ? `${iv.length_minutes} minutes` : ""].filter(Boolean).join(", ");
    const questions = iv.questions.length
      ? `<div class="table-wrap"><table><thead><tr><th>Question</th><th>Story</th><th>How it landed</th><th>On prep sheet</th><th><span class="visually-hidden">Remove</span></th></tr></thead><tbody>
        ${iv.questions.map((q) => `<tr>
          <td>${esc(q.question)}</td>
          <td>${q.story_number != null ? `${q.story_number}${titles[q.story_number] ? `. ${esc(titles[q.story_number])}` : ""}` : '<span class="muted">None</span>'}</td>
          <td><select aria-label="How it landed" data-change="question-field" data-field="landed" data-id="${q.id}">${options(["good", "ok", "weak"], LANDED_LABEL, q.landed, "Not rated")}</select></td>
          <td><input type="checkbox" aria-label="Was on the prep sheet" data-change="question-field" data-field="on_prep_sheet" data-id="${q.id}" ${q.on_prep_sheet ? "checked" : ""}></td>
          <td><button type="button" class="button link" data-action="delete-question" data-id="${q.id}">Remove</button></td>
        </tr>`).join("")}</tbody></table></div>`
      : `<p class="muted small">No questions recorded. Run <code>/debrief</code> after the interview, or add them below.</p>`;
    return `<div class="interview">
      <div class="interview-head">
        <div><h3>${esc(STAGE_LABEL[iv.stage])}</h3><div class="muted">${esc(fmtWhen(iv.scheduled_at))}${iv.scheduled_at ? ` (${esc(relative(iv.scheduled_at))})` : ""}${meta ? `, ${esc(meta)}` : ""}</div></div>
        <div class="inline-form">
          <label>Outcome <select data-change="interview-field" data-field="outcome" data-id="${iv.id}">${options(OUTCOMES, OUTCOME_LABEL, iv.outcome, "Not recorded")}</select></label>
          <label>How it felt <select data-change="interview-field" data-field="feeling" data-id="${iv.id}">${options([1, 2, 3, 4, 5], { 1: "1, badly", 2: "2", 3: "3", 4: "4", 5: "5, very well" }, iv.feeling, "Not rated")}</select></label>
          <button type="button" class="button" data-action="edit-interview" data-id="${iv.id}">Edit</button>
          <button type="button" class="button danger" data-action="delete-interview" data-id="${iv.id}">Delete</button>
        </div>
      </div>
      <div class="people">${iv.interviewers.map((p) => `<span class="chip">${esc(p.name)}${p.title ? `, ${esc(p.title)}` : ""}<button type="button" aria-label="Remove ${esc(p.name)}" data-action="remove-interviewer" data-interview="${iv.id}" data-id="${p.id}">×</button></span>`).join("")}
        <form class="inline-form" data-submit="add-interviewer" data-id="${iv.id}"><input name="person" placeholder="Name, title" aria-label="Add an interviewer"><button class="button" type="submit">Add interviewer</button></form>
      </div>
      ${iv.files.length ? `<div class="files">${iv.files.map(fileLink).join("")}</div>` : ""}
      ${questions}
      <form class="inline-form" data-submit="add-question" data-id="${iv.id}">
        <label class="grow">Question asked <input name="question" required></label>
        <label>Story used <input name="story_number" type="number" min="1" list="stories" size="4"></label>
        <label>How it landed <select name="landed">${options(["good", "ok", "weak"], LANDED_LABEL, "", "Not rated")}</select></label>
        <label class="check"><input type="checkbox" name="on_prep_sheet"> On the prep sheet</label>
        <button class="button" type="submit">Add question</button>
      </form>
    </div>`;
  }

  // -------------------------------------------------------------------------
  // What's working
  // -------------------------------------------------------------------------

  async function pageAnalytics() {
    const an = await api("GET", "/api/analytics");
    const k = an.kpis;
    if (!k.submitted) {
      main.innerHTML = `${demoBanner()}<div class="page-head"><div><h1>What's working</h1></div></div>
        <p class="empty-state">This page fills in once you have sent a few applications. Mark drafts as sent on the Applications page, and record interviews as they happen.</p>`;
      return;
    }
    const funnel = barChart(an.funnel.map((f, i) => ({
      label: f.label, value: f.count, text: i ? `${f.count} (${pct(f.rate)} of sent)` : `${f.count}`,
      tip: `${f.label}: ${f.count} of ${an.funnel[0].count} sent applications`,
    })), { title: "From sent to offer", max: an.funnel[0].count, headers: ["Step", "Applications"] });

    const insights = an.insights.length
      ? `<ul class="insights">${an.insights.map((i) => `<li><span class="chip ${i.strength === "pattern" ? "" : "ok"} strength">${i.strength === "pattern" ? "Pattern" : "Early signal"}</span><strong>${esc(i.factor)}.</strong> ${esc(i.text)}</li>`).join("")}</ul>`
      : `<p class="muted">No clear differences yet. A difference shows here once two groups each have at least ${an.min_group} sent applications and their interview rates are 20 points or more apart.</p>`;
    const factorCharts = an.factors.filter((f) => f.groups.length).map((f) => `<div class="chart-block"><h3>${esc(f.name)}</h3>${barChart(f.groups.map((g) => ({
      label: `${g.label} (${plural(g.n, "application")})`, value: g.interview_rate || 0, quiet: g.n < an.min_group,
      text: g.n < an.min_group ? `${g.interviewed} of ${g.n}, too few to compare` : `${pct(g.interview_rate)} got an interview`,
      tip: `${g.label}: ${g.interviewed} of ${g.n} got an interview, ${g.responded} got a reply, ${g.offers} offers`,
    })), { title: `Interview rate by ${f.name.toLowerCase()}`, headers: ["Group", "Interview rate"] })}</div>`).join("");

    const weeks = an.weekly.map((w, i) => ({
      label: `Week of ${fmtDay(w.week_start)}`, value: w.count, tick: i % 4 === 0 ? fmtDay(w.week_start) : "",
      tip: `Week of ${fmtDay(w.week_start)}: ${plural(w.count, "application")} sent`,
    }));
    const rt = an.response_times;
    const waits = rt.buckets.map((b) => ({ label: b.label, value: b.count, tick: b.label, tip: `${b.label}: ${plural(b.count, "reply", "replies")}` }));

    const stages = an.stages.length
      ? barChart(an.stages.map((s) => ({
          label: `${s.label} (${plural(s.total, "interview")})`, value: s.pass_rate || 0, quiet: s.passed + s.failed < 2,
          text: s.passed + s.failed ? `${pct(s.pass_rate)} went through (${s.passed} of ${s.passed + s.failed} decided)` : "None decided yet",
          tip: `${s.label}: ${s.passed} went through, ${s.failed} did not, ${s.pending} waiting`,
        })), { title: "Pass rate by interview stage", headers: ["Stage", "Pass rate"] })
      : `<p class="muted">No interviews recorded yet.</p>`;
    const f = an.feeling;
    const feeling = f.went_well.n && f.went_badly.n
      ? `<p>Interviews you went through, you rated ${f.went_well.average} of 5 on average (${plural(f.went_well.n, "interview")}). Ones that ended in a rejection, ${f.went_badly.average} (${plural(f.went_badly.n, "interview")}). ${Math.abs(f.went_well.average - f.went_badly.average) < 0.5 ? "Your gut feeling has not been a good guide to the result so far, so do not read too much into how one went." : "Your sense of how an interview went has matched the result fairly well."}</p>`
      : `<p class="muted">Rate how each interview felt to see whether your gut feeling predicts the result.</p>`;

    const stories = an.stories.length
      ? `<div class="table-wrap"><table><thead><tr><th>Story</th><th class="num">Times told</th><th>How it landed</th><th>Heard by</th><th>Last told</th></tr></thead><tbody>
        ${an.stories.map((s) => `<tr>
          <td><strong>${s.number}.</strong> ${esc(s.title || "")} ${s.weak >= 2 && s.weak >= s.good ? '<span class="chip weak">Needs work</span>' : ""}${!s.uses ? '<span class="chip">Not used yet</span>' : ""}</td>
          <td class="num">${s.uses}</td>
          <td>${s.uses ? `${s.good} well, ${s.ok} ok, ${s.weak} badly${s.unrated ? `, ${s.unrated} not rated` : ""}` : ""}</td>
          <td>${esc(s.companies.join(", "))}</td>
          <td>${esc(fmtDay(s.last_used))}</td>
        </tr>`).join("")}</tbody></table></div>`
      : `<p class="muted">Record which story you used for each question (with <code>/debrief</code> or on an application page) to see which ones work.</p>`;
    const told = an.stories.filter((s) => s.good + s.ok + s.weak > 0);
    const storyChart = told.length ? `<div class="chart-block"><h3>Share of tellings that landed well</h3>${barChart(told.map((s) => ({
      label: `${s.number}. ${s.title || "Story " + s.number}`, value: s.good_rate || 0, quiet: s.good + s.ok + s.weak < 2,
      text: `${pct(s.good_rate)} (${s.good} of ${s.good + s.ok + s.weak})`, tip: `${s.good} landed well, ${s.ok} ok, ${s.weak} badly`,
    })), { title: "Share of tellings that landed well", headers: ["Story", "Landed well"] })}</div>` : "";

    const q = an.questions;
    const questions = q.total
      ? `<p><strong>${pct(q.predicted_rate)}</strong> of the questions you were asked were on your prep sheet (${q.predicted} of ${q.total}).</p>
        <div class="grid-2">
          <div><h3>Asked most often</h3><div class="table-wrap"><table><thead><tr><th>Question</th><th class="num">Times</th><th class="num">Landed badly</th></tr></thead><tbody>
            ${q.common.map((c) => `<tr><td>${esc(c.question)}<div class="small muted">${esc(c.companies.join(", "))}</div></td><td class="num">${c.count}</td><td class="num">${c.weak || ""}</td></tr>`).join("")}
          </tbody></table></div></div>
          <div><h3>Answers that landed badly</h3>${q.hardest.length ? `<ul class="notes-list">${q.hardest.map((h) => `<li>${esc(h.question)} <span class="muted">(<a href="#/app/${h.app_id}">${esc(h.company)}</a>, ${esc(STAGE_LABEL[h.stage].toLowerCase())})</span></li>`).join("")}</ul><p class="small muted">Practise these out loud. They are the ones most likely to come up again.</p>` : '<p class="muted">None so far.</p>'}</div>
        </div>`
      : `<p class="muted">No questions recorded yet.</p>`;

    main.innerHTML = `${demoBanner()}
      <div class="page-head"><div><h1>What's working</h1>
        <p>Based on ${plural(k.submitted, "sent application")}. Groups are only compared when each has at least ${an.min_group}, and small numbers are labelled as early signals.</p></div></div>
      <section><h2>From sent to offer</h2><p class="section-note">Each step counts the sent applications that reached it.</p><div class="chart-block">${funnel}</div></section>
      <section><h2>What seems to make a difference</h2><p class="section-note">Interview rates for different kinds of application. These are patterns in your own search, not proof of cause.</p>
        ${insights}<div class="grid-2">${factorCharts}</div></section>
      <section><h2>Pace</h2><div class="grid-2">
        <div class="chart-block"><h3>Applications sent per week</h3><p class="note">The last 26 weeks.</p>${columnChart(weeks, { title: "Applications sent per week", valueName: "Sent" })}</div>
        <div class="chart-block"><h3>How long replies take</h3><p class="note">${rt.n ? `Median ${plural(rt.median, "day")}, from ${plural(rt.n, "reply", "replies")}.` : "No replies timed yet."}</p>${columnChart(waits, { title: "Days from sending to a reply", valueName: "Replies" })}</div>
      </div></section>
      <section><h2>Interviews</h2><div class="grid-2"><div class="chart-block"><h3>Pass rate by stage</h3>${stages}</div><div><h3>Gut feeling against the result</h3>${feeling}</div></div></section>
      <section><h2>Stories</h2><p class="section-note">From the questions you recorded, matched to <code>story_bank.md</code>.</p>${storyChart}${stories}</section>
      <section><h2>Questions</h2>${questions}</section>`;
  }

  // -------------------------------------------------------------------------
  // Compare
  // -------------------------------------------------------------------------

  async function pageCompare(r) {
    const rows = await api("GET", "/api/applications");
    const a = r.params.get("a"), b = r.params.get("b");
    const pick = (name, selected) => `<label>${name === "a" ? "First application" : "Second application"}
      <select name="${name}" required>${options(rows.map((x) => x.id), Object.fromEntries(rows.map((x) => [x.id, `${appLabel(x)} (${STATUS_LABEL[x.status].toLowerCase()})`])), selected, "Choose an application")}</select></label>`;
    let result = `<p class="muted">Pick two applications, for example one that led to an interview and one that did not. The comparison explains what was different about them and how much those differences have mattered across your whole search.</p>`;
    if (a && b) {
      const c = await api("GET", `/api/compare?a=${encodeURIComponent(a)}&b=${encodeURIComponent(b)}`);
      const lead = (side) => (c.leader === side ? " lead" : "");
      result = `<section><h2>${c.leader ? `${esc(c[c.leader].label)} did better` : "Both got to the same point"}</h2>
        ${c.reasons.length ? `<ul class="reasons">${c.reasons.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : ""}
        <p class="muted small">${esc(c.caveat)}</p>
        <div class="table-wrap"><table><thead><tr><th></th><th><a href="#/app/${c.a.id}">${esc(c.a.label)}</a></th><th><a href="#/app/${c.b.id}">${esc(c.b.label)}</a></th></tr></thead>
        <tbody>${c.rows.map((row, i) => `<tr><th scope="row">${esc(row.label)}</th><td class="${i === 0 ? lead("a") : ""}">${esc(row.a ?? "Unknown")}</td><td class="${i === 0 ? lead("b") : ""}">${esc(row.b ?? "Unknown")}</td></tr>`).join("")}</tbody></table></div></section>`;
    }
    main.innerHTML = `${demoBanner()}
      <div class="page-head"><div><h1>Compare two applications</h1><p>Why did one get further than the other?</p></div></div>
      <form class="compare-picks" data-submit="compare">${pick("a", a)}${pick("b", b)}<button class="button primary" type="submit">Compare</button></form>
      ${rows.length < 2 ? '<p class="empty-state">You need at least two applications to compare.</p>' : result}`;
  }

  // -------------------------------------------------------------------------
  // Help
  // -------------------------------------------------------------------------

  function pageHelp() {
    main.innerHTML = `${demoBanner()}<div class="help">
      <div class="page-head"><div><h1>Help</h1><p>How the tracker works, what the numbers mean, and where the advice comes from.</p></div></div>
      <h2>How an application moves through the tracker</h2>
      <ol>
        <li><strong>Draft.</strong> The CV agent records an application when it saves your CV and cover letter. You can also add one here with <strong>Add application</strong>.</li>
        <li><strong>Send.</strong> When you submit it, mark it as applied (on its page, in the list, or from the advice on Today). The date matters: it is what reply times are measured from.</li>
        <li><strong>Interview.</strong> <code>/prep</code> in Claude Code records each interview and its prep sheet. You can also add interviews here. Adding one moves the application to Interviewing.</li>
        <li><strong>Debrief.</strong> After each interview, <code>/debrief</code> records the questions, the stories you used and how they landed. You can also add questions on the application page.</li>
        <li><strong>Result.</strong> Set the interview's outcome. An offer, a rejection or withdrawing updates the application's status for you.</li>
      </ol>
      <h2>Statuses</h2>
      <dl>
        <dt>Drafting</dt><dd>Documents prepared, not sent yet.</dd>
        <dt>Applied</dt><dd>Sent, waiting for a reply.</dd>
        <dt>Interviewing</dt><dd>At least one interview booked or done.</dd>
        <dt>Offer</dt><dd>You have an offer.</dd>
        <dt>Rejected</dt><dd>They said no, at any point.</dd>
        <dt>Withdrawn</dt><dd>You pulled out.</dd>
        <dt>Ghosted</dt><dd>No reply for long enough that you have stopped expecting one. You can change it back if they get in touch.</dd>
      </dl>
      <p><strong>Reapply</strong> starts a new application for the same company and role, linked to the old one, so each attempt keeps its own history. <strong>Delete</strong> removes an application and its interviews for good; use Withdrawn or Ghosted if you only want it out of the way.</p>
      <h2>How the numbers are worked out</h2>
      <dl>
        <dt>Sent</dt><dd>Applications with a sent date, an interview, or a status past drafting. Drafts are left out of every rate.</dd>
        <dt>Got a reply</dt><dd>An interview, an offer or a rejection.</dd>
        <dt>Interview rate</dt><dd>Sent applications with at least one interview, divided by all sent applications.</dd>
        <dt>Wait for a reply</dt><dd>Days from the sent date to the first move to interviewing, rejected or offer.</dd>
        <dt>Got past a round</dt><dd>At least one interview went through, or there was an offer.</dd>
        <dt>Patterns</dt><dd>Groups are only compared when each has at least 3 sent applications, and only differences of 20 points or more in interview rate are shown. With fewer than 15 applications between the two groups, a difference is labelled an early signal. These are patterns in your own search, not proof of what causes what.</dd>
      </dl>
      <h2>Where the advice comes from</h2>
      <dl>
        <dt>Prepare</dt><dd>An interview in the next 7 days without a prep sheet.</dd>
        <dt>Debrief</dt><dd>A past interview with no debrief file and no questions recorded.</dd>
        <dt>Chase</dt><dd>An interview more than 7 days ago with no outcome.</dd>
        <dt>Follow up</dt><dd>No reply after your usual wait: the median of your own reply times once you have 5 or more, otherwise 7 days.</dd>
        <dt>Ghosted</dt><dd>No reply after twice the time that 80% of your replies arrived within (at least 21 days), otherwise 30 days.</dd>
        <dt>Send or drop</dt><dd>A draft older than 5 days.</dd>
        <dt>Rework a story</dt><dd>A story that has landed badly at least twice, and at least as often as it landed well.</dd>
      </dl>
      <h2>From the terminal</h2>
      <p>Everything here can also be done with <code>python tracker/jobdb.py</code> (use <code>python3</code> on Mac or Linux). Run it with <code>--help</code> to see every command. Claude Code can run these for you too.</p>
      <h2>Privacy</h2>
      <p>The dashboard runs only on this computer and only accepts requests from this page. Your data stays in <code>tracker/job_search.db</code>, which is never added to Git. When Claude Code reads the tracker for <code>/prep</code> or <code>/debrief</code>, what it reads is sent to Claude like the rest of your files.</p>
    </div>`;
  }

  // -------------------------------------------------------------------------
  // Dialogs
  // -------------------------------------------------------------------------

  function openDialog(title, body, submitLabel, onSubmit, { danger = false } = {}) {
    dialog.innerHTML = `<form method="dialog" novalidate><h2 id="dialog-title">${esc(title)}</h2>${body}
      <div class="form-error" hidden></div>
      <div class="form-actions"><button type="button" class="button" data-action="close-dialog">Cancel</button>
      <button type="submit" class="button ${danger ? "danger" : "primary"}">${esc(submitLabel)}</button></div></form>`;
    const form = dialog.querySelector("form");
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!form.checkValidity()) { form.reportValidity(); return; }
      const button = form.querySelector('[type="submit"]');
      button.disabled = true;
      try {
        await onSubmit(formValues(form));
        dialog.close();
      } catch (err) {
        const box = form.querySelector(".form-error");
        box.textContent = err.message;
        box.hidden = false;
        button.disabled = false;
      }
    });
    dialog.showModal();
    dialog.querySelector("input, select, textarea")?.focus();
  }

  function formValues(form) {
    const values = Object.fromEntries(new FormData(form));
    form.querySelectorAll('input[type="checkbox"][name]').forEach((c) => { values[c.name] = c.checked; });
    return values;
  }

  const field = (label, html, wide) => `<label class="${wide ? "wide" : ""}">${esc(label)}${html}</label>`;
  const input = (name, value, attrs = "") => `<input name="${name}" value="${esc(value ?? "")}" ${attrs}>`;

  async function applicationDialog(existing) {
    const sources = [...new Set(state.rows.map((r) => r.source).filter(Boolean))];
    const a = existing || {};
    const body = `<div class="form-grid">
      ${existing ? "" : field("Company", input("company", "", "required autocomplete=off"))}
      ${field("Role", input("role_title", a.role_title, "required"), !!existing)}
      ${existing ? "" : field("Status", `<select name="status">${options(STATUSES, STATUS_LABEL, "applied")}</select>`)}
      ${field("Sent on", input("applied_on", a.applied_on || (existing ? "" : todayIso()), 'type="date"'))}
      ${field("Where you found it", input("source", a.source, 'list="sources" placeholder="LinkedIn, referral, recruiter"') + `<datalist id="sources">${sources.map((s) => `<option value="${esc(s)}">`).join("")}</datalist>`)}
      ${field("Company website", input("website", a.website, 'type="url" placeholder="https://"'))}
      ${field("Job posting link", input("job_url", a.job_url, 'type="url" placeholder="https://"'))}
      ${field("Salary from", input("salary_min", a.salary_min, 'type="number" min="0" step="1000"'))}
      ${field("Salary to", input("salary_max", a.salary_max, 'type="number" min="0" step="1000"'))}
      ${field("Currency", input("salary_currency", a.salary_currency, 'placeholder="GBP" maxlength="3"'))}
      ${field("Notes", `<textarea name="notes">${esc(a.notes || "")}</textarea>`, true)}
      ${field("Job spec", `<textarea name="job_spec" placeholder="Paste the job description, so you still have it when the posting is taken down">${esc(a.job_spec || "")}</textarea>`, true)}
    </div>`;
    openDialog(existing ? "Edit application" : "Add an application", body, existing ? "Save changes" : "Add application", async (v) => {
      if (existing) {
        if (!v.website) delete v.website;
        await api("PATCH", `/api/applications/${existing.id}`, v);
        toast("Changes saved.");
        await render();
      } else {
        const created = await api("POST", "/api/applications", v);
        toast("Application added.");
        location.hash = `#/app/${created.id}`;
      }
    });
  }

  function interviewDialog(appId, existing) {
    const iv = existing || {};
    const when = iv.scheduled_at ? iv.scheduled_at.replace(" ", "T") : "";
    const body = `<div class="form-grid">
      ${field("Stage", `<select name="stage" required>${options(STAGES, STAGE_LABEL, iv.stage || "recruiter_screen")}</select>`)}
      ${field("Date and time", input("scheduled_at", when, 'type="datetime-local"'))}
      ${field("Format", input("format", iv.format, 'list="formats" placeholder="video, in person, phone"') + '<datalist id="formats"><option value="video"><option value="in person"><option value="phone"></datalist>')}
      ${field("Length in minutes", input("length_minutes", iv.length_minutes, 'type="number" min="5" step="5"'))}
      ${field("Outcome", `<select name="outcome">${options(OUTCOMES, OUTCOME_LABEL, iv.outcome, "Not recorded")}</select>`)}
      ${field("How it felt", `<select name="feeling">${options([1, 2, 3, 4, 5], null, iv.feeling, "Not rated")}</select>`)}
      ${existing ? "" : field("Interviewers, one per line as Name, title", '<textarea name="interviewers" placeholder="Priya Shah, Head of Delivery"></textarea>', true)}
    </div>`;
    openDialog(existing ? "Edit interview" : "Add an interview", body, existing ? "Save changes" : "Add interview", async (v) => {
      if (existing) await api("PATCH", `/api/interviews/${existing.id}`, v);
      else await api("POST", `/api/applications/${appId}/interviews`, v);
      toast(existing ? "Interview saved." : "Interview added.");
      await render();
    });
  }

  function confirmDialog(title, message, label, onConfirm) {
    openDialog(title, `<p>${esc(message)}</p>`, label, onConfirm, { danger: true });
  }

  // -------------------------------------------------------------------------
  // Actions, wired once through event delegation
  // -------------------------------------------------------------------------

  const ACTIONS = {
    "close-dialog": () => dialog.close(),
    "new-application": () => applicationDialog(null),
    "edit-application": async (el) => {
      const d = await attempt(() => api("GET", `/api/applications/${el.dataset.id}`));
      if (d) applicationDialog(d.app);
    },
    "delete-application": (el) => confirmDialog("Delete this application?",
      "This permanently removes the application with its interviews, questions and history. To keep it but move it out of the way, set its status to withdrawn or ghosted instead.",
      "Delete for good", async () => {
        await api("DELETE", `/api/applications/${el.dataset.id}`);
        toast("Application deleted.");
        location.hash = "#/applications";
      }),
    "reapply": (el) => confirmDialog("Reapply for this role?",
      "This starts a new application for the same company and role, linked to this one, as a draft. This application and its history stay as they are.",
      "Start a new application", async () => {
        const created = await api("POST", `/api/applications/${el.dataset.id}/reapply`);
        toast("New application started.");
        location.hash = `#/app/${created.id}`;
      }),
    "quick-status": (el) => attempt(async () => { await changeStatus([Number(el.dataset.id)], el.dataset.status); await render(); }),
    "advice-status": (el) => attempt(async () => {
      el.disabled = true;
      await changeStatus(el.dataset.ids.split(",").map(Number), el.dataset.status);
      await render();
    }),
    "compare-with": (el) => { location.hash = `#/compare?a=${el.dataset.id}`; },
    "new-interview": (el) => interviewDialog(el.dataset.id, null),
    "edit-interview": async (el) => {
      const d = await attempt(() => api("GET", `/api/applications/${route().id}`));
      const iv = d?.app.interviews.find((x) => String(x.id) === el.dataset.id);
      if (iv) interviewDialog(null, iv);
    },
    "delete-interview": (el) => confirmDialog("Delete this interview?", "Its questions and interviewers go with it.", "Delete interview", async () => {
      await api("DELETE", `/api/interviews/${el.dataset.id}`);
      toast("Interview deleted.");
      await render();
    }),
    "remove-interviewer": (el) => attempt(async () => {
      await api("DELETE", `/api/interviews/${el.dataset.interview}/interviewers/${el.dataset.id}`);
      await render();
    }),
    "delete-question": (el) => attempt(async () => {
      await api("DELETE", `/api/questions/${el.dataset.id}`);
      toast("Question removed.");
      await render();
    }),
    "filter-status": (el) => {
      const s = el.dataset.status;
      if (state.statusFilter.has(s)) state.statusFilter.delete(s); else state.statusFilter.add(s);
      el.setAttribute("aria-pressed", String(state.statusFilter.has(s)));
      if (location.hash.includes("status=")) history.replaceState(null, "", "#/applications");
      renderAppsBody();
    },
    "mode": (el) => {
      state.mode = el.dataset.mode;
      remember("appsMode", state.mode);
      document.querySelectorAll('[data-action="mode"]').forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.mode === state.mode)));
      renderAppsBody();
    },
    "sort": (el) => {
      const key = el.dataset.key;
      state.sort = { key, dir: state.sort.key === key ? -state.sort.dir : 1 };
      renderAppsBody();
    },
    "clear-selection": () => { state.selected.clear(); renderAppsBody(); },
  };

  const CHANGES = {
    "row-status": (el) => attempt(async () => {
      await changeStatus([Number(el.dataset.id)], el.value);
      state.rows = await api("GET", "/api/applications");
      renderAppsBody();
    }),
    "select-row": (el) => {
      const id = Number(el.dataset.id);
      if (el.checked) state.selected.add(id); else state.selected.delete(id);
      renderAppsBody();
    },
    "select-all": (el) => {
      visibleRows().forEach((r) => (el.checked ? state.selected.add(r.id) : state.selected.delete(r.id)));
      renderAppsBody();
    },
    "interview-field": (el) => attempt(async () => {
      await api("PATCH", `/api/interviews/${el.dataset.id}`, { [el.dataset.field]: el.value });
      toast("Interview updated.");
      await render();
    }),
    "question-field": (el) => attempt(async () => {
      await api("PATCH", `/api/questions/${el.dataset.id}`, { [el.dataset.field]: el.type === "checkbox" ? el.checked : el.value });
    }),
  };

  const SUBMITS = {
    "status": (form) => attempt(async () => {
      const v = formValues(form);
      await changeStatus([Number(form.dataset.id)], v.status, v.date);
      await render();
    }),
    "bulk-status": (form) => attempt(async () => {
      const ids = [...state.selected];
      await changeStatus(ids, formValues(form).status);
      state.selected.clear();
      state.rows = await api("GET", "/api/applications");
      renderAppsBody();
    }),
    "add-interviewer": (form) => attempt(async () => {
      const person = formValues(form).person.trim();
      if (!person) return;
      await api("PATCH", `/api/interviews/${form.dataset.id}`, { interviewers: [person] });
      await render();
    }),
    "add-question": (form) => attempt(async () => {
      await api("POST", `/api/interviews/${form.dataset.id}/questions`, formValues(form));
      toast("Question added.");
      await render();
    }),
    "compare": (form) => {
      const v = formValues(form);
      location.hash = `#/compare?a=${encodeURIComponent(v.a)}&b=${encodeURIComponent(v.b)}`;
    },
  };

  document.addEventListener("click", (e) => {
    const el = e.target.closest("[data-action]");
    if (el && ACTIONS[el.dataset.action]) { e.preventDefault(); ACTIONS[el.dataset.action](el, e); }
  });
  document.addEventListener("change", (e) => {
    const el = e.target.closest("[data-change]");
    if (el && CHANGES[el.dataset.change]) CHANGES[el.dataset.change](el, e);
  });
  document.addEventListener("submit", (e) => {
    const form = e.target.closest("form[data-submit]");
    if (form && SUBMITS[form.dataset.submit]) { e.preventDefault(); SUBMITS[form.dataset.submit](form); }
  });
  document.addEventListener("input", (e) => {
    if (e.target.matches('[data-input="search"]')) { state.search = e.target.value; renderAppsBody(); }
  });

  // -------------------------------------------------------------------------
  // Routing
  // -------------------------------------------------------------------------

  const PAGES = {
    overview: pageOverview, applications: pageApplications, app: pageApplication,
    analytics: pageAnalytics, compare: pageCompare, help: pageHelp,
  };

  function route() {
    const [path, query] = (location.hash.slice(1) || "/").split("?");
    const parts = path.split("/").filter(Boolean);
    return { name: parts[0] || "overview", id: parts[1], params: new URLSearchParams(query || "") };
  }

  async function render() {
    const r = route();
    const page = PAGES[r.name] || PAGES.overview;
    const nav = r.name === "app" ? "applications" : r.name in PAGES ? r.name : "overview";
    document.querySelectorAll("[data-nav]").forEach((a) => {
      if (a.dataset.nav === nav) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
    });
    const scroll = window.scrollY;
    try {
      await page(r);
      window.scrollTo(0, scroll);
    } catch (e) {
      main.innerHTML = `<div class="page-head"><div><h1>That did not load</h1><p>${esc(e.message)}</p></div></div>
        <p><a href="#/">Back to Today</a></p>`;
    }
  }

  window.addEventListener("hashchange", async () => {
    tooltip.hidden = true;
    await render();
    window.scrollTo(0, 0);
    main.focus({ preventScroll: true });
  });

  (async () => {
    document.getElementById("export-link").href = `/export.csv?t=${encodeURIComponent(TOKEN)}`;
    state.meta = await attempt(() => api("GET", "/api/meta")) || state.meta;
    document.getElementById("source-label").textContent = state.meta.demo ? "Showing demo data" : `Data: ${state.meta.db}`;
    if (route().name !== "applications") state.rows = (await attempt(() => api("GET", "/api/applications"))) || [];
    await render();
  })();
})();
