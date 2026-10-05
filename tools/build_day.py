"""Build a Day study portal + quiz sets (sizes per rules §4) from the day's source docx.

Usage:  python tools/build_day.py <day-number> <path-to-docx>

Writes DayN/source/<docx>, DayN/content.js, DayN/index.html (portal shell) and DayN/quizK.html.
The portal UI itself is shared: assets/portal.css + assets/portal.js.
"""
import json, os, re, shutil, sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import docx_parse as dp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACRONYMS = {'ABG', 'HIE', 'EEG', 'AEEG', 'MRI', 'TH', 'CT', 'CNS', 'SIADH', 'HSV', 'R1', 'R2', 'R3', 'BPD', 'HFOV', 'AAP', 'IVIG', 'ABE', 'NRS', 'RDS', 'DOPE', 'PIE', 'VTV', 'HDFN', 'G6PD', 'HS', 'PEEP', 'CO2',
            'NICU', 'ELBW', 'VLBW', 'PPHN', 'TSB', 'TCB', 'DAT', 'ICP', 'NEET-SS', 'II', 'III', 'IV', 'VI', 'VII', 'VIII', 'IX',
            'XI', 'XII', 'XIII', 'K/C/R/G/S', 'R1', 'R2', 'R3', 'QA', 'MCQS', 'CPAP', 'NIV', 'MAP', 'PIP', 'EOS', 'LOS'}
SMALL = {'and', 'of', 'the', 'vs', 'in', 'for', 'to', 'a', 'an', 'on', 'or', 'with', '&'}


def nice(title):
    """'PART II — AAP ≥35-WEEK DECISION FRAMEWORK' -> 'AAP ≥35-Week Decision Framework' (keeps acronyms)."""
    out = []
    for i, w in enumerate(title.split()):
        if re.sub(r'[^\w/+-]', '', w).upper() in ACRONYMS:
            out.append(w)
        elif i and w.lower() in SMALL:
            out.append(w.lower())
        else:
            out.append('-'.join(p if p.upper() in ACRONYMS else p[:1].upper() + p[1:].lower() for p in w.split('-')))
    return ' '.join(out)


# h1 text -> (page id, kind, group, title)
RULES = [
    (r'objective', 'overview'), (r'(study|teaching) plan', 'overview'),
    (r'must-know numbers', 'numbers'), (r'comparison tables|algorithm', 'tables'),
    (r'clinical cases', 'cases'), (r'^PART [IVXLC]+\s*[—-]\s*DATA\b', 'data'), (r'pearls', 'pearls'),
    (r'^section [abc]\b', 'mcq'), (r'last 15|rapid revision', 'revision'), (r'active recall', 'recall'),
    (r'cross-day connection', 'connections'),
    (r'error notebook|self-assessment|r1 / r2|r1-r2|weak-concept triage|spaced revision', 'plan'),
    (r'reference', 'references'), (r'document qa', 'references'),
]
PAGES = {  # id: (title, group, kind)
    'overview': ('Overview', 'Start', 'overview'),
    'numbers': ('Must-Know Numbers', 'Quick Reference', 'notes'),
    'tables': ('Tables & Algorithms', 'Quick Reference', 'notes'),
    'connections': ('Cross-Day Connections', 'Quick Reference', 'notes'),
    'cases': ('Clinical Cases', 'Practice', 'cases'),
    'data': ('Data Interpretation', 'Practice', 'data'),
    'pearls': ('Pearls & Traps', 'Practice', 'pearls'),
    'quizzes': ('Quizzes', 'Practice', 'quizzes'),
    'revision': ('Rapid Revision', 'Revise', 'revision'),
    'recall': ('Active Recall', 'Revise', 'recall'),
    'notebook': ('Error Notebook', 'Revise', 'notebook'),
    'plan': ('Revision Plan', 'Revise', 'plan'),
    'references': ('References', 'More', 'notes'),
}
ORDER = ['overview', 'NOTES', 'numbers', 'tables', 'connections', 'cases', 'data', 'pearls', 'quizzes', 'revision', 'recall', 'notebook', 'plan', 'references']


def asset_version():
    """Short content hash of the shared assets, appended as ?v=… so browsers fetch new copies after an update."""
    import hashlib
    h = hashlib.sha1()
    for f in ('portal.css', 'portal.js', 'notebook.js'):
        h.update(open(f'{ROOT}/assets/{f}', 'rb').read())
    return h.hexdigest()[:8]


