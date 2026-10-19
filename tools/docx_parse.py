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
            if st.startswith('heading 2') or st.startswith('heading 3') or st == 'h1x':
                sections.append({'title': t, 'blocks': []})
                lst = None
                continue
            listy, numbered = is_list(doc, el)
            m = re.match(r'^[PR]?(\d+)\.\s+(.+)$', t) if not listy else None   # "1. …", "P1. …" or "R1. …" (recall prompts)
            if listy or m:
                numbered = numbered or bool(m)
                item = rich(el)
                if m:
                    item = re.sub(r'^(<strong>)?[PR]?\d+\.\s+', r'\1', item)
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
            if st.startswith('heading 1') or st == 'part' or (st == 'title' and re.match(r'^SECTION [A-Z]\b', text(el))):
                # some packs style their part headings "part"; Day 18 five-hour edition styles "SECTION N — …" as Title
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
               'This numerical choice results from a unit, decimal, frequency or fluid-allocation error',
               'This option proposes “', 'This prioritizes “', 'This delays or de-escalates care despite',
               'Although superficially plausible, this choice conflicts', 'This would fit a different clinical setting',
               'Distractor revised to be closer to the tested concept')
RETEST = re.compile(r'^EXTRA NOTEBOOK RETEST\b', re.I)
RETEST_LABEL = re.compile(r'^EXTRA NOTEBOOK RETEST\s*[—–-]\s*NOT PART OF (?:THE )?(?:BASE )?\d+(?: MCQS)?\s*[.:]?\s*(?:[—–-]\s*)?', re.I)


def parse_calc(sections):
    """CALCULATION DRILL sections ("1. Feed volume" + Data/question, Formula/substitution/final answer, Trap)
    -> [{num, title, question, working, trap, answer, unit}]. The answer is the last "= <number> <unit>" of the working."""
    out = []
    titles = {}
    for s in sections:
        for b in s['blocks']:
            if b['t'] == 'table' and len(b['head']) >= 3 and re.search(r'problem', re.sub(r'<[^>]+>', '', b['head'][1]), re.I):
                for r in b['rows']:
                    plain = [html.unescape(re.sub(r'<[^>]+>', '', c)).strip() for c in r]
                    bold = re.findall(r'<strong>(.*?)</strong>', r[2]) or [plain[2]]
                    n = re.match(r'^\s*D?(-?[0-9]+(?:\.[0-9]+)?)\s*(%|[A-Za-zµ/]+(?:/[A-Za-z]+)*)?', html.unescape(re.sub(r'<[^>]+>', '', bold[-1])))
                    out.append({'num': len(out) + 1, 'title': f'Problem {plain[0]}', 'question': plain[1], 'working': plain[2],
                                'trap': plain[3] if len(plain) > 3 else '', 'answer': float(n[1]) if n else 0.0,
                                'unit': (n[2] or '') if n else '', 'tol': None})
    if out:
        return out
    for s in sections:
        for b in s['blocks']:
            t = html.unescape(re.sub(r'<[^>]+>', '', b.get('html', ''))) if b['t'] == 'p' and isinstance(b.get('html'), str) else ''
            m = re.match(r'^Drill (\d+)\.\s*(.+?)\s*[—–-]\s*Data/question:', t)
            if m:
                titles[int(m[1])] = m[2].strip()
    for s in sections:
        for b in s['blocks']:
            items = b.get('items', []) if b['t'] == 'list' else [b['html']] if b['t'] == 'p' and isinstance(b.get('html'), str) else []
            for i, it in enumerate(items):
                t = html.unescape(re.sub(r'<[^>]+>', '', it))
                dn = re.match(r'^Drill (\d+)\.\s*', t)
                if dn:
                    t = re.sub(r'^Drill \d+\.\s*Data:', 'Data/question:', t)
                k = re.match(r'^Data/question:\s*(.+?)\s*Formula:\s*(.+?)\s*Substitution:\s*(.+?)\s*Final answer:\s*(.+?)\s*Trap:\s*(.+)$', t)
                if not k:
                    continue
                q, formula, sub, final, trap = (x.strip() for x in k.groups())
                n = re.match(r'^\s*(-?[0-9]+(?:\.[0-9]+)?)\s*(?:±\s*([0-9.]+))?\s*(%|[A-Za-zµ/]+(?:/[A-Za-z]+)*)?\s*(?:±\s*([0-9.]+))?', final)
                if not n:
                    raise SystemExit(f'Calculation Drill {i + 1}: no numeric final answer in "{final}"')
                out.append({'num': len(out) + 1, 'title': (titles.get(int(dn[1])) if dn else None) or re.sub(r'\?$', '', q.rsplit(':', 1)[-1]).strip() or f'Problem {len(out) + 1}',
                            'question': q, 'working': f'Formula: {formula} Substitution: {sub} Final answer: {final}',
                            'trap': trap, 'answer': float(n[1]), 'unit': (n[3] or '').strip(), 'tol': float(n[2] or n[4]) if (n[2] or n[4]) else None})
        m = re.match(r'^(\d+)\.\s*(.+)$', s['title']) or re.match(r'^Drill (\d+)()\s*$', s['title'])
        if not m:
            continue
        g = {}
        for b in s['blocks']:
            t = html.unescape(re.sub(r'<[^>]+>', '', b.get('html', '') if isinstance(b.get('html'), str) else ''))
            k = re.match(r'^(Data & question|Formula, substitution, units & arithmetic|Final answer|Common trap)\s*:\s*(.+)$', t, re.I)
            if k:
                g[k[1].lower()] = k[2].strip()
        if g.get('data & question') and g.get('final answer'):
            n = re.match(r'^\s*(-?[0-9]+(?:\.[0-9]+)?)\s*(%|[A-Za-zµ/]+(?:/[A-Za-z]+)*)?', g['final answer'])
            out.append({'num': int(m[1]), 'title': m[2].strip() or f'Drill {m[1]}', 'question': g['data & question'],
                        'working': f"{g.get('formula, substitution, units & arithmetic', '')} Final answer: {g['final answer']}".strip(),
                        'trap': g.get('common trap', ''), 'answer': float(n[1]) if n else 0.0, 'unit': (n[2] or '') if n else '', 'tol': None})
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

