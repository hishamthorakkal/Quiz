"""Build a Day study portal + quiz sets (sizes per rules §4) from the day's source docx.

Usage:  python tools/build_day.py <day-number> <path-to-docx>

Writes DayN/source/<docx>, DayN/content.js, DayN/index.html (portal shell) and DayN/quizK.html.
The portal UI itself is shared: assets/portal.css + assets/portal.js.
"""
import html, json, os, re, shutil, sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import docx_parse as dp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACRONYMS = {'LP', 'ADEM', 'MOGAD', 'NMOSD', 'TBM', 'AES', 'JE', 'CSF', 'TOF', 'RVOT', 'RVOTO', 'MAPCA', 'MAPCAS', 'DORV', 'CMR', 'PGE1', 'PDA', 'VSD', 'AVSD', 'PAPVC', 'PVR', 'PVRI', 'ABG', 'HIE', 'EEG', 'AEEG', 'MRI', 'TH', 'CT', 'CNS', 'SIADH', 'HSV', 'R1', 'R2', 'R3', 'BPD', 'HFOV', 'AAP', 'IVIG', 'ABE', 'NRS', 'RDS', 'DOPE', 'PIE', 'VTV', 'HDFN', 'G6PD', 'HS', 'PEEP', 'CO2',
            'NICU', 'ELBW', 'VLBW', 'PPHN', 'TSB', 'TCB', 'DAT', 'ICP', 'NEET-SS', 'II', 'III', 'IV', 'VI', 'VII', 'VIII', 'IX',
            'XI', 'XII', 'XIII', 'K/C/R/G/S', 'R1', 'R2', 'R3', 'QA', 'MCQS', 'CPAP', 'NIV', 'PIP', 'EOS', 'LOS',
            'NEC', 'TPN', 'PN', 'NNF', 'IEM', 'ASD', 'ADHD', 'CHD', 'CCHD', 'ECG', 'CXR', 'IAP-NNF', 'SIP', 'GIR', 'PDHM', 'MOM', 'HMF', 'IUGR', 'SGA', 'IV/PN'}
SMALL = {'and', 'of', 'the', 'vs', 'in', 'for', 'to', 'a', 'an', 'on', 'or', 'with', '&'}


def nice(title):
    """'PART II — AAP ≥35-WEEK DECISION FRAMEWORK' -> 'AAP ≥35-Week Decision Framework' (keeps acronyms).

    Each letter/digit run inside a word is cased on its own, so "(TPN/PN)" and "EEG-aEEG" keep their acronyms."""
    out = []
    for i, w in enumerate(title.split()):
        if re.sub(r'[^\w/+-]', '', w).upper() in ACRONYMS:
            out.append(w)
        elif i and w.lower() in SMALL and not (w == 'A' and re.match(r'(?i)algorithm|station|part|table|figure|section', title.split()[i - 1])):
            out.append(w.lower())
        else:
            out.append(re.sub(r'[^\W_]+', lambda m: m[0] if m[0].upper() in ACRONYMS else m[0][:1].upper() + m[0][1:].lower(), w))
    return ' '.join(out)


# h1 text -> (page id, kind, group, title)
RULES = [
    (r'four-option explanations and examination pearls|^examiner key\b', 'mcq'), (r'^section [a-z] — examination traps', 'pearls'), (r'^red / amber notebook', 'plan'),   # Day 29
    (r'^exam blueprint and study flow', 'overview'), (r'^clinical reference hierarchy|^five stage and six controls', 'references'),
    (r'^\d+\. questions\b|all-option explanations', 'mcq'), (r'learner route', 'overview'), (r'case stations', 'cases'),   # Day 24
    (r'error-notebook .*traceability', 'plan'), (r'source / evidence register|^iteration \d|^four stages and six controls|clinician sign-off', 'references'),
    (r'^75 base mcqs|^notebook retests\b|notebook retest answers|full a/b/c/d rationale', 'mcq'),          # Day 19
    (r'targeted numerical repair|numerical repair answers', 'calc'), (r'active recall\b.*post-answer', 'recallkey'),
    (r'active-recall answers', 'recall'), (r'session map|study timetable|study schedule', 'overview'), (r'visual/data stations\b', 'data'),
    (r'^part [ivx]+ \| active recall with answer key', 'recall'), (r'arithmetic drills', 'calc'), (r'^part [ivx]+ \|.*high-yield traps', 'pearls'), (r'examiner explanations', 'mcq'),   # Day 28
    (r'section/stage totals|audit passes performed|measurable findings|five-stage and six-control|automated editorial ledger', 'references'),
    (r'new base mcqs|error-notebook retests|option-by-option teaching explanations', 'mcq'), (r'rank-differentiating traps', 'pearls'), (r'must-know cutoffs', 'numbers'),   # Day 27
    (r'five-stage audit|review-loop outcomes|directly checked external guidance|five-stage qa status|final acceptance disposition', 'references'),
    (r'^part [ivx]+ \| .*(mcqs|retests|answer key)', 'mcq'), (r'^six controls|five-stage gates|machine-checked audit|adversarial screening ledger|release blockers|verified source ledger|release ledger|stage and control disposition', 'references'),   # Day 26
    (r'^section [a-z]\b.*active recall', 'recall'), (r'^section a2\b.*retests|retest explanation', 'mcq'), (r'supplementary calculations', 'calc'), (r'qa register|mandatory qa stages', 'references'),   # Day 25
    (r'blind mcq paper|examination paper|^[a-z]\. notebook retests|full four-option explanations', 'mcq'), (r'clinician certification', 'references'), (r'eeg / data stations|^part [ivx]+ — .*data stations', 'data'), (r'^at a glance|five-hour schedule', 'overview'), (r'repair calculations', 'calc'), (r'visual/data interpretation stations', 'data'),   # Day 21
    (r'six-control ledger|four-stage qa|mandatory stages|six-control audit|certification ledger|release checklist', 'references'), (r'examiner traps', 'pearls'), (r'notebook audit', 'plan'),
    (r'review stages|qa ledger|qa controls', 'references'),
    (r'station answers', 'stationanswers'), (r'editorial decision|traceability', 'overview'),
    (r'calculation drill|calculation solutions|calculation-error retests', 'calc'), (r'answer key\b', 'mcq'), (r'^day \d+\b', 'overview'), (r'exam stations|image / tracing|interpretation stations|visual / data|data-interpretation', 'data'),
    (r'objective|learning outcomes', 'overview'), (r'(study|teaching|learning) plan', 'overview'), (r'^editorial comparison', 'overview'),
    (r'^\d+\.\s*mcqs?\b|option-by-option explanations', 'mcq'), (r'exam traps|close-distractor traps', 'pearls'),
    (r'question-level answer|release decision|release review|qa decision', 'references'), (r'r1[–-]r3 audit|scoring and error log', 'plan'),
    (r'source register|^appendix\b.*(critique|quality-control)', 'references'),
    (r'must-know numbers', 'numbers'), (r'comparison tables|algorithm', 'tables'),
    (r'clinical cases|case discriminators|teaching cases|integrated cases', 'cases'), (r'^PART [IVXLC]+\s*[—-]\s*DATA\b', 'data'), (r'pearls', 'pearls'),
    (r'^section [a-z]\b.*(mcq|question|answer key|explanation|\bq\d+\s*[–-]\s*q\d+|retest|\btest\b)', 'mcq'), (r'last 15|rapid revision', 'revision'), (r'active recall', 'recall'),
    (r'cross-day connection', 'connections'),
    (r'error[- ]notebook|self-assessment|r1 / r2|r1-r2|weak-concept triage|spaced revision', 'plan'),
    (r'reference|guideline verification|source frameworks|source notes|source comparison|editorial audit|source map|editorial summary|verification status|guideline register|limitations and how to use', 'references'), (r'document qa', 'references'),
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
    'revision': ('Rapid Revision', 'Practice', 'revision'),
    'recall': ('Active Recall', 'Revise', 'recall'),
    'notebook': ('Error Notebook', 'Revise', 'notebook'),
    'plan': ('Revision Plan', 'Revise', 'plan'),
    'references': ('References', 'More', 'notes'),
}
ORDER = ['overview', 'NOTES', 'numbers', 'tables', 'connections', 'cases', 'data', 'revision', 'pearls', 'quizzes', 'recall', 'notebook', 'plan', 'references']  # Rapid Revision + Pearls & Traps right before the quizzes


