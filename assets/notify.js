/* Reliable ntfy.sh notifications for quizzes, drills, active recall and the error notebook.
   - keepalive fetch: the request survives leaving the page (tapping "Quiz Sets", going back, locking the phone)
   - body capped below ntfy's 4096-byte limit (larger bodies would arrive as a file attachment)
   - failed sends go to a small outbox in localStorage and are retried on the next page load / when back online
   - a toast shows "Notification sent" or "will retry", so a missing notification is never silent */
(function () {
  const TOPIC = 'https://ntfy.sh/neetss', KEY = 'neetss:ntfy:outbox', MAX = 3900;
  const bytes = s => new Blob([s]).size;
  function cap(body) {
    if (bytes(body) <= MAX) return body;
    const lines = String(body).split('\n'), out = [];
    for (const l of lines) {
      if (bytes(out.concat(l, '…(message shortened)').join('\n')) > MAX) break;
      out.push(l);
    }
    return out.concat('…(message shortened)').join('\n');
  }
  const load = () => { try { return JSON.parse(localStorage.getItem(KEY)) || []; } catch (e) { return []; } };
  const save = q => { try { localStorage.setItem(KEY, JSON.stringify(q.slice(-20))); } catch (e) {} };

  function toast(text, ok) {
    if (!document.body) return;
    let t = document.getElementById('ntfy-toast');
    if (!t) {
      t = document.createElement('div'); t.id = 'ntfy-toast';
      t.style.cssText = 'position:fixed;left:50%;bottom:18px;transform:translateX(-50%);z-index:9999;padding:9px 14px;border-radius:10px;font:600 13px Segoe UI,Arial,sans-serif;box-shadow:0 6px 20px rgba(0,0,0,.18);max-width:92vw;text-align:center;transition:opacity .3s';
      document.body.appendChild(t);
    }
    t.textContent = text;
    t.style.background = ok ? '#dcfce7' : '#fef3c7'; t.style.color = ok ? '#14532d' : '#7c2d12'; t.style.border = '1px solid ' + (ok ? '#86efac' : '#fcd34d');
    t.style.opacity = '1'; clearTimeout(t._h); t._h = setTimeout(() => { t.style.opacity = '0'; }, 4000);
  }

  function post(m) {
    const url = `${TOPIC}?title=${encodeURIComponent(m.title)}${m.tags ? '&tags=' + encodeURIComponent(m.tags) : ''}`;
    return fetch(url, { method: 'POST', body: m.body, keepalive: true }).then(r => { if (!r.ok) throw new Error('ntfy ' + r.status); return r; });
  }

  /** Send one notification. Resolves true when ntfy accepted it, false when it was queued for retry. */
  function send(title, tags, body, opts) {
    const m = { title: String(title), tags: tags || '', body: cap(String(body)), at: Date.now() };
    const quiet = opts && opts.quiet;
    return post(m).then(() => { if (!quiet) toast('🔔 Notification sent', true); return true; })
      .catch(() => { const q = load(); q.push(m); save(q); if (!quiet) toast('⚠ Couldn’t send the notification — it will be retried automatically', false); return false; });
  }

  let flushing = false;
  function flush() {
    if (flushing || !navigator.onLine) return;
    const q = load(); if (!q.length) return;
    flushing = true;
    const m = q[0], late = Math.round((Date.now() - m.at) / 60000);
    const msg = Object.assign({}, m, { title: m.title + (late >= 2 ? ` (sent ${late} min late)` : '') });
    post(msg).then(() => { save(load().slice(1)); flushing = false; toast('🔔 Earlier notification delivered', true); setTimeout(flush, 1500); })
      .catch(() => { flushing = false; });
  }
  window.Notify = { send, flush, pending: () => load().length };
  window.addEventListener('online', flush);
  setTimeout(flush, 1200);
})();
