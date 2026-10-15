import json, os, re, shutil, subprocess, sys
V = sys.argv[1]  # '2'..'6'
ROOT = '/home/claude/montage'; FL = f'{ROOT}/fl3'; OUT = f'{FL}/v{V}'; os.makedirs(OUT, exist_ok=True)
FPS = 30
CFG = json.load(open(f'{FL}/cfg.json'))[V]
plan = json.load(open(f'{ROOT}/v{V}/plan.json'))
# blocks (merge consecutive same blk)
blocks = []
for s in plan['shots']:
    if blocks and blocks[-1]['blk'] == s['blk']:
        blocks[-1]['t1'] = s['t1']
        if s.get('card'): blocks[-1]['card'] = s['card']; blocks[-1]['mode'] = s['mode']
    else:
        blocks.append({'blk': s['blk'], 't0': s['t0'], 't1': s['t1'], 'card': s.get('card'), 'mode': s['mode']})
end = blocks[-1]['t1']
lines = []
for b in blocks:
    L = dict(CFG['scenes'].get(b['blk'], {}))
    if b['card']: L.setdefault('scene', 'card'); 
    lines.append(L)
script = {'color': CFG['color'], 'lines': lines}
# subtitles
SHORTW = {'в','и','из','за','от','не','как','а','на','с','по','к','у','о','что','это','то'}
chunks = []
for t0, t1, txt, *_ in plan['subs']:
    ws = [w for w in re.sub(r'\\N', ' ', txt).split() if w]
    ws = [w.lower() for w in ws]
    ws = [('Claude' if w == 'claude' else w) for w in ws]
    if chunks == [] or True:
        pass
    lens = [len(w) + 2 for w in ws]; tot = sum(lens); c = t0; items = []
    for w, l in zip(ws, lens):
        d = (t1 - t0) * l / tot; items.append([w, round(c, 2), round(c + d, 2)]); c += d
    chunks.append([round(t0, 2), round(t1, 2), items])
# capitalise first word of each sentence-ish: first chunk word after long gap
prev_end = -9
for ch in chunks:
    if ch[0] - prev_end > 0.35 and ch[2]:
        w = ch[2][0][0]; ch[2][0][0] = w[:1].upper() + w[1:]
    prev_end = ch[1]
for k in range(len(chunks) - 1):
    chunks[k][1] = min(chunks[k][1], chunks[k + 1][0])
open(f'{OUT}/words.js', 'w').write('const WORDS=1;const CHUNKS=' + json.dumps(chunks, ensure_ascii=False) + ';')
open(f'{OUT}/script.js', 'w').write('const SCRIPT=' + json.dumps(script, ensure_ascii=False) + ';')
for f in ['reel.html', 'scenes_base.js', 'scenes_extra.js']: shutil.copy(f'{FL}/{f}', OUT)
tl = ','.join(str(round(b['t0'], 3)) for b in blocks) + f',{round(end, 3)}'
json.dump({'blocks': blocks, 'tl': tl, 'end': end}, open(f'{OUT}/blocks.json', 'w'), indent=1)
if '--norender' in sys.argv: sys.exit()
from playwright.sync_api import sync_playwright
fr = f'{OUT}/frames'; shutil.rmtree(fr, ignore_errors=True); os.makedirs(fr)
url = f'file://{OUT}/reel.html?tl={tl}'
with sync_playwright() as p:
    br = p.chromium.launch(); pg = br.new_page(viewport={'width': 1080, 'height': 1920})
    pg.goto(url + '&nosub=1'); pg.wait_for_timeout(1500); pg.evaluate(f"renderAt({CFG.get('cover_t', 2.0)})")
    pg.screenshot(path=f'{OUT}/cover.png')
    pg.goto(url); pg.wait_for_timeout(1500)
    n = int(round(end * FPS))
    for i in range(n):
        pg.evaluate(f'renderAt({i / FPS})'); pg.screenshot(path=f'{fr}/{i:05d}.jpg', type='jpeg', quality=90)
    br.close()
# compose: frames + card overlays + voice
ins = ['-framerate', str(FPS), '-i', f'{fr}/%05d.jpg', '-i', f'{OUT}/cover.png', '-i', f'{ROOT}/v{V}/edit.mp4']
fc = []; last = '[0:v]'; k = 3
cover_full = None
for b in blocks:
    if not b['card']: continue
    d = b['t1'] - b['t0']
    full = b['mode'] == 'screen'
    ins += ['-i', b['card']]
    fc.append(f"[{k}:v]tpad=stop_mode=clone:stop_duration={d + 1},trim=duration={d:.3f},fps={FPS},"
              + ("scale=1080:1920," if full else "scale=1080:960,") + f"setpts=PTS-STARTPTS+{b['t0']:.3f}/TB[c{k}]")
    y = 0 if full else 300
    fc.append(f"{last}[c{k}]overlay=0:{y}:eof_action=pass:enable='between(t,{b['t0']:.3f},{b['t1'] - 0.001:.3f})'[o{k}]")
    last = f'[o{k}]'; k += 1
fc.append(f"{last}[1:v]overlay=enable='eq(n,0)'[v]")
subprocess.run(['ffmpeg', '-y', '-v', 'error', *ins, '-filter_complex', ';'.join(fc), '-map', '[v]', '-map', '2:a',
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-c:a', 'aac', '-b:a', '192k', '-t', f'{end:.3f}',
                '-movflags', '+faststart', f'{OUT}/video.mp4'], check=True)
print('done', V, end)