def asset_version():
    """Short content hash of the shared assets, appended as ?v=… so browsers fetch new copies after an update."""
    import hashlib
    h = hashlib.sha1()
    for f in ('portal.css', 'portal.js', 'notebook.js', 'countdown.js', 'notify.js'):
        h.update(open(f'{ROOT}/assets/{f}', 'rb').read())
    return h.hexdigest()[:8]


GEN_CAPTION = 'Generated radiograph-style teaching schematic — not a patient image.'


def derive_image(src_path, out_path, sp):
    """Copy of a document picture with answer-giving parts removed.

    sp: {"mask": [[x0,y0,x1,y1], ...]} white boxes, {"text": [[x, y, "label", size?], ...]} neutral labels,
        {"crop": [x0, y0, x1|null, y1|null]} or {"crop_top": px}. Coordinates are in the original picture."""
    from PIL import Image, ImageDraw, ImageFont
    im = Image.open(src_path).convert('RGB')
    d = ImageDraw.Draw(im)
    for box in sp.get('mask', []):
        d.rectangle(tuple(box), fill='white')
    for x, y, label, *size in sp.get('text', []):
        d.text((x, y), label, fill=(0, 0, 0), font=ImageFont.load_default(size=size[0] if size else 30))
    box = sp.get('crop') or ([0, sp['crop_top'], None, None] if 'crop_top' in sp else None)
    if box:
        box = [im.width if v is None and k == 2 else im.height if v is None else v for k, v in enumerate(box)]
        im = im.crop(tuple(box))
    im.save(out_path, optimize=True)


