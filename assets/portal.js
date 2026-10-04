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
  const tracked = pages.filter(p => !['overview', 'quizzes', 'references'].includes(p.id));
  const strip = h => String(h).replace(/<[^>]+>/g, '').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
  const escT = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  // ---------- progress ----------
  const done = () => new Set(LS.get('done', []));
  const quizStats = () => LS.get('quiz', {});
  function progress() {
    const d = done(), q = quizStats();
    const pd = tracked.filter(p => d.has(p.id)).length, qd = P.quizSets.filter(s => q[s.k]).length;
    const total = tracked.length + P.quizSets.length, pct = total ? Math.round((pd + qd) / total * 100) : 0;
    LS.set('summary', { pct, pagesDone: pd, pages: tracked.length, quizDone: qd, quizzes: P.quizSets.length, at: Date.now() });
    return { pct, pd, qd };
  }
  function toggleDone(id) { const d = done(); d.has(id) ? d.delete(id) : d.add(id); LS.set('done', [...d]); render(); }

  // ---------- shell ----------
  app.innerHTML = `<header class="top"><button class="menu-btn" aria-label="Menu">☰</button><a href="../index.html">← Home</a>
    <div class="ttl">Day ${P.day} — ${escT(P.title)}<small>Study portal</small></div><a href="#" id="printBtn" title="Print this page">🖨 Print</a></header>
    <div class="bar-prog"><i id="progBar"></i></div>
    <div class="layout"><aside class="side"><input class="search" id="q" placeholder="Search Day ${P.day}…" autocomplete="off"><nav class="nav" id="nav"></nav></aside><main id="main"></main></div>
    <div class="results" id="results"></div>`;
  const $ = s => app.querySelector(s);
  $('.menu-btn').onclick = () => document.body.classList.toggle('nav-open');
  $('#printBtn').onclick = e => { e.preventDefault(); window.print(); };

  function renderNav(cur) {
    const d = done(); let html = '', g = '';
    pages.forEach(p => {
      if (p.group !== g) { g = p.group; html += `<div class="grp">${escT(g)}</div>`; }
      const isDone = p.id === 'quizzes' ? P.quizSets.every(s => quizStats()[s.k]) : d.has(p.id);
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
    if (b.t === 'grid') return `<div class="grid5">${b.items.map(i => `<div><b>${escT(i.label)}</b>${i.html}</div>`).join('')}</div>`;
    if (b.t === 'table') {
      const blurCol = ctx.page.kind === 'data' && /interpretation/i.test(strip(b.head[b.head.length - 1])) ? b.head.length - 1 : -1;
      const planChk = ctx.page.kind === 'overview' && /^time$/i.test(strip(b.head[0]));
      const plan = LS.get('plan', {});
      return `${blurCol >= 0 ? '<div class="toolbar"><button class="btn ghost sm" data-act="reveal-all">Reveal all interpretations</button><button class="btn ghost sm" data-act="hide-all">Hide again</button></div>' : ''}
        <div class="tw"><table><thead><tr>${planChk ? '<th>✓</th>' : ''}${b.head.map(h => `<th>${h}</th>`).join('')}</tr></thead><tbody>${b.rows.map((r, ri) =>
        `<tr>${planChk ? `<td><input type="checkbox" class="chk" data-plan="${ri}" ${plan[ri] ? 'checked' : ''}></td>` : ''}${r.map((c, ci) => ci === blurCol ? `<td class="blur"><span>${c}</span></td>` : `<td>${c}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
    }
    return '';
  }
  function recallCards(items) {
    const st = LS.get('recall', {}), only = LS.get('recallOnly', false);
    const got = items.filter((_, i) => st[i] === 'got').length, again = items.filter((_, i) => st[i] === 'again').length;
    return `<div class="toolbar"><span class="pill g">Knew it: ${got}</span><span class="pill a">Revise again: ${again}</span><span class="pill">Not rated: ${items.length - got - again}</span>
      <button class="btn ghost sm" data-act="recall-only">${only ? 'Show all prompts' : 'Show only “revise again”'}</button><button class="btn ghost sm" data-act="recall-reset">Reset ratings</button></div>
      <p class="lede">Answer each prompt aloud or on paper from memory, then check your notes and rate yourself.</p>
      <div class="cards">${items.map((it, i) => (only && st[i] !== 'again') ? '' : `<div class="card ${st[i] || ''}"><div class="case-no">PROMPT ${i + 1}</div><div class="q">${it}</div>
      <div class="acts"><button class="btn sm ${st[i] === 'got' ? 'ok' : 'ghost'}" data-recall="${i}" data-v="got">✓ Knew it</button><button class="btn sm sec" data-recall="${i}" data-v="again">↺ Revise again</button></div></div>`).join('')}</div>`;
  }

  // ---------- pages ----------
  function sectionHTML(page, s, i) {
    const ctx = { page, sec: s };
    let inner;
    if (page.kind === 'cases' && s.blocks.length > 1) {
      let k = s.blocks.findIndex((b, j) => j > 0 && (isNext(b) || (b.t === 'p' && /^(<strong>)?\s*(Reasoning|Answer|Next step|Management|Approach)\b/i.test(b.html))));
      if (k < 0) k = 1;
      const stem = s.blocks.slice(0, k).map(b => block(b, ctx)).join('');
      const rest = s.blocks.slice(k).map(b => block(b, { ...ctx, noReveal: true })).join('');
      inner = `<div class="case-stem">${stem}</div>${reveal(rest, 'Show reasoning & answer')}`;
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
      <div class="stat"><strong>${avg == null ? '—' : avg + '%'}</strong><span>Avg best quiz score</span></div></div>`;
  }
  function quizzesPage() {
    const q = quizStats();
    return `<section class="sec"><h2>${P.mcqCount} MCQs · ${P.quizSets.length} sets of up to 15</h2><p class="lede">NEET-SS marking: +4 correct, −1 wrong, 0 unattempted. Instant feedback with explanation and exam pearl; skip and return; wrong-answer report.</p>
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
    body += page.sections.map((s, i) => sectionHTML(page, s, i)).join('');
    if (page.kind === 'plan') body += planExtra();
    if (page.kind !== 'overview' && page.kind !== 'quizzes' && page.id !== 'references')
      body += `<div class="done-box"><button class="btn ${d.has(page.id) ? 'ok' : ''}" data-act="done">${d.has(page.id) ? '✓ Marked as done' : 'Mark this section as done'}</button></div>`;
    body += `<div class="pager">${prev ? `<a class="btn ghost" href="#/${prev.id}">← ${escT(prev.title)}</a>` : '<span></span>'}${next ? `<a class="btn" href="#/${next.id}">${escT(next.title)} →</a>` : ''}</div>`;
    const main = $('#main'); main.innerHTML = body;
    $('#progBar').style.width = progress().pct + '%';
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
    else if (t.dataset.act === 'recall-reset') { if (confirm('Clear all active-recall ratings?')) { LS.set('recall', {}); render(false); } }
    else if (t.dataset.plan != null) { const p = LS.get('plan', {}); p[t.dataset.plan] = t.checked; LS.set('plan', p); }
    else if (t.dataset.act === 'reset-progress') {
      if (confirm(`Reset all Day ${P.day} progress (sections, plan ticks, recall ratings and quiz scores)?`)) {
        ['done', 'plan', 'recall', 'recallOnly', 'quiz', 'last', 'summary'].forEach(k => localStorage.removeItem(NS + k)); render(false);
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
  window.addEventListener('storage', e => { if (e.key && e.key.startsWith(NS)) render(false); });
  if (!location.hash) location.replace('#/' + (byId[LS.get('last', '')] ? LS.get('last') : 'overview'));
  render();
})();
