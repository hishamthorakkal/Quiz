"""Parse a NEET-SS day docx into portal pages + quiz questions.

Reads the docx XML directly (no third-party packages). Every Word block is kept:
headings, paragraphs (bold/italic/sub/superscript), bullet/numbered lists, tables,
one-cell "callout" boxes and WHAT/WHY/HOW grids. MCQs come from Sections A-C.
"""
import html, re, zipfile
from xml.etree import ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
BLIP = '{http://schemas.openxmlformats.org/drawingml/2006/main}blip'
EMBED = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed'
DOCPR = '{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}docPr'


def esc(s):
    return html.escape(s, quote=False)


class Doc:
    def __init__(self, path):
        z = zipfile.ZipFile(path)
        self.styles = {}
        if 'word/styles.xml' in z.namelist():
            for s in ET.fromstring(z.read('word/styles.xml')).iter(W + 'style'):
                n = s.find(W + 'name')
                self.styles[s.get(W + 'styleId')] = n.get(W + 'val') if n is not None else ''
        self.body = list(ET.fromstring(z.read('word/document.xml')).find(W + 'body'))
        self.zip, self.rels = z, {}
        if 'word/_rels/document.xml.rels' in z.namelist():
            for r in ET.fromstring(z.read('word/_rels/document.xml.rels')):
                self.rels[r.get('Id')] = r.get('Target')

    def images(self, el):
        """Embedded pictures in an element -> [(zip path, alt text)] (only images actually placed in the document)."""
        out, alt = [], ''
        for d in el.iter():
            if d.tag == DOCPR:
                alt = d.get('descr') or d.get('title') or ''
            if d.tag == BLIP and d.get(EMBED) in self.rels:
                out.append(('word/' + self.rels[d.get(EMBED)].lstrip('/').replace('word/', '', 1), alt))
        return out

    def style(self, p):
        ps = p.find(W + 'pPr/' + W + 'pStyle')
        return self.styles.get(ps.get(W + 'val'), ps.get(W + 'val')).lower() if ps is not None else ''


def _on(rp, tag):
    e = rp.find(W + tag) if rp is not None else None
    return e is not None and e.get(W + 'val') not in ('0', 'false')


def text(p):
    return ''.join(t.text or '' for t in p.iter(W + 't')).strip()


def rich(p):
    """Paragraph -> HTML with bold/italic/sub/sup preserved."""
    out = []
    for r in p.iter(W + 'r'):
        t = ''.join((x.text or '') if x.tag == W + 't' else ('\n' if x.tag == W + 'br' else '\t' if x.tag == W + 'tab' else '')
                    for x in r if x.tag in (W + 't', W + 'br', W + 'tab'))
        if not t:
            continue
        s = esc(t).replace('\n', '<br>')
        rp = r.find(W + 'rPr')
        va = rp.find(W + 'vertAlign') if rp is not None else None
        if va is not None and va.get(W + 'val') in ('subscript', 'superscript'):
            s = f"<{'sub' if va.get(W + 'val') == 'subscript' else 'sup'}>{s}</{'sub' if va.get(W + 'val') == 'subscript' else 'sup'}>"
        if _on(rp, 'i'):
            s = f'<em>{s}</em>'
        if _on(rp, 'b'):
            s = f'<strong>{s}</strong>'
        out.append(s)
    h = ''.join(out).strip()
    return re.sub(r'</strong>(\s*)<strong>', r'\1', h)


def is_list(doc, p):
    st = doc.style(p)
    return 'list' in st or p.find(W + 'pPr/' + W + 'numPr') is not None, ('number' in st)


def cell_paras(tc):
    return [p for p in tc.iter(W + 'p') if text(p)]


def shade(tc):
    s = tc.find(W + 'tcPr/' + W + 'shd')
    return (s.get(W + 'fill') or '').upper() if s is not None else ''


GRID_LABELS = ('WHAT', 'WHY', 'HOW', 'RECOGNIZE', 'WHAT NEXT')