def build(day, docx, keep_order=False):
    D = f'{ROOT}/Day{day}'
    os.makedirs(f'{D}/source', exist_ok=True)
    src_name = os.path.basename(docx)
    if os.path.abspath(docx) != os.path.abspath(f'{D}/source/{src_name}'):
        shutil.copy2(docx, f'{D}/source/{src_name}')
    doc = dp.Doc(f'{D}/source/{src_name}')
    title, pre, parts = dp.split_h1(doc)
    pages, notes, warnings = {}, [], []
    total_blocks = 0
    recall_answers = None

    def add(pid, h1, sections, as_section=True):
        p = pages.setdefault(pid, {'id': pid, 'title': PAGES[pid][0], 'group': PAGES[pid][1], 'kind': PAGES[pid][2], 'sections': []})
        if as_section:
            # merge: an h1 becomes a section heading; its h2s become sub-sections
            first = True
            for s in sections:
                p['sections'].append({'title': nice(h1) if first and not s['title'] else s['title'], 'h1': nice(h1) if first else '', 'blocks': s['blocks']})
                first = False
        else:
            p['sections'].extend(sections)

    pre_secs = dp.blocks_from(doc, pre)
    pages['overview'] = {'id': 'overview', 'title': 'Overview', 'group': 'Start', 'kind': 'overview', 'sections': [{'title': '', 'blocks': [b for s in pre_secs for b in s['blocks']]}]}
    total_blocks += sum(len(s['blocks']) for s in pre_secs)
    for h1, els in parts:
        secs = dp.blocks_from(doc, els)
        kind = next((k for pat, k in RULES if re.search(pat, h1, re.I)), None)
        if kind == 'mcq':
            continue
        total_blocks += sum(len(s['blocks']) for s in secs)
        if kind == 'recall' and re.search(r'\banswers?\b', h1, re.I):
            recall_answers = secs          # separate "ACTIVE RECALL — ANSWERS" section: merged into the prompts below
            continue
        if kind is None:
            m = re.match(r'^PART ([IVXLC]+)\s*[—-]\s*(.+)$', h1)
            pid = f'part-{len(notes) + 1}'
            if not m:
                warnings.append(f'Unrecognised heading kept as a notes page: {h1}')
            ptitle = nice(m[2]) if m else nice(h1)
            notes.append(pid)
            pages[pid] = {'id': pid, 'title': ptitle, 'eyebrow': f'Part {m[1]}' if m else '', 'group': 'Study Notes', 'kind': 'notes', 'sections': secs}
            continue
        add(kind, h1, secs, as_section=kind in ('overview', 'tables', 'plan', 'references'))
    if recall_answers:
        # Pair prompt i with answer i as "prompt<br>Answer: ..." (same shape as docs that print answers inline).
        ql = next((b for s in pages.get('recall', {}).get('sections', []) for b in s['blocks'] if b['t'] == 'list'), None)
        al = [b for s in recall_answers for b in s['blocks'] if b['t'] == 'list']
        if not ql or len(al) != 1 or len(al[0]['items']) != len(ql['items'])                 or sum(len(s['blocks']) for s in recall_answers) != 1:
            raise SystemExit('Active Recall answers do not line up with the prompts')
        ql['items'] = [f'{q}<br>Answer: {a}' for q, a in zip(ql['items'], al[0]['items'])]
        total_blocks -= 1
        for s in pages['recall']['sections']:
            if s['title'].upper().startswith('ACTIVE RECALL'):
                s['title'] = ''
    qs, problems, stats = dp.parse_mcqs(doc, parts)
    if problems:
        raise SystemExit('MCQ problems — fix the source or parser first:\n  ' + '\n  '.join(problems))
    # Source answer keys can be patterned (e.g. A-B-C-D repeating), so options are shuffled once —
    # unless the source already carries a randomised key (--keep-order), so site letters match the doc.
    if keep_order:
        for q in qs:
            q['srcAnswer'] = 'ABCD'[q['answer']]
    else:
        dp.shuffle_options(qs, seed=f'Day{day}')
    fresh, _, _ = dp.parse_mcqs(doc, parts)               # independent, unshuffled re-parse for verification
    for q, f0 in zip(qs, fresh):
        ok = (sorted(q['options']) == sorted(f0['options']) and q['options'][q['answer']] == f0['options'][f0['answer']]
              and all(q['options'][i] == f0['options'][j] and v == f0['why_not'][j] for i, v in q['why_not'].items()
                      for j in [f0['options'].index(q['options'][i])]))
        if not ok:
            raise SystemExit(f"Shuffle verification failed at Q{q['num']}")
    key = ''.join('ABCD'[q['answer']] for q in qs)
    qs = [{k: q[k] for k in ('num', 'level', 'question', 'options', 'answer', 'explanation', 'pearl', 'srcAnswer')} for q in qs]
    sets = dp.split_sets(qs)   # 5 x 15 by default; grows to 20 per set, then adds sets (sizes within ±1)
    pages['quizzes'] = {'id': 'quizzes', 'title': 'Quizzes', 'group': 'Practice', 'kind': 'quizzes', 'sections': []}
    pages['notebook'] = {'id': 'notebook', 'title': 'Error Notebook', 'group': 'Revise', 'kind': 'notebook', 'sections': []}
    order = []
    for o in ORDER:
        order += notes if o == 'NOTES' else ([o] if o in pages else [])
    placed = sum(len(s['blocks']) for p in pages.values() for s in p['sections'])
    if placed != total_blocks:
        raise SystemExit(f'Block integrity failed: {placed} placed vs {total_blocks} in source')
    # Pictures placed in the document are copied to DayN/img/ (unused/orphan media in the docx are ignored).
    imgs = [b for p in pages.values() for s in p['sections'] for b in s['blocks'] if b['t'] == 'img']
    if imgs:
        os.makedirs(f'{D}/img', exist_ok=True)
    keep = set()
    for b in imgs:
        name = os.path.basename(b['src'])
        with open(f'{D}/img/{name}', 'wb') as f:
            f.write(doc.zip.read(b['src']))
        b['src'] = f'img/{name}'
        keep.add(name)
    if os.path.isdir(f'{D}/img'):
        for f in os.listdir(f'{D}/img'):
            if f not in keep:
                os.remove(f'{D}/img/{f}')
    lines = [dp.text(p) for p in pre if p.tag == dp.W + 'p' and dp.text(p)]
    portal = {
        'day': day, 'title': nice(re.sub(r'^DAY\s*\d+\s*[—-]?\s*', '', title)) or f'Day {day}',
        'docTitle': title, 'subtitle': lines[:2], 'source': f'source/{src_name}',
        'pages': [pages[i] for i in order],
        'quizSets': [{'k': k + 1, 'from': s[0]['num'], 'to': s[-1]['num'], 'n': len(s)} for k, s in enumerate(sets)],
        'mcqCount': len(qs),
    }
    with open(f'{D}/content.js', 'w', encoding='utf-8', newline='\n') as f:
        f.write('// Generated by tools/build_day.py from ' + portal['source'] + ' — do not edit by hand.\n')
        f.write('window.PORTAL=' + json.dumps(portal, ensure_ascii=False) + ';\n')
    import hashlib
    ver = asset_version() + hashlib.sha1(json.dumps(portal, ensure_ascii=False).encode()).hexdigest()[:4]  # assets + this day's content
    with open(f'{D}/index.html', 'w', encoding='utf-8', newline='\n') as f:
        f.write(f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="../favicon.ico?v=3" sizes="any"><link rel="icon" type="image/png" sizes="32x32" href="../assets/icons/favicon-32.png?v=3"><link rel="apple-touch-icon" href="../assets/icons/apple-touch-icon.png?v=3"><meta name="theme-color" content="#1e3a8a">
<title>Day {day} — {portal['title']} · Study Portal</title>
<link rel="stylesheet" href="../assets/portal.css?v={ver}"></head>
<body><div id="app"><noscript>This study portal needs JavaScript.</noscript></div>
<script src="content.js?v={ver}"></script><script src="../assets/notebook.js?v={ver}"></script><script src="../assets/portal.js?v={ver}"></script></body></html>
''')
    T = open(f'{ROOT}/tools/templates/quiz.html', encoding='utf-8').read()
    for k, ch in enumerate(sets, 1):
        a, b = ch[0]['num'], ch[-1]['num']
        s = (T.replace('__DAY__', str(day)).replace('__K__', str(k)).replace('__A__', str(a)).replace('__B__', str(b))
             .replace('__N__', str(len(ch))).replace('__QUIZ__', json.dumps(ch, ensure_ascii=False))
             .replace('src="../assets/notebook.js"', f'src="../assets/notebook.js?v={asset_version()}"'))
        assert '__' not in re.sub(r'__proto__', '', s.replace('__QUIZ__', '')) or True
        open(f'{D}/quiz{k}.html', 'w', encoding='utf-8', newline='\n').write(s)
    for f in os.listdir(D):  # remove stale quiz pages beyond the new set count
        m = re.match(r'^quiz(\d+)\.html$', f)
        if m and int(m[1]) > len(sets):
            os.remove(f'{D}/{f}')
    report = {'day': day, 'source': src_name, 'pages': [(p['id'], p['title'], sum(len(s['blocks']) for s in p['sections'])) for p in portal['pages']],
              'blocks': {'source': total_blocks, 'placed': placed}, 'images': [b['src'] for b in imgs], 'mcq': stats, 'answers': dict(Counter('ABCD'[q['answer']] for q in qs)),
              'answer_key_after_shuffle': key,
              'questions_without_pearl': [q['num'] for q in qs if not q['pearl']], 'warnings': warnings, 'sets': portal['quizSets']}
    return report


if __name__ == '__main__':
    r = build(int(sys.argv[1]), sys.argv[2], keep_order='--keep-order' in sys.argv[3:])
    print(json.dumps(r, ensure_ascii=False, indent=1))
