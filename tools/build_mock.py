"""Build a timed NEET-SS mock (3 sections x 50 questions x 50 minutes) from a mock docx.

Usage: python tools/build_mock.py <MockId> <docx> [--title "..."]
Writes Mock/<MockId>/{index.html, exam.html, source/<docx>} and refreshes Mock/index.html.
Optional Mock/<MockId>/source/extras.json:
  {"why_not": {"12": {"A": "reason", ...}}}  — wrong-option reasons written for the site when the document's are
  placeholders; shown as "Why not the others (added — not from source)".
Exam engine: tools/templates/mock_exam.html (the Grand Mock exam page: strict per-section timer, no return to a locked
section, no feedback until the end, section- and topic-wise results, answer review, error notebook, ntfy result).
"""
import html, json, os, re, shutil, sys
sys.path.insert(0, os.path.dirname(__file__))
import mock_parse as mp
from build_day import asset_version

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
esc = html.escape


def build(mock_id, docx, title=None):
    D = f'{ROOT}/Mock/{mock_id}'
    os.makedirs(f'{D}/source', exist_ok=True)
    name = os.path.basename(docx)
    if os.path.abspath(docx) != os.path.abspath(f'{D}/source/{name}'):
        shutil.copy2(docx, f'{D}/source/{name}')
    meta, qs, problems = mp.parse(f'{D}/source/{name}')
    if problems:
        raise SystemExit('Mock problems:\n  ' + '\n  '.join(problems))
    xf = f'{D}/source/extras.json'
    extras = json.load(open(xf, encoding='utf-8')) if os.path.exists(xf) else {}
    added = extras.get('why_not', {})
    Q, missing = [], []
    for q in qs:
        wn = dict(q['why_not'])
        src_why = bool(wn)
        for L, reason in added.get(str(q['num']), {}).items():
            i = 'ABCD'.index(L)
            if i == q['answer']:
                raise SystemExit(f"extras why_not: Q{q['num']} {L} is the keyed answer")
            wn.setdefault(i, reason)
        missing += [f"Q{q['num']}{'ABCD'[i]}" for i in range(4) if i != q['answer'] and i not in wn]
        expl = q['core']
        if wn:
            lab = 'Why not the others:' if src_why and len(wn) == len(q['why_not']) else 'Why not the others (added — not from source):'
            expl += f' {lab} ' + '; '.join(f"{'ABCD'[i]}. {q['options'][i]} — {v}" for i, v in sorted(wn.items()))
        Q.append({'num': q['num'], 'pos': q['num'], 'section': q['section'], 'topic': q.get('topic', ''),
                  'question': q['question'], 'options': q['options'], 'answer': q['answer'],
                  'explanation': expl, 'pearl': q.get('pearl', ''),
                  'note': f"From Day {q['day']} · {q.get('level', '')}" if q.get('day') else ''})
    if missing and added:
        raise SystemExit('extras why_not missing for: ' + ', '.join(missing))
    secs = sorted({q['section'] for q in Q})
    title = title or re.sub(r'\s+', ' ', meta['title']).strip()
    exam = {'id': mock_id, 'title': title, 'source': f'source/{name}', 'sectionMinutes': 50,
            'sections': [{'name': f'Section {"ABC"[s]}'} for s in secs],
            'marking': {'correct': 4, 'wrong': -1, 'unattempted': 0},
            'pattern': 'NEET-SS pattern — 3 time-bound sections of 50 questions / 50 minutes, +4/−1/0'}
    ver = asset_version()
    T = open(f'{ROOT}/tools/templates/mock_exam.html', encoding='utf-8').read()
    page = (T.replace('__TITLE__', esc(title)).replace('__EXAM__', json.dumps(exam, ensure_ascii=False))
            .replace('__Q__', json.dumps(Q, ensure_ascii=False))
            .replace('src="../../assets/notify.js"', f'src="../../assets/notify.js?v={ver}"')
            .replace('src="../../assets/notebook.js"', f'src="../../assets/notebook.js?v={ver}"'))
    open(f'{D}/exam.html', 'w', encoding='utf-8', newline='\n').write(page)
    # landing / instructions page: the document's status lines are shown as written
    pre_lines = [mp.dp.text(p) for p in meta['pre'] if p.tag == mp.dp.W + 'p' and mp.dp.text(p)]
    intro = next((els for h, els in meta['parts'] if not re.match(r'^(SECTION|ANSWER KEY|DETAILED)', h)), [])
    notes = [mp.dp.text(p) for p in intro if p.tag == mp.dp.W + 'p' and mp.dp.text(p)][:5]
    topics = {}
    for q in Q:
        topics[q['topic']] = topics.get(q['topic'], 0) + 1
    I = open(f'{ROOT}/tools/templates/mock_index.html', encoding='utf-8').read()
    idx = (I.replace('__TITLE__', esc(title)).replace('__ID__', mock_id).replace('__N__', str(len(Q)))
           .replace('__MIN__', str(50 * len(secs))).replace('__MAX__', str(4 * len(Q)))
           .replace('__SECS__', ', '.join(f'Section {"ABC"[s]} (Q{min(q["num"] for q in Q if q["section"] == s)}–{max(q["num"] for q in Q if q["section"] == s)})' for s in secs))
           .replace('__TOPICS__', ' · '.join(f'{esc(t)} {n}' for t, n in topics.items()))
           .replace('__NOTES__', ''.join(f'<p class="small">{esc(t)}</p>' for t in pre_lines + notes)))
    open(f'{D}/index.html', 'w', encoding='utf-8', newline='\n').write(idx)
    return {'id': mock_id, 'title': title, 'questions': len(Q), 'sections': len(secs), 'topics': topics,
            'added_why_not': sum(len(v) for v in added.values()), 'missing_why_not': len(missing)}


if __name__ == '__main__':
    a = sys.argv[1:]
    t = a[a.index('--title') + 1] if '--title' in a else None
    print(json.dumps(build(a[0], a[1], t), ensure_ascii=False, indent=1))
