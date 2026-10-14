"""Render HTML motion cards to video: python3 render_cards.py card dur out.mp4 [w h] [alpha]"""
import sys, os, subprocess, tempfile, shutil
from playwright.sync_api import sync_playwright

FPS = 30


def render(card, dur, out, w=1080, h=960, alpha=False, page_file="cards.html"):
    tmp = tempfile.mkdtemp(prefix="cards-")
    url = "file://" + os.path.abspath(os.path.join(os.path.dirname(__file__), page_file)) + f"?card={card}"
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=None)
        pg = b.new_page(viewport={"width": w, "height": h})
        pg.goto(url)
        pg.wait_for_timeout(300)
        n = int(dur * FPS)
        for i in range(n):
            pg.evaluate(f"renderAt({i / FPS})")
            pg.screenshot(path=os.path.join(tmp, f"{i:05d}.png"), omit_background=alpha)
        b.close()
    if alpha:
        cmd = ["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", os.path.join(tmp, "%05d.png"),
               "-c:v", "qtrle", out]
    else:
        cmd = ["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", os.path.join(tmp, "%05d.png"),
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", out]
    subprocess.run(cmd, check=True)
    shutil.rmtree(tmp)


if __name__ == "__main__":
    a = sys.argv
    render(a[1], float(a[2]), a[3], int(a[4]) if len(a) > 4 else 1080, int(a[5]) if len(a) > 5 else 960,
           len(a) > 6 and a[6] == "alpha", a[7] if len(a) > 7 else "cards.html")