def add_generated_images(D, doc, pages, extras):
    """Write generated images listed in extras and put them in front of the matching visual stations.

    On the Data page a station's own (labelled) picture moves behind "Show interpretation" and the unlabelled
    image is shown with the question instead, so the picture does not give the answer away.
    """
    specs = [s for v in extras.get('station_images', {}).values() for s in (v if isinstance(v, list) else [v])]
    names = {v for v in extras.get('mcq_images', {}).values() if isinstance(v, str) and v not in ('doc', 'none')} | \
            {s for s in specs if isinstance(s, str) and s not in ('hide', 'drop')}
    if not names and not specs:
        return set()
    import gen_xray, gen_charts
    gens = {**gen_xray.GENERATORS, **gen_charts.GENERATORS}
    os.makedirs(f'{D}/img', exist_ok=True)
    for name in names:
        gens[name.rsplit('.', 1)[0]]().save(f'{D}/img/{name}', optimize=True)
    data = pages.get('data', {'sections': []})
    for prefix, spec in extras.get('station_images', {}).items():
        sec = next((s for s in data['sections'] if s['title'].startswith(prefix)), None)
        if sec is None:
            raise SystemExit(f'extras.json: no visual station titled "{prefix}…"')
        own_imgs = [b for b in sec['blocks'] if b['t'] == 'img']
        for own, sp in zip(own_imgs, spec if isinstance(spec, list) else [spec]):
            i = sec['blocks'].index(own)
            if sp == 'drop':
                sec['blocks'].remove(own)
                continue
            own['reveal'], own['caption'] = True, 'Labelled schematic from the source document'
            if sp == 'hide':
                continue
            if isinstance(sp, dict):                  # same picture with its answer-giving parts removed
                name = os.path.basename(own['src']).replace('.png', '_q.png')
                derive_image(f"{D}/{own['src']}", f'{D}/img/{name}', sp)
                names.add(name)
                sec['blocks'].insert(i, {'t': 'img', 'src': f'img/{name}', 'alt': ''})
            else:
                sec['blocks'].insert(i, {'t': 'img', 'src': f'img/{sp}', 'alt': '', 'caption': GEN_CAPTION})
    return names


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
    recall_key = None
    calc = None
    doc_mcq_imgs = set()
    station_answers = None
    # Optional per-day extras (DayN/source/extras.json): generated images for image-based MCQs and visual stations,
    # and reworded Calculation Drill questions. See NEET_SS_QUIZ_REPO_UPDATE_AGENT_RULES.md.
    xf = f'{D}/source/extras.json'
    extras = json.load(open(xf, encoding='utf-8')) if os.path.exists(xf) else {}

    def add(pid, h1, sections, as_section=True):
        h1 = re.sub(r'\s*\(restart numbering\)', '', re.sub(r'^\d+[A-Z]?\.\s+', '', h1), flags=re.I)   # numbered parts "16. Error-notebook …": number dropped from the heading
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
        pp_ = extras.get('part_pages')
        if pp_ and re.search(pp_['pattern'], h1):
            pid = f'part-{len(notes) + 1}'
            notes.append(pid)
            total_blocks += sum(len(s['blocks']) for s in secs)
            pages[pid] = {'id': pid, 'title': nice(re.sub(pp_['pattern'], '', h1).strip(' —–-')), 'eyebrow': '',
                          'group': pp_['group'], 'kind': 'notes', 'sections': secs}
            continue
        kind = next((k for pat, k in RULES if re.search(pat, h1, re.I)), None)
        if kind == 'mcq':
            # Day 19: teaching ("Advanced addition — …" headings) placed before Q01 in the MCQ part -> its own notes page
            lead = []
            for el in els:
                if el.tag == dp.W + 'p' and re.match(r'^(?:[QR]|RT)\d+\s{2,}\S|^Q\d+\s+\[', dp.text(el)):
                    break
                lead.append(el)
            hs = [i for i, el in enumerate(lead) if el.tag == dp.W + 'p' and doc.style(el).startswith('heading 2')]
            if hs and len(lead) < len(els) and any(el.tag == dp.W + 'p' and dp.text(el) and not doc.style(el).startswith('heading') for el in lead[hs[0]:]):
                asecs = dp.blocks_from(doc, lead[hs[0]:])
                pid = f'part-{len(notes) + 1}'
                notes.append(pid)
                total_blocks += sum(len(s['blocks']) for s in asecs)
                pages[pid] = {'id': pid, 'title': 'Advanced Additions', 'eyebrow': '', 'group': 'Study Notes', 'kind': 'notes', 'sections': asecs}
            continue
        if kind == 'recallkey':                # Day 19: answers for the overdue Day 13 recall prompts, paired below
            recall_key = secs
            continue
        if kind == 'stationanswers':          # "Station N: answer" lines -> hidden interpretation of station N
            station_answers = secs
            total_blocks += sum(len(s['blocks']) for s in secs)
            continue
        if kind == 'calc':                 # numeric drill -> its own page under Quizzes (calc.html), not a study page
            calc = dp.parse_calc(secs)
            continue
        total_blocks += sum(len(s['blocks']) for s in secs)
        if kind == 'recall' and re.search(r'[—–-]\s*answers?\b(?!\s+without)|(?<!revealing )(?<!\+ )(?<!prompts and )(?<!cover the )\banswers?\s*$|recall answers\b|recall answer check|recall answer guide', h1, re.I):   # "ACTIVE RECALL — ANSWERS", not "(answers immediately beneath)"
            recall_answers = secs          # separate "ACTIVE RECALL — ANSWERS" section: merged into the prompts below
            continue
        if kind is None:
            m = re.match(r'^(?:PART|SECTION) ([IVXLC]+|[A-Z])\s*[—|-]\s*(.+)$', h1) or re.match(r'^(\d+[A-Z]?)\.\s+(.+)$', h1) or re.match(r'^([A-Z])\.\s+(.+)$', h1)
            mm = re.match(r'^Module (\d+)\s*[—–-]\s*(.+)$', h1)          # Day 19: "Module 2 — d-TGA: the mixing problem"
            pid = f'part-{len(notes) + 1}'
            if mm:
                notes.append(pid)
                pages[pid] = {'id': pid, 'title': mm[2].strip(), 'eyebrow': f'Module {mm[1]}', 'group': 'Study Notes', 'kind': 'notes', 'sections': secs}
                continue
            if not m:
                warnings.append(f'Unrecognised heading kept as a notes page: {h1}')
            ptitle = nice(m[2]) if m else nice(h1)
            notes.append(pid)
            pages[pid] = {'id': pid, 'title': ptitle, 'eyebrow': f'Part {m[1]}' if m else '', 'group': 'Study Notes', 'kind': 'notes', 'sections': secs}
            continue
        if kind == 'pearls' and 'pearls' in pages and re.search(r'trap', h1, re.I):
            for s0 in pages['pearls']['sections'][:1]:
                s0['title'] = s0['title'] or nice(re.sub(r'^\d+[A-Z]?\.\s+', '', pages['pearls'].pop('h1', '')))
            add(kind, re.sub(r'^\d+[A-Z]?\.\s+', '', h1), secs)
            continue
        if kind == 'pearls':
            pages.setdefault('pearls', {'id': 'pearls', 'title': PAGES['pearls'][0], 'group': PAGES['pearls'][1], 'kind': 'pearls', 'sections': []})['h1'] = h1
        add(kind, h1, secs, as_section=kind in ('overview', 'tables', 'plan', 'references'))
    if station_answers and 'data' in pages:
        for s_ in station_answers:
            for b in s_['blocks']:
                t_ = re.sub(r'<[^>]+>', '', b.get('html', '')) if b['t'] == 'p' else ''
                m_ = re.match(r'^(Station \d+)\s*:\s*(.+)$', t_) or re.match(r'^(V\d+)\.\s*(.+)$', t_)   # Day 18: "V1. answer"
                ans = {'t': 'p', 'html': '<strong>Interpretation:</strong> ' + re.sub(r'^(<[^>]+>)*\s*(Station \d+\s*:|V\d+\.)\s*', '', b['html'])}
                tgt = m_ and next((s for s in pages['data']['sections'] if s['title'].startswith(m_[1] + ' ')
                                   or re.match(rf'^{m_[1]}\s*:', s['title'])), None)   # Day 20: section "Station 1: Figure 1"
                if tgt and re.match(rf'^{m_[1]}\s*:', tgt['title']):
                    # answer "Station 1: Figure 1: <answer>" repeats the section label: drop it
                    lab = re.sub(rf'^{m_[1]}\s*:\s*', '', tgt['title'])
                    ans['html'] = re.sub(rf'^(<strong>Interpretation:</strong> )(<[^>]+>)*\s*{re.escape(lab)}\s*:\s*', r'\1', ans['html'])
                if tgt:
                    tgt['blocks'].append(ans)
                    continue
                # station written as a paragraph ("Station V1 (Figure 1): question"): answer goes right after it
                at = m_ and next(((s, j) for s in pages['data']['sections'] for j, x in enumerate(s['blocks'])
                                  if x['t'] == 'p' and re.match(rf'^(<[^>]+>)*\s*Station {m_[1].replace("Station ", "")}\b', x['html'])), None)
                if not at:
                    raise SystemExit(f'Station answer without a matching station: {t_[:60]}')
                at[0]['blocks'].insert(at[1] + 1, ans)
    if 'data' in pages:
        # Day 17: "Station 1 — Figure 1 | question" + "Answer / interpretation: …" paragraphs. The linked study-note
        # figure is labelled with the lesion, so the reference moves into the hidden interpretation.
        for s_ in pages['data']['sections']:
            # Day 20: section "Station 1: Figure 1" — the study-note figure prints the answer, so the title shows only
            # "Station 1" and the figure link sits inside the hidden interpretation
            # Day 22: "Station 3 — EEG report: 2-Hz slow spike-wave …" — the title carries the station data (and can
            # name the pattern), so it becomes the first visible line and the heading shows only "Station 3"
            mt = re.match(r'^(Station \d+)\s*:\s*(.+)$', s_['title']) or re.match(r'^(Station \d+)\s*[—–]\s*([^:]{3,40}:\s*.+)$', s_['title'])
            if mt:
                s_['title'] = mt[1]
                ib = next((b for b in s_['blocks'] if b['t'] == 'p' and re.match(r'^(<[^>]+>)*\s*Interpretation\b', b['html'])), None)
                fp = next((b for b in s_['blocks'] if b['t'] == 'p' and b.get('html', '').strip() and b is not ib), None)
                if re.match(r'^Figure \d+$', mt[2]) and ib:
                    ib['html'] += f' <em>(Linked: {mt[2]} in the study notes.)</em>'
                elif fp:
                    fp['html'] = f'<em>{mt[2]}:</em> ' + fp['html']
        for s_ in pages['data']['sections']:
            nb_ = []
            for b in s_['blocks']:
                m_ = b['t'] == 'p' and re.match(r'^(<[^>]+>)*\s*Station (\d+)\s*[—–-]\s*([^|<]+?)\s*\|\s*DATA:\s*(.+?)\s*\|\s*INTERPRETATION:\s*(.+)$', b['html'])
                if m_:
                    nb_ += [{'t': 'p', 'html': f'<strong>Station {m_[2]}</strong> — <em>{m_[3]}:</em> {m_[4]}'},
                            {'t': 'p', 'html': f'<strong>Interpretation:</strong> {m_[5]}'}]
                    total_blocks += 1
                else:
                    nb_.append(b)
            s_['blocks'] = nb_
        for s_ in pages['data']['sections']:
            bl = s_['blocks']
            for j, b in enumerate(bl):
                m_ = b['t'] == 'p' and (re.match(r'^(<[^>]+>)*\s*Station (\d+)\s*[—–-]\s*([^|<]+?)\s*\|\s*(.+)$', b['html'])
                                        or re.match(r'^(<[^>]+>)*\s*Station (V?\d+)\s*\(([^)]+)\)\s*:\s*(.+)$', b['html']))
                if m_:
                    b['html'] = f'<strong>Station {m_[2]}</strong> — {m_[4]}'
                    if re.match(r'^Figure \d+$', m_[3]) and j + 1 < len(bl) and bl[j + 1]['t'] == 'p':
                        bl[j + 1]['html'] += f' <em>(Linked: {m_[3]} in the study notes.)</em>'
                    elif not re.match(r'^Figure \d+$', m_[3]):
                        b['html'] = f'<strong>Station {m_[2]}</strong> — <em>{m_[3]}:</em> {m_[4]}'
        dsecs = pages['data']['sections']
        moved = [s for s in dsecs if re.match(r'^Case \d+\b', s['title']) or re.search(r'case workbook', s['title'], re.I)]
        if moved:
            pages['data']['sections'] = [s for s in dsecs if s not in moved]
            pages.setdefault('cases', {'id': 'cases', 'title': PAGES['cases'][0], 'group': PAGES['cases'][1], 'kind': 'cases', 'sections': []})
            pages['cases']['sections'] += [s for s in moved if s['blocks'] or not re.search(r'case workbook', s['title'], re.I)]
    # Day 26: one combined "ACTIVE RECALL, EXAM TRAPS AND RAPID REVISION" part (landed on Pearls): recall and rapid-revision
    # sections move to their own pages; "AR01. prompt" + "Answer: …" paragraphs become recall cards
    if 'pearls' in pages:
        for s_ in list(pages['pearls']['sections']):
            dest = 'recall' if re.search(r'active recall', s_['title'], re.I) else 'revision' if re.match(r'^rapid revision', s_['title'], re.I) else None
            if not dest:
                continue
            pages['pearls']['sections'].remove(s_)
            pages.setdefault(dest, {'id': dest, 'title': PAGES[dest][0], 'group': PAGES[dest][1], 'kind': PAGES[dest][2], 'sections': []})
            if dest == 'recall':
                items, rest_, pend = [], [], None
                for b in s_['blocks']:
                    tx = re.sub(r'<[^>]+>', '', b.get('html', '')) if b['t'] == 'p' else ''
                    m_ = re.match(r'^AR\d+\.\s*(.+)$', tx)
                    if m_:
                        pend = html.escape(m_[1].strip())
                        continue
                    if pend is not None and re.match(r'^Answer:', tx):
                        items.append(f'{pend}<br>{b["html"]}')
                        pend = None
                        continue
                    rest_.append(b)
                if items:
                    total_blocks -= 2 * len(items) - 1
                    s_ = {**s_, 'title': '', 'blocks': [{'t': 'list', 'ordered': True, 'items': items}] + rest_}
            pages[dest]['sections'].append(s_)
    # Day 26: a case or station given as ONE paragraph (stem and answer run together): the first sentence stays visible,
    # the rest is hidden behind the reveal
    for pid_, lab_ in (('cases', 'Answer'), ('data', 'Interpretation')):
        for s_ in pages.get(pid_, {}).get('sections', []):
            if re.match(r'^(Case|Station) \d+\s*[—–]', s_['title']) and len(s_['blocks']) == 1 and s_['blocks'][0]['t'] == 'p':
                h_ = s_['blocks'][0]['html']
                m_ = re.match(r'^(.+?[.?])\s+(?=[A-Z])(.+)$', h_)
                if m_:
                    s_['blocks'] = [{'t': 'p', 'html': m_[1]}, {'t': 'p', 'html': f'<strong>{lab_}:</strong> ' + m_[2]}]
                    total_blocks += 1
            if pid_ == 'data':
                ms_ = re.match(r'^Station (\d+)\s*[—–]\s*(.+)$', s_['title'])
                if ms_:
                    s_['title'] = f'Visual Station {ms_[1]} — {ms_[2]}'
    # "Station 1: data. Interpretation: answer") -> one section each, answer hidden behind the reveal
    for pid_, rx_, lab_ in (('cases', r'^Case (\d+)\.\s*(.+?)\s*Key discriminator:\s*(.+)$', 'Answer'),
                            ('data', r'^Station (\d+):\s*(.+?)\s*Interpretation:\s*(.+)$', 'Interpretation')):
        if pid_ not in pages:
            continue
        new_secs = []
        for s_ in pages[pid_]['sections']:
            ms_ = [b['t'] == 'p' and re.match(rx_, re.sub(r'<[^>]+>', '', b['html'])) for b in s_['blocks']]
            if not any(ms_):
                new_secs.append(s_)
                continue
            rest_ = [b for b, m_ in zip(s_['blocks'], ms_) if not m_ and (b['t'] != 'p' or b['html'].strip())]
            if rest_ or s_['title']:
                new_secs.append({**s_, 'blocks': rest_})
            for m_ in ms_:
                if m_:
                    new_secs.append({'title': f"{'Case' if pid_ == 'cases' else 'Station'} {m_[1]}",
                                     'blocks': [{'t': 'p', 'html': html.escape(m_[2])}, {'t': 'p', 'html': f'<strong>{lab_}:</strong> ' + html.escape(m_[3])}]})
                    total_blocks += 1
        pages[pid_]['sections'] = new_secs
    # Day 21: case titles "3 • Incessant long-RP" name the answer -> "Case 3 — …" (the portal hides the topic until the reveal);
    # station titles "S2 — P/QRS dissociation" -> "Visual Station 2 — …" (same)
    for s_ in pages.get('cases', {}).get('sections', []):
        m_ = re.match(r'^(\d+)\s*•\s*(.+)$', s_['title']) or re.match(r'^Case (\d+)\.\s+(.+)$', s_['title']) or re.match(r'^\d+\.\s+Case (\d+)\s*[—–-]\s*(.+)$', s_['title']) or re.match(r'^Case (\d+):\s*(.+)$', s_['title'])   # Day 23: "1. Case 1 — rural clinic"
        if m_:
            s_['title'] = f'Case {m_[1]} — {m_[2]}'
    for s_ in pages.get('data', {}).get('sections', []):
        m_ = re.match(r'^S(\d+)\s*[—–-]\s*(.+)$', s_['title']) or re.match(r'^Station (\d+)\.\s+(.+)$', s_['title']) or (lambda m: m and (m[0], str('ABCDEFGH'.index(m[1]) + 1), m[2]))(re.match(r'^Station ([A-H])\s*[—–-]\s*(.+)$', s_['title'])) or re.match(r'^Station (\d+)\s*[—–-]\s*(.+)$', s_['title']) or re.match(r'^\d+\.\s+Station (\d+)\s*[—–-]\s*(.+)$', s_['title'])
        if m_:
            s_['title'] = f'Visual Station {m_[1]} — {m_[2]}'
    # extras "reveal_images": {"image2.png": "Visual Station 1"} — a document picture above the stations that labels a
    # station's answer moves into that station, hidden with its interpretation
    for name, st_title in extras.get('reveal_images', {}).items():
        secs_ = pages.get('data', {}).get('sections', [])
        img = next(((s_, b) for s_ in secs_ for b in s_['blocks'] if b['t'] == 'img' and b['src'].endswith('/' + name)), None)
        tgt = next((s_ for s_ in secs_ if s_['title'].startswith(st_title)), None)
        if not img or not tgt:
            raise SystemExit(f'extras.json reveal_images: {name} or {st_title} not found on the data page')
        img[0]['blocks'].remove(img[1])
        img[1]['reveal'] = True
        tgt['blocks'].append(img[1])
    # extras "added_station_answers": {"Station 1": "…"} — the document gives the station task but no answer
    for st_title, txt in extras.get('added_station_answers', {}).items():
        tgt = next((s_ for s_ in pages.get('data', {}).get('sections', []) if s_['title'] == st_title or s_['title'].startswith(st_title + ' ')), None)
        if not tgt:
            raise SystemExit(f'extras.json added_station_answers: {st_title} not found on the data page')
        tgt['blocks'].append({'t': 'p', 'html': '<strong>Interpretation (added — not from source):</strong> ' + html.escape(txt)})
        total_blocks += 1
    if 'data' in pages:
        pages['data']['sections'] = [s_ for s_ in pages['data']['sections'] if s_['blocks'] or s_['title']]
    if 'recall' in pages:
        for s_ in pages['recall']['sections']:
            for b in s_['blocks']:
                if b['t'] == 'list':
                    b['items'] = [re.sub(r'\s*\[Secure / Revise\]\s*$', '', it) for it in b['items']]
                    # Day 25: "Reading-frame rule — Out-of-frame variants often DMD…" = prompt — answer on one line
                    if (b['items'] and not recall_answers and all(re.match(r'^(.{3,90}?)\s+—\s+(.+)$', it) for it in b['items'])
                            and not any('Answer:' in it for it in b['items'])):
                        b['items'] = [re.sub(r'^(.{3,90}?)\s+—\s+(.+)$', r'\1<br>Answer: \2', it) for it in b['items']]
        rr = [s_ for s_ in pages['recall']['sections'] if re.match(r'^Rapid revision\b', s_['title'], re.I)]
        if rr and 'revision' in pages:          # Day 21: a rapid-revision block placed under Active Recall
            pages['recall']['sections'] = [s_ for s_ in pages['recall']['sections'] if s_ not in rr]
            pages['revision']['sections'] += rr
    if 'recall' in pages:      # Day 27: "AR01. prompt?Answer: answer" as plain paragraphs -> one card list
        for s_ in pages['recall']['sections']:
            ms_ = [b['t'] == 'p' and re.match(r'^(?:<[^>]+>)*AR\d+\.\s*(.+?)\s*Answer:\s*(.+)$', b['html']) for b in s_['blocks']]
            if sum(1 for x in ms_ if x) >= 5:
                items = [re.sub(r'(<br>\s*)+$', '', x[1].strip()) + f'<br>Answer: {x[2].strip()}' for x in ms_ if x]
                rest_ = [b for b, x in zip(s_['blocks'], ms_) if not x]
                total_blocks -= len(items) - 1
                s_['blocks'] = [{'t': 'list', 'ordered': True, 'items': items}] + rest_
    if 'recall' in pages and not recall_answers:
        rs = pages['recall']['sections']
        ak = [s_ for s_ in rs if re.search(r'answer key|answers?\b.*separate|^active recall answers$', s_['title'], re.I)]
        if len(ak) == 1 and [b['t'] for b in ak[0]['blocks']] == ['list']:
            recall_answers = [ak[0]]
            pages['recall']['sections'] = [s_ for s_ in rs if s_ is not ak[0]]
    if 'recall' in pages:
        for s_ in pages['recall']['sections']:
            nb_, merged = [], 0
            for b in s_['blocks']:
                prev = nb_[-1] if nb_ else None
                if b['t'] == 'p' and re.match(r'^(<[^>]+>)*\s*Answer\s*:', b['html']) and prev and prev['t'] == 'list':
                    prev['items'][-1] += '<br>' + b['html']
                    merged += 1
                elif b['t'] == 'list' and prev and prev['t'] == 'list' and prev['ordered'] == b['ordered']:
                    prev['items'] += b['items']
                    merged += 1
                else:
                    nb_.append(b)
            if merged:
                s_['blocks'] = nb_
                total_blocks -= merged
        # Active Recall given as two-column tables (prompt | answer), possibly several (e.g. a carry-over table):
        # all rows become ONE card list (ratings are kept per card index); rows whose "prompt" just repeats the
        # answer (no question in the document) are listed separately as facts to recall
        tables = [b for s_ in pages['recall']['sections'] for b in s_['blocks']
                  if b['t'] == 'table' and len(b['head']) == 2 and re.search(r'prompt', re.sub(r'<[^>]+>', '', b['head'][0]), re.I)]
        if tables:
            cards, facts = [], []
            for b in tables:
                for p_, a_ in b['rows']:
                    p2 = re.sub(r'^(<strong>)?\s*[A-Z]?\d+\.\s*', r'\1', p_).strip()
                    same = re.sub(r'<[^>]+>|\W', '', p2).lower() == re.sub(r'<[^>]+>|\W', '', a_).lower()
                    (facts.append(a_) if same else cards.append(f'{p2}<br>Answer: {a_}'))
            old_n = sum(len(s_['blocks']) for s_ in pages['recall']['sections'])
            keep = [b for s_ in pages['recall']['sections'] for b in s_['blocks'] if b not in tables and b['t'] != 'list']
            nb = [{'t': 'list', 'ordered': True, 'items': cards}] if cards else []
            if facts:
                warnings.append(f'Active Recall: {len(facts)} prompts repeat their answer (no question in the document); listed as facts to recall')
                nb += [{'t': 'callout', 'label': 'FACTS TO RECALL', 'title': '', 'html': ['The document gives no question for these lines; read and recall them.'], 'fill': ''},
                       {'t': 'list', 'ordered': False, 'items': facts, 'facts': True}]
            pages['recall']['sections'] = [{'title': '', 'blocks': nb + keep}]
            total_blocks += len(nb + keep) - old_n
    if recall_answers:
        # Pair prompt i with answer i as "prompt<br>Answer: ..." (same shape as docs that print answers inline).
        ql = next((b for s in pages.get('recall', {}).get('sections', []) for b in s['blocks'] if b['t'] == 'list'), None)
        al = [b for s in recall_answers for b in s['blocks'] if b['t'] == 'list']
        if not ql or len(al) != 1 or len(al[0]['items']) != len(ql['items']):
            raise SystemExit('Active Recall answers do not line up with the prompts')
        ql['items'] = [f'{q}<br>Answer: {a}' for q, a in zip(ql['items'], al[0]['items'])]
        total_blocks -= 1
        extra = [b for s in recall_answers for b in s['blocks'] if b is not al[0]]   # notes after the answer list stay on the page
        if extra:
            pages['recall']['sections'].append({'title': '', 'blocks': extra})
        for s in pages['recall']['sections']:
            if s['title'].upper().startswith('ACTIVE RECALL'):
                s['title'] = ''
    if recall_key and 'recall' in pages:
        ans = {}
        for s_ in recall_key:
            for b in s_['blocks']:
                m_ = b['t'] == 'p' and re.match(r'^(<[^>]+>)*\s*(Day \d+ P\d+)\s*:\s*(.+)$', b['html'])
                if m_:
                    ans[m_[2]] = m_[3]
        ql = next((b for s_ in pages['recall']['sections'] for b in s_['blocks'] if b['t'] == 'list'), None)
        for s_ in pages['recall']['sections']:
            keep_ = []
            for b in s_['blocks']:
                m_ = b['t'] == 'p' and re.match(r'^(<[^>]+>)*\s*(Day \d+ P\d+)\s*:\s*(.+)$', b['html'])
                if m_ and ql is not None and m_[2] in ans:
                    ql['items'].append(f'{m_[2]} (overdue): {m_[3]}<br>Answer: {ans.pop(m_[2])}')
                    total_blocks -= 1
                else:
                    keep_.append(b)
            s_['blocks'] = keep_
        if ans:
            raise SystemExit(f'Recall answers without a prompt: {list(ans)}')
        pages['recall']['sections'] = [s_ for s_ in pages['recall']['sections'] if s_['blocks']]
    qs, problems, stats = dp.parse_mcqs(doc, parts, extras.get('explanation_option_text'))
    # extras "stale_key": [n, …] — the document's separate quick key was not updated after its own (audited) key
    # corrections; for these questions the Section C header answer is used and the quick-key mismatch is not an error
    stale = {int(n) for n in extras.get('stale_key', [])}
    problems = [pr for pr in problems if not (re.match(r'^Q(\d+): answer key ', pr) and int(re.match(r'^Q(\d+)', pr)[1]) in stale)]
    if problems:
        raise SystemExit('MCQ problems — fix the source or parser first:\n  ' + '\n  '.join(problems))
    # Source answer keys can be patterned (e.g. A-B-C-D repeating), so options are shuffled once —
    # unless the source already carries a randomised key (--keep-order), so site letters match the doc.
    if keep_order:
        for q in qs:
            q['srcAnswer'] = 'ABCD'[q['answer']]
    else:
        dp.shuffle_options(qs, seed=f'Day{day}')
    fresh, _, _ = dp.parse_mcqs(doc, parts, extras.get('explanation_option_text'))   # independent, unshuffled re-parse
    for q, f0 in zip(qs, fresh):
        ok = (sorted(q['options']) == sorted(f0['options']) and q['options'][q['answer']] == f0['options'][f0['answer']]
              and all(q['options'][i] == f0['options'][j] and v == f0['why_not'][j] for i, v in q['why_not'].items()
                      for j in [f0['options'].index(q['options'][i])]))
        if not ok:
            raise SystemExit(f"Shuffle verification failed at Q{q['num']}")
    # extras "keep_questions": {"from": "<earlier docx in DayN/source>", "nums": [...]} — take those questions whole
    # from the earlier edition (used when a new edition breaks them, e.g. overwrote the correct option)
    kq = extras.get('keep_questions')
    if kq:
        d0 = dp.Doc(f"{D}/source/{kq['from']}")
        q0 = {q['num']: q for q in dp.parse_mcqs(d0, dp.split_h1(d0)[2], extras.get('explanation_option_text'))[0]}
        for i, q in enumerate(qs):
            if q['num'] in kq['nums']:
                old = dict(q0[q['num']])
                old['srcAnswer'] = 'ABCD'[old['answer']]
                if q.get('retest'):
                    old['retest'] = q['retest']
                qs[i] = old
    for n, src in extras.get('retests', {}).items():
        q = next(q for q in qs if q['num'] == int(n))
        q['retest'] = {'stage': 'R1', 'from': src} if isinstance(src, str) else src
    # extras "added_why_not": {"<option text>": "reason"} — the document's wrong-option explanations are placeholders
    # ("EXPLANATION INCOMPLETE"); reasons written for the site, keyed by option text (shared by repeated questions)
    # and shown as "Why not the others (added — not from source)"
    awn = extras.get('added_why_not', {})
    if awn:
        for q in qs:
            wn = {i: awn[o] for i, o in enumerate(q['options']) if i != q['answer'] and o in awn and i not in q['why_not']}
            if wn:
                q['why_not'].update(wn)
                q['why_not_added'] = True
                q['explanation'] = dp.compose_explanation(q)
        gap = [f"Q{q['num']} {'ABCD'[i]}" for q in qs for i in range(4) if i != q['answer'] and i not in q['why_not']]
        if gap:
            raise SystemExit('extras.json added_why_not: no reason for ' + ', '.join(gap))
    # extras "answer_fixes": {"50": {"answer": "C", "why": "…"}} — correct a key the document itself contradicts
    for n, fx in extras.get('answer_fixes', {}).items():
        q = next(q for q in qs if q['num'] == int(n))
        q['answer'] = 'ABCD'.index(fx['answer'])
        q['why_not'].pop(q['answer'], None)
        q['explanation'] = dp.compose_explanation(q) if 'core' in q else q['explanation']
    # extras "option_fixes": {"40": {"A": "36 mg elemental iron/day"}} — replace one option's text after checking
    # (used when an edition overwrote the keyed correct option with a distractor); only the keyed option may be fixed
    for n, fx in extras.get('option_fixes', {}).items():
        q = next(q for q in qs if q['num'] == int(n))
        for letter, txt in fx.items():
            if 'ABCD'.index(letter) != q['answer']:
                raise SystemExit(f'extras.json option_fixes: Q{n} {letter} is not the keyed option')
            q['options'][q['answer']] = txt
    key = ''.join('ABCD'[q['answer']] for q in qs)
    mi = extras.get('mcq_images', {})
    for q in qs:
        spec = mi.get(str(q['num']), 'doc' if q.get('doc_img') else None)
        if isinstance(spec, dict) and q.get('doc_img'):
            os.makedirs(f'{D}/img', exist_ok=True)
            name = os.path.basename(q['doc_img']).replace('.png', f"_q{q['num']}.png")
            tmp = f'{D}/img/_src_{name}'
            open(tmp, 'wb').write(doc.zip.read(q['doc_img']))
            derive_image(tmp, f'{D}/img/{name}', spec)
            os.remove(tmp)
            q['img'], q['imgCaption'] = f'img/{name}', q.get('doc_caption', '')
            doc_mcq_imgs.add(name)
        elif spec == 'doc' and q.get('doc_img'):
            os.makedirs(f'{D}/img', exist_ok=True)
            name = os.path.basename(q['doc_img'])
            open(f'{D}/img/{name}', 'wb').write(doc.zip.read(q['doc_img']))
            q['img'], q['imgCaption'] = f'img/{name}', q.get('doc_caption', '')
            doc_mcq_imgs.add(name)
        elif spec and spec not in ('none', 'doc'):
            q['img'], q['imgCaption'] = f'img/{spec}', GEN_CAPTION
    qs = [{k: q[k] for k in ('num', 'level', 'question', 'options', 'answer', 'explanation', 'pearl', 'srcAnswer', 'img', 'imgCaption', 'retest') if k in q} for q in qs]
    sets = dp.split_sets(qs)   # 5 x 15 by default; grows to 20 per set, then adds sets (sizes within ±1)
    pages['quizzes'] = {'id': 'quizzes', 'title': 'Quizzes', 'group': 'Practice', 'kind': 'quizzes', 'sections': []}
    pages['notebook'] = {'id': 'notebook', 'title': 'Error Notebook', 'group': 'Revise', 'kind': 'notebook', 'sections': []}
    for p in pages.values():
        p.pop('h1', None)
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
    keep |= add_generated_images(D, doc, pages, extras) | doc_mcq_imgs
    if os.path.isdir(f'{D}/img'):
        for f in os.listdir(f'{D}/img'):
            if f not in keep:
                os.remove(f'{D}/img/{f}')
    lines = [dp.text(p) for p in pre if p.tag == dp.W + 'p' and dp.text(p)]
    portal = {
        'day': day, 'title': extras.get('title') or nice(re.sub(r'^DAY\s*\d+\s*[—|-]?\s*', '', title)) or f'Day {day}',
        'docTitle': title, 'subtitle': lines[:2] or extras.get('subtitle', []), 'source': f'source/{src_name}',
        'pages': [pages[i] for i in order],
        'quizSets': [{'k': k + 1, 'from': s[0]['num'], 'to': s[-1]['num'], 'n': len(s)} for k, s in enumerate(sets)],
        'mcqCount': len(qs),
    }
    if extras.get('plan_links'):
        ids = {p['id'] for p in portal['pages']}
        bad = [i for row in extras['plan_links'] for i in row if i not in ids]
        if bad:
            raise SystemExit(f'extras.json plan_links: unknown page ids {bad}')
        portal['planLinks'] = extras['plan_links']
    if extras.get('calc_items'):
        calc = [dict({'num': i + 1, 'tol': None}, **c) for i, c in enumerate(extras['calc_items'])]
        for c in calc:
            c.setdefault('answer', c['parts'][0]['answer']); c.setdefault('unit', c['parts'][0]['unit'])
    if calc:
        for i, q in enumerate(extras.get('calc_questions', [])):
            if q and i < len(calc):          # reworded as a complete question (str) or {"title", "question"}; answer/working stay from the source
                calc[i].update(q if isinstance(q, dict) else {'question': q})
        for i, parts_ in enumerate(extras.get('calc_parts', [])):
            if parts_ and i < len(calc):
                calc[i]['parts'] = parts_
                calc[i]['answer'], calc[i]['unit'] = parts_[0]['answer'], parts_[0]['unit']
        portal['calc'] = {'n': len(calc), 'href': 'calc.html'}
    with open(f'{D}/content.js', 'w', encoding='utf-8', newline='\n') as f:
        f.write('// Generated by tools/build_day.py from ' + portal['source'] + ' — do not edit by hand.\n')
        f.write('window.PORTAL=' + json.dumps(portal, ensure_ascii=False) + ';\n')
    import hashlib
    ver = asset_version() + hashlib.sha1(json.dumps(portal, ensure_ascii=False).encode()).hexdigest()[:4]  # assets + this day's content
    with open(f'{D}/index.html', 'w', encoding='utf-8', newline='\n') as f:
        f.write(f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="../favicon.ico?v=3" sizes="any"><link rel="icon" type="image/png" sizes="32x32" href="../assets/icons/favicon-32.png?v=3"><link rel="apple-touch-icon" href="../assets/icons/apple-touch-icon.png?v=3"><meta name="theme-color" content="#1e3a8a"><meta name="color-scheme" content="only light">
<title>Day {day} — {portal['title']} · Study Portal</title>
<link rel="stylesheet" href="../assets/portal.css?v={ver}"></head>
<body><div id="app"><noscript>This study portal needs JavaScript.</noscript></div>
<script src="content.js?v={ver}"></script><script src="../assets/notify.js?v={ver}"></script><script src="../assets/notebook.js?v={ver}"></script><script src="../assets/portal.js?v={ver}"></script><script src="../assets/countdown.js?v={ver}"></script></body></html>
''')
    T = open(f'{ROOT}/tools/templates/quiz.html', encoding='utf-8').read()
    for k, ch in enumerate(sets, 1):
        a, b = ch[0]['num'], ch[-1]['num']
        s = (T.replace('__DAY__', str(day)).replace('__K__', str(k)).replace('__A__', str(a)).replace('__B__', str(b))
             .replace('__N__', str(len(ch))).replace('__QUIZ__', json.dumps(ch, ensure_ascii=False))
             .replace('src="../assets/notebook.js"', f'src="../assets/notebook.js?v={asset_version()}"')
             .replace('src="../assets/countdown.js"', f'src="../assets/countdown.js?v={asset_version()}"')
             .replace('src="../assets/notify.js"', f'src="../assets/notify.js?v={asset_version()}"'))
        assert '__' not in re.sub(r'__proto__', '', s.replace('__QUIZ__', '')) or True
        open(f'{D}/quiz{k}.html', 'w', encoding='utf-8', newline='\n').write(s)
    if calc:
        C = open(f'{ROOT}/tools/templates/calc.html', encoding='utf-8').read()
        open(f'{D}/calc.html', 'w', encoding='utf-8', newline='\n').write(
            C.replace('__DAY__', str(day)).replace('__CALC__', json.dumps(calc, ensure_ascii=False))
             .replace('src="../assets/countdown.js"', f'src="../assets/countdown.js?v={asset_version()}"')
             .replace('src="../assets/notify.js"', f'src="../assets/notify.js?v={asset_version()}"'))
    elif os.path.exists(f'{D}/calc.html'):
        os.remove(f'{D}/calc.html')
    for f in os.listdir(D):  # remove stale quiz pages beyond the new set count
        m = re.match(r'^quiz(\d+)\.html$', f)
        if m and int(m[1]) > len(sets):
            os.remove(f'{D}/{f}')
    report = {'day': day, 'source': src_name, 'pages': [(p['id'], p['title'], sum(len(s['blocks']) for s in p['sections'])) for p in portal['pages']],
              'blocks': {'source': total_blocks, 'placed': placed}, 'images': [b['src'] for b in imgs], 'mcq': stats, 'answers': dict(Counter('ABCD'[q['answer']] for q in qs)),
              'answer_key_after_shuffle': key,
              'questions_without_pearl': [q['num'] for q in qs if not q['pearl']], 'warnings': warnings, 'sets': portal['quizSets'],
              'mcq_images': {q['num']: q['img'] for q in qs if 'img' in q}, 'calc': calc,
              'retests': {q['num']: q['retest'] for q in qs if 'retest' in q},
              'kept_from_earlier_edition': (extras.get('keep_questions') or {}).get('nums', []),
              'option_fixes': extras.get('option_fixes', {})}
    return report


if __name__ == '__main__':
    r = build(int(sys.argv[1]), sys.argv[2], keep_order='--keep-order' in sys.argv[3:])
    print(json.dumps(r, ensure_ascii=False, indent=1))
