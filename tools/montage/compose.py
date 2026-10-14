"""Talking-head auto-edit compositor.

plan.json:
{
 "src": "raw.mov",
 "face": [cx, cy],            # face center, fractions of source frame
 "keep": [[s,e], ...],        # source ranges to keep (in order)
 "shots": [ {"t0":0,"t1":2.4,"mode":"full","z":1.5,"push":true} ,
            {"t0":..,"t1":..,"mode":"split","card":"cards/copywriter.mp4"} ],   # output timeline
 "subs": [[t0,t1,"text", ["hi","words"]], ...],   # output timeline, optional highlight words
 "overlays": [{"file":"hook.mov","t0":0}],          # alpha videos full-frame
 "sfx": [[t,"whoosh"],[t,"pop"]],
 "out": "edit.mp4"
}
"""
import json, os, subprocess, sys, tempfile, shutil

W, H, FPS = 1080, 1920, 30
FONT_DIR = "/usr/share/fonts/opentype/inter"


def run(cmd):
    subprocess.run(cmd, check=True)


def ts(t):
    t = max(0, t)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def build_talk(plan, work):
    """Cut keep-ranges frame-accurately: every piece is an exact number of frames, audio padded/trimmed
    to the same length, so voice and picture never drift apart after concatenation."""
    lst = os.path.join(work, "keep.txt")
    with open(lst, "w") as f:
        for i, (s, e) in enumerate(plan["keep"]):
            n = max(1, round((e - s) * FPS))
            dur = n / FPS
            p = os.path.join(work, f"k{i:03d}.mov")
            run(["ffmpeg", "-y", "-v", "error", "-ss", f"{s:.3f}", "-i", plan["src"], "-t", f"{dur:.4f}",
                 "-vf", f"fps={FPS},scale=1072:1904,setsar=1", "-frames:v", str(n),
                 "-af", f"aresample=48000,atrim=0:{dur:.4f},apad=whole_dur={dur:.4f},"
                        f"afade=t=in:d=0.02,afade=t=out:st={max(0, dur - 0.03):.4f}:d=0.03",
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-c:a", "pcm_s16le", p])
            f.write(f"file '{p}'\n")
    talk = os.path.join(work, "talk.mov")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", talk])
    return talk


def crop_expr(cx, cy, z, push, dur, sw=1072, sh=1904):
    n = max(1, int(dur * FPS))
    ze = f"{z}*(1+0.08*on/{n})" if push else f"{z}"
    x = f"max(0,min(iw-iw/zoom,{cx:.4f}*iw-iw/zoom/2))"
    y = f"max(0,min(ih-ih/zoom,{cy:.4f}*ih-ih/zoom/2))"
    return f"zoompan=z='{ze}':x='{x}':y='{y}':d=1:s={W}x{H}:fps={FPS}"


def render_shot(i, shot, talk, plan, work):
    t0, t1 = shot["t0"], shot["t1"]
    dur = t1 - t0
    cx, cy = plan["face"]
    out = os.path.join(work, f"s{i:03d}.mp4")
    if shot["mode"] == "full":
        z = shot.get("z", 1.5)
        cyo = shot.get("cy", cy)
        vf = f"fps={FPS}," + crop_expr(cx, cyo, z, shot.get("push", False), dur) + ",setsar=1"
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", talk, "-vf", vf, "-an",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", out])
    else:  # split: card on top, face crop at bottom
        ch_frac = shot.get("face_h", 0.47)  # fraction of source height shown in bottom half
        sh, sw = 1904, 1072
        chh = ch_frac * sh
        cww = chh * W / (H / 2)
        cww = min(cww, sw)
        chh = cww * (H / 2) / W
        fy = shot.get("fy", cy - 0.04)
        x = max(0, min(sw - cww, cx * sw - cww / 2))
        y = max(0, min(sh - chh, fy * sh - chh / 2))
        card = shot["card"]
        fc = (f"[0:v]crop={cww:.1f}:{chh:.1f}:{x:.1f}:{y:.1f},scale={W}:{H // 2},setsar=1,fps={FPS}[face];"
              f"[1:v]scale={W}:{H // 2},setsar=1,fps={FPS},tpad=stop_mode=clone:stop_duration=30,trim=duration={dur:.3f}[card];"
              f"[card][face]vstack=2[v]")
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", talk, "-i", card,
             "-filter_complex", fc, "-map", "[v]", "-an", "-t", f"{dur:.3f}",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", out])
    return out


