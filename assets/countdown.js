/* Exam countdowns (home banners + compact chip on portal and quiz pages).
   Fills every element with data-countdown="banner" (data-exam="icp" | "neetss", default neetss) or data-countdown="chip"
   (the next upcoming exam); ticks once a second. Runs entirely in the browser; times are fixed to India Standard Time
   so every device shows the same count. */
(function () {
  const EXAMS = {
    icp: { name: 'ICP exam', short: 'ICP', at: Date.parse('2026-11-22T09:00:00+05:30'), label: 'Sun, 22 Nov 2026 · 9:00 AM IST', tone: 'teal' },
    neetss: { name: 'NEET-SS exam', short: 'NEET-SS', at: Date.parse('2026-12-11T09:00:00+05:30'), label: 'Fri, 11 Dec 2026 · 9:00 AM IST', tone: '' },
  };
  const DAY = 86400000;
  const pad = n => String(n).padStart(2, '0');

  const css = document.createElement('style');
  css.textContent = `
.cd-banner{display:flex;align-items:center;gap:14px;flex-wrap:wrap;background:#0f2d5e;color:#fff;border-radius:14px;padding:12px 16px;margin:0 0 12px}
.cd-banner.teal{background:#0f5e57}
.cd-banner .cd-t{font-size:13px;color:#bfdbfe;line-height:1.4}.cd-banner .cd-t b{display:block;color:#fff;font-size:16px}
.cd-banner.teal .cd-t{color:#ccfbf1}
.cd-units{display:flex;gap:8px;margin-left:auto}
.cd-u{background:rgba(255,255,255,.12);border-radius:10px;min-width:62px;padding:6px 4px;text-align:center}
.cd-u b{display:block;font-size:26px;line-height:1.1;font-variant-numeric:tabular-nums}
.cd-u span{font-size:11px;color:#bfdbfe;letter-spacing:.05em}
.cd-banner.teal .cd-u span{color:#ccfbf1}
.cd-banner.cd-over{justify-content:center;font-size:17px;font-weight:600}
.cd-chip{display:inline-block;background:#0f2d5e;border:1px solid #1e40af;border-radius:999px;padding:3px 10px;font-size:12px;color:#e0f2fe;white-space:nowrap;font-variant-numeric:tabular-nums}
.cd-chip.teal{background:#0f5e57;border-color:#14b8a6;color:#ccfbf1}
.cd-chip:empty{display:none}
@media (max-width:640px){
 .cd-banner{padding:10px 12px;gap:8px}.cd-banner .cd-t b{font-size:15px}
 .cd-units{margin:0;width:100%;justify-content:space-between}.cd-u{min-width:0;flex:1}.cd-u b{font-size:22px}
 .top .cd-chip{font-size:11px;padding:2px 8px}
}
@media print{.cd-banner,.cd-chip{display:none!important}}`;
  document.head.appendChild(css);

  function parts(ex) {
    const left = ex.at - Date.now(), s = Math.max(0, Math.floor(left / 1000));
    return { left, d: Math.floor(s / 86400), h: pad(Math.floor(s % 86400 / 3600)), m: pad(Math.floor(s % 3600 / 60)), s: pad(s % 60) };
  }
  // next exam that is not yet over (an exam stays "current" through its own day)
  const nextExam = () => Object.values(EXAMS).filter(ex => ex.at - Date.now() > -DAY).sort((a, b) => a.at - b.at)[0];

  function chip(el) {
    const ex = nextExam();
    if (!ex) { el.innerHTML = ''; el.className = 'cd-chip'; return; }
    const p = parts(ex);
    el.className = 'cd-chip ' + ex.tone;
    el.title = Object.values(EXAMS).map(e => `${e.name}: ${e.label}`).join('\n');
    el.textContent = p.left <= 0 ? `${ex.short} exam day — all the best` : `${ex.short} in ${p.d}d ${p.h}h ${p.m}m ${p.s}s`;
  }
  function banner(el) {
    const ex = EXAMS[el.dataset.exam || 'neetss'];
    if (!ex) return;
    const p = parts(ex);
    if (p.left <= -DAY) { el.innerHTML = ''; el.className = ''; return; }          // hidden from the day after the exam
    if (p.left <= 0) { el.className = `cd-banner cd-over ${ex.tone}`; el.textContent = `${ex.name} day — all the best!`; return; }
    if (!el.querySelector('.cd-units')) {
      el.className = `cd-banner ${ex.tone}`;
      el.setAttribute('role', 'timer');
      el.innerHTML = `<div class="cd-t"><b>${ex.name}</b>${ex.label}</div><div class="cd-units">` +
        [['d', 'DAYS'], ['h', 'HRS'], ['m', 'MIN'], ['s', 'SEC']].map(([k, l]) => `<div class="cd-u"><b data-k="${k}"></b><span>${l}</span></div>`).join('') + '</div>';
    }
    el.querySelectorAll('[data-k]').forEach(b => { b.textContent = p[b.dataset.k]; });
    el.setAttribute('aria-label', `${p.d} days ${+p.h} hours ${+p.m} minutes to the ${ex.name}`);
  }
  function tick() {
    document.querySelectorAll('[data-countdown]').forEach(el => (el.dataset.countdown === 'chip' ? chip : banner)(el));
  }
  const start = () => { tick(); setInterval(tick, 1000); };
  document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', start) : start();
})();
