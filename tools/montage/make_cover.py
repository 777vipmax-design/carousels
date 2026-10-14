"""python3 make_cover.py out.png "LINE1" "LINE2" [tag] — transparent 1080x1920 headline overlay"""
import sys, os, urllib.parse
from playwright.sync_api import sync_playwright
out, a, b = sys.argv[1], sys.argv[2], sys.argv[3]
tag = sys.argv[4] if len(sys.argv) > 4 else ""
acc = sys.argv[5] if len(sys.argv) > 5 else "#FF7A45"
q = urllib.parse.urlencode({"a": a, "b": b, "tag": tag, "acc": acc})
url = "file://" + os.path.abspath(os.path.join(os.path.dirname(__file__), "cover.html")) + "?" + q
with sync_playwright() as p:
    br = p.chromium.launch(); pg = br.new_page(viewport={"width": 1080, "height": 1920})
    pg.goto(url); pg.wait_for_timeout(300)
    pg.screenshot(path=out, omit_background=True); br.close()
