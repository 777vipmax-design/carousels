"""Faceless story reels: stock video + emotional voice + code-made editing.

scenes = [{
  "say":  "текст озвучки",
  "sub":  "текст субтитров (по умолчанию = say)",
  "q":    "stock search query (english)",       # or "clips": [url, ...]
  "big":  "267 000 ₽",                           # optional big text in the middle
  "count": 267000, "suffix": " ₽",               # optional: animated count-up instead of big
  "title": "СВАРЩИК vs АЙТИШНИК",                 # optional big title at the top (hook)
  "hit": true                                    # optional: impact sound at scene start
}]
"""
import json
import os
import random
import re
import shutil
import subprocess
import tempfile

W, H, FPS = 1080, 1920, 30
CUT = 2.6          # seconds per stock shot
YELLOW = "&H0000D7FF&"   # ASS colours are &HBBGGRR&
RED = "&H00303BFF&"
WHITE = "&H00FFFFFF&"


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


# ------------------------------------------------------------------ sfx

def make_sfx(d):
    """Synthesised whoosh and impact so no sound library is needed."""
    whoosh = os.path.join(d, "whoosh.wav")
    hit = os.path.join(d, "hit.wav")
    if not os.path.exists(whoosh):
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.45:c=pink:a=0.9",
             "-af", "highpass=f=400,lowpass=f=6000,afade=t=in:d=0.25,afade=t=out:st=0.25:d=0.2,volume=0.55",
             "-ar", "44100", "-ac", "2", whoosh])
    if not os.path.exists(hit):
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=55:d=0.7", "-f", "lavfi", "-i",
             "anoisesrc=d=0.12:c=brown:a=0.8", "-filter_complex",
             "[0]afade=t=out:st=0.05:d=0.65,volume=2.2[a];[1]afade=t=out:d=0.12[b];[a][b]amix=2:normalize=0,"
             "alimiter=limit=0.9", "-ar", "44100", "-ac", "2", hit])
    return whoosh, hit


# ------------------------------------------------------------------ subtitles (ASS)

def ts(t):
    t = max(0.0, t)
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def esc(s):
    return s.replace("\\", "").replace("{", "(").replace("}", ")")


def fmt_num(n):
    return f"{int(n):,}".replace(",", " ")


def words_with_times(text, start, dur):
    words = re.sub(r"\[[^\]]*\]", " ", text).split()
    total = sum(len(w) + 2 for w in words) or 1
    t, out = start, []
    for w in words:
        d = dur * (len(w) + 2) / total
        out.append((w, t, t + d))
        t += d
    return out


def chunks_of(words, max_words=3, max_chars=18):
    cur, out = [], []
    for w in words:
        if cur and (len(cur) >= max_words or sum(len(x[0]) + 1 for x in cur) + len(w[0]) > max_chars
                    or cur[-1][0][-1:] in ".!?:"):
            out.append(cur)
            cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    return out


def build_ass(scenes, timeline, total):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Inter Black,92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,7,3,5,60,60,0,1
Style: Big,Inter Black,170,&H00303BFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,9,4,5,40,40,0,1
Style: Src,Inter Medium,38,&H00E6E6E6,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,3,1,5,40,40,0,1
Style: Title,Inter Black,104,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,8,4,8,60,60,230,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    pop = r"{\fscx70\fscy70\t(0,120,\fscx112\fscy112)\t(120,220,\fscx100\fscy100)}"
    for sc, (s0, s1, voice_dur) in zip(scenes, timeline):
        # karaoke-style subtitles in the lower third
        sub = sc.get("sub") or sc["say"]
        if not sc.get("nosub"):
            for ch in chunks_of(words_with_times(sub, s0, voice_dur)):
                for i, (w, a, b) in enumerate(ch):
                    end = ch[i + 1][1] if i + 1 < len(ch) else min(b + 0.25, s1)
                    parts = []
                    for j, (w2, _, _) in enumerate(ch):
                        t = esc(w2.upper())
                        parts.append(r"{\c" + YELLOW + r"\fscx108\fscy108}" + t + r"{\c" + WHITE + r"\fscx100\fscy100}"
                                     if j == i else t)
                    intro = pop if i == 0 else ""
                    ev.append(f"Dialogue: 1,{ts(a)},{ts(end)},Sub,,0,0,0,,{{\\pos({W // 2},1330)}}{intro}{' '.join(parts)}")
        if sc.get("src"):
            ev.append(f"Dialogue: 2,{ts(s0 + 0.2)},{ts(s1)},Src,,0,0,0,,{{\\pos({W // 2},960)}}{esc(sc['src'])}")
        # hook title on top
        if sc.get("title"):
            ev.append(f"Dialogue: 2,{ts(s0)},{ts(s1)},Title,,0,0,0,,{pop}{esc(sc['title'])}")
        # big number / word in the middle
        if sc.get("count") is not None:
            n, suf, steps = float(sc["count"]), sc.get("suffix", ""), 18
            for k in range(steps):
                a = s0 + 0.15 + k * 0.045
                v = n * (1 - (1 - (k + 1) / steps) ** 3)
                b = a + 0.045 if k < steps - 1 else s1
                ev.append(f"Dialogue: 3,{ts(a)},{ts(b)},Big,,0,0,0,,{{\\pos({W // 2},820)}}{fmt_num(v)}{esc(suf)}")
        elif sc.get("big"):
            ev.append(f"Dialogue: 3,{ts(s0 + 0.1)},{ts(s1)},Big,,0,0,0,,{{\\pos({W // 2},820)}}{pop}{esc(sc['big'])}")
    return head + "\n".join(ev) + "\n"