def table_block(tbl):
    rows = [tr.findall(W + 'tc') for tr in tbl.findall(W + 'tr')]
    if not rows:
        return None
    ncol = max(len(r) for r in rows)
    # one-cell callout box: label row + body row(s)
    if ncol == 1 and len(rows) >= 2:
        label = text(rows[0][0])
        title = ''
        if '|' in label:
            label, title = [x.strip() for x in label.split('|', 1)]
        body = []
        for r in rows[1:]:
            body += [rich(p) for p in cell_paras(r[0])]
        return {'t': 'callout', 'label': label, 'title': title, 'html': body, 'fill': shade(rows[0][0])}
    if ncol == 1 and len(rows) == 1:
        return {'t': 'callout', 'label': '', 'title': '', 'html': [rich(p) for p in cell_paras(rows[0][0])], 'fill': shade(rows[0][0])}
    # WHAT / WHY / HOW / RECOGNIZE / WHAT NEXT grid (header row form, or label-inside-cell form)
    head = [text(c).upper() for c in rows[0]]
    if len(rows) == 2 and tuple(head) == GRID_LABELS:
        return {'t': 'grid', 'items': [{'label': GRID_LABELS[i], 'html': '<br>'.join(rich(p) for p in cell_paras(c))} for i, c in enumerate(rows[1])]}
    if len(rows) == 1 and all(text(c).upper().startswith(GRID_LABELS[i]) for i, c in enumerate(rows[0])) and len(rows[0]) == 5:
        items = []
        for i, c in enumerate(rows[0]):
            h = '<br>'.join(rich(p) for p in cell_paras(c))
            h = re.sub(r'^<strong>' + re.escape(GRID_LABELS[i]) + r'\s*(<br>\s*)*</strong>\s*(<br>\s*)*', '', h, flags=re.I)
            items.append({'label': GRID_LABELS[i], 'html': h})
        return {'t': 'grid', 'items': items}
    cell = lambda c: '<br>'.join(rich(p) for p in cell_paras(c))
    return {'t': 'table', 'head': [cell(c) for c in rows[0]], 'rows': [[cell(c) for c in r] for r in rows[1:]]}


def blocks_from(doc, elements):
    """Convert a run of body elements (no heading-1s) into blocks grouped under heading-2 sections."""
    sections = [{'title': '', 'blocks': []}]
    lst = None
    for el in elements:
        if el.tag == W + 'p':
            t = text(el)
            for src, alt in doc.images(el):     # pictures (e.g. EEG/aEEG visual stations) become image blocks
                lst = None
                sections[-1]['blocks'].append({'t': 'img', 'src': src, 'alt': alt})
            if not t:
                continue
            st = doc.style(el)
            if st.startswith('heading 2') or st.startswith('heading 3'):
                sections.append({'title': t, 'blocks': []})
                lst = None
                continue
            listy, numbered = is_list(doc, el)
            m = re.match(r'^(\d+)\.\s+(.+)$', t) if not listy else None
            if listy or m:
                numbered = numbered or bool(m)
                item = rich(el)
                if m:
                    item = re.sub(r'^(<strong>)?\d+\.\s+', r'\1', item)
                if lst is None or lst['ordered'] != numbered:
                    lst = {'t': 'list', 'ordered': numbered, 'items': []}
                    sections[-1]['blocks'].append(lst)
                lst['items'].append(item)
                continue
            lst = None
            sections[-1]['blocks'].append({'t': 'p', 'html': rich(el)})
        elif el.tag == W + 'tbl':
            lst = None
            b = table_block(el)
            if b:
                sections[-1]['blocks'].append(b)
    return [s for s in sections if s['title'] or s['blocks']]


def split_h1(doc):
    """Return (title, preface_elements, [(h1_text, elements)])."""
    title, pre, parts, cur = '', [], [], None
    for el in doc.body:
        if el.tag == W + 'p':
            st = doc.style(el)
            if st == 'title' and not title:
                title = ' '.join(x.text or '' for x in el.iter(W + 't') if True)
                title = re.sub(r'\s+', ' ', ''.join((x.text or '') if x.tag == W + 't' else ' ' for x in el.iter() if x.tag in (W + 't', W + 'br'))).strip()
                continue
            if st.startswith('heading 1'):
                cur = (text(el), [])
                parts.append(cur)
                continue
        (cur[1] if cur else pre).append(el)
    return title, pre, parts