def sub_ass(plan, work, total):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Inter Black,66,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,7,3,5,110,110,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    for ev in plan.get("subs", []):
        t0, t1, text = ev[0], ev[1], ev[2]
        hi = set(w.lower() for w in (ev[3] if len(ev) > 3 else []))
        y = ev[4] if len(ev) > 4 else plan.get("sub_y", 1400)
        words = []
        for w in text.split():
            core = w.strip(".,!?«»—:;").lower()
            if core in hi:
                words.append("{\\c&H4579FF&}" + w + "{\\c&HFFFFFF&}")
            else:
                words.append(w)
        fade = "{\\fad(80,60)}"
        lines.append(f"Dialogue: 1,{ts(t0)},{ts(min(t1, total))},Sub,,0,0,0,,{{\\pos({W // 2},{y})}}{fade}" + " ".join(words))
    p = os.path.join(work, "subs.ass")
    with open(p, "w", encoding="utf-8") as f:
        f.write(head + "\n".join(lines) + "\n")
    return p


def make_sfx(work):
    wh = os.path.join(work, "whoosh.wav")
    run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anoisesrc=d=0.45:c=pink:a=0.6",
         "-af", "highpass=f=400,lowpass=f=5000,afade=t=in:d=0.18,afade=t=out:st=0.2:d=0.25,volume=0.55", wh])
    pop = os.path.join(work, "pop.wav")
    run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "sine=f=880:d=0.09",
         "-af", "afade=t=out:st=0.02:d=0.07,volume=0.35", pop])
    hit = os.path.join(work, "hit.wav")
    run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "sine=f=60:d=0.35",
         "-af", "afade=t=out:st=0.05:d=0.3,volume=0.9", hit])
    return {"whoosh": wh, "pop": pop, "hit": hit}


def main(plan_path):
    plan = json.load(open(plan_path))
    base = os.path.dirname(os.path.abspath(plan_path))
    os.chdir(base)
    work = tempfile.mkdtemp(prefix="cmp-")
    try:
        talk = build_talk(plan, work)
        total = plan["shots"][-1]["t1"]
        seg_list = os.path.join(work, "shots.txt")
        with open(seg_list, "w") as f:
            for i, s in enumerate(plan["shots"]):
                f.write(f"file '{render_shot(i, s, talk, plan, work)}'\n")
        video = os.path.join(work, "video.mp4")
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", seg_list, "-c", "copy", video])
        ass = sub_ass(plan, work, total)
        sfx = make_sfx(work)
        # video chain: subs + overlays
        inputs = ["-i", video, "-i", talk]
        fc = [f"[0:v]ass={ass}:fontsdir={FONT_DIR}[v0]"]
        last = "v0"
        k = 2
        for j, ov in enumerate(plan.get("overlays", [])):
            inputs += ["-itsoffset", f"{ov['t0']:.3f}", "-i", ov["file"]]
            fc.append(f"[{k}:v]format=rgba[o{j}];[{last}][o{j}]overlay=0:0:eof_action=pass[v{j + 1}]")
            last = f"v{j + 1}"
            k += 1
        # audio: voice + sfx (+music later)
        amix = ["[1:a]aresample=48000,volume=1.0[voice]"]
        alabels = ["[voice]"]
        for j, (t, kind) in enumerate(plan.get("sfx", [])):
            inputs += ["-i", sfx[kind]]
            d = int(t * 1000)
            amix.append(f"[{k}:a]adelay={d}|{d},aresample=48000[x{j}]")
            alabels.append(f"[x{j}]")
            k += 1
        if plan.get("music"):
            inputs += ["-stream_loop", "-1", "-i", plan["music"]]
            amix.append(f"[{k}:a]aresample=48000,volume={plan.get('music_vol', 0.12)}[mus]")
            alabels.append("[mus]")
            k += 1
        amix.append("".join(alabels) + f"amix=inputs={len(alabels)}:normalize=0:duration=first,"
                    f"loudnorm=I=-15:TP=-1.5:LRA=11,afade=t=out:st={max(0, total - 1.0):.2f}:d=1.0[a]")
        fc.append(f"[{last}]fade=t=out:st={max(0, total - 0.6):.2f}:d=0.6,format=yuv420p[vout]")
        cmd = ["ffmpeg", "-y", "-v", "error"] + inputs + ["-filter_complex", ";".join(fc + amix),
               "-map", "[vout]", "-map", "[a]", "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium",
               "-crf", "19", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", plan["out"]]
        run(cmd)
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1])