# ------------------------------------------------------------------ video

def shot_filter(i, dur, push):
    frames = max(1, int(dur * FPS))
    z = f"min(1+0.08*on/{frames},1.08)" if push else "1.04"
    return (f"[{i}:v]scale=w='if(gt(iw/ih,{W}/{H}),-2,{W})':h='if(gt(iw/ih,{W}/{H}),{H},-2)',"
            f"crop={W}:{H},setsar=1,fps={FPS},"
            f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS},"
            f"trim=duration={dur:.3f},setpts=PTS-STARTPTS[v{i}]")


def render(scenes, voice_files, clip_files, out_path, work, title_frames=None):
    """voice_files[i] = path to voice of scene i; clip_files[i] = list of local video paths."""
    from_dur = []
    for v in voice_files:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                              "-of", "default=nw=1:nk=1", v], capture_output=True, text=True, check=True)
        from_dur.append(float(out.stdout.strip()))
    gap = 0.12
    timeline, t = [], 0.0
    for d in from_dur:
        timeline.append((t, t + d + gap, d))
        t += d + gap
    total = t + 0.4

    # shots: cut every ~CUT seconds inside each scene, alternate clips of the scene
    shots = []   # (path, src_offset, dur, push)
    rnd = random.Random(7)
    for i, (s0, s1, _) in enumerate(timeline):
        if i == len(timeline) - 1:
            s1 = total
        clips = clip_files[i] or clip_files[max(0, i - 1)]
        n = max(1, round((s1 - s0) / CUT))
        seg = (s1 - s0) / n
        for k in range(n):
            path, clip_len = clips[k % len(clips)]
            off = 0.0 if clip_len <= seg + 0.5 else rnd.uniform(0, max(0.0, clip_len - seg - 0.3))
            shots.append((path, off, seg, (len(shots) % 2 == 0)))

    cmd = ["ffmpeg", "-y", "-v", "error"]
    for path, off, dur, _ in shots:
        cmd += ["-ss", f"{off:.2f}", "-t", f"{dur + 0.2:.2f}", "-stream_loop", "-1", "-i", path]
    fc = [shot_filter(i, dur, push) for i, (_, _, dur, push) in enumerate(shots)]
    fc.append("".join(f"[v{i}]" for i in range(len(shots))) + f"concat=n={len(shots)}:v=1:a=0[cat]")
    ass_path = os.path.join(work, "subs.ass")
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(build_ass(scenes, timeline, total))
    fontsdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
    fc.append(f"[cat]eq=brightness=-0.06:saturation=1.12:contrast=1.08,vignette=PI/4.5,"
              f"drawbox=x=0:y=0:w=iw:h=14:color=black@0.45:t=fill,"
              f"drawbox=x=0:y=0:w='iw*t/{total:.3f}':h=14:color=0xFF3B30@1:t=fill,"
              f"ass={ass_path}:fontsdir={fontsdir},format=yuv420p[vout]")
    silent = os.path.join(work, "video.mp4")
    run(cmd + ["-filter_complex", ";".join(fc), "-map", "[vout]", "-t", f"{total:.3f}",
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-r", str(FPS), silent])

    # audio: voices on the timeline + whoosh on every cut + hit where asked
    whoosh, hit = make_sfx(work)
    a_in, a_fc, labels = [], [], []
    for i, (v, (s0, _, _)) in enumerate(zip(voice_files, timeline)):
        a_in += ["-i", v]
        a_fc.append(f"[{i}:a]aresample=44100,aformat=channel_layouts=stereo,adelay={int(s0 * 1000)}:all=1[a{i}]")
        labels.append(f"[a{i}]")
    k = len(voice_files)
    cut_t, acc = [], 0.0
    for _, _, dur, _ in shots[:-1]:
        acc += dur
        cut_t.append(acc)
    for j, ct in enumerate(cut_t):
        a_in += ["-i", whoosh]
        a_fc.append(f"[{k}:a]volume=0.35,adelay={int(max(0, ct - 0.2) * 1000)}:all=1[w{j}]")
        labels.append(f"[w{j}]")
        k += 1
    for i, sc in enumerate(scenes):
        if sc.get("hit") or sc.get("count") is not None or sc.get("big"):
            a_in += ["-i", hit]
            a_fc.append(f"[{k}:a]volume=0.6,adelay={int(timeline[i][0] * 1000 + 100)}:all=1[h{i}]")
            labels.append(f"[h{i}]")
            k += 1
    a_fc.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=longest,"
                f"alimiter=limit=0.95,apad,atrim=0:{total:.3f}[aout]")
    audio = os.path.join(work, "audio.m4a")
    run(["ffmpeg", "-y", "-v", "error"] + a_in + ["-filter_complex", ";".join(a_fc), "-map", "[aout]",
                                                    "-c:a", "aac", "-b:a", "192k", audio])
    run(["ffmpeg", "-y", "-v", "error", "-i", silent, "-i", audio, "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "copy", "-shortest", "-movflags", "+faststart", out_path])
    # preview frames
    previews = []
    for j, frac in enumerate((0.03, 0.35, 0.7)):
        p = os.path.join(work, f"prev{j}.jpg")
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{total * frac:.2f}", "-i", out_path, "-frames:v", "1", p])
        previews.append(p)
    return {"seconds": round(total, 1), "shots": len(shots), "previews": previews}
