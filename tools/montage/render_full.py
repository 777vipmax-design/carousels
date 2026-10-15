"""Render full.html timeline to mp4 (1080x1920, 30fps). usage: render_full.py tl out.mp4 [snap t1,t2,...]"""
import sys, os, subprocess, tempfile, shutil
from playwright.sync_api import sync_playwright
FPS = 30
tl, out = sys.argv[1], sys.argv[2]
snaps = [float(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else None
url = "file://" + os.path.abspath("full.html") + "?tl=" + tl + "&s=" + os.environ.get("SC", "fl1")
end = float(tl.split(",")[-1])
tmp = tempfile.mkdtemp(prefix="full-")
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.goto(url); pg.wait_for_timeout(400)
    if snaps:
        for s in snaps:
            pg.evaluate(f"renderAt({s})"); pg.screenshot(path=f"{out}_{s:05.2f}.png", type="png")
        sys.exit(0)
    n = int(round(end * FPS))
    for i in range(n):
        pg.evaluate(f"renderAt({i / FPS})")
        pg.screenshot(path=os.path.join(tmp, f"{i:05d}.jpg"), type="jpeg", quality=92)
    b.close()
subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", os.path.join(tmp, "%05d.jpg"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "21", "-preset", "medium", out], check=True)
shutil.rmtree(tmp)
