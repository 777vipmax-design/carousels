"""mkwords.py name timeline.json words.json -> words_<name>.js  (script text timed by whisper words)"""
import json, re, sys
name, tlf, wf = sys.argv[1:4]
tl = json.load(open(tlf)); W = json.load(open(wf))
SHORT = {'в','и','из','за','от','не','как','а','А','И','То','ты','Он','на','с','по','к','у','о','что','это','—'}
out = []
for p in tl:
    if p['kind'] != 'say': continue
    txt = re.sub(r'\[[^\]]*\]', '', p['text']).strip().replace('Claude Code', 'Claude\u00a0Code')
    toks = [x for x in txt.split(' ') if x]
    ws = [w for w in W if w[0] >= p['start'] - 0.3 and w[1] <= p['end'] + 0.4 and w[2] != '—']
    words = [t for t in toks if t != '—']
    if len(ws) == len(words):
        times = [(w[0], w[1]) for w in ws]
    else:
        a = ws[0][0] if ws else p['start']; b = ws[-1][1] if ws else p['end']
        L = [len(x) + 2 for x in words]; s = sum(L); c = a; times = []
        for l in L:
            d = (b - a) * l / s; times.append((c, c + d)); c += d
    # build display items (dash attaches to previous word)
    items = []; j = 0
    for t in toks:
        if t == '—':
            if items: items[-1][0] += ' —'
            continue
        clean = re.sub(r'[.,!?:;«»"]', '', t)
        end = bool(re.search(r'[.,!?:;]$', t))
        items.append([clean, times[j][0], times[j][1], end]); j += 1
    chunk = []
    for k, it in enumerate(items):
        chunk.append(it)
        nxt = items[k + 1] if k + 1 < len(items) else None
        brk = it[3] or len(chunk) >= 3 or nxt is None
        if brk and nxt and it[0].lower().rstrip(' —') in SHORT and not it[3]: brk = False
        if len(chunk) >= 4: brk = True
        if brk:
            if out and len(chunk) == 1 and len(chunk[0][0]) <= 11 and len(out[-1]) <= 4 and out[-1][-1][2] > chunk[0][1] - 0.4 and not out[-1][-1][3]:
                out[-1].append(chunk[0])
            else:
                out.append(chunk)
            chunk = []
CH = []
for j, c in enumerate(out):
    s = c[0][1] - 0.05; nx = out[j + 1][0][1] - 0.05 if j + 1 < len(out) else 1e9
    CH.append([round(s, 2), round(min(nx, c[-1][2] + 0.7), 2), [[x[0], round(x[1], 2), round(x[2], 2)] for x in c]])
open(f'words_{name}.js', 'w').write('const WORDS=1;const CHUNKS=' + json.dumps(CH, ensure_ascii=False) + ';')
for c in CH: print(c[0], c[1], ' '.join(x[0] for x in c[2]))
