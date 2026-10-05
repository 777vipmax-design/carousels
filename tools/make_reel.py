"""Build a 9:16 Reels slideshow from carousel slides 01..10.

python3 tools/make_reel.py posts/<folder>
-> posts/<folder>/reel.mp4

Each 3:4 slide is scaled to 1000 px wide and placed near the top of a
1080x1920 frame on the brand background, so the text stays clear of the
Reels caption and buttons. Cover 2.5 s, other slides 3.5 s, 0.3 s fades.
"""
import os
import subprocess
import sys
import tempfile

from PIL import Image

W, H, BG = 1080, 1920, (17, 18, 20)
COVER, SLIDE, FADE = 2.5, 3.5, 0.3


def frame(src, dst):
    s = Image.open(src).convert("RGB")
    w = 1000
    h = round(s.height * w / s.width)
    s = s.resize((w, h), Image.LANCZOS)
    f = Image.new("RGB", (W, H), BG)
    f.paste(s, ((W - w) // 2, 150))
    f.save(dst)


def main(folder):
    slides = [os.path.join(folder, f"{i:02d}.png") for i in range(1, 11)]
    slides = [s for s in slides if os.path.exists(s)]
    tmp = tempfile.mkdtemp()
    frames = []
    for i, s in enumerate(slides):
        p = os.path.join(tmp, f"f{i:02d}.png")
        frame(s, p)
        frames.append(p)
    durs = [COVER] + [SLIDE] * (len(frames) - 1)
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for p, d in zip(frames, durs):
        cmd += ["-loop", "1", "-t", f"{d + FADE}", "-i", p]
    total = sum(durs) + FADE
    cmd += ["-f", "lavfi", "-t", f"{total}", "-i", "anullsrc=r=44100:cl=stereo"]
    parts, last, offset = [], "[0:v]", 0.0
    for i in range(1, len(frames)):
        offset += durs[i - 1]
        out = f"[v{i}]"
        parts.append(f"{last}[{i}:v]xfade=transition=fade:duration={FADE}:offset={offset:.2f}{out}")
        last = out
    parts.append(f"{last}format=yuv420p,fps=30[vout]")
    cmd += ["-filter_complex", ";".join(parts), "-map", "[vout]", "-map", f"{len(frames)}:a",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "128k",
            "-shortest", "-movflags", "+faststart", os.path.join(folder, "reel.mp4")]
    subprocess.run(cmd, check=True)
    print(os.path.join(folder, "reel.mp4"), f"{sum(durs):.1f}s")


if __name__ == "__main__":
    main(sys.argv[1])
