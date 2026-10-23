"""Parse a NEET-SS cumulative/grand mock docx (150 MCQs in SECTION A/B/C, answer key, detailed explanations).

Format (Cumulative Mock Day 25, 23 Oct 2026):
  "Q1. stem" + caption "Day 20  |  Cardiology  |  Basic-but-easily-confused" + "A. …" options + "Answer: □ A …" line
  ANSWER KEY: "1: D     2: D …"
  DETAILED EXPLANATIONS: "Q1 — D. <option text>", "Rationale: …", "Why not A? <option> — <reason>",
  "EXAM PEARL: …", "WHY THIS QUESTION MATTERS: …", "Reference family: …"
Wrong-option reasons that are placeholders ("…requires independent source audit") are dropped.
"""
import re
import docx_parse as dp

PLACEHOLDER = ('exact distractor rationale requires independent source audit', 'less appropriate than the keyed option')


def parse(path):
    doc = dp.Doc(path)
    title, pre, parts = dp.split_h1(doc)
    qs, problems, cur, sec = [], [], None, -1
    key, ex = {}, {}
    for h, els in parts:
        ms = re.match(r'^SECTION ([ABC])\b', h)
        if ms:
            sec = 'ABC'.index(ms[1])
            for el in els:
                if el.tag != dp.W + 'p':
                    continue
                t = dp.text(el)
                m = re.match(r'^Q(\d+)\.\s*(.+)$', t)
                if m:
                    cur = {'num': int(m[1]), 'section': sec, 'question': m[2].strip(), 'options': []}
                    qs.append(cur)
                    continue
                m = re.match(r'^Day\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*(.+)$', t)
                if m and cur is not None and not cur['options']:
                    cur.update(day=int(m[1]), topic=m[2].strip(), level=m[3].strip())
                    continue
                m = re.match(r'^([A-D])\.\s+(.+)$', t)
                if m and cur is not None:
                    if 'ABCD'.index(m[1]) != len(cur['options']):
                        problems.append(f"Q{cur['num']}: option order")
                    cur['options'].append(m[2].strip())
                    continue
                if t and cur is not None and not cur['options'] and not t.startswith('Answer:'):
                    cur['question'] += ' ' + t
        elif re.match(r'^ANSWER KEY', h):
            for el in els:
                if el.tag == dp.W + 'p':
                    for n, a in re.findall(r'\b(\d+)\s*:\s*([A-D])\b', dp.text(el)):
                        key[int(n)] = a
        elif re.match(r'^DETAILED EXPLANATIONS', h):
            e = None
            for el in els:
                if el.tag != dp.W + 'p':
                    continue
                t = dp.text(el)
                m = re.match(r'^Q(\d+)\s*[—–-]\s*([A-D])\.\s*(.+)$', t)
                if m:
                    e = {'ans': m[2], 'text': m[3].strip(), 'why_not': {}, 'core': '', 'pearl': ''}
                    ex[int(m[1])] = e
                    continue
                if e is None:
                    continue
                m = re.match(r'^Rationale:\s*(.+)$', t)
                if m:
                    e['core'] = m[1].strip()
                    continue
                m = re.match(r'^Why not ([A-D])\?\s*(.+)$', t)
                if m:
                    reason = m[2].split(' — ', 1)[1].strip() if ' — ' in m[2] else ''
                    if reason and not any(p in reason for p in PLACEHOLDER):
                        e['why_not'][m[1]] = reason
                    continue
                m = re.match(r'^EXAM PEARL:\s*(.+)$', t, re.I)
                if m:
                    e['pearl'] = m[1].strip()
    Q = {q['num']: q for q in qs}
    for q in qs:
        n, e = q['num'], ex.get(q['num'])
        if len(q['options']) != 4:
            problems.append(f'Q{n}: {len(q["options"])} options')
        if not e:
            problems.append(f'Q{n}: no explanation')
            continue
        if key.get(n) != e['ans']:
            problems.append(f'Q{n}: key {key.get(n)} != explanation {e["ans"]}')
        a = 'ABCD'.index(e['ans'])
        if q['options'] and q['options'][a].rstrip('.') != e['text'].rstrip('.'):
            problems.append(f'Q{n}: explanation header text does not match option {e["ans"]}')
        q.update(answer=a, core=e['core'], pearl=e['pearl'],
                 why_not={'ABCD'.index(k): v for k, v in e['why_not'].items()})
    if [q['num'] for q in qs] != list(range(1, len(qs) + 1)):
        problems.append('question numbering not contiguous')
    return {'title': title, 'pre': pre, 'parts': parts, 'doc': doc}, qs, problems
