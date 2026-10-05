/* NEET-SS exam countdown (home banner + compact chip on portal and quiz pages).
   Fills every element with data-countdown="banner" or data-countdown="chip"; ticks once a second.
   Runs entirely in the browser; times are fixed to India Standard Time so every device shows the same count. */
(function () {
  const EXAM = { name: 'NEET-SS exam', at: Date.parse('2026-12-11T09:00:00+05:30'), label: 'Fri, 11 Dec 2026 · 9:00 AM IST', short: '11 Dec 2026' };
  const DAY = 86400000;
  const pad = n => String(n).padStart(2, '0');

  const css = document.createElement('style');
  css.textContent = `
.cd-banner{display:flex;align-items:center;gap:14px;flex-wrap:wrap;background:#0f2d5e;color:#fff;border-radius:14px;padding:12px 16px;margin:0 0 16px}
.cd-banner .cd-t{font-size:13px;color:#bfdbfe;line-height:1.4}.cd-banner .cd-t b{display:block;color:#fff;font-size:16px}
.cd-units{display:flex;gap:8px;margin-left:auto}
.cd-u{background:rgba(255,255,255,.12);border-radius:10px;min-width:62px;padding:6px 4px;text-align:center}
.cd-u b{display:block;font-size:26px;line-height:1.1;font-variant-numeric:tabular-nums}
.cd-u span{font-size:11px;color:#bfdbfe;letter-spacing:.05em}
.cd-banner.cd-over{justify-content:center;font-size:17px;font-weight:600}
.cd-chip{display:inline-block;background:#0f2d5e;border:1px solid #1e40af;border-radius:999px;padding:3px 10px;font-size:12px;color:#e0f2fe;white-space:nowrap;font-variant-numeric:tabular-nums}
.cd-chip:empty{display:none}
@media (max-width:640px){
 .cd-banner{padding:10px 12px;gap:8px}.cd-banner .cd-t b{font-size:15px}
 .cd-units{margin:0;width:100%;justify-content:space-between}.cd-u{min-width:0;flex:1}.cd-u b{font-size:22px}
 .top .cd-chip{font-size:11px;padding:2px 8px}
}
@media print{.cd-banner,.cd-chip{display:none!important}}`;
  document.head.appendChild(css);

  function parts() {
    const s = Math.max(0, Math.floor((EXAM.at - Date.now()) / 1000));
    return { left: EXAM.at - Date.now(), d: Math.floor(s / 86400), h: pad(Math.floor(s % 86400 / 3600)), m: pad(Math.floor(s % 3600 / 60)), s: pad(s % 60) };
  }
  function tick() {
    const p = parts(), over = p.left <= 0, gone = p.left <= -DAY;   // exam day, then hidden from the next day
    document.querySelectorAll('[data-countdown]').forEach(el => {
      const kind = el.dataset.countdown;
      if (gone) { el.innerHTML = ''; el.className = kind === 'chip' ? 'cd-chip' : ''; return; }
      if (kind === 'chip') {
        el.className = 'cd-chip';
        el.title = `${EXAM.name}: ${EXAM.label}`;
        el.textContent = over ? 'Exam day — all the best' : `Exam in ${p.d}d ${p.h}h ${p.m}m ${p.s}s`;
        return;
      }
      if (over) { el.className = 'cd-banner cd-over'; el.textContent = `${EXAM.name} day — all the best!`; return; }
      if (!el.querySelector('.cd-units')) {
        el.className = 'cd-banner';
        el.setAttribute('role', 'timer');
        el.innerHTML = `<div class="cd-t"><b>${EXAM.name}</b>${EXAM.label}</div><div class="cd-units">` +
          [['d', 'DAYS'], ['h', 'HRS'], ['m', 'MIN'], ['s', 'SEC']].map(([k, l]) => `<div class="cd-u"><b data-k="${k}"></b><span>${l}</span></div>`).join('') + '</div>';
      }
      el.querySelectorAll('[data-k]').forEach(b => { b.textContent = p[b.dataset.k]; });
      el.setAttribute('aria-label', `${p.d} days ${+p.h} hours ${+p.m} minutes to the ${EXAM.name}`);
    });
  }
  const start = () => { tick(); setInterval(tick, 1000); };
  document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', start) : start();
})();