def parse_mcqs(doc, parts, aliases=None):
    find = lambda pat: next((els for h, els in parts if re.match(pat, h, re.I)), None)
    # Questions: the first "SECTION A/B" part that really holds "1. [Level] …" / "Qn. …" lines (some documents
    # also name study-note parts "SECTION A — …"); explanations: SECTION C.
    has_q = lambda els: sum(1 for el in els if el.tag == W + 'p' and (re.match(r'^Q?\d+\.\s*(\[|\S)', text(el)) or re.match(r'^Q\d+\s+\[', text(el))
                                                        or re.match(r'^Q\d+\s*[—–-]\s*Spaced revision\b', text(el), re.I)
                                                        or re.match(r'^[QR]\d+\s{2,}[^|\s]', text(el)))) >= 5 and \
        any(el.tag == W + 'p' and re.match(r'^[A-D]\.\s', text(el)) for el in els)
    A = next((els for h, els in parts if re.match(r'^SECTION A', h, re.I) and has_q(els)), None)
    B, C = find(r'^SECTION B'), find(r'^SECTION C')
    named = next((els for h, els in parts if re.search(r'question booklet|\bmcqs?\b|questions\b|revision test', h, re.I)
                  and not re.search(r'explanation|answer', h, re.I) and has_q(els)), None)
    if A is not None and B is not None and has_q(B) and not any(el.tag == W + 'tbl' for el in B):
        A, B = A + B, None             # Day 18: base MCQs in Section A, notebook retests in Section B
    if A is None and named is not None and (B is None or not has_q(B)):
        A, B = named, None
        # Day 19: notebook retests ("R01  stem") in their own part after the base MCQs
        rp = next((els for h, els in parts if re.search(r'notebook retests', h, re.I) and not re.search(r'answer', h, re.I)
                   and els is not named), None)
        if rp is not None:
            A = A + rp
    expl = next((els for h, els in parts if re.search(r'explanation', h, re.I)), None)
    if expl is None:   # Day 19: "Full A/B/C/D rationale — every base MCQ" + "Notebook retest answers …"
        ex_parts = [els for h, els in parts if re.search(r'\brationale\b|retest answers', h, re.I)]
        expl = [el for els in ex_parts for el in els] or None
    if expl is not None:
        C = expl
    if A is None and B is not None and has_q(B) and not any(el.tag == W + 'tbl' for el in B) and \
            any(el.tag == W + 'p' and re.match(r'^Q\d+\.', text(el)) for el in B):
        A, B = B, None                 # questions are in Section B; answer key comes from Section C
    problems, qs, cur, fixed = [], [], None, []
    pending_retest = False
    rbase = 0          # Day 19: retest "R01" is numbered after the last base question (R01 -> Q76)
    for el in A or []:
        if el.tag != W + 'p':
            continue
        if cur is not None:
            for src, _ in doc.images(el):          # picture placed with the question in the document
                cur['doc_img'] = src
        t = text(el)
        if RETEST.match(t) and not RETEST_LABEL.sub('', t).strip():
            # "EXTRA NOTEBOOK RETEST — NOT PART OF THE BASE 120" on its own line: after a stem (no options yet) it
            # belongs to that question; between questions it marks the next one
            if cur is not None and not cur['options']:
                cur['retest'] = True
            else:
                pending_retest = True
            continue
        if cur is not None and re.match(r'^Question-linked\b', t, re.I):
            cur['doc_caption'] = t                 # caption of that picture, not part of the stem
            continue
        m = (re.match(r'^(\d+)\.\s*\[([^\]]+)\]\s*(.+)$', t) or re.match(r'^Q(\d+)\.\s*\[([^\]]+)\]\s*(.+)$', t)
             or re.match(r'^Q(\d+)\.\s*()(.+)$', t)
             or re.match(r'^Q(\d+)\s+\[([^\]]+)\]()\s*(?:\S.*)?$', t)    # Day 17: "Q01  [Level]  Topic" heading, stem below (Day 20: no topic)
             or re.match(r'^Q(\d+)\s*[—–-]\s*(Spaced revision)()\s*$', t, re.I))   # Day 18: "Q76 — Spaced revision" = notebook retest
        m19 = not m and re.match(r'^([QR])(\d+)\s{2,}([^|\s].*)$', t)   # Day 19: "Q01  stem"; "R01  stem" = notebook retest
        if m19:
            if m19[1] == 'Q':
                rbase = max(rbase, int(m19[2]))
            cur = {'num': int(m19[2]) + (rbase if m19[1] == 'R' else 0), 'level': '', 'question': m19[3].strip(), 'options': [],
                   'retest': m19[1] == 'R'}
            qs.append(cur)
            continue
        if m:
            stem, retest = m[3].strip(), False
            if RETEST.match(stem):     # "Qn. EXTRA NOTEBOOK RETEST — NOT PART OF THE BASE 75 [— stem]": label dropped
                stem, retest = RETEST_LABEL.sub('', stem).strip(), True
            lev = m[2].strip()
            if re.search(r'retest|spaced revision', lev, re.I):
                retest, lev = True, ''
            elif re.match(r'^(base|extra[ -]gap[- ]fill|gap[- ]fill|extra)$', lev, re.I):
                lev = ''
            cur = {'num': int(m[1]), 'level': lev, 'question': stem, 'options': [], 'retest': retest or pending_retest}
            pending_retest = False
            qs.append(cur)
            continue
        m = re.match(r'^([A-D])\.\s+(.+)$', t)
        if m and cur:
            if 'ABCD'.index(m[1]) == len(cur['options']) + 1 and cur.get('unlabelled'):
                cur['options'].append(cur.pop('unlabelled'))
                fixed.append(f"Q{cur['num']}: option {'ABCD'[len(cur['options']) - 1]} had no letter label in the document")
            if 'ABCD'.index(m[1]) != len(cur['options']):
                problems.append(f"Q{cur['num']}: option order")
            cur['options'].append(m[2].strip())
        elif t and cur and 0 < len(cur['options']) < 4:
            cur['unlabelled'] = t
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
    for el in C or []:
        if el.tag == W + 'p' and re.match(r'^Quick key\b', text(el), re.I):
            for n_, a_ in re.findall(r'\b(\d+)\s*([A-D])\b', text(el)):
                key[int(n_)] = a_
    for h, els in parts:
        if re.search(r'\bANSWER KEY\b', h, re.I) and not re.search(r'EXPLANATION|recall', h, re.I):
            for el in els:
                t_ = text(el) if el.tag == W + 'p' else ' '.join(text(p_) for p_ in el.iter(W + 'p'))
                for n_, a_ in re.findall(r'\bQ(\d+)\s+([A-D])\b', t_) + re.findall(r'\b(\d+)\s*:\s*([A-D])\b', t_):
                    key[int(n_)] = a_
                for l_, n_, a_ in re.findall(r'\b([QR])(\d+)\s*:\s*([A-D])\b', t_):    # Day 19: "Q01:C", "R01:B"
                    key[int(n_) + (rbase if l_ == 'R' else 0)] = a_
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
            m = re.match(r'^Q(\d+)\s*[—–-]\s*([A-D])\s*\|', t) or re.match(r'^Q(\d+)\s*•\s*([A-D])\s*•', t)   # Day 20 "Q01 — A | Topic"; Day 21 "Q001 • A • Topic"
            if m:
                e = {'ans': m[2], 'lev': None, 'core': [], 'why_not': {}, 'marked': [], 'q': Q.get(int(m[1]))}
                ex[int(m[1])] = e
                continue
            m = re.match(r'^Q(\d+)\s*[—–-]\s*([A-D])\.\s*(.+)$', t)
            if m:
                e = {'ans': m[2], 'lev': None, 'core': [], 'why_not': {}, 'marked': [], 'q': Q.get(int(m[1]))}
                ex[int(m[1])] = e
                if e['q'] and e['q']['options']['ABCD'.index(m[2])].rstrip('.') != m[3].strip().rstrip('.'):
                    problems.append(f"Q{m[1]}: header answer text does not match option {m[2]}")
                continue
            m = (re.match(r'^Q(\d+)\s*[—–-]\s*Correct\s+([A-D])\b', t)      # Day 17: "Q1 — Correct C | Topic"
                 or re.match(r'^Q(\d+)\s*[—–-][^|]*\|\s*Correct:?\s*([A-D])\b\s*(?:\|\s*Original failed question:\s*(.+))?$', t))   # Day 18: "Q01 — Topic | Correct: D [| Original failed question: Day 10 Q8 — name]"
            if m:
                e = {'ans': m[2], 'lev': None, 'core': [], 'why_not': {}, 'marked': [], 'q': Q.get(int(m[1]))}
                if m.lastindex >= 3 and m[3]:
                    e['retest'], e['retest_from'] = True, m[3].strip()
                ex[int(m[1])] = e
                continue
            # Day 19: "Q01  |  TGA  |  Core  |  Best: C" and "R01 — R1 repeat repair — Best: B"
            m = re.match(r'^Q(\d+)\s*\|.*\|\s*Best:\s*([A-D])\s*$', t) or re.match(r'^R(\d+)\s*[—–-]\s*(?:(R\d)\b[^—–]*[—–-]\s*)?Best:\s*([A-D])\s*$', t)
            if m:
                rr = t.startswith('R')
                n_ = int(m[1]) + (rbase if rr else 0)
                e = {'ans': m[3] if rr else m[2], 'lev': None, 'core': [], 'why_not': {}, 'marked': [], 'q': Q.get(n_)}
                if rr:
                    e['retest'], e['stage'] = True, m[2]
                ex[n_] = e
                continue
            m = re.match(r'^ORIGINAL FAILED QUESTION(?:\s*/\s*NOTIFICATION)?:\s*([^|]+)(.*)$', t, re.I)
            if m and e and m[2]:     # Day 20: "Day 15 — Q61 — name | ERR-D15-Q61 | Retest R1 | …"
                st = re.search(r'\bRetest\s+(R\d)\b', m[2])
                e['retest'], e['stage'] = True, st[1] if st else e.get('stage')
                e['retest_from'] = re.sub(r'^(Day\s*\d+)\s*[—–-]\s*(Q\d+)\b', r'\1 \2', m[1].strip())
                continue
            if m and e:
                e['retest_from'] = m[1].strip()
                continue
            m = re.match(r'^([A-D]):\s+(.+?)\s+—\s+(Correct|Not best)\s+—\s+(.+)$', t)   # Day 19: "A: <option> — Not best — reason"
            if m and e and e['q']:
                if m[2].rstrip('.') != e['q']['options']['ABCD'.index(m[1])].rstrip('.'):
                    problems.append(f"Q{e['q']['num']}: explanation line for {m[1]} does not match option text")
                    continue
                if m[3] == 'Correct':
                    e['marked'].append(m[1])
                    e['correct_reason'] = m[4].strip()
                else:
                    e['labelled'] = True
                    if not any(b in m[4] for b in BOILERPLATE):
                        e['why_not'][m[1]] = m[4].strip()
                continue
            m = re.match(r'^Q(\d+)\s+Answer\s+([A-D])\b\s*(.*)$', t)
            if m:
                tag = m[3].strip()
                e = {'ans': m[2], 'lev': None, 'core': [], 'why_not': {}, 'marked': [], 'q': Q.get(int(m[1]))}
                if re.search(r'retest', tag, re.I):
                    e['retest'] = True
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
            m = re.match(r'^([A-D])\.\s+(.+)$', t) if not e['core'] and not e['why_not'] and ' — ' not in t else None
            if m and e['q'] and 'restated' not in e:     # restatement of the keyed answer right after the header
                e['restated'] = (m[1], m[2].strip())
                continue
            m = re.match(r'^Source:\s*(Day\s*\d+)(?:\s*Q(\d+))?', t)
            if m:
                e['retest_from'] = m[1] + (f' Q{m[2]}' if m[2] else '')
                continue
            m = re.match(r'^([A-D])\.\s+(BEST|NOT BEST)\s+—\s+(.+)$', t)   # Day 21: "A. BEST — <option text>. reason"
            if m and e and e['q']:
                opt = e['q']['options']['ABCD'.index(m[1])]
                if not m[3].startswith(opt):
                    problems.append(f"Q{e['q']['num']}: explanation line for {m[1]} does not match option text")
                    continue
                reason = m[3][len(opt):].lstrip(' .:—–-').strip()
                if m[2] == 'BEST':
                    e['marked'].append(m[1])
                    e['correct_reason'] = reason
                else:
                    e['labelled'] = True
                    if reason and not any(b in reason for b in BOILERPLATE):
                        e['why_not'][m[1]] = reason
                continue
            if e and re.match(r'^Competing-option check:', t):   # Day 21: generated restatement of the stem, not an explanation
                continue
            m = re.match(r'^([A-D])\s*([×✗✓])\s*[—–]\s*(.+)$', t)     # Day 20: "A ✓ — reason" (no option text)
            if m and e and e['q']:
                if m[2] == '✓':
                    e['marked'].append(m[1])
                    e['correct_reason'] = m[3].strip()
                else:
                    e['labelled'] = True
                    if not any(b in m[3] for b in BOILERPLATE):
                        e['why_not'][m[1]] = m[3].strip()
                continue
            m = re.match(r'^([A-D])\s*([×✗✓])\s*(.+)$', t)     # Day 18: "A × <option text>: reason" / "D ✓ <option text>: reason"
            if m and e['q']:
                opt, rest = e['q']['options']['ABCD'.index(m[1])], m[3].strip()
                if not rest.startswith(opt + ':'):
                    problems.append(f"Q{e['q']['num']}: explanation line for {m[1]} does not match option text")
                    continue
                rest = rest[len(opt) + 1:].strip()
                if m[2] == '✓':
                    e['marked'].append(m[1])
                    e['correct_reason'] = rest
                else:
                    e['labelled'] = True
                    if not any(b in rest for b in BOILERPLATE):
                        e['why_not'][m[1]] = rest
                continue
            m = re.match(r'^([A-D])\s*\((CORRECT|Incorrect|Wrong)\)\s*:\s*(.+)$', t, re.I)   # Day 17: "A (Incorrect): …"
            if m and e['q']:
                if m[2].lower() == 'correct':
                    e['marked'].append(m[1])
                    e['correct_reason'] = m[3].strip()
                else:
                    e['labelled'] = True
                    if not any(b in m[3] for b in BOILERPLATE):
                        e['why_not'][m[1]] = m[3].strip()
                continue
            m = re.match(r'^Option ([A-D])\s*[—–-]\s*(.+)$', t) or re.match(r'^([A-D]):\s+(.+)$', t)
            if m and e['q']:
                reason = m[2].strip()
                if re.match(r'^correct\b', reason, re.I):
                    e['marked'].append(m[1])
                    e['correct_reason'] = re.sub(r'^correct\b[.:!]?\s*', '', reason, flags=re.I)
                else:
                    e['labelled'] = e.get('labelled') or bool(re.match(r'^(Incorrect|Wrong)\b', reason, re.I))
                    reason = re.sub(r'^(Incorrect|Wrong)[.:]\s*', '', reason)
                    if not any(b in reason for b in BOILERPLATE):
                        e['why_not'][m[1]] = reason
                continue
            m = re.match(r'^([A-D])\.\s+(.+)$', t)
            if m and e['q']:
                opt = e['q']['options']['ABCD'.index(m[1])]
                rest = m[2]
                alias = ((aliases or {}).get(str(e['q']['num'])) or {}).get(m[1])
                if alias and rest.startswith(alias + ' — '):   # explanation words the option differently (known, reviewed)
                    rest = opt + rest[len(alias):]
                if not rest.startswith(opt + ' — '):
                    problems.append(f"Q{e['q']['num']}: explanation line for {m[1]} does not match option text")
                    continue
                reason = rest[len(opt) + 3:].strip()
                if re.match(r'^correct\b', reason, re.I):
                    e['marked'].append(m[1])
                    e['correct_reason'] = re.sub(r'^correct\b[.:!]?\s*', '', reason, flags=re.I)
                else:
                    if re.match(r'^(Incorrect|Wrong)\b', reason, re.I):
                        e['labelled'] = True
                    reason = re.sub(r'^(Incorrect|Wrong)\.\s*', '', reason)
                    if not any(b in reason for b in BOILERPLATE):
                        e['why_not'][m[1]] = reason
                continue
            if RETEST.match(t):
                e['retest'] = True
                m = re.search(r'Source:\s*ERR-D(\d+)-Q(\d+)', t)
                if m and not e.get('retest_from'):
                    e['retest_from'] = f'Day {m[1]} Q{m[2]}'
                continue
            m = re.match(r'^(?:Notebook trace-back|Error-notebook source)[^:]*:\s*(.+)$', t)
            if m:
                body = re.sub(r'—\s*—', '—', re.sub(r'\bERR-D(\d+)-Q(\d+)\b:?', r'Day \1 Q\2 —', m[1]))
                st = re.search(r'\b(R\d)\b', body)
                e['retest_from'] = re.split(r'\s*[•;]\s*', body)[0].strip().rstrip(' —–-')
                e['stage'] = st[1] if st else None
                continue
            m = re.match(r'^(?:EXAM )?PEARL\s*[—:-]\s*(.+)$', t, re.I)
            if m:
                e['pearl'] = m[1].strip()
                continue
            m = re.match(r'^WHY THIS (?:QUESTION )?MATTERS\s*[:—-]\s*(.+)$', t, re.I)
            if m:
                e['why'] = re.sub(r'\s*Distinguish the nearest plausible competing option using [^.]*\.', '', m[1]).strip()
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
    unlabelled = []
    for q in qs:
        n, e = q['num'], ex.get(q['num'])
        if len(q['options']) != 4:
            problems.append(f'Q{n}: {len(q["options"])} options')
        if not e:
            problems.append(f'Q{n}: no explanation')
            continue
        if key and key.get(n) != e['ans']:
            problems.append(f'Q{n}: answer key {key.get(n)} != explanation {e["ans"]}')
        if e.get('restated'):
            rl, rt = e['restated']
            if rl != e['ans']:
                problems.append(f'Q{n}: restated answer letter {rl} != header answer {e["ans"]}')
            elif rt.rstrip('.') != q['options']['ABCD'.index(rl)].rstrip('.'):
                fixed.append(f'Q{n}: restated answer wording differs from option {rl}')
        if not e['marked'] and e.get('labelled'):
            problems.append(f'Q{n}: no option marked Correct in the explanation')
        if not e['marked'] and not e.get('labelled'):
            unlabelled.append(n)
            e['why_not'].pop(e['ans'], None)       # keyed option's line explains why it is right
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
        core = ' '.join(e['core']).strip() or e.get('correct_reason', '')   # no core paragraph: use the keyed option's "Correct:" reason
        # why_not is keyed by option INDEX so it survives option shuffling; compose_explanation() adds letters.
        why_not = {'ABCD'.index(k): v for k, v in e['why_not'].items()}
        if e.get('disc'):
            core = (core + ' Closest distractor: ' + e['disc']).strip()
        item = {'num': n, 'level': q['level'], 'question': q['question'], 'options': q['options'],
                'answer': 'ABCD'.index(e['ans']), 'core': core, 'why_not': why_not, 'pearl': pearl}
        # "Refer to Visual A. Refer to Visual Station 1. Visual A — purpose-built …; not a patient image." at the end
        # of a stem points at the picture: move it out of the question text (the picture itself is placed by the build)
        refs = re.findall(r'\s*(?:Refer to Visual(?: Station)? [A-Z0-9]+\.|Visual [A-Z] — [^.]*?not a (?:clinical )?patient [^.]*\.)', item['question'])
        if refs:
            item['question'] = re.sub(r'\s*(?:Refer to Visual(?: Station)? [A-Z0-9]+\.|Visual [A-Z] — [^.]*?not a (?:clinical )?patient [^.]*\.)', '', item['question']).strip()
            q.setdefault('doc_caption', 'Purpose-built educational schematic; not a patient image.')
        for k in ('doc_img', 'doc_caption'):
            if q.get(k):
                item[k] = q[k]
        if q.get('retest') or e.get('retest') or RETEST.match(e['lev'] or ''):
            # notebook retest: shown as a normal question, tracked internally (stage defaults to R1 = first retest)
            src = e.get('retest_from', '')
            if not src:   # older docs: "WHY THIS QUESTION MATTERS: Spaced repair of Day 5 — DOPE" / "retrieval of the Day 5 Q34 …"
                m = re.search(r'(?:repair|retrieval) of (?:the )?(Day\s*\d+(?:\s*Q\d+)?(?:\s*[—-]\s*[^.;]+)?)', e.get('why', ''))
                src = m[1].strip() if m else ''
            item['retest'] = {'stage': e.get('stage') or 'R1', 'from': src}
        item['explanation'] = compose_explanation(item)
        out.append(item)
    out.sort(key=lambda q: q['num'])      # Day 20 interleaves the retests (Q76 after Q08); sets run in number order
    nums = [q['num'] for q in out]
    if nums != list(range(1, len(nums) + 1)):
        problems.append('question numbering not contiguous')
    if len(set(q['question'] for q in out)) != len(out):
        problems.append('duplicate question stems')
    if unlabelled:
        fixed.append(f'{len(unlabelled)} explanations mark no option as Correct/Incorrect; the "Answer X" header is the key')
    stats = {'mcq': len(qs), 'key': len(key), 'explanations': len(ex), 'built': len(out), 'source_fixes': fixed,
             'pearls_relabelled': shifted, 'why_not_kept': sum(1 for e in ex.values() if e['why_not'])}
    return out, problems, stats
