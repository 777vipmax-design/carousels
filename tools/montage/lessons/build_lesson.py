import json, os, re, shutil, subprocess, sys
N = sys.argv[1]  # '01'
B = '/home/claude/montage/lessons'; OUT = f'{B}/out/{N}'; os.makedirs(OUT, exist_ok=True)
S = json.load(open(f'{B}/l{N}.json')); tl = json.load(open(f'{B}/tl_{N}.json'))
says = [(x['start'], x['end']) for x in tl['timeline']]
end = round(tl['seconds'] + 1.2, 3)
SHORT = {"в","и","из","за","от","не","как","а","на","с","по","к","у","о","что","это","то","для","или"}
chunks = []
for L, (a, b) in zip(S['lines'], says):
    toks = [x for x in L['say'].split(' ') if x]
    words = [x for x in toks if x not in ('—', '–')]
    lens = [len(x) + 2 for x in words]; tot = sum(lens); c = a; times = []
    for l in lens:
        d = (b - a) * l / tot; times.append((c, c + d)); c += d
    items, j = [], 0
    for x in toks:
        if x in ('—', '–'):
            if items: items[-1][0] += ' —'
            continue
        items.append([re.sub(r'[.,!?:;]', '', x), times[j][0], times[j][1], bool(re.search(r'[.,!?:;]$', x))]); j += 1
    cur = []
    for k, it in enumerate(items):
        cur.append(it); nxt = items[k + 1] if k + 1 < len(items) else None
        brk = (it[3] and len(cur) >= 2) or len(cur) >= 6 or nxt is None
        if brk and nxt and it[0].lower() in SHORT: brk = False
        if brk or len(cur) >= 7:
            chunks.append(cur); cur = []
out = []
for j, c in enumerate(chunks):
    s = c[0][1] - 0.05; nx = chunks[j + 1][0][1] - 0.05 if j + 1 < len(chunks) else 1e9
    out.append([round(s, 2), round(min(nx, c[-1][2] + 0.8), 2), [[x[0], round(x[1], 2), round(x[2], 2)] for x in c]])
open(f'{OUT}/words.js', 'w').write('const CHUNKS=' + json.dumps(out, ensure_ascii=False) + ';')
open(f'{OUT}/script.js', 'w').write('const SCRIPT=' + json.dumps(S, ensure_ascii=False) + ';')
shutil.copy(f'{B}/engine/lesson.html', OUT)
starts = [0.0] + [round(a - 0.15, 3) for a, _ in says[1:]]
tls = ','.join(map(str, starts)) + f',{end}'
from playwright.sync_api import sync_playwright
fr = f'{OUT}/frames'; shutil.rmtree(fr, ignore_errors=True); os.makedirs(fr)
with sync_playwright() as p:
    br = p.chromium.launch(); pg = br.new_page(viewport={'width': 1280, 'height': 720})
    pg.goto(f'file://{OUT}/lesson.html?tl={tls}'); pg.wait_for_timeout(800)
    for i in range(int(round(end * 30))):
        pg.evaluate(f'renderAt({i / 30})'); pg.screenshot(path=f'{fr}/{i:05d}.jpg', type='jpeg', quality=90)
    br.close()
cover = f'/home/claude/carousels/media/course/l{N}.png'
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-framerate', '30', '-i', f'{fr}/%05d.jpg', '-i', cover,
                '-filter_complex', "[1]scale=1280:720[c];[0][c]overlay=enable='eq(n,0)'", '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                '-crf', '20', '-movflags', '+faststart', f'{OUT}/video.mp4'], check=True)
shutil.rmtree(fr)
sfx = []
for i, (s, L) in enumerate(zip(starts, S['lines'])):
    if i: sfx.append({'t': round(s - .1, 2), 'kind': 'whoosh', 'vol': .35})
    k = L['scene']
    if k == 'pipeline' and L.get('hl', -1) < 0: sfx += [{'t': round(s + .2 + j * .45, 2), 'kind': 'pop', 'vol': .35} for j in range(7)]
    elif k in ('bullets', 'pipeline'): sfx += [{'t': round(s + .45 + j * .7, 2), 'kind': 'pop', 'vol': .3} for j in range(len(L.get('items', [])))]
    elif k in ('stats', 'homework', 'quote'): sfx.append({'t': round(s + .1, 2), 'kind': 'pop', 'vol': .35})
json.dump({'end': end, 'sfx': sfx}, open(f'{OUT}/meta.json', 'w'))
print('done', N, end)
