import json, os, re, shutil, subprocess, sys
sys.path.insert(0, '/home/claude/carousels/content/course/kit')
from make import subtitles
K = sys.argv[1]; B = '/home/claude/montage/b1'; OUT = f'{B}/out/{K}'; os.makedirs(OUT, exist_ok=True)
S = json.load(open(f'{B}/scripts.json'))[K]
tlj = json.load(open(f'{B}/tl_{K}.json'))
says = [x for x in tlj['timeline'] if x['kind'] == 'say']
tl = [(x['start'], x['end']) for x in says]
end = round(tlj['seconds'] + 0.5, 3)
for f in ['reel.html', 'scenes_base.js', 'scenes_extra.js']: shutil.copy(f'{B}/engine/{f}', OUT)
open(f'{OUT}/words.js', 'w').write('const WORDS=1;const CHUNKS=' + json.dumps(subtitles(S['lines'], tl), ensure_ascii=False) + ';')
open(f'{OUT}/script.js', 'w').write('const SCRIPT=' + json.dumps({'color': S['color'], 'lines': S['lines']}, ensure_ascii=False) + ';')
starts = [0.0] + [round(a - 0.12, 3) for a, _ in tl[1:]]
tls = ','.join(str(x) for x in starts) + f',{end}'
json.dump({'starts': starts, 'end': end}, open(f'{OUT}/tl.json', 'w'))
from playwright.sync_api import sync_playwright
fr = f'{OUT}/frames'; shutil.rmtree(fr, ignore_errors=True); os.makedirs(fr)
url = f'file://{OUT}/reel.html?tl={tls}'
with sync_playwright() as p:
    br = p.chromium.launch(); pg = br.new_page(viewport={'width': 1080, 'height': 1920})
    pg.goto(url + '&nosub=1'); pg.wait_for_timeout(1500); pg.evaluate(f'renderAt({min(2.2, starts[1] - .1)})')
    pg.screenshot(path=f'{OUT}/cover.png')
    pg.goto(url); pg.wait_for_timeout(1500)
    for i in range(int(round(end * 30))):
        pg.evaluate(f'renderAt({i / 30})'); pg.screenshot(path=f'{fr}/{i:05d}.jpg', type='jpeg', quality=90)
    br.close()
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-framerate', '30', '-i', f'{fr}/%05d.jpg', '-i', f'{OUT}/cover.png',
                '-filter_complex', "[0][1]overlay=enable='eq(n,0)'", '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20',
                '-movflags', '+faststart', f'{OUT}/video.mp4'], check=True)
shutil.rmtree(fr)
# sfx
kinds = [L['scene'] for L in S['lines']]; sfx = []
for i, (s, k) in enumerate(zip(starts, kinds)):
    d = (starts[i + 1] if i + 1 < len(starts) else end) - s
    if i: sfx.append({'t': round(s - .1, 2), 'kind': 'whoosh', 'vol': .6})
    if k == 'hook': sfx += [{'t': round(.7 + j * .2, 2), 'kind': 'pop', 'vol': .5} for j in range(len(S['lines'][0].get('chips', [])))]
    elif k == 'quote': sfx.append({'t': round(s + .12, 2), 'kind': 'pop', 'vol': .6})
    elif k == 'chat': sfx.append({'t': round(s + .4, 2), 'kind': 'type', 'vol': .4, 'dur': 1.2})
    elif k == 'code': sfx.append({'t': round(s + .45, 2), 'kind': 'type', 'vol': .4, 'dur': 1.4})
    elif k == 'list': sfx += [{'t': round(s + .4 + j * min(.5, d * .6 / max(1, len(S['lines'][i]['items']))), 2), 'kind': 'pop', 'vol': .45} for j in range(len(S['lines'][i].get('items', [])))]
    elif k == 'number': sfx.append({'t': round(s + 1.4, 2), 'kind': 'ding', 'vol': .5})
    elif k == 'cta': sfx += [{'t': round(s + .1, 2), 'kind': 'pop', 'vol': .7}, {'t': round(s + .5, 2), 'kind': 'type', 'vol': .5, 'dur': .6}] + [{'t': round(s + 1.2 + j * .25, 2), 'kind': 'click', 'vol': .6} for j in range(3)]
json.dump(sfx, open(f'{OUT}/sfx.json', 'w'))
print('done', K, end)
