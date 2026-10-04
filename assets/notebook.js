/* NEET-SS + ICP Paediatrics — automatic K/C/R/G/S error notebook (shared by quizzes, mocks, grand mock and portals).
   Wrong answers are recorded automatically when a test finishes; the K/C/R/G/S tag and note are added by the learner.
   Stored in this browser only (localStorage key below). */
(function () {
  const KEY = 'neetss:notebook:v1', H = 3600e3;
  const TAGS = { K: 'Knowledge', C: 'Concept', R: 'Reasoning', G: 'Guess', S: 'Silly' };
  const L = i => String.fromCharCode(65 + i);
  const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const day = t => { const d = new Date(t); return `${d.getDate()} ${MON[d.getMonth()]} ${d.getFullYear()}`; };
  function range(a, b) {
    const x = new Date(a), y = new Date(b);
    if (x.getMonth() === y.getMonth() && x.getFullYear() === y.getFullYear()) return `${x.getDate()}–${y.getDate()} ${MON[y.getMonth()]} ${y.getFullYear()}`;
    return `${day(a)} – ${day(b)}`;
  }

  const NB = {
    TAGS,
    load() { try { const d = JSON.parse(localStorage.getItem(KEY)); return d && d.entries ? d : { entries: {} }; } catch (e) { return { entries: {} }; } },
    save(d) { try { localStorage.setItem(KEY, JSON.stringify(d)); } catch (e) {} },
    /** Record a finished test. items: [{num, srcNum, question, options, chosen, answer, explanation, pearl, correct}]
        Returns ids of the entries for this test's wrong answers. Correct answers mark existing entries as fixed. */
    record(ctx, items) {
      const d = this.load(), now = Date.now(), ids = [];
      for (const it of items) {
        if (it.chosen == null) continue;
        const id = ctx.srcId + ':' + it.srcNum, e = d.entries[id];
        if (it.correct) { if (e && !e.fixed) { e.fixed = true; e.fixedAt = now; } continue; }
        if (e) Object.assign(e, { count: e.count + 1, lastAt: now, chosen: it.chosen, set: ctx.set, num: it.num, href: ctx.href, fixed: false, fixedAt: null, retest: now + 48 * H });
        else d.entries[id] = { id, srcId: ctx.srcId, src: ctx.label, set: ctx.set, href: ctx.href, num: it.num, srcNum: it.srcNum,
          question: it.question, options: it.options, chosen: it.chosen, answer: it.answer, explanation: it.explanation || '', pearl: it.pearl || '',
          tag: null, note: '', count: 1, firstAt: now, lastAt: now, retest: now + 48 * H, fixed: false, fixedAt: null };
        // tag/note chosen during the quiz (learning mode) — the latest attempt's reason wins
        if (it.tag) d.entries[id].tag = it.tag;
        if (it.note) d.entries[id].note = it.note;
        ids.push(id);
      }
      this.save(d);
      return ids;
    },
    update(id, patch) { const d = this.load(); if (d.entries[id]) { Object.assign(d.entries[id], patch); this.save(d); } },
    remove(id) { const d = this.load(); delete d.entries[id]; this.save(d); },
    list(filter) { return Object.values(this.load().entries).filter(e => !filter || !filter.srcId || e.srcId === filter.srcId).sort((a, b) => b.lastAt - a.lastAt); },
    /** One mistake per line:  Day → Question → Chosen answer → Correct answer → Error type → optional note
        e.g.  Day 6 → Q16 → C → B → R → DAT is etiology, not a threshold   (untagged = ?, repeats add "(2×)") */
    HEADER: 'Day → Question → Chosen → Correct → Type → Note',
    line(e) { return `${e.src} → Q${e.num} → ${L(e.chosen)} → ${L(e.answer)} → ${e.tag || '?'}${e.count > 1 ? ` (${e.count}×)` : ''}${e.note ? ' → ' + e.note : ''}`; },
    lines(es, budget) {
      const out = [];
      for (let i = 0; i < es.length; i++) {
        const l = this.line(es[i]);
        if (new Blob([out.concat(l).join('\n')]).size > budget) { out.push(`…and ${es.length - i} more`); break; }
        out.push(l);
      }
      return out;
    },
    summary(es) {
      const tot = {};
      es.forEach(e => { const t = e.tag || '?'; tot[t] = (tot[t] || 0) + 1; });
      return 'Total: ' + ['K', 'C', 'R', 'G', 'S', '?'].filter(t => tot[t]).map(t => t + tot[t]).join(' ') +
        ' · Retest: ' + range(Math.min(...es.map(e => e.retest)), Math.max(...es.map(e => e.retest)) + 24 * H);
    },
    /** Separate error-notes message (grand mock, "Send updated notes"). */
    message(ids) {
      const d = this.load(), es = ids.map(i => d.entries[i]).filter(Boolean);
      if (!es.length) return 'No wrong answers.';
      return [this.HEADER, ...this.lines(es, 3300), this.summary(es)].join('\n');
    },
    /** Error notes inside the result notification (learning-mode quizzes, where tags are chosen during the quiz). */
    compact(ids) {
      const d = this.load(), es = ids.map(i => d.entries[i]).filter(Boolean);
      if (!es.length) return [];
      return [`Wrong (${es.length}): ${this.HEADER}`, ...this.lines(es, 3000), this.summary(es)];
    },
    send(ids, title) {
      return fetch(`https://ntfy.sh/neetss?title=${encodeURIComponent(title)}&tags=ledger`, { method: 'POST', body: this.message(ids) });
    },

    // ---------------- UI ----------------
    css() {
      if (document.getElementById('nb-css')) return;
      const s = document.createElement('style'); s.id = 'nb-css';
      s.textContent = `.nb{border:1px solid #c7d2fe;background:#f8faff;border-radius:14px;padding:14px;margin:14px 0;line-height:1.45}
.nb h3{margin:0 0 4px;font-size:17px}.nb .nb-sub{font-size:12.5px;color:#64748b;margin:0 0 10px}
.nb-row{background:#fff;border:1px solid #dbe4f0;border-radius:12px;padding:10px;margin:8px 0}
.nb-row .nb-q{font-size:14px}.nb-row .nb-q b{color:#1e3a8a}.nb-rep{display:inline-block;background:#fee2e2;color:#991b1b;border-radius:999px;padding:1px 8px;font-size:11.5px;font-weight:700;margin-left:6px}
.nb-tags{display:flex;gap:6px;margin:8px 0 6px;flex-wrap:wrap}.nb-tags button{min-width:40px;min-height:38px;border-radius:9px;border:1.5px solid #cbd5e1;background:#fff;font-weight:800;font-size:15px;cursor:pointer;color:#334155}
.nb-tags button.on{background:#1d4ed8;border-color:#1d4ed8;color:#fff}.nb-note{width:100%;border:1.5px solid #dbe4f0;border-radius:9px;padding:8px 10px;font-size:15px;font-family:inherit}
.nb-actions{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:10px}.nb-btn{border:0;border-radius:10px;padding:10px 14px;font-weight:700;cursor:pointer;font-size:14px;background:#2563eb;color:#fff;font-family:inherit}
.nb-btn.ghost{background:#e2e8f0;color:#1e293b}.nb-status{font-size:13px;color:#15803d;font-weight:700}
.nb-legend{font-size:12px;color:#475569;margin:6px 0 0}.nb-legend b{color:#1e293b}
.nb-card{background:#fff;border:1px solid #dbe4f0;border-radius:14px;padding:14px;margin:0 0 12px}.nb-card.fixed{opacity:.7;border-color:#86efac;background:#f0fdf4}
.nb-meta{font-size:12px;color:#64748b;margin-bottom:4px}.nb-due{display:inline-block;background:#fef3c7;color:#92400e;border-radius:999px;padding:1px 8px;font-weight:700;margin-left:6px}
.nb-ok{display:inline-block;background:#dcfce7;color:#15803d;border-radius:999px;padding:1px 8px;font-weight:700;margin-left:6px}
.nb-ans{font-size:14px;margin:6px 0}.nb-exp{display:none;background:#f8fafc;border-left:4px solid #94a3b8;border-radius:7px;padding:9px;margin-top:8px;font-size:14px}.nb-card.open .nb-exp{display:block}
.nb-filters{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0 14px}.nb-filters button{border:1.5px solid #cbd5e1;background:#fff;border-radius:999px;padding:6px 12px;font-weight:700;font-size:13px;cursor:pointer}
.nb-filters button.on{background:#0f172a;color:#fff;border-color:#0f172a}.nb-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(80px,1fr));gap:8px;margin:6px 0 12px}
.nb-stat{background:#fff;border:1px solid #dbe4f0;border-radius:12px;padding:8px;text-align:center;font-size:12px;color:#64748b}.nb-stat b{display:block;font-size:20px;color:#172033}`;
      document.head.appendChild(s);
    },
    tagButtons(e) {
      return `<div class="nb-tags">${Object.keys(TAGS).map(t => `<button type="button" data-nb-tag="${t}" class="${e.tag === t ? 'on' : ''}" title="${TAGS[t]}">${t}</button>`).join('')}</div>`;
    },
    legend() { return `<p class="nb-legend">${Object.entries(TAGS).map(([k, v]) => `<b>${k}</b> ${v}`).join(' · ')}</p>`; },
    wire(root, onChange) {
      root.addEventListener('click', ev => {
        const b = ev.target.closest('[data-nb-tag]'); if (!b) return;
        const row = b.closest('[data-nb-id]'), id = row.dataset.nbId, cur = this.load().entries[id];
        const tag = cur && cur.tag === b.dataset.nbTag ? null : b.dataset.nbTag;
        this.update(id, { tag });
        row.querySelectorAll('[data-nb-tag]').forEach(x => x.classList.toggle('on', x.dataset.nbTag === tag));
        onChange && onChange();
      });
      root.addEventListener('change', ev => {
        const inp = ev.target.closest('.nb-note'); if (!inp) return;
        this.update(inp.closest('[data-nb-id]').dataset.nbId, { note: inp.value.trim().slice(0, 140) });
        onChange && onChange();
      });
    },
    /** Result-screen panel for the wrong answers of the test just finished. */
    panel(container, ids, title, opts) {
      if (!container) return;
      opts = opts || {};
      this.css();
      const d = this.load(), es = ids.map(i => d.entries[i]).filter(Boolean);
      if (!es.length) { container.innerHTML = ''; return; }
      const intro = opts.inResult
        ? `These ${es.length} wrong answer${es.length > 1 ? 's were' : ' was'} saved to your notebook with the K/C/R/G/S tag${es.length > 1 ? 's' : ''} you chose and included in the result notification. You can still change a tag or add a correction rule and send an update.`
        : opts.auto
        ?`These ${es.length} wrong answer${es.length > 1 ? 's were' : ' was'} saved to your notebook with the K/C/R/G/S tag${es.length > 1 ? 's' : ''} you chose, and your error notes were sent. You can still change a tag or add a correction rule and send an update.`
        : `These ${es.length} wrong answer${es.length > 1 ? 's were' : ' was'} saved to your notebook automatically. Tap why you got each one wrong (optional), then send your error notes.`;
      container.innerHTML = `<div class="nb"><h3>📒 Error notebook${opts.auto || opts.inResult ? '' : ' — tag your mistakes'}</h3>
        <p class="nb-sub">${intro}</p>
        ${es.map(e => `<div class="nb-row" data-nb-id="${esc(e.id)}"><div class="nb-q"><b>Q${e.num}</b> · chose ${L(e.chosen)} → correct ${L(e.answer)}${e.count > 1 ? `<span class="nb-rep">${e.count}× wrong</span>` : ''}</div>
          ${this.tagButtons(e)}<input class="nb-note" maxlength="140" placeholder="One-line correction rule (optional)" value="${esc(e.note)}"></div>`).join('')}
        ${this.legend()}
        <div class="nb-actions"><button type="button" class="nb-btn" data-nb-send>${opts.auto || opts.inResult ? 'Send updated notes' : 'Save error notes &amp; send'}</button><span class="nb-status"></span></div></div>`;
      this.wire(container);
      const btn = container.querySelector('[data-nb-send]'), st = container.querySelector('.nb-status');
      const go = async (auto) => {
        btn.disabled = true; st.textContent = 'Sending…';
        try { await this.send(ids, title); st.textContent = auto ? '✓ Error notes sent' : '✓ Updated notes sent'; if (!auto) btn.textContent = 'Send again'; }
        catch (e) { st.textContent = 'Saved. Sending failed — check your connection and tap send again.'; }
        btn.disabled = false;
      };
      btn.onclick = () => go(false);
      if (opts.auto) setTimeout(() => go(true), 1500);   // after the result message, so it arrives second
    },
    /** Full notebook page. filter: {srcId} for one day, or {} for everything. */
    page(container, filter, prefix) {
      if (!container) return;
      prefix = prefix || '';
      this.css();
      const state = { f: 'all' };
      const draw = () => {
        const all = this.list(filter), now = Date.now();
        const due = e => !e.fixed && now >= e.retest;
        const counts = { all: all.length, open: all.filter(e => !e.fixed).length, due: all.filter(due).length, untagged: all.filter(e => !e.tag && !e.fixed).length, fixed: all.filter(e => e.fixed).length };
        Object.keys(TAGS).forEach(t => counts[t] = all.filter(e => e.tag === t).length);
        const pick = { all: () => true, open: e => !e.fixed, due, untagged: e => !e.tag && !e.fixed, fixed: e => e.fixed };
        Object.keys(TAGS).forEach(t => pick[t] = e => e.tag === t);
        const shown = all.filter(pick[state.f]);
        const multi = !filter || !filter.srcId;
        container.innerHTML = `<div class="nb-stats">${['open', 'due', 'untagged', 'fixed', 'K', 'C', 'R', 'G', 'S'].map(k => `<div class="nb-stat"><b>${counts[k]}</b>${{ open: 'Open', due: 'Retest due', untagged: 'Untagged', fixed: 'Fixed' }[k] || TAGS[k]}</div>`).join('')}</div>
          <div class="nb-filters">${[['all', 'All'], ['open', 'Open'], ['due', 'Retest due'], ['untagged', 'Untagged'], ...Object.keys(TAGS).map(t => [t, t + ' · ' + TAGS[t]]), ['fixed', 'Fixed']].map(([k, l]) => `<button type="button" data-f="${k}" class="${state.f === k ? 'on' : ''}">${l} (${counts[k]})</button>`).join('')}</div>
          ${this.legend()}
          <div class="nb-actions" style="margin:4px 0 14px"><button type="button" class="nb-btn ghost" data-nb-export>Download as Word</button></div>
          ${shown.length ? shown.map(e => `<div class="nb-card ${e.fixed ? 'fixed' : ''}" data-nb-id="${esc(e.id)}">
            <div class="nb-meta">${multi ? `<b>${esc(e.src)}</b> · ` : ''}${esc(e.set)} · Q${e.num} · last wrong ${day(e.lastAt)}${e.count > 1 ? `<span class="nb-rep">${e.count}× wrong</span>` : ''}${e.fixed ? '<span class="nb-ok">✓ fixed</span>' : due(e) ? '<span class="nb-due">retest due</span>' : ` · retest from ${day(e.retest)}`}</div>
            <div><b>${esc(e.question)}</b></div>
            <div class="nb-ans">Your answer: ${L(e.chosen)}. ${esc(e.options[e.chosen])}<br>Correct: <b>${L(e.answer)}. ${esc(e.options[e.answer])}</b></div>
            ${this.tagButtons(e)}<input class="nb-note" maxlength="140" placeholder="One-line correction rule (optional)" value="${esc(e.note)}">
            <div class="nb-exp">${e.explanation ? `<b>Explanation:</b> ${esc(e.explanation)}` : ''}${e.pearl ? `<br><b>Exam pearl:</b> ${esc(e.pearl)}` : ''}</div>
            <div class="nb-actions"><button type="button" class="nb-btn ghost" data-nb-open>Explanation</button>
              <button type="button" class="nb-btn ghost" data-nb-fix>${e.fixed ? 'Reopen' : '✓ Mark fixed'}</button>
              ${e.href ? `<a class="nb-btn ghost" style="text-decoration:none" href="${esc(prefix + e.href)}">Retake ${/Full|Grand/i.test(e.set + e.src) ? 'test' : 'set'}</a>` : ''}
              <button type="button" class="nb-btn ghost" data-nb-del title="Remove from notebook">Remove</button></div></div>`).join('')
            : '<p class="nb-sub">No entries here yet. Wrong answers appear automatically when you finish a quiz set or mock.</p>'}`;
      };
      draw();
      this.wire(container, null);
      container.addEventListener('click', ev => {
        const t = ev.target.closest('button'); if (!t) return;
        const card = t.closest('[data-nb-id]'), id = card && card.dataset.nbId;
        if (t.dataset.f) { state.f = t.dataset.f; draw(); }
        else if (t.hasAttribute('data-nb-open')) card.classList.toggle('open');
        else if (t.hasAttribute('data-nb-fix')) { const e = this.load().entries[id]; this.update(id, { fixed: !e.fixed, fixedAt: e.fixed ? null : Date.now() }); draw(); }
        else if (t.hasAttribute('data-nb-del')) { if (confirm('Remove this question from your error notebook?')) { this.remove(id); draw(); } }
        else if (t.hasAttribute('data-nb-export')) this.exportWord(filter);
        else if (t.dataset.nbTag) draw();
      });
    },
    exportWord(filter) {
      const es = this.list(filter);
      let h = `<h1>Error Notebook — K/C/R/G/S</h1><p>${es.length} entries · exported ${day(Date.now())}</p>`;
      es.forEach((e, i) => { h += `<hr><h3>${i + 1}. ${esc(e.src)} · ${esc(e.set)} · Q${e.num} — ${e.tag ? e.tag + ' (' + TAGS[e.tag] + ')' : 'untagged'}${e.count > 1 ? ` · ${e.count}× wrong` : ''}${e.fixed ? ' · fixed' : ''}</h3>
        <p><b>${esc(e.question)}</b></p><p>Your answer: ${L(e.chosen)}. ${esc(e.options[e.chosen])}<br>Correct: ${L(e.answer)}. ${esc(e.options[e.answer])}</p>
        ${e.note ? `<p><b>Correction rule:</b> ${esc(e.note)}</p>` : ''}${e.explanation ? `<p><b>Explanation:</b> ${esc(e.explanation)}</p>` : ''}${e.pearl ? `<p><b>Exam pearl:</b> ${esc(e.pearl)}</p>` : ''}`; });
      const d = new Date(), p = n => String(n).padStart(2, '0');
      const b = new Blob([`<!doctype html><html><head><meta charset="utf-8"></head><body style="font-family:Calibri,Arial">${h}</body></html>`], { type: 'application/msword' });
      const u = URL.createObjectURL(b), a = document.createElement('a');
      a.href = u; a.download = `Error_Notebook_${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}.doc`; a.click(); URL.revokeObjectURL(u);
    }
  };
  window.Notebook = NB;
})();
