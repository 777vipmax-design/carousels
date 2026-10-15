"""Автомонтаж рилса одной командой:  python make.py script.json

Что делает:
 1. Голос: нейросеть (kie.ai, ключ в переменной KIE_API_KEY) или твои записи (voice/01.mp3, 02.mp3 …)
 2. Тайминги фраз → границы сцен и субтитры
 3. Сцены на весь экран (engine/reel.html) → видео 1080×1920, 30 кадров/с
 4. Обложка первым кадром, музыка фоном, звуки на смене сцен → final.mp4
Нужно: Python 3.10+, ffmpeg, playwright (pip install playwright && playwright install chromium).
"""
import json, os, re, shutil, subprocess, sys, tempfile, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.join(HERE, "engine")
FPS = 30


def run(*a):
    subprocess.run(a, check=True, capture_output=True)


def dur(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                         capture_output=True, text=True).stdout
    return float(out.strip())


# ---------- 1. голос ----------
def kie(method, path, body=None):
    key = os.environ.get("KIE_API_KEY")
    if not key:
        sys.exit("Нет ключа: задай переменную окружения KIE_API_KEY (или используй свой голос: voice.mode = own)")
    req = urllib.request.Request("https://api.kie.ai/api/v1/jobs/" + path, method=method,
                                 data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def tts_kie(text, voice, speed, out):
    name, style = (voice.split(":") + ["Promo/Hype"])[:2]
    inp = {"temperature": 1, "scene": "Озвучка короткого вертикального ролика на русском языке.",
           "sample_context": "Живой уверенный голос рассказчика, чистое русское произношение.",
           "speakers": [{"speaker_id": "Speaker 1", "voice_name": name, "audio_profile": "Уверенный рассказчик с эмоцией",
                         "accent": "Neutral", "style": style, "pace": "Natural"}],
           "dialogue_turns": [{"speaker_id": "Speaker 1", "text": text}]}
    task = kie("POST", "createTask", {"model": "google/gemini-3-1-flash-tts", "input": inp})["data"]["taskId"]
    for _ in range(150):
        time.sleep(4)
        info = kie("GET", "recordInfo?taskId=" + task).get("data") or {}
        if info.get("state") == "success":
            url = json.loads(info["resultJson"])["resultUrls"][0]
            raw = out + ".src"
            urllib.request.urlretrieve(url, raw)
            run("ffmpeg", "-y", "-v", "error", "-i", raw, "-af", f"atempo={speed}", out)
            os.remove(raw)
            return
        if info.get("state") == "fail":
            sys.exit("kie.ai: " + str(info.get("failMsg")))
    sys.exit("kie.ai: не дождался озвучки")


def build_voice(cfg, lines, work):
    v = cfg.get("voice", {})
    mode, files = v.get("mode", "own"), []
    for i, L in enumerate(lines, 1):
        dst = os.path.join(work, f"v{i:02d}.wav")
        if mode == "kie":
            mp3 = dst.replace(".wav", ".mp3")
            print(f"  озвучка {i}/{len(lines)}…")
            tts_kie(L["say"], v.get("kie_voice", "Gacrux:Promo/Hype"), float(v.get("speed", 1.15)), mp3)
            src = mp3
        else:
            src = os.path.join(HERE, "voice", f"{i:02d}.mp3")
            if not os.path.exists(src):
                sys.exit(f"Нет файла голоса {src} — запиши фразу №{i}: «{L['say']}»")
        # обрезаем тишину по краям и выравниваем громкость
        run("ffmpeg", "-y", "-v", "error", "-i", src, "-af",
            "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse",
            "-ar", "44100", "-ac", "1", dst)
        files.append(dst)
    gap = os.path.join(work, "gap.wav")
    run("ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "0.22", gap)
    lst, t, tl = os.path.join(work, "list.txt"), 0.0, []
    with open(lst, "w") as f:
        for p in files:
            d = dur(p)
            tl.append((round(t, 3), round(t + d, 3)))
            t += d + 0.22
            f.write(f"file '{p}'\nfile '{gap}'\n")
    out = os.path.join(work, "voice.wav")
    run("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-af", "loudnorm=I=-14:TP=-1", out)
    return out, tl, t + 0.4


# ---------- 2. субтитры ----------
SHORT = {"в", "и", "из", "за", "от", "не", "как", "а", "на", "с", "по", "к", "у", "о", "что", "это", "то"}


def subtitles(lines, tl):
    chunks = []
    for L, (a, b) in zip(lines, tl):
        toks = [x for x in re.sub(r"\[[^\]]*\]", "", L["say"]).split(" ") if x]
        words = [x for x in toks if x != "—"]
        lens = [len(x) + 2 for x in words]
        tot, c, times = sum(lens), a, []
        for l in lens:
            d = (b - a) * l / tot
            times.append((c, c + d))
            c += d
        items, j = [], 0
        for x in toks:
            if x == "—":
                if items:
                    items[-1][0] += " —"
                continue
            items.append([re.sub(r"[.,!?:;«»\"]", "", x), times[j][0], times[j][1], bool(re.search(r"[.,!?:;]$", x))])
            j += 1
        cur = []
        for k, it in enumerate(items):
            cur.append(it)
            nxt = items[k + 1] if k + 1 < len(items) else None
            brk = it[3] or len(cur) >= 3 or nxt is None
            if brk and nxt and it[0].lower() in SHORT and not it[3]:
                brk = False
            if brk or len(cur) >= 4:
                chunks.append(cur)
                cur = []
    out = []
    for j, c in enumerate(chunks):
        s = c[0][1] - 0.05
        nx = chunks[j + 1][0][1] - 0.05 if j + 1 < len(chunks) else 1e9
        out.append([round(s, 2), round(min(nx, c[-1][2] + 0.7), 2), [[x[0], round(x[1], 2), round(x[2], 2)] for x in c]])
    return out


# ---------- 3. видео ----------
def render(tl_str, total, work, cover_t=2.5):
    from playwright.sync_api import sync_playwright
    frames = os.path.join(work, "frames")
    os.makedirs(frames, exist_ok=True)
    url = "file://" + os.path.join(ENG, "reel.html") + "?tl=" + tl_str
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto(url + "&nosub=1")
        pg.wait_for_timeout(1500)
        pg.evaluate(f"renderAt({cover_t})")
        pg.screenshot(path=os.path.join(HERE, "cover.png"))
        pg.goto(url)
        pg.wait_for_timeout(1500)
        n = int(round(total * FPS))
        for i in range(n):
            pg.evaluate(f"renderAt({i / FPS})")
            pg.screenshot(path=os.path.join(frames, f"{i:05d}.jpg"), type="jpeg", quality=92)
            if i % 150 == 0:
                print(f"  кадры {i}/{n}")
        b.close()
    shutil.copy(os.path.join(HERE, "cover.png"), os.path.join(frames, "00000.png"))
    vid = os.path.join(work, "video.mp4")
    run("ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", os.path.join(frames, "%05d.jpg"),
        "-i", os.path.join(HERE, "cover.png"), "-filter_complex", "[0][1]overlay=enable='eq(n,0)'",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", vid)
    return vid


# ---------- 4. звук ----------
def sfx(kind, path):
    fc = {"whoosh": "anoisesrc=d=0.45:c=pink:a=0.6,highpass=f=400,lowpass=f=5000,afade=t=in:d=0.18,afade=t=out:st=0.2:d=0.25",
          "pop": "sine=f=900:d=0.12,volume='1.2*exp(-30*t)':eval=frame,afade=t=out:st=0.05:d=0.07"}[kind]
    run("ffmpeg", "-y", "-v", "error", "-filter_complex", fc, "-ar", "44100", "-ac", "1", path)


def mix(vid, voice, tl, music, work, out):
    w, p = os.path.join(work, "whoosh.wav"), os.path.join(work, "pop.wav")
    sfx("whoosh", w)
    sfx("pop", p)
    ins = ["-i", vid, "-i", voice]
    fc, labels, k = [], ["[1:a]"], 2
    if music:
        ins += ["-stream_loop", "-1", "-i", music]
        fc.append(f"[{k}:a]volume=0.2,afade=t=in:d=0.8[m];[m][1:a]sidechaincompress=threshold=0.03:ratio=6[md]")
        labels.append("[md]")
        k += 1
    for i, (a, _) in enumerate(tl):
        for kind, t, vol in ([("whoosh", a - 0.15, 0.6)] if i else []) + [("pop", a + 0.4, 0.5)]:
            ins += ["-i", w if kind == "whoosh" else p]
            ms = int(max(0, t) * 1000)
            fc.append(f"[{k}:a]volume={vol},adelay={ms}|{ms}[s{k}]")
            labels.append(f"[s{k}]")
            k += 1
    fc.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=first,alimiter=limit=0.95[a]")
    run("ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", ";".join(fc), "-map", "0:v", "-map", "[a]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out)


def main():
    cfg = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "script.json"), encoding="utf-8"))
    lines = cfg["lines"]
    work = tempfile.mkdtemp(prefix="reel-")
    print("1/4 голос")
    voice, tl, total = build_voice(cfg, lines, work)
    print("2/4 субтитры")
    with open(os.path.join(ENG, "words.js"), "w", encoding="utf-8") as f:
        f.write("const WORDS=1;const CHUNKS=" + json.dumps(subtitles(lines, tl), ensure_ascii=False) + ";")
    with open(os.path.join(ENG, "script.js"), "w", encoding="utf-8") as f:
        f.write("const SCRIPT=" + json.dumps(cfg, ensure_ascii=False) + ";")
    tl_str = ",".join(str(a) for a, _ in tl) + f",{round(total, 3)}"
    print("3/4 видео (самый долгий шаг)")
    vid = render(tl_str, total, work)
    print("4/4 звук")
    music = cfg.get("music")
    music = os.path.join(HERE, music) if music and not os.path.isabs(music) else music
    out = os.path.join(HERE, cfg.get("out", "final.mp4"))
    mix(vid, voice, tl, music if music and os.path.exists(music) else None, work, out)
    shutil.rmtree(work, ignore_errors=True)
    print("Готово:", out, f"({total:.1f} с)")


if __name__ == "__main__":
    main()
