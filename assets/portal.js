/* NEET-SS + ICP Paediatrics — shared Study Portal engine (all days use this file).
   Content comes from DayN/content.js (window.PORTAL), generated from the day's source docx by tools/build_day.py.
   Progress is stored only in this browser (localStorage). No backend. */
(function () {
  const P = window.PORTAL, app = document.getElementById('app');
  if (!P) { app.textContent = 'Portal content missing.'; return; }
  const NS = 'portal:Day' + P.day + ':';
  const LS = {
    get(k, d) { try { const v = JSON.parse(localStorage.getItem(NS + k)); return v == null ? d : v; } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem(NS + k, JSON.stringify(v)); } catch (e) {} }
  };
  const pages = P.pages, byId = Object.fromEntries(pages.map(p => [p.id, p]));
  const tracked = pages.filter(p => !['overview', 'quizzes', 'notebook', 'references'].includes(p.id));
  const strip = h => String(h).replace(/<[^>]+>/g, '').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
  const escT = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  // ---------- progress ----------
  const done = () => new Set(LS.get('done', []));
  const quizStats = () => LS.get('quiz', {});
  function progress() {
    const d = done(), q = quizStats();
    const pd = tracked.filter(p => d.has(p.id)).length, qd = P.quizSets.filter(s => q[s.k]).length;
    const total = tracked.length + P.quizSets.length, pct = total ? Math.round((pd + qd) / total * 100) : 0;
    // Only write when the numbers change: writes fire 'storage' events in other open tabs of this day.
    const prev = LS.get('summary', null);
    if (!prev || prev.pct !== pct || prev.pagesDone !== pd || prev.quizDone !== qd || prev.pages !== tracked.length || prev.quizzes !== P.quizSets.length)
      LS.set('summary', { pct, pagesDone: pd, pages: tracked.length, quizDone: qd, quizzes: P.quizSets.length, at: Date.now() });
    return { pct, pd, qd };
  }
  // ---------- overview study plan ----------
  // Each "Time | Focus" row of the overview plan is linked to the portal sections it covers (worked out from the
  // row text). A row ticks itself once all its linked sections are done; Overview is complete when every row is ticked.
  /*PLANLINKS*/function planLinks(pages, rows) {
    const STOP = new Set('and the with for from into after before plus its this that all per vs interpretation style image patterns progressive review targeted strategy'.split(' '));
    const words = s => String(s).toLowerCase().replace(/<[^>]+>/g, ' ').split(/[^a-z0-9]+/).filter(w => w.length > 2 && !STOP.has(w));
    const parts = pages.filter(p => /^part-\d+$/.test(p.id)).map(p => {
      const ws = words(p.title);
      const acr = p.title.split(/[\s-]+/).filter(w => /^[a-z]/i.test(w) && !STOP.has(w.toLowerCase()) && w !== '&').map(w => w[0]).join('').toLowerCase();
      return { id: p.id, ws: acr.length > 2 ? ws.concat(acr) : ws };
    });
    const same = (a, b) => a === b || (Math.min(a.length, b.length) >= 5 && (a.includes(b) || b.includes(a)))
      || (Math.min(a.length, b.length) >= 6 && a.slice(0, 6) === b.slice(0, 6));
    const has = id => pages.some(p => p.id === id);
    const SPECIAL = [[/\bcases?\b/, 'cases'], [/\bdata\b/, 'data'], [/\bmcqs?\b/, 'quizzes'], [/visual stations?|image-style/, 'data'], [/rapid revision|last 15/, 'revision'], [/\btriage\b|error-review/, 'plan'],
      [/active recall/, 'recall'], [/pearls?\b|traps?\b/, 'pearls'], [/must-know|key numbers/, 'numbers'], [/algorithm|comparison table/, 'tables']];
    return rows.map(text => {
      const t = String(text).toLowerCase(), score = {};
      for (const w of words(t)) {   // a word counts only if it points at exactly one notes page
        const hit = parts.filter(p => p.ws.some(x => same(w, x)));
        if (hit.length === 1) score[hit[0].id] = (score[hit[0].id] || 0) + 1;
      }
      const best = Math.max(0, ...Object.values(score)), ids = parts.map(p => p.id).filter(id => score[id] === best);
      for (const [re, id] of SPECIAL) if (re.test(t) && has(id) && !ids.includes(id)) ids.push(id);
      return ids;
    });
  }/*END*/
  const planTable = ((byId.overview || {}).sections || []).flatMap(s => s.blocks).find(b => b.t === 'table' && /^time$/i.test(strip(b.head[0]).trim()));
  const planMap = planTable ? planLinks(pages, planTable.rows.map(r => r.slice(1).join(' '))) : [];
  const isComplete = id => id === 'quizzes' ? P.quizSets.every(s => quizStats()[s.k]) : done().has(id);
  const planAuto = ri => planMap[ri] && planMap[ri].length > 0 && planMap[ri].every(isComplete);
  const planTicked = ri => planAuto(ri) || !!LS.get('plan', {})[ri];
  const overviewDone = () => !!planTable && planTable.rows.every((_, ri) => planTicked(ri));
  const planLinksHTML = ri => (planMap[ri] || []).length ? `<div class="plan-links">${planMap[ri].map(id =>
    `<a href="#/${id}" class="${isComplete(id) ? 'ok' : ''}">${isComplete(id) ? '✓ ' : ''}${escT(byId[id].eyebrow ? byId[id].eyebrow + ' · ' + byId[id].title : byId[id].title)}</a>`).join('')}</div>` : '';

  function toggleDone(id) { const d = done(); if (!d.has(id)) recallNotify(); d.has(id) ? d.delete(id) : d.add(id); LS.set('done', [...d]); render(); }

  // Active Recall: when leaving the page via "Mark as done" or "Next" with prompts rated "Revise again",
  // send one ntfy message listing them. Re-sent only if the set of prompts changed since the last message.
  function recallNotify() {
    if (curId !== 'recall' || !byId.recall) return;
    const list = byId.recall.sections.flatMap(s => s.blocks).find(b => b.t === 'list');
    if (!list) return;
    const st = LS.get('recall', {}), again = list.items.map((it, i) => [i, it]).filter(([i]) => st[i] === 'again');
    if (!again.length) return;
    const sig = again.map(([i]) => i).join(',');
    if (LS.get('recallSent', '') === sig) return;
    const lines = [];
    for (const [i, it] of again) {
      const l = `P${i + 1}. ${strip(splitRecall(it)[0]).replace(/\s+/g, ' ').trim()}`;
      if (new Blob([lines.concat(l).join('\n')]).size > 3500) { lines.push(`…and ${again.length - lines.length} more`); break; }
      lines.push(l);
    }
    const title = `Day ${P.day} — Active Recall: revise again (${again.length})`;
    fetch(`https://ntfy.sh/neetss?title=${encodeURIComponent(title)}&tags=repeat`, { method: 'POST', body: lines.join('\n') })
      .then(() => LS.set('recallSent', sig)).catch(() => {});
  }

  // ---------- shell ----------
  app.innerHTML = `<header class="top"><button class="menu-btn" aria-label="Menu">☰</button><a href="../index.html">← Home</a>
    <div class="ttl">Day ${P.day} — ${escT(P.title)}<small>Study portal</small></div><a href="#" id="printBtn" title="Print this page">🖨 Print</a></header>
    <div class="bar-prog"><i id="progBar"></i></div>
    <div class="layout"><aside class="side"><input class="search" id="q" placeholder="Search Day ${P.day}…" autocomplete="off"><nav class="nav" id="nav"></nav></aside><main id="main"></main></div>
    <div class="results" id="results"></div><div class="scrim" id="scrim"></div>
    <nav class="mbar" aria-label="Page navigation"><a id="mPrev" href="#">‹ Prev</a><button id="mDone" type="button">✓ Done</button><a id="mNext" href="#">Next ›</a></nav>`;
  const $ = s => app.querySelector(s);
  $('.menu-btn').onclick = () => document.body.classList.toggle('nav-open');
  $('#scrim').onclick = () => document.body.classList.remove('nav-open');
  $('#mDone').onclick = () => { if (curId && !$('#mDone').disabled) toggleDone(curId); };
  // "Next" (desktop pager or phone bar) from Active Recall also sends the revise-again list
  app.addEventListener('click', e => {
    const a = e.target.closest('a'); if (!a || curId !== 'recall') return;
    if (a.id === 'mNext' || (a.closest('.pager') && !a.classList.contains('ghost'))) recallNotify();
  });
  $('#printBtn').onclick = e => { e.preventDefault(); window.print(); };

  function renderNav(cur) {
    const d = done(); let html = '', g = '';
    pages.forEach(p => {
      if (p.group !== g) { g = p.group; html += `<div class="grp">${escT(g)}</div>`; }
      const isDone = p.id === 'overview' ? overviewDone() : isComplete(p.id);
      html += `<a href="#/${p.id}" class="${p.id === cur ? 'on' : ''} ${isDone ? 'done' : ''}"><span class="tick"></span>${p.eyebrow ? `<span class="eb">${escT(p.eyebrow.replace(/^Part\s+/, ''))}</span>` : ''}${escT(p.title)}</a>`;
    });
    $('#nav').innerHTML = html;
  }

  // ---------- blocks ----------
  function tone(label) {
    const L = (label || '').toUpperCase();
    if (/WHAT WOULD YOU DO NEXT/.test(L)) return 'teal';
    if (/TRAP|CRITICAL|EMERGENCY|DANGER|CAUTION|AVOID|DO NOT/.test(L)) return 'red';
    if (/ADVANCED|RANK/.test(L)) return 'purple';
    if (/WHY THIS/.test(L)) return 'green';
    if (/PEARL|HIGH[- ]YIELD|MUST|KEY|MISSION|NUMBER/.test(L)) return 'amber';
    return '';
  }
  const isNext = b => b.t === 'callout' && /WHAT WOULD YOU DO NEXT/i.test(b.label);
  const reveal = (inner, label) => `<div class="reveal-wrap"><button class="rv-btn">👁 ${label}</button><div class="hidden-body">${inner}</div></div>`;
  function block(b, ctx) {
    if (b.t === 'p') return `<p>${b.html}</p>`;
    if (b.t === 'list') {
      const tag = b.ordered ? 'ol' : 'ul';
      let cls = '';
      if (ctx.page.kind === 'pearls') cls = /trap/i.test(ctx.sec.title) ? 'list-trap' : 'list-pearl';
      if (ctx.page.kind === 'revision') return `<ol class="facts">${b.items.map(i => `<li>${i}</li>`).join('')}</ol>`;
      if (ctx.page.kind === 'recall') return recallCards(b.items);
      return `<${tag} class="${cls}">${b.items.map(i => `<li>${i}</li>`).join('')}</${tag}>`;
    }
    if (b.t === 'callout') {
      const html = `<div class="callout ${tone(b.label)}">${b.label ? `<div class="lb">${escT(b.label)}${b.title ? `<span class="tt">${escT(b.title)}</span>` : ''}</div>` : ''}${b.html.map(h => `<p>${h}</p>`).join('')}</div>`;
      return isNext(b) && !ctx.noReveal ? reveal(html, 'What would you do next? — show answer') : html;
    }
    if (b.t === 'img') return `<figure class="fig"><a href="${b.src}" target="_blank" rel="noopener" title="Open full size"><img src="${b.src}" alt="${escT(b.alt || '')}" loading="lazy"></a></figure>`;
    if (b.t === 'grid') return `<div class="grid5">${b.items.map(i => `<div><b>${escT(i.label)}</b>${i.html}</div>`).join('')}</div>`;
    if (b.t === 'table') {
      const blurCol = ctx.page.kind === 'data' && /interpretation/i.test(strip(b.head[b.head.length - 1])) ? b.head.length - 1 : -1;
      const planChk = ctx.page.kind === 'overview' && /^time$/i.test(strip(b.head[0]));
      // 3+ column tables become labelled cards on phones (CSS .stack); each cell carries its column name
      const stack = b.head.length >= 3 && !planChk, lab = b.head.map(h => escT(strip(h)));
      return `${blurCol >= 0 ? '<div class="toolbar"><button class="btn ghost sm" data-act="reveal-all">Reveal all interpretations</button><button class="btn ghost sm" data-act="hide-all">Hide again</button></div>' : ''}
        <div class="tw"><table class="${stack ? 'stack' : ''}"><thead><tr>${planChk ? '<th>✓</th>' : ''}${b.head.map(h => `<th>${h}</th>`).join('')}</tr></thead><tbody>${b.rows.map((r, ri) =>
        `<tr class="${planChk && planTicked(ri) ? 'plan-done' : ''}">${planChk ? `<td>${planAuto(ri) ? `<input type="checkbox" class="chk" checked disabled title="Ticked automatically: all linked sections are done">` : `<input type="checkbox" class="chk" data-plan="${ri}" ${planTicked(ri) ? 'checked' : ''}>`}</td>` : ''}${r.map((c, ci) => ci === blurCol ? `<td class="blur" data-label="${lab[ci]}"><span>${c}</span></td>` : `<td data-label="${lab[ci]}">${c}${planChk && ci === r.length - 1 ? planLinksHTML(ri) : ''}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
    }
    return '';
  }
  // A recall item may carry its answer after "Answer:" (same bullet, usually after a line break).
  function splitRecall(it) {
    const m = String(it).match(/^([\s\S]*?)(?:\s*<br>)*\s*(?:<strong>)?\s*Answer\s*:\s*(?:<\/strong>)?\s*([\s\S]*)$/i);
    return m && m[2].trim() ? [m[1], m[2]] : [it, ''];
  }
  function recallCards(items) {
    const st = LS.get('recall', {}), only = LS.get('recallOnly', false);
    const got = items.filter((_, i) => st[i] === 'got').length, again = items.filter((_, i) => st[i] === 'again').length;
    const hasAns = items.some(it => splitRecall(it)[1]);
    return `<div class="toolbar"><span class="pill g">Knew it: ${got}</span><span class="pill a">Revise again: ${again}</span><span class="pill">Not rated: ${items.length - got - again}</span>
      <button class="btn ghost sm" data-act="recall-only">${only ? 'Show all prompts' : 'Show only “revise again”'}</button><button class="btn ghost sm" data-act="recall-reset">Reset ratings</button></div>
      <p class="lede">Answer each prompt aloud or on paper from memory, then rate yourself.${hasAns ? ' Tapping <b>Revise again</b> shows the answer.' : ' Check your notes for the answer.'}</p>
      <div class="cards">${items.map((it, i) => { if (only && st[i] !== 'again') return ''; const [q, ans] = splitRecall(it);
      return `<div class="card ${st[i] || ''}"><div class="case-no">PROMPT ${i + 1}</div><div class="q">${q}</div>
      ${ans && st[i] === 'again' ? `<div class="ans"><b>Answer:</b> ${ans}</div>` : ''}
      <div class="acts"><button class="btn sm ${st[i] === 'got' ? 'ok' : 'ghost'}" data-recall="${i}" data-v="got">✓ Knew it</button><button class="btn sm ${st[i] === 'again' ? 'warn' : 'ghost'}" data-recall="${i}" data-v="again">↺ Revise again</button></div></div>`; }).join('')}</div>`;
  }

  // ---------- pages ----------
  const DATA_ANS = /^(<strong>)?\s*(Interpretation|Closest distractor|Discriminator|Next management step|Next step|Exam trap|Answer)\b/i;
  function sectionHTML(page, s, i) {
    const ctx = { page, sec: s };
    let inner;
    if (page.kind === 'cases' && s.blocks.length > 1) {
      // Answer part of a case = first "Reasoning/Answer/Trap…" line or "What would you do next?" box onward.
      // Some documents put the whole case (patient, labs, question, reasoning) in one paragraph with line breaks,
      // so such paragraphs are split at the first answer line.
      const ANS = /^(<strong>)?\s*(Structured reasoning|Reasoning|Answer|Trap identified|Management|Next step|Approach|Explanation)\b/i;
      const bl = [];
      s.blocks.forEach(b => {
        if (b.t === 'p' && b.html.includes('<br>')) {
          const ls = b.html.split('<br>'), at = ls.findIndex(l => ANS.test(l.trim()));
          if (at > 0) { bl.push({ t: 'p', html: ls.slice(0, at).join('<br>') }, { t: 'p', html: ls.slice(at).join('<br>') }); return; }
        }
        bl.push(b);
      });
      let k = bl.findIndex((b, j) => j > 0 && (isNext(b) || (b.t === 'p' && ANS.test(b.html))));
      if (k < 0) k = 1;
      const stem = bl.slice(0, k).map(b => block(b, ctx)).join('');
      const rest = bl.slice(k).map(b => block(b, { ...ctx, noReveal: true })).join('');
      inner = `<div class="case-stem">${stem}</div>${reveal(rest, 'Show reasoning & answer')}`;
    } else if (page.kind === 'data' && s.blocks.some(b => b.t === 'p' && DATA_ANS.test(b.html))) {
      // Visual stations: title + image + question stay visible; interpretation, discriminator, next step and trap
      // lines are hidden behind one reveal button per station.
      let out = '', hid = [];
      const flush = () => { if (hid.length) out += reveal(hid.join(''), 'Show interpretation'); hid = []; };
      s.blocks.forEach(b => {
        if (b.t === 'p' && DATA_ANS.test(b.html)) { hid.push(block(b, ctx)); return; }
        flush();
        out += b.t === 'p' && /^(<strong>)?\s*Visual Station \d+/i.test(b.html) ? `<h3 class="station">${b.html}</h3>` : block(b, ctx);
      });
      flush();
      inner = out;
    } else inner = s.blocks.map(b => block(b, ctx)).join('');
    const h1 = s.h1 && s.h1 !== s.title ? `<div class="h1tag">${escT(s.h1)}</div>` : '';
    return `<section class="sec" id="s-${i}">${h1}${s.title ? `<h2>${escT(s.title)}</h2>` : ''}${inner}</section>`;
  }
  function overview() {
    const pr = progress(), q = quizStats(), last = LS.get('last', null);
    const best = P.quizSets.map(s => q[s.k]).filter(Boolean);
    const avg = best.length ? Math.round(best.reduce((a, x) => a + x.bestPct, 0) / best.length) : null;
    const cont = last && byId[last] && last !== 'overview' ? last : (tracked[0] || pages[1]).id;
    return `<div class="hero"><div class="eyebrow" style="color:#bfdbfe">Day ${P.day} · Study portal</div><h1>${escT(P.title)}</h1>
      <div class="sub">${P.subtitle.map(escT).join(' · ')}</div>
      <div class="toolbar" style="margin:14px 0 0"><a class="btn" style="background:#fff;color:#1e3a8a" href="#/${cont}">${last && last !== 'overview' ? 'Continue: ' : 'Start: '}${escT(byId[cont].title)} →</a><a class="btn ghost" href="#/quizzes">Quizzes</a></div></div>
      <div class="stats"><div class="stat"><div class="ring" style="--p:${pr.pct}"><b>${pr.pct}%</b></div><span>Day progress</span></div>
      <div class="stat"><strong>${pr.pd}/${tracked.length}</strong><span>Sections done</span></div>
      <div class="stat"><strong>${pr.qd}/${P.quizSets.length}</strong><span>Quiz sets attempted</span></div>
      <div class="stat"><strong>${avg == null ? '—' : avg + '%'}</strong><span>Avg best quiz score</span></div></div>
      ${planTable ? (overviewDone() ? `<div class="plan-banner ok">✓ Overview complete — every block of the study plan is ticked.</div>`
        : `<div class="plan-banner">Study plan: <b>${planTable.rows.filter((_, ri) => planTicked(ri)).length}/${planTable.rows.length}</b> blocks ticked. A block ticks itself when you mark its linked sections done (and attempt all quiz sets for MCQ blocks).</div>`) : ''}`;
  }
  function quizzesPage() {
    const q = quizStats();
    const sz = P.quizSets.map(s => s.n), lo = Math.min(...sz), hi = Math.max(...sz);
    return `<section class="sec"><h2>${P.mcqCount} MCQs · ${P.quizSets.length} sets of ${lo === hi ? lo : lo + '–' + hi} questions</h2><p class="lede">NEET-SS marking: +4 correct, −1 wrong, 0 unattempted. Instant feedback with explanation and exam pearl; skip and return; wrong-answer report.</p>
      ${P.quizSets.map(s => { const r = q[s.k];
        return `<div class="quiz-row"><div class="info"><b>Quiz Set ${s.k}</b> · Questions ${s.from}–${s.to} (${s.n})<br>${r ? `<span class="pill g">Best ${r.best}/${r.bestMax} · ${r.bestPct}%</span> <span class="pill">Last ${r.last.score}/${r.last.max} · ${r.attempts} attempt${r.attempts > 1 ? 's' : ''}</span>` : '<span class="pill">Not attempted</span>'}</div>
        <a class="btn ${r ? 'ghost' : ''}" href="quiz${s.k}.html">${r ? 'Retake' : 'Start'} Set ${s.k}</a></div>`; }).join('')}</section>`;
  }
  function planExtra() {
    const pr = progress();
    return `<section class="sec"><h2>Your progress on this device</h2><p>Day progress: <b>${pr.pct}%</b> — ${pr.pd}/${tracked.length} sections marked done, ${pr.qd}/${P.quizSets.length} quiz sets attempted.</p>
      <p class="lede">Progress is saved in this browser only. Wrong answers from each quiz set can be downloaded from the quiz result screen as a Word/PDF report for your error notebook.</p>
      <button class="btn ghost sm" data-act="reset-progress">Reset Day ${P.day} progress</button></section>`;
  }

  // ---------- render ----------
  let curId = null;
  function render(scrollSec) {
    const [, id = 'overview', sec] = (location.hash.match(/^#\/([^/]+)(?:\/(\d+))?/) || [null, undefined, undefined]);
    const page = byId[id] || byId.overview;
    if (page.id !== curId) window.scrollTo(0, 0);
    curId = page.id; if (page.id !== 'overview') LS.set('last', page.id);
    renderNav(page.id);
    const idx = pages.indexOf(page), prev = pages[idx - 1], next = pages[idx + 1], d = done();
    let body = '';
    if (page.kind === 'overview') body = overview();
    else body = `${page.eyebrow ? `<div class="eyebrow">${escT(page.eyebrow)}</div>` : `<div class="eyebrow">${escT(page.group)}</div>`}<h1 class="pt">${escT(page.title)}</h1>`;
    if (page.kind === 'cases') body += '<p class="lede">Read each case, decide your next step, then reveal the reasoning.</p>';
    if (page.kind === 'data') body += '<p class="lede">Interpret each station yourself first — tap an interpretation cell to check it.</p>';
    if (page.kind === 'quizzes') body += quizzesPage();
    if (page.kind === 'notebook') body += `<p class="lede">Every wrong answer from Day ${P.day} quiz sets is saved here automatically. Tag why you got it wrong (K/C/R/G/S), add a one-line correction rule, and retest after 48–72 h. <a href="../notebook.html">All days &amp; mocks →</a></p><section class="sec" id="nbPage"></section>`;
    body += page.sections.map((s, i) => sectionHTML(page, s, i)).join('');
    if (page.kind === 'plan') body += planExtra();
    if (page.kind !== 'overview' && page.kind !== 'quizzes' && page.kind !== 'notebook' && page.id !== 'references')
      body += `<div class="done-box"><button class="btn ${d.has(page.id) ? 'ok' : ''}" data-act="done">${d.has(page.id) ? '✓ Marked as done' : 'Mark this section as done'}</button></div>`;
    body += `<div class="pager">${prev ? `<a class="btn ghost" href="#/${prev.id}">← ${escT(prev.title)}</a>` : '<span></span>'}${next ? `<a class="btn" href="#/${next.id}">${escT(next.title)} →</a>` : ''}</div>`;
    const main = $('#main'); main.innerHTML = body;
    if (page.kind === 'notebook' && window.Notebook) Notebook.page(main.querySelector('#nbPage'), { srcId: 'Day' + P.day }, '../');
    $('#progBar').style.width = progress().pct + '%';
    // phone bottom bar: previous / mark done / next
    const canDone = page.kind !== 'overview' && page.kind !== 'quizzes' && page.kind !== 'notebook' && page.id !== 'references';
    $('#mPrev').href = prev ? '#/' + prev.id : '#/' + page.id; $('#mPrev').classList.toggle('off', !prev);
    $('#mNext').href = next ? '#/' + next.id : '#/' + page.id; $('#mNext').classList.toggle('off', !next);
    $('#mNext').textContent = next ? 'Next ›' : 'End';
    const md = $('#mDone'); md.disabled = !canDone; md.classList.toggle('on', canDone && d.has(page.id));
    md.textContent = !canDone ? (page.kind === 'quizzes' ? 'Quizzes' : page.kind === 'notebook' ? 'Notebook' : 'Day ' + P.day) : d.has(page.id) ? '✓ Done' : 'Mark done';
    document.title = `Day ${P.day} — ${page.title} · Study Portal`;
    document.body.classList.remove('nav-open');
    if (sec != null && scrollSec !== false) { const el = main.querySelector('#s-' + sec); if (el) { el.scrollIntoView(); el.classList.add('flash'); } }
  }
  app.addEventListener('click', e => {
    const t = e.target.closest('button,td.blur,input.chk'); if (!t) return;
    if (t.matches('.rv-btn')) t.parentElement.classList.add('revealed');
    else if (t.matches('td.blur')) t.classList.remove('blur');
    else if (t.dataset.act === 'reveal-all') t.closest('section').querySelectorAll('td.blur').forEach(c => c.classList.remove('blur'));
    else if (t.dataset.act === 'hide-all') render(false);
    else if (t.dataset.act === 'done') toggleDone(curId);
    else if (t.dataset.recall != null) { const st = LS.get('recall', {}); st[t.dataset.recall] = st[t.dataset.recall] === t.dataset.v ? undefined : t.dataset.v; LS.set('recall', st); render(false); }
    else if (t.dataset.act === 'recall-only') { LS.set('recallOnly', !LS.get('recallOnly', false)); render(false); }
    else if (t.dataset.act === 'recall-reset') { if (confirm('Clear all active-recall ratings?')) { LS.set('recall', {}); LS.set('recallSent', ''); render(false); } }
    else if (t.dataset.plan != null) { const p = LS.get('plan', {}); p[t.dataset.plan] = t.checked; LS.set('plan', p); render(false); }
    else if (t.dataset.act === 'reset-progress') {
      if (confirm(`Reset all Day ${P.day} progress (sections, plan ticks, recall ratings and quiz scores)?`)) {
        ['done', 'plan', 'recall', 'recallOnly', 'recallSent', 'quiz', 'last', 'summary'].forEach(k => localStorage.removeItem(NS + k)); render(false);
      }
    }
  });

  // ---------- search ----------
  const index = [];
  pages.forEach(p => p.sections.forEach((s, i) => {
    const txt = [s.title, ...s.blocks.map(b => b.t === 'p' ? b.html : b.t === 'list' ? b.items.join(' ') : b.t === 'callout' ? b.label + ' ' + b.title + ' ' + b.html.join(' ')
      : b.t === 'grid' ? b.items.map(x => x.label + ' ' + x.html).join(' ') : b.t === 'table' ? [b.head, ...b.rows].flat().join(' ') : '')].map(strip).join(' ');
    index.push({ p, i, title: s.title || s.h1 || p.title, txt });
  }));
  const results = $('#results');
  $('#q').addEventListener('input', e => {
    const q = e.target.value.trim().toLowerCase();
    if (q.length < 2) { results.classList.remove('show'); return; }
    const hits = index.filter(x => x.txt.toLowerCase().includes(q)).slice(0, 40);
    results.innerHTML = hits.length ? hits.map(h => {
      const at = h.txt.toLowerCase().indexOf(q), snip = h.txt.slice(Math.max(0, at - 60), at + q.length + 80);
      const mk = escT(snip).replace(new RegExp(q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'ig'), m => `<mark>${m}</mark>`);
      return `<a href="#/${h.p.id}/${h.i}"><b>${escT(h.p.title)}</b> · ${escT(h.title)}<small>…${mk}…</small></a>`;
    }).join('') : '<p class="lede">No matches.</p>';
    results.classList.add('show');
  });
  results.addEventListener('click', e => { if (e.target.closest('a')) { results.classList.remove('show'); $('#q').value = ''; } });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') results.classList.remove('show'); });

  window.addEventListener('hashchange', () => render());
  // Sync with other open tabs — only for data that changes what this page shows (never summary/last, which
  // every render may touch; reacting to those made two open tabs re-render each other endlessly).
  const SYNC = ['done', 'quiz', 'recall', 'recallOnly', 'plan'].map(k => NS + k);
  window.addEventListener('storage', e => { if (SYNC.includes(e.key)) render(false); });
  if (!location.hash) location.replace('#/' + (byId[LS.get('last', '')] ? LS.get('last') : 'overview'));
  render();
})();
