import json, os, shutil, sys
from playwright.sync_api import sync_playwright
K=sys.argv[1]; S=json.load(open('scripts.json'))[K]; O=f'/home/claude/montage/ru1/prev/{K}'; os.makedirs(O,exist_ok=True)
for f in os.listdir('engine'): shutil.copy('engine/'+f,O)
open(f'{O}/script.js','w').write('const SCRIPT='+json.dumps({'color':S['color'],'lines':S['lines']},ensure_ascii=False)+';')
open(f'{O}/words.js','w').write('')
n=len(S['lines']); tl=','.join(str(i*5) for i in range(n+1))
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1080,'height':1920}); pg.goto(f'file://{O}/reel.html?tl={tl}'); pg.wait_for_timeout(1200)
    for i in range(n):
        pg.evaluate(f'renderAt({i*5+4.5})'); pg.screenshot(path=f'{O}/s{i}.png')
    b.close()
