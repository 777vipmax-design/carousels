"""python3 gaps.py audio.wav start end -> micro silences (-32dB, 0.06s) within range"""
import sys, subprocess, re
a, s, e = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
r = subprocess.run(["ffmpeg", "-ss", str(s), "-t", str(e - s), "-i", a, "-af", "silencedetect=n=-32dB:d=0.06", "-f", "null", "-"], capture_output=True, text=True).stderr
ss = [float(x) + s for x in re.findall(r"silence_start: (-?[\d.]+)", r)]
se = [float(x) + s for x in re.findall(r"silence_end: ([\d.]+)", r)]
print(" ".join(f"[{x:.2f}-{y:.2f}]" for x, y in zip(ss, se)))