# ---------------------------------------------------------------- MCQs
def set_sizes(n):
    """Quiz-set sizes for n questions (learning mode, contiguous order).

    Default 5 sets of 15. Up to 75 questions: sets of at most 15. 76-100: always 5 sets (15-20 each).
    Over 100: as many sets as needed so none exceeds 20. Sizes differ by at most 1 (larger sets first).
    """
    if n <= 0:
        return []
    k = -(-n // 15) if n <= 75 else 5 if n <= 100 else -(-n // 20)
    base, extra = divmod(n, k)
    return [base + 1 if i < extra else base for i in range(k)]


def split_sets(items):
    out, i = [], 0
    for s in set_sizes(len(items)):
        out.append(items[i:i + s])
        i += s
    return out


def compose_explanation(q):
    """Core reasoning + 'Why not the others' with the CURRENT option letters (works after shuffling)."""
    expl = q['core']
    if q['why_not']:
        expl += ' Why not the others: ' + '; '.join(f"{'ABCD'[i]}. {q['options'][i]} — {v}" for i, v in sorted(q['why_not'].items()))
    return expl


def shuffle_options(qs, seed):
    """Shuffle each question's options once (deterministic per seed).

    Correct answers end up evenly spread over A-D, never more than 3 identical letters in a row,
    and never in a repeating 4-letter cycle. why_not reasons follow their option.
    """
    import random
    rng = random.Random(seed)
    n = len(qs)
    while True:
        targets = [i % 4 for i in range(n)]
        rng.shuffle(targets)
        runs = max(len(m.group(0)) for m in re.finditer(r'(.)\1*', ''.join(map(str, targets)))) if n else 0
        cyclic = n >= 8 and all(targets[i] == targets[i % 4] for i in range(n))
        if runs <= 3 and not cyclic:
            break
    for q, t in zip(qs, targets):
        old = list(range(4))
        others = [i for i in old if i != q['answer']]
        rng.shuffle(others)
        order = others[:t] + [q['answer']] + others[t:]          # order[new_index] = old_index
        q['srcAnswer'] = 'ABCD'[q['answer']]
        correct_text = q['options'][q['answer']]
        q['options'] = [q['options'][i] for i in order]
        q['why_not'] = {order.index(i): v for i, v in q['why_not'].items()}
        q['answer'] = t
        assert q['options'][t] == correct_text
        q['explanation'] = compose_explanation(q)
    return qs


# ----
BOILERPLATE = ('represents a different diagnosis or intervention', 'Not the single best answer for this exact decision point',
               'would require a different clinical or data pattern', 'This stage does not match the severity pattern in the stem',
               'This numerical choice results from a unit, decimal, frequency or fluid-allocation error')
RETEST = re.compile(r'^EXTRA NOTEBOOK RETEST\b', re.I)


def parse_calc(sections):
    """CALCULATION DRILL sections ("1. Feed volume" + Data/question, Formula/substitution/final answer, Trap)
    -> [{num, title, question, working, trap, answer, unit}]. The answer is the last "= <number> <unit>" of the working."""
    out = []
    for s in sections:
        m = re.match(r'^(\d+)\.\s*(.+)$', s['title'])
        if not m:
            continue
        f = {}
        for b in s['blocks']:
            t = html.unescape(re.sub(r'<[^>]+>', '', b.get('html', '') if isinstance(b.get('html'), str) else ''))
            k = re.match(r'^(Data/question|Formula/substitution/final answer|Trap)\s*:\s*(.+)$', t, re.I)
            if k:
                f[k[1].lower()] = k[2].strip()
        work = f.get('formula/substitution/final answer', '')
        nums = re.findall(r'=\s*([0-9]+(?:\.[0-9]+)?)\s*((?:mg|g|mL|kcal|mmol|mEq|µg|mcg|kg|L|min|h|%)[A-Za-z/]*)', work)
        if not f.get('data/question') or not nums:
            raise SystemExit(f'Calculation Drill {m[1]}: could not read the question or a numeric answer')
        out.append({'num': int(m[1]), 'title': m[2].strip(), 'question': f['data/question'], 'working': work,
                    'trap': f.get('trap', ''), 'answer': float(nums[-1][0]), 'unit': nums[-1][1]})
    return out

def parse_mcqs(doc, parts):
    find = lambda pat: next((els for h, els in parts if re.match(pat, h, re.I)), None)
    A, B, C = find(r'^SECTION A'), find(r'^SECTION B'), find(r'^SECTION C')
    if A is None and B is not None and find(r'^SECTION B\b.*\bQUESTIONS\b'):
        A, B = B, None                 # questions are in Section B; answer key comes from Section C
    problems, qs, cur = [], [], None
    for el in A or []:
        if el.tag != W + 'p':
            continue
        t = text(el)
        m = re.match(r'^(\d+)\.\s*\[([^\]]+)\]\s*(.+)$', t) or re.match(r'^Q(\d+)\.\s*()(.+)$', t)
        if m:
            stem = m[3].strip()
            if RETEST.match(stem):     # "Qn. EXTRA NOTEBOOK RETEST — …": label dropped, stem is on the next line
                stem = ''
            cur = {'num': int(m[1]), 'level': m[2].strip(), 'question': stem, 'options': []}
            qs.append(cur)
            continue
        m = re.match(r'^([A-D])\.\s+(.+)$', t)
        if m and cur:
            if 'ABCD'.index(m[1]) != len(cur['options']):
                problems.append(f"Q{cur['num']}: option order")
            cur['options'].append(m[2].strip())
        elif t and cur and not cur['options']:
            cur['question'] = (cur['question'] + ' ' + t).strip()
    key, klev = {}, {}
    for el in B or []:
        if el.tag == W + 'tbl':
            for tr in el.findall(W + 'tr'):
                c = [text(tc) for tc in tr.findall(W + 'tc')]
                for i in range(0, len(c) - 1, 3 if len(c) == 3 else 2):
                    if c[i].isdigit():
                        key[int(c[i])] = c[i + 1].strip()
                        if len(c) == 3:
                            klev[int(c[i])] = c[2].strip()
    Q = {q['num']: q for q in qs}
    ex, e, pearl_labels = {}, None, {}
    for el in C or []:
        if el.tag == W + 'p':
            t = text(el)
            m = re.match(r'^Q(\d+)\.\s*Answer:?\s*([A-D])\s*[—-]\s*(.+)$', t)
            if m:
                e = {'ans': m[2], 'lev': m[3].strip(), 'core': [], 'why_not': {}, 'marked': [], 'q': Q.get(int(m[1]))}
                ex[int(m[1])] = e
                continue
            # Day 7+ format: "12. Correct answer: B — <option text>" (no level on the header line)
            m = re.match(r'^Q?(\d+)\.\s*Correct answer:?\s*([A-D])\s*[—-]\s*(.+)$', t)
            if m:
                e = {'ans': m[2], 'lev': None, 'core': [], 'why_not': {}, 'marked': [], 'q': Q.get(int(m[1]))}
                ex[int(m[1])] = e
                if e['q'] and e['q']['options'][ 'ABCD'.index(m[2])] != m[3].strip():
                    problems.append(f"Q{m[1]}: 'Correct answer' text does not match option {m[2]}")
                continue
            if not e or not t:
                continue
            m = re.match(r'^([A-D])\.\s+(.+)$', t)
            if m and e['q']:
                opt = e['q']['options']['ABCD'.index(m[1])]
                rest = m[2]
                if not rest.startswith(opt + ' — '):
                    problems.append(f"Q{e['q']['num']}: explanation line for {m[1]} does not match option text")
                    continue
                reason = rest[len(opt) + 3:].strip()
                if reason.lower().startswith('correct'):
                    e['marked'].append(m[1])
                else:
                    reason = re.sub(r'^(Incorrect|Wrong)\.\s*', '', reason)
                    if not any(b in reason for b in BOILERPLATE):
                        e['why_not'][m[1]] = reason
                continue
            m = re.match(r'^EXAM PEARL\s*[—:-]\s*(.+)$', t)
            if m:
                e['pearl'] = m[1].strip()
                continue
            m = re.match(r'^WHY THIS QUESTION MATTERS\s*[:—-]\s*(.+)$', t)
            if m:
                e['why'] = m[1].strip()
                continue
            m = re.match(r'^Closest[- ]distractor discriminator\s*:\s*(?:Closest distractor:\s*)?(.+)$', t, re.I)
            if m:
                e['disc'] = m[1].strip()
                continue
            e['core'].append(re.sub(r'^(Core reasoning|Reasoning):\s*', '', t))
        elif el.tag == W + 'tbl' and e:
            b = table_block(el)
            if b and b['t'] == 'callout':
                body = ' '.join(re.sub(r'<[^>]+>', '', h) for h in b['html']).strip()
                body = html.unescape(body)
                if b['label'].upper().startswith('EXAM PEARL'):
                    m = re.match(r'^Q(\d+) pearl\s*[—-]\s*(.+)$', body)
                    if m:
                        pearl_labels[int(m[1])] = m[2].strip()
                        e.setdefault('pearl_in_block', m[2].strip())
                    else:
                        e['pearl'] = body
                elif b['label'].upper().startswith('WHY THIS'):
                    e['why'] = body
    out = []
    shifted = []
    for q in qs:
        n, e = q['num'], ex.get(q['num'])
        if len(q['options']) != 4:
            problems.append(f'Q{n}: {len(q["options"])} options')
        if not e:
            problems.append(f'Q{n}: no explanation')
            continue
        if key and key.get(n) != e['ans']:
            problems.append(f'Q{n}: answer key {key.get(n)} != explanation {e["ans"]}')
        if not e['marked']:
            problems.append(f'Q{n}: no option marked Correct in the explanation')
        if not q['level']:
            q['level'] = '' if RETEST.match(e['lev'] or '') else (e['lev'] or '')
        if e['marked'] and e['marked'] != [e['ans']]:
            problems.append(f'Q{n}: option marked correct {e["marked"]} != {e["ans"]}')
        if klev and not (q['level'] == klev.get(n) == (e['lev'] or q['level'])):
            problems.append(f'Q{n}: level mismatch {q["level"]}/{klev.get(n)}/{e["lev"]}')
        # Pearls labelled "Qn pearl — ..." are matched by their label (some docs print them under the wrong question).
        pearl = pearl_labels.get(n) or e.get('pearl', '')
        if n in pearl_labels and e.get('pearl_in_block') != pearl_labels[n]:
            shifted.append(n)
        core = ' '.join(e['core']).strip()
        # why_not is keyed by option INDEX so it survives option shuffling; compose_explanation() adds letters.
        why_not = {'ABCD'.index(k): v for k, v in e['why_not'].items()}
        if e.get('disc'):
            core = (core + ' Closest distractor: ' + e['disc']).strip()
        item = {'num': n, 'level': q['level'], 'question': q['question'], 'options': q['options'],
                'answer': 'ABCD'.index(e['ans']), 'core': core, 'why_not': why_not, 'pearl': pearl}
        item['explanation'] = compose_explanation(item)
        out.append(item)
    nums = [q['num'] for q in out]
    if nums != list(range(1, len(nums) + 1)):
        problems.append('question numbering not contiguous')
    if len(set(q['question'] for q in out)) != len(out):
        problems.append('duplicate question stems')
    stats = {'mcq': len(qs), 'key': len(key), 'explanations': len(ex), 'built': len(out),
             'pearls_relabelled': shifted, 'why_not_kept': sum(1 for e in ex.values() if e['why_not'])}
    return out, problems, stats
