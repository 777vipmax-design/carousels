"""python3 islands.py audio words.json -> speech islands with whisper words inside"""
import sys, json, subprocess, re
aud, wj = sys.argv[1], sys.argv[2]
r = subprocess.run(["ffmpeg", "-i", aud, "-af", "silencedetect=n=-35dB:d=0.25", "-f", "null", "-"], capture_output=True, text=True).stderr
ss = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r)]
se = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r)]
dur = float(re.search(r"Duration: (\d+):(\d+):([\d.]+)", r).group(3)) + 60 * int(re.search(r"Duration: (\d+):(\d+):", r).group(2))
isl = []; cur = 0.0
for a, b in zip(ss, se + [dur]):
    if a - cur > 0.15: isl.append((cur, a))
    cur = b
if dur - cur > 0.15: isl.append((cur, dur))
W = json.load(open(wj)); W = W["words"] if isinstance(W, dict) else W
for a, b in isl:
    ws = [w[2] for w in W if w[0] < b + 0.3 and w[1] > a - 0.3]
    print(f"{a:7.2f} {b:7.2f} ({b-a:4.2f})  {' '.join(ws)}")
