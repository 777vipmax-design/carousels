"""Carousel media server: kie.ai covers, ElevenLabs voice (via kie.ai) and Reels.

A small MCP server (Streamable HTTP, stateless JSON responses) written with the
standard library only, so it has no Python dependencies besides Pillow.

Endpoint:  POST https://<domain>/mcp/<TOKEN>
Files:     https://<domain>/f/<post>/<file>   (served by Caddy from FILES_DIR)

Config comes from /etc/carousel.env (see install.sh).
"""
import base64
import hashlib
import io
import json
import re
import os
import shutil
import subprocess
import tempfile
import threading
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from PIL import Image, ImageDraw, ImageFont

KIE_KEY = os.environ.get("KIE_API_KEY", "")
TOKEN = os.environ.get("MCP_TOKEN", "")
DOMAIN = os.environ.get("DOMAIN", "localhost")
FILES_DIR = os.environ.get("FILES_DIR", "/var/lib/carousel/files")
REPO_DIR = os.environ.get("REPO_DIR", "/opt/carousel/repo")
PORT = int(os.environ.get("PORT", "8000"))
RAW_BASE = os.environ.get("RAW_BASE", "https://raw.githubusercontent.com/777vipmax-design/carousels/main")
KIE_API = "https://api.kie.ai/api/v1/jobs"
PIXABAY_KEY = os.environ.get("PIXABAY_KEY", "")
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
VERSION = "2.4"
TTS_TIMESTAMPS = os.environ.get("TTS_TIMESTAMPS", "0") == "1"
ELEVEN_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
EL_UA = "elevenlabs-python/2.16.0 carousel-server"
ELEVEN_MODEL = os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")

BG = (17, 18, 20)
RED = (255, 59, 48)
W, H = 1080, 1920

JOBS = {}
JOBS_LOCK = threading.Lock()
POOL = ThreadPoolExecutor(max_workers=6)  # long kie waits (Kling) must not block quick renders; RENDER_LOCK still serialises ffmpeg
TTS_POOL = ThreadPoolExecutor(max_workers=4)
RENDER_LOCK = threading.Lock()  # 2 GB RAM: render one video at a time (parallel builds were OOM-killed)


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# ---------------------------------------------------------------- helpers

def public_url(post, name):
    return f"https://{DOMAIN}/f/{post}/{name}"


def post_dir(post):
    safe = "".join(c for c in post if c.isalnum() or c in "-_")
    if not safe:
        raise ValueError("bad post name")
    d = os.path.join(FILES_DIR, safe)
    os.makedirs(d, exist_ok=True)
    return safe, d


def http_get(url, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": "carousel-server"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def kie(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{KIE_API}/{path}", data=data, method=method, headers={
        "Authorization": f"Bearer {KIE_KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def kie_task(model, inp, max_wait=900):
    """Create a kie.ai task and wait for it. Returns (urls, info)."""
    res = kie("POST", "createTask", {"model": model, "input": inp})
    task = (res.get("data") or {}).get("taskId")
    if not task:
        raise RuntimeError(f"kie.ai createTask failed: {res}")
    t0 = time.time()
    while time.time() - t0 < max_wait:
        time.sleep(4)
        info = kie("GET", f"recordInfo?taskId={task}").get("data") or {}
        state = info.get("state")
        if state == "success":
            rj = info.get("resultJson") or "{}"
            rj = json.loads(rj) if isinstance(rj, str) else rj
            return rj.get("resultUrls") or [], {"taskId": task, "credits": info.get("creditsConsumed"), "result": rj}
        if state == "fail":
            raise RuntimeError(f"kie.ai task failed: {info.get('failMsg')}")
    raise TimeoutError("kie.ai task timeout")


def font(weight, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, f"Inter-{weight}.otf"), size)


def preview_jpeg(path_or_img, max_side=700):
    im = path_or_img if isinstance(path_or_img, Image.Image) else Image.open(path_or_img)
    im = im.convert("RGB")
    im.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=80)
    return base64.b64encode(buf.getvalue()).decode()


def probe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", path], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


# ---------------------------------------------------------------- jobs

def start_job(kind, fn, *args):
    jid = uuid.uuid4().hex[:10]
    with JOBS_LOCK:
        JOBS[jid] = {"id": jid, "kind": kind, "state": "running", "started": time.time()}

    def run():
        try:
            result = fn(*args)
            with JOBS_LOCK:
                JOBS[jid].update(state="done", result=result, finished=time.time())
        except Exception as e:  # noqa: BLE001
            log("job", jid, "failed", traceback.format_exc())
            with JOBS_LOCK:
                JOBS[jid].update(state="error", error=str(e), finished=time.time())
    POOL.submit(run)
    return jid


# ---------------------------------------------------------------- cover

def do_cover(post, prompt, refs, aspect_ratio, resolution, out):
    post, d = post_dir(post)
    urls, info = kie_task("nano-banana-pro", {
        "prompt": prompt, "image_input": refs or [], "aspect_ratio": aspect_ratio,
        "resolution": resolution, "output_format": "png"})
    if not urls:
        raise RuntimeError("no image returned")
    path = os.path.join(d, out)
    with open(path, "wb") as f:
        f.write(http_get(urls[0]))
    return {"url": public_url(post, out), "file": path, "credits": info.get("credits")}


# ---------------------------------------------------------------- voice

def tts_eleven(text, voice, speed, out_path):
    """Direct ElevenLabs API with character timestamps (for subtitles).
    voice = 'VOICE_ID' or 'MODEL_ID|VOICE_ID'."""
    model = ELEVEN_MODEL
    if "|" in voice:
        model, voice = voice.split("|", 1)
    body = {"text": text, "model_id": model,
            "voice_settings": {"stability": 0.45, "similarity_boost": 0.75, "style": 0.2,
                               "use_speaker_boost": True, "speed": speed}}
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128",
        data=json.dumps(body).encode(), method="POST",
        headers={"xi-api-key": ELEVEN_KEY, "User-Agent": EL_UA, "Accept": "application/json", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            res = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"ElevenLabs {e.code}: {e.read().decode()[:300]}") from None
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(res["audio_base64"]))
    return {"alignment": res.get("alignment") or res.get("normalized_alignment")}


GEMINI_MODELS = {"g31": "google/gemini-3-1-flash-tts", "g38": "google/gemini-3-8-flash-tts",
                 "g25": "google/gemini-2-5-pro-tts"}


GEMINI_PROFILES = {
    "": ("Уверенный русскоязычный рассказчик, говорит с эмоцией",
         "Живой, уверенный мужской голос рассказчика, чистое русское произношение."),
    "raspy": ("Низкий грубоватый мужской голос с заметной хрипотцой, дерзкий, ироничный, с усмешкой",
              "Бывалый уверенный мужик рассказывает другу неприятную правду о деньгах: хрипловато, "
              "с сарказмом и паузами для эффекта, чистое русское произношение."),
    "loud": ("Тот же мужской голос, но на эмоциях: громко, напористо, почти кричит на ключевых словах, возмущение и азарт",
             "Эмоциональный монолог для вирусного ролика: человек возмущён и взбудоражен, резкие акценты, "
             "короткие паузы перед цифрами, на главных словах повышает голос. Чистое русское произношение."),
    "lyuba": ("Громкий, хрипловатый, напористый женский голос тётки лет пятидесяти, бывалой и острой на язык, с азартом и сарказмом",
              "Тётя Люба — домашняя гадалка с советской кухни: говорит громко, эмоционально, по-базарному смешно, "
              "резко повышает голос на ответе, делает театральные паузы, ироничные интонации. Чистое русское произношение."),
    "rough": ("Низкий, плотный, хриплый мужской голос, энергичный и напористый",
              "Жёсткий мотивирующий монолог: напор, хрипотца, короткие рубленые фразы, чистое русское произношение."),
}


_RUBBERBAND = None


def tempo_filter(speed):
    """Speed up speech without changing the voice: rubberband keeps pitch and formants
    (atempo is the fallback and can sound 'thinner' at 1.4+)."""
    global _RUBBERBAND
    if _RUBBERBAND is None:
        out = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
        _RUBBERBAND = " rubberband " in out
    if _RUBBERBAND and os.environ.get("TEMPO_RUBBERBAND") == "1":
        return f"rubberband=tempo={speed:.3f}:pitchq=quality:formant=preserved:transients=smooth:detector=soft"
    return f"atempo={speed:.3f}"


def tts_gemini(text, voice, speed, out_path):
    """voice = 'g31:Charon[:Style]' — Gemini TTS through kie.ai (no word timestamps)."""
    parts = voice.split(":")
    model = GEMINI_MODELS[parts[0]]
    name = parts[1] if len(parts) > 1 else "Charon"
    style = parts[2] if len(parts) > 2 and parts[2] else ("Promo/Hype" if speed >= 1.05 else "Empathetic")
    prof = GEMINI_PROFILES.get(parts[3] if len(parts) > 3 else "", GEMINI_PROFILES[""])
    pace = "Natural"
    inp = {"temperature": 1,
           "scene": "Озвучка короткого вертикального ролика в Instagram на русском языке.",
           "sample_context": prof[1],
           "speakers": [{"speaker_id": "Speaker 1", "voice_name": name,
                         "audio_profile": prof[0],
                         "accent": "Neutral", "style": style, "pace": pace}],
           "dialogue_turns": [{"speaker_id": "Speaker 1", "text": text}]}
    urls, info = kie_task(model, inp, max_wait=600)
    if not urls:
        raise RuntimeError(f"no audio for: {text[:40]}")
    raw = out_path + ".src"
    with open(raw, "wb") as f:
        f.write(http_get(urls[0]))
    af = ["-af", tempo_filter(speed)] if abs(speed - 1) > 0.01 else []
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, *af, "-b:a", "160k", out_path], check=True)
    os.remove(raw)
    return info.get("result") or {}


def tts(text, voice, speed, out_path):
    if voice.split(":")[0] in GEMINI_MODELS:
        for attempt in range(3):  # kie sometimes answers "internal error"
            try:
                return tts_gemini(text, voice, speed, out_path)
            except Exception:  # noqa: BLE001
                if attempt == 2:
                    raise
                time.sleep(5)
    if ELEVEN_KEY:
        return tts_eleven(text, voice, speed, out_path)
    inp = {"text": text, "voice": voice, "stability": 0.5, "similarity_boost": 0.75, "style": 0,
           "speed": speed, "timestamps": TTS_TIMESTAMPS, "previous_text": "", "next_text": "",
           "language_code": ""}
    urls, info = kie_task("elevenlabs/text-to-speech-multilingual-v2", inp, max_wait=600)
    if not urls:
        raise RuntimeError(f"no audio for: {text[:40]}")
    with open(out_path, "wb") as f:
        f.write(http_get(urls[0]))
    return info.get("result") or {}


def find_alignment(obj):
    """Find an ElevenLabs-style character alignment anywhere in the result."""
    if isinstance(obj, dict):
        if "character_start_times_seconds" in obj and "characters" in obj:
            return obj
        for v in obj.values():
            r = find_alignment(v)
            if r:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = find_alignment(v)
            if r:
                return r
    elif isinstance(obj, str) and "character_start_times_seconds" in obj:
        try:
            return find_alignment(json.loads(obj))
        except ValueError:
            return None
    return None


def word_times(text, duration, result):
    """Return [(word, start, end)] using alignment if available, else by length."""
    words = re.sub(r"\[[^\]]*\]", " ", text).split()
    al = find_alignment(result)
    if al:
        chars, starts = al["characters"], al["character_start_times_seconds"]
        ends = al.get("character_end_times_seconds", starts)
        out, cur, cs, ce, depth = [], "", None, None, 0
        for ch, s, e in zip(chars, starts, ends):
            if ch == "[":  # audio tags like [excited] are not shown in subtitles
                depth += 1
                continue
            if ch == "]":
                depth = max(0, depth - 1)
                continue
            if depth:
                continue
            if ch.isspace():
                if cur:
                    out.append((cur, cs, ce))
                cur, cs = "", None
                continue
            if cs is None:
                cs = s
            cur += ch
            ce = e
        if cur:
            out.append((cur, cs, ce))
        if out:
            return out
    total = sum(len(w) + 1 for w in words) or 1
    t, out = 0.0, []
    for w in words:
        dur = duration * (len(w) + 1) / total
        out.append((w, t, t + dur))
        t += dur
    return out


def do_voice_samples(text, voices, speed):
    post, d = post_dir("voice-samples")
    res = {}
    for v in voices:
        name = "".join(c for c in v.lower().replace("|", "-") if c.isalnum() or c in "-_") + ".mp3"
        try:
            tts(text, v, speed, os.path.join(d, name))
            res[v] = public_url(post, name)
        except Exception as e:  # noqa: BLE001
            res[v] = f"ошибка: {e}"
    return res


# ---------------------------------------------------------------- reel

def chunk_words(wt, max_chars=22):
    chunks, cur = [], []
    for w in wt:
        if cur and (sum(len(x[0]) + 1 for x in cur) + len(w[0]) > max_chars
                    or cur[-1][0][-1:] in ".!?:"):
            chunks.append(cur)
            cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    return [(" ".join(x[0] for x in c), c[0][1], c[-1][2]) for c in chunks]


def base_frame(slide_img, layout="fit"):
    """fit  — slide 920 px wide, subtitles under it on the dark background.
    full — slide edge to edge (1080 px), subtitles over the lower part of the picture.
    A 9:16 image (generated cover) always fills the whole frame."""
    s = slide_img.convert("RGB")
    if s.height / s.width > 1.6:
        s = s.resize((W, H), Image.LANCZOS)
        return s, 1180
    if layout == "full":
        sh = round(s.height * W / s.width)
        s = s.resize((W, sh), Image.LANCZOS)
        f = Image.new("RGB", (W, H), BG)
        top = 110
        f.paste(s, (0, top))
        return f, top + sh - 330
    sw = 920
    sh = round(s.height * sw / s.width)
    s = s.resize((sw, sh), Image.LANCZOS)
    f = Image.new("RGB", (W, H), BG)
    f.paste(s, ((W - sw) // 2, 100))
    return f, 100 + sh


def draw_sub(frame, text, top):
    im = frame.copy()
    if not text:
        return im
    d = ImageDraw.Draw(im)
    f = font("Black", 64)
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if f.getlength(t) > 960 and cur:
            lines.append(cur)
            cur = w
        else:
            cur = t
    if cur:
        lines.append(cur)
    y = top + 40
    for i, ln in enumerate(lines[:2]):
        x = (W - f.getlength(ln)) / 2
        d.text((x, y), ln, font=f, fill=(255, 255, 255) if i == 0 else (255, 255, 255),
               stroke_width=6, stroke_fill=(0, 0, 0))
        y += 78
    return im


def do_reel(post, lines, voice, speed, gap, slides_base, layout="fit"):
    post, d = post_dir(post)
    work = tempfile.mkdtemp(prefix="reel-")
    try:
        # 1. slides
        imgs = {}
        for ln in lines:
            n = ln["slide"]
            if n in imgs:
                continue
            local = os.path.join(d, f"{n}.png")
            if os.path.exists(local):
                imgs[n] = Image.open(local)
            else:
                imgs[n] = Image.open(io.BytesIO(http_get(f"{slides_base}/{n}.png")))
        # 2. voice, in parallel
        futs = []
        for i, ln in enumerate(lines):
            p = os.path.join(work, f"a{i:02d}.mp3")
            futs.append((p, TTS_POOL.submit(tts, ln["say"], voice, speed, p)))
        results = [(p, f.result()) for p, f in futs]
        # 3. frames + audio
        concat_v, concat_a = [], []
        total = 0.0
        for i, (ln, (apath, res)) in enumerate(zip(lines, results)):
            dur = probe_duration(apath)
            seg = dur + gap
            frame, sub_top = base_frame(imgs[ln["slide"]], ln.get("layout", layout))
            chunks = [] if ln.get("nosub") else chunk_words(word_times(ln.get("sub") or ln["say"], dur, res))
            if not chunks:
                chunks = [("", 0.0, seg)]
            t = 0.0
            for j, (txt, s, e) in enumerate(chunks):
                end = chunks[j + 1][1] if j + 1 < len(chunks) else seg
                if j == 0:
                    s = 0.0
                fp = os.path.join(work, f"f{i:02d}_{j:02d}.png")
                draw_sub(frame, txt, sub_top).save(fp)
                concat_v.append((fp, max(0.05, end - s)))
                t = end
            wav = os.path.join(work, f"a{i:02d}.wav")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", apath, "-af", f"apad=pad_dur={gap}",
                            "-ar", "44100", "-ac", "2", wav], check=True)
            concat_a.append(wav)
            total += seg
        vlist = os.path.join(work, "v.txt")
        with open(vlist, "w") as f:
            for fp, du in concat_v:
                f.write(f"file '{fp}'\nduration {du:.3f}\n")
            f.write(f"file '{concat_v[-1][0]}'\n")
        alist = os.path.join(work, "a.txt")
        with open(alist, "w") as f:
            for a in concat_a:
                f.write(f"file '{a}'\n")
        out = os.path.join(d, "reel.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", vlist,
                        "-f", "concat", "-safe", "0", "-i", alist,
                        "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "veryfast",
                        "-crf", "21", "-c:a", "aac", "-b:a", "160k", "-shortest",
                        "-movflags", "+faststart", out], check=True)
        frames = [concat_v[0][0], concat_v[len(concat_v) // 2][0], concat_v[-1][0]]
        prev_dir = os.path.join(d, "_preview")
        os.makedirs(prev_dir, exist_ok=True)
        previews = []
        for k, fp in enumerate(frames):
            pp = os.path.join(prev_dir, f"frame{k}.png")
            shutil.copy(fp, pp)
            previews.append(pp)
        return {"url": public_url(post, "reel.mp4"), "seconds": round(total, 1),
                "previews": previews}
    finally:
        shutil.rmtree(work, ignore_errors=True)


# ---------------------------------------------------------------- tools

def eleven_models():
    if not ELEVEN_KEY:
        return None
    try:
        req = urllib.request.Request("https://api.elevenlabs.io/v1/models", headers={"xi-api-key": ELEVEN_KEY, "User-Agent": EL_UA, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read()
            try:
                return [m.get("model_id") for m in json.loads(body.decode())]
            except ValueError:
                return f"non-json {r.status} {dict(r.headers)}: {body[:300]!r}"
    except Exception as e:
        return f"error: {e}"


def pixabay_videos(q, n=10):
    """Search Pixabay videos. Returns [{id, url, w, h, dur, tags, thumb}]."""
    url = ("https://pixabay.com/api/videos/?" + urllib.parse.urlencode(
        {"key": PIXABAY_KEY, "q": q, "per_page": max(3, min(int(n), 50)), "safesearch": "true"}))
    data = json.loads(http_get(url, timeout=30).decode())
    out = []
    for h in data.get("hits", []):
        v = h.get("videos", {})
        best = v.get("large") if (v.get("large") or {}).get("url") else v.get("medium") or {}
        if (best.get("width") or 0) > 2000 and (v.get("medium") or {}).get("url"):
            best = v["medium"]  # 4K is too heavy for the 1-CPU server
        out.append({"id": h.get("id"), "url": best.get("url"), "w": best.get("width"), "h": best.get("height"),
                    "dur": h.get("duration"), "tags": h.get("tags"), "thumb": best.get("thumbnail")})
    return out


def pixabay_check():
    if not PIXABAY_KEY:
        return None
    try:
        return f"ok, {len(pixabay_videos('money', 3))} hits"
    except urllib.error.HTTPError as e:
        return f"error {e.code}: {e.read()[:200]!r}; key length {len(PIXABAY_KEY)}"
    except Exception as e:  # noqa: BLE001
        return f"error: {e}"


def tool_stock(a):
    try:
        res = pixabay_videos(a["q"], a.get("n", 10))
    except Exception as e:  # noqa: BLE001
        return text_result(f"pixabay error: {e}", True)
    return text_result(json.dumps(res, ensure_ascii=False, indent=1))


def do_story(post, scenes, voice, speed):
    with RENDER_LOCK:
        return _do_story(post, scenes, voice, speed)


def _do_story(post, scenes, voice, speed):
    import story
    post, d = post_dir(post)
    with open(os.path.join(d, "scenes.json"), "w") as f:
        json.dump({"voice": voice, "speed": speed, "scenes": scenes}, f, ensure_ascii=False, indent=1)
    work = tempfile.mkdtemp(prefix="story-")
    try:
        futs = []
        for i, sc in enumerate(scenes):
            p = os.path.join(work, f"v{i:02d}.mp3")
            futs.append((p, TTS_POOL.submit(tts, sc["say"], voice, speed, p)))
        voices = [p for p, f in futs if f.result() is not None or True]
        used, clip_files, picked = set(), [], []
        for i, sc in enumerate(scenes):
            files = []
            urls = list(sc.get("clips") or [])
            if not urls and sc.get("q"):
                for h in pixabay_videos(sc["q"], 15):
                    tags = (h.get("tags") or "").lower()
                    bad = any(b in tags for b in ("cartoon", "3d", "animation", "cgi", "green screen", "chroma",
                                                  "anime", "illustration", "space station",
                                                  "anthropomorphic", "temple", "pagoda", "christmas", "xmas"))
                    keys = [k for k in re.split(r"\W+", sc["q"].lower()) if len(k) > 3]
                    if keys and not any(k[:5] in tags for k in keys):
                        bad = True  # tags must mention at least one word of the query
                    if h["url"] and not bad and h["id"] not in used and (h.get("dur") or 0) >= 3:
                        urls.append(h["url"])
                        used.add(h["id"])
                        picked.append({"scene": i, "id": h["id"], "tags": h["tags"]})
                    if len(urls) >= int(sc.get("n", 2)):
                        break
            for j, u in enumerate(urls):
                fp = os.path.join(work, f"c{i:02d}_{j}.mp4")
                with open(fp, "wb") as f:
                    f.write(http_get(u, timeout=180))
                files.append((fp, probe_duration(fp)))
            clip_files.append(files)
        if not any(clip_files):
            raise RuntimeError("no stock clips found")
        out = os.path.join(d, "reel.mp4")
        res = story.render(scenes, voices, clip_files, out, work)
        prev_dir = os.path.join(d, "_preview")
        os.makedirs(prev_dir, exist_ok=True)
        previews = []
        for k, pth in enumerate(res["previews"]):
            dst = os.path.join(prev_dir, f"frame{k}.jpg")
            shutil.copy(pth, dst)
            previews.append(dst)
        return {"url": public_url(post, "reel.mp4"), "seconds": res["seconds"], "shots": res["shots"],
                "clips": picked, "previews": previews}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def do_remix(post, music_url, vol, src_name, out_name, mute=None, sfx=None):
    """Lay a music track (e.g. Suno via kie) under an already built reel, ducking it under the voice."""
    post, d = post_dir(post)
    src = os.path.join(d, src_name)
    if not os.path.isfile(src):
        raise RuntimeError(f"нет {src_name} в {post}")
    work = tempfile.mkdtemp(prefix="remix-")
    try:
        mp = os.path.join(work, "music.mp3")
        with open(mp, "wb") as f:
            f.write(http_get(music_url, timeout=180))
        dur = probe_duration(src)
        vf = "".join(f",volume=0:enable='between(t,{float(a):.3f},{float(b):.3f})'" for a, b in (mute or []))
        sfx_in, sfx_fc, sfx_lbl = [], "", ""
        for j, e in enumerate(sfx or []):
            sp = os.path.join(work, f"sfx{j:02d}.wav")
            _sfx(e["kind"], sp, e.get("dur"))
            sfx_in += ["-i", sp]
            ms = int(float(e["t"]) * 1000)
            sfx_fc += (f"[{j + 2}:a]aresample=44100,aformat=channel_layouts=stereo,"
                       f"volume={float(e.get('vol', 1.0))},adelay={ms}|{ms}[x{j}];")
            sfx_lbl += f"[x{j}]"
        n = len(sfx or [])
        fc = (f"[0:a]anull{vf}[v0];" + sfx_fc +
              (f"[v0]{sfx_lbl}amix=inputs={n + 1}:normalize=0:duration=first[v1];" if n else "[v0]anull[v1];") +
              f"[v1]asplit=2[v][sc];"
              f"[1:a]aresample=44100,aformat=channel_layouts=stereo,volume={vol},"
              f"afade=t=in:d=0.8,afade=t=out:st={max(0, dur - 2):.2f}:d=2[m];"
              f"[m][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=350[md];"
              f"[v][md]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[aout]")
        out = os.path.join(d, out_name)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-stream_loop", "-1", "-i", mp, *sfx_in,
                        "-filter_complex", fc, "-map", "0:v", "-map", "[aout]", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "192k", "-t", f"{dur:.3f}", "-movflags", "+faststart", out],
                       check=True, capture_output=True)
        return {"url": public_url(post, out_name), "seconds": round(dur, 1)}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def do_mux(post, video_url, voice_name, out_name):
    """Silent video (any aspect) + voice file from the post folder -> out_name, audio padded/cut to video length."""
    post, d = post_dir(post)
    work = tempfile.mkdtemp(prefix="mux-")
    try:
        vp = os.path.join(work, "v.mp4")
        with open(vp, "wb") as f:
            f.write(http_get(video_url, timeout=300))
        dur = probe_duration(vp)
        out = os.path.join(d, out_name)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vp, "-i", os.path.join(d, voice_name),
                        "-filter_complex", f"[1:a]apad,atrim=0:{dur:.3f}[a]", "-map", "0:v", "-map", "[a]",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out],
                       check=True, capture_output=True)
        return {"url": public_url(post, out_name), "seconds": round(dur, 2)}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def do_batch_reels(spec_url):
    """[{post, video, voice, end, music, vol, sfx}] -> compose (video + voice) then remix (music + sfx), one by one."""
    items = json.loads(http_get(spec_url, timeout=60).decode())
    out = []
    for it in items:
        try:
            do_compose(it["post"], {"music": it["voice"], "start": 0, "end": float(it["end"]), "pop": False,
                                    "parts": [{"t0": 0, "t1": float(it["end"]), "video": it["video"]}]})
            r = do_remix(it["post"], it["music"], float(it.get("vol", 0.22)), "reel.mp4", "reel_music.mp4",
                         None, it.get("sfx"))
            out.append({"post": it["post"], "url": r["url"], "seconds": r["seconds"]})
        except Exception as e:  # noqa: BLE001
            out.append({"post": it.get("post"), "error": str(e)[:200]})
    return out


def do_audio_batch(spec_url):
    """[{post, pieces, voice, speed, out}] -> audio_build for each; returns compact timelines (say pieces only)."""
    items = json.loads(http_get(spec_url, timeout=60).decode())
    out = []
    for it in items:
        for attempt in range(3):
            try:
                r = do_audio_build(it["post"], it["pieces"], it.get("voice", "g31:Gacrux:Promo/Hype:loud"),
                                   float(it.get("speed", 1.15)), it.get("out", "voice.mp3"))
                out.append({"post": it["post"], "seconds": r["seconds"],
                            "say": [[x["start"], x["end"]] for x in r["timeline"] if x["kind"] == "say"]})
                break
            except Exception as e:  # noqa: BLE001
                if attempt == 2:
                    out.append({"post": it["post"], "error": str(e)[:200]})
    return out


def _sfx(kind, path, dur=None):
    """Synthesised sound effects: slam (palm hits a table), riffle (card shuffle), shuffle (long riffle,
    dur), shake (8-ball rattle, dur), whoosh."""
    if kind == "shuffle":
        d = float(dur or 3.0)
        fc = (f"anoisesrc=d={d:.2f}:c=white:a=0.4,highpass=f=1700,lowpass=f=7500,"
              "volume='(0.3+0.7*abs(sin(2*PI*30*t)))*(0.2+0.8*pow(abs(sin(2*PI*1.6*t)),2))':eval=frame,"
              f"afade=t=in:d=0.05,afade=t=out:st={max(0, d - 0.25):.2f}:d=0.25")
    elif kind == "shake":
        d = float(dur or 2.0)
        fc = (f"anoisesrc=d={d:.2f}:c=pink:a=0.8,bandpass=f=1400:w=1800,"
              "volume='0.15+1.6*pow(abs(sin(2*PI*3.2*t)),8)':eval=frame,"
              f"afade=t=in:d=0.05,afade=t=out:st={max(0, d - 0.2):.2f}:d=0.2")
    elif kind == "click":
        fc = ("anoisesrc=d=0.04:c=white:a=0.9,highpass=f=2500,afade=t=out:st=0:d=0.04[a];"
              "sine=f=1800:d=0.03,volume=0.5,afade=t=out:st=0:d=0.03[b];[a][b]amix=inputs=2:normalize=0")
    elif kind == "type":
        d = float(dur or 1.5)
        fc = (f"anoisesrc=d={d:.2f}:c=white:a=0.6,highpass=f=2200,lowpass=f=8000,"
              "volume='pow(abs(sin(2*PI*7*t+sin(2*PI*1.3*t)*2)),24)*2.2':eval=frame,"
              f"afade=t=out:st={max(0, d - 0.1):.2f}:d=0.1")
    elif kind == "pop":
        fc = "sine=f=900:d=0.12,volume='1.2*exp(-30*t)':eval=frame,asetrate=44100*1.0,afade=t=out:st=0.05:d=0.07"
    elif kind == "ding":
        fc = ("sine=f=1320:d=0.7,volume='0.8*exp(-5*t)':eval=frame[a];sine=f=1980:d=0.7,volume='0.4*exp(-6*t)':eval=frame[b];"
              "[a][b]amix=inputs=2:normalize=0")
    elif kind == "slam":
        fc = ("sine=f=55:d=0.45,volume=1.6,afade=t=out:st=0.02:d=0.42[a];"
              "anoisesrc=d=0.25:c=brown:a=0.9,lowpass=f=900,afade=t=out:st=0.01:d=0.22,volume=1.4[b];"
              "anoisesrc=d=0.08:c=white:a=0.5,highpass=f=1500,afade=t=out:st=0.0:d=0.08[c];"
              "[a][b][c]amix=inputs=3:normalize=0,alimiter=limit=0.97")
    elif kind == "riffle":
        fc = ("anoisesrc=d=0.9:c=white:a=0.35,highpass=f=1800,lowpass=f=7000,"
              "volume='0.4+0.6*abs(sin(2*PI*28*t))':eval=frame,afade=t=in:d=0.05,afade=t=out:st=0.7:d=0.2")
    else:
        fc = "anoisesrc=d=0.45:c=pink:a=0.6,highpass=f=400,lowpass=f=5000,afade=t=in:d=0.18,afade=t=out:st=0.2:d=0.25"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-filter_complex", fc, "-ar", "44100", "-ac", "1", path],
                   check=True, capture_output=True)


def do_audio_build(post, pieces, voice, speed, out_name):
    """Build one voice track from pieces: {"say": text} (TTS), {"silence": sec}, {"sfx": "slam"|"riffle"|"whoosh"}.
    Returns the track url and a timeline of every piece (start/end in seconds)."""
    post, d = post_dir(post)
    work = tempfile.mkdtemp(prefix="ab-")
    try:
        files, timeline, t = [], [], 0.0
        for k, pc in enumerate(pieces):
            raw = os.path.join(work, f"p{k:02d}_raw.mp3")
            if pc.get("say"):
                tts(pc["say"], pc.get("voice", voice), float(pc.get("speed", speed)), raw)
            elif pc.get("sfx"):
                _sfx(pc["sfx"], raw, pc.get("dur"))
            elif pc.get("file"):  # cut [from, to] out of an existing track (to splice a re-voiced line)
                srcf = os.path.join(work, "src_" + hashlib.md5(pc["file"].encode()).hexdigest()[:8] + ".mp3")
                if not os.path.isfile(srcf):
                    with open(srcf, "wb") as f:
                        f.write(http_get(pc["file"], timeout=180))
                a0, a1 = float(pc.get("from", 0)), float(pc["to"])
                subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{a0:.3f}", "-t", f"{a1 - a0:.3f}", "-i", srcf,
                                "-c:a", "libmp3lame", "-b:a", "256k", raw], check=True, capture_output=True)
            else:
                subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                                f"anullsrc=r=44100:cl=mono", "-t", f"{float(pc.get('silence', 0.3)):.3f}", raw],
                               check=True, capture_output=True)
            wav = os.path.join(work, f"p{k:02d}.wav")
            vol = float(pc.get("vol", 1.0))
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af", f"volume={vol}", "-ar", "44100", "-ac", "1",
                            wav], check=True, capture_output=True)
            dur = probe_duration(wav)
            files.append(wav)
            timeline.append({"k": k, "kind": "say" if pc.get("say") else ("sfx" if pc.get("sfx") else ("file" if pc.get("file") else "silence")),
                             "start": round(t, 3), "end": round(t + dur, 3), "text": pc.get("say", pc.get("sfx", ""))})
            t += dur
        lst = os.path.join(work, "l.txt")
        with open(lst, "w") as f:
            for w in files:
                f.write(f"file '{w}'\n")
        out = os.path.join(d, out_name)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst,
                        "-af", "loudnorm=I=-14:TP=-1:LRA=9", "-ar", "44100", "-ac", "2", "-b:a", "192k", out],
                       check=True, capture_output=True)
        return {"url": public_url(post, out_name), "seconds": round(t, 2), "timeline": timeline}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def do_frames(post, url, times):
    """Grab still frames of any video at given seconds (to look at a clip without downloading it)."""
    post, d = post_dir(post)
    work = tempfile.mkdtemp(prefix="fr-")
    try:
        src = os.path.join(work, "v.mp4")
        with open(src, "wb") as f:
            f.write(http_get(url, timeout=300))
        prev_dir = os.path.join(d, "_frames")
        os.makedirs(prev_dir, exist_ok=True)
        out = []
        for t in times:
            fp = os.path.join(prev_dir, f"f_{float(t):06.2f}.jpg")
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{float(t):.3f}", "-i", src, "-frames:v", "1",
                            "-vf", "scale=360:-2", fp], check=True, capture_output=True)
            out.append(fp)
        return {"seconds": round(probe_duration(src), 2), "times": times, "previews": out}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def do_crop(post, src_name, out_name, box, fade):
    """Re-frame a finished reel: crop box [x,y,w,h] in fractions of the frame, scale back to 1080x1920
    (used to cut away artefacts such as fake captions a video model drew near the bottom)."""
    post, d = post_dir(post)
    src = os.path.join(d, src_name)
    x, y, w, h = [float(v) for v in box]
    vf = (f"crop=iw*{w}:ih*{h}:iw*{x}:ih*{y},scale=1080:1920:flags=lanczos,setsar=1")
    dur = probe_duration(src)
    if fade:
        vf += f",fade=t=out:st={max(0, dur - 1.2):.2f}:d=1.2"
    out = os.path.join(d, out_name)
    tmp = out + ".tmp.mp4"
    with RENDER_LOCK:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-vf", vf, "-c:v", "libx264", "-preset", "medium",
                        "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", tmp],
                       check=True, capture_output=True)
    os.replace(tmp, out)
    return {"url": public_url(post, out_name), "seconds": round(dur, 1)}


def do_brand_cover(post, bg_url, ov_url, out_name, reel_src, reel_out):
    """Composite a transparent headline PNG over a background (1080x1920 cover). Optionally burn the
    cover into the FIRST FRAME of a reel (1 frame, no shift of audio) so Instagram uses it as thumbnail."""
    post, d = post_dir(post)
    work = tempfile.mkdtemp(prefix="bcov-")
    try:
        bg = os.path.join(work, "bg.png")
        with open(bg, "wb") as f:
            f.write(http_get(bg_url, timeout=120))
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", bg]
        fc = "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[b]"
        if ov_url:
            ov = os.path.join(work, "ov.png")
            with open(ov, "wb") as f:
                f.write(http_get(ov_url, timeout=120))
            cmd += ["-i", ov]
            fc += ";[1:v]scale=1080:1920[o];[b][o]overlay=0:0[c]"
        else:
            fc += ";[b]null[c]"
        out = os.path.join(d, out_name)
        subprocess.run(cmd + ["-filter_complex", fc, "-map", "[c]", "-frames:v", "1", out],
                       check=True, capture_output=True)
        res = {"url": public_url(post, out_name), "file": out}
        if reel_src:
            src = os.path.join(d, reel_src)
            dst = os.path.join(d, reel_out)
            tmp = dst + ".tmp.mp4"
            with RENDER_LOCK:
                subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-i", out, "-filter_complex",
                                "[1:v]scale=1080:1920,format=yuv420p[c];[0:v][c]overlay=0:0:enable='eq(n,0)'[v]",
                                "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                                "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", tmp],
                               check=True, capture_output=True)
            os.replace(tmp, dst)
            res["reel"] = public_url(post, reel_out)
        return res
    finally:
        shutil.rmtree(work, ignore_errors=True)


def do_mv(post, spec):
    with RENDER_LOCK:
        import story
        post, d = post_dir(post)
        with open(os.path.join(d, "mv.json"), "w") as f:
            json.dump(spec, f, ensure_ascii=False, indent=1)
        work = tempfile.mkdtemp(prefix="mv-")
        try:
            song = os.path.join(work, "song.mp3")
            with open(song, "wb") as f:
                f.write(http_get(spec["music"], timeout=180))
            clips = []
            for j, u in enumerate(spec["clips"]):
                fp = os.path.join(work, f"c{j:02d}.mp4")
                with open(fp, "wb") as f:
                    f.write(http_get(u, timeout=180))
                clips.append((fp, probe_duration(fp)))
            out = os.path.join(d, "reel.mp4")
            bpm, offset = spec.get("bpm", "auto"), spec.get("offset")
            if bpm == "auto":
                bpm, ph = story.detect_beat(song)
                offset = ph if offset is None else offset
            step = 60.0 / float(bpm) * int(spec.get("beats", 4))
            offset = float(offset or 0)
            while offset > step:
                offset -= step
            res = story.render_mv(song, clips, out, work, float(bpm), int(spec.get("beats", 4)),
                                  offset, float(spec.get("max_len", 60)),
                                  [tuple(x) for x in spec.get("texts", [])], bool(spec.get("shuffle", True)))
            prev_dir = os.path.join(d, "_preview")
            os.makedirs(prev_dir, exist_ok=True)
            previews = []
            for k, pth in enumerate(res["previews"]):
                dst = os.path.join(prev_dir, f"frame{k}.jpg")
                shutil.copy(pth, dst)
                previews.append(dst)
            return {"url": public_url(post, "reel.mp4"), "seconds": res["seconds"], "shots": res["shots"],
                    "bpm": bpm, "offset": round(offset, 3), "previews": previews}
        finally:
            shutil.rmtree(work, ignore_errors=True)


def do_talk(post, spec):
    """Lip-sync a portrait to a song segment with InfiniteTalk (<=15 s per task), then assemble the reel."""
    import math
    import story
    from concurrent.futures import ThreadPoolExecutor as TPE
    post, d = post_dir(post)
    with open(os.path.join(d, "talk.json"), "w") as f:
        json.dump(spec, f, ensure_ascii=False, indent=1)
    work = tempfile.mkdtemp(prefix="talk-")
    try:
        song = os.path.join(work, "song.mp3")
        with open(song, "wb") as f:
            f.write(http_get(spec["music"], timeout=180))
        start = float(spec.get("start", 0))
        end = min(float(spec.get("end", 60)), probe_duration(song))
        total = end - start
        n = max(1, math.ceil(total / float(spec.get("chunk", 14.5))))
        step = total / n
        seg = os.path.join(d, "talk_song.m4a")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{start:.3f}", "-t", f"{total:.3f}", "-i", song,
                        "-c:a", "aac", "-b:a", "192k", seg], check=True)
        if spec.get("loop"):  # no lip-sync: a seamless idle clip looped under the song
            lp = os.path.join(work, "loop_src.mp4")
            with open(lp, "wb") as f:
                f.write(http_get(spec["loop"], timeout=300))
            looped = os.path.join(work, "loop_full.mp4")
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-stream_loop", "-1", "-i", lp, "-t", f"{total:.3f}",
                            "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", looped], check=True)
            with RENDER_LOCK:
                out = os.path.join(d, "reel.mp4")
                res = story.render_talk([looped], [total], seg, out, work, [tuple(x) for x in spec.get("texts", [])])
            prev_dir = os.path.join(d, "_preview")
            os.makedirs(prev_dir, exist_ok=True)
            previews = []
            for k, pth in enumerate(res["previews"]):
                dst = os.path.join(prev_dir, f"frame{k}.jpg")
                shutil.copy(pth, dst)
                previews.append(dst)
            return {"url": public_url(post, "reel.mp4"), "seconds": res["seconds"], "credits": 0, "previews": previews}
        urls, durs = [], []
        for k in range(n):
            name = f"talk_a{k:02d}.mp3"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{start + k * step:.3f}", "-t", f"{step:.3f}",
                            "-i", song, "-c:a", "libmp3lame", "-b:a", "192k", os.path.join(d, name)], check=True)
            urls.append(public_url(post, name))
            durs.append(step)
        prompt = spec.get("prompt") or ("A beautiful young woman sings a tender song with real emotion, natural "
                                        "lip movement, gentle head motion and blinking, warm cozy room, static camera")

        def one(k):
            res_urls, info = kie_task("infinitalk/from-audio", {"image_url": spec["image"], "audio_url": urls[k],
                                                                "prompt": prompt,
                                                                "resolution": spec.get("resolution", "480p")},
                                      max_wait=1500)
            vp = os.path.join(work, f"lip{k:02d}.mp4")
            with open(vp, "wb") as f:
                f.write(http_get(res_urls[0], timeout=300))
            shutil.copy(vp, os.path.join(d, f"talk_v{k:02d}.mp4"))
            return vp, info.get("credits")

        with TPE(max_workers=3) as ex:
            results = list(ex.map(one, range(n)))
        vids = [r[0] for r in results]
        credits = sum(float(r[1] or 0) for r in results)
        with RENDER_LOCK:
            out = os.path.join(d, "reel.mp4")
            res = story.render_talk(vids, durs, seg, out, work, [tuple(x) for x in spec.get("texts", [])])
        prev_dir = os.path.join(d, "_preview")
        os.makedirs(prev_dir, exist_ok=True)
        previews = []
        for k, pth in enumerate(res["previews"]):
            dst = os.path.join(prev_dir, f"frame{k}.jpg")
            shutil.copy(pth, dst)
            previews.append(dst)
        return {"url": public_url(post, "reel.mp4"), "seconds": res["seconds"], "chunks": n,
                "credits": credits, "previews": previews}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def do_compose(post, spec):
    """parts: [{t0,t1,video}|{t0,t1,clips,beats}|{t0,t1,lipsync:model,image,prompt}] over song [start,end]."""
    import story
    from concurrent.futures import ThreadPoolExecutor as TPE
    post, d = post_dir(post)
    with open(os.path.join(d, "compose.json"), "w") as f:
        json.dump(spec, f, ensure_ascii=False, indent=1)
    work = tempfile.mkdtemp(prefix="comp-")
    try:
        song = os.path.join(work, "song.mp3")
        with open(song, "wb") as f:
            f.write(http_get(spec["music"], timeout=180))
        start, end = float(spec.get("start", 0)), float(spec["end"])
        seg = os.path.join(work, "seg.m4a")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{start:.3f}", "-t", f"{end - start:.3f}", "-i", song,
                        "-c:a", "aac", "-b:a", "192k", seg], check=True)
        bpm, phase = story.detect_beat(song)
        parts = spec["parts"]
        credits = [0.0]

        def lip(k, p):
            name = f"comp_a{k:02d}.mp3"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{p['t0']:.3f}", "-t", f"{p['t1'] - p['t0']:.3f}",
                            "-i", song, "-c:a", "libmp3lame", "-b:a", "192k", os.path.join(d, name)], check=True)
            inp = {"image_url": p["image"], "audio_url": public_url(post, name),
                   "prompt": p.get("prompt") or "A beautiful young woman sings with real emotion, natural lip "
                                                 "movement, gentle head motion, static camera"}
            if p["lipsync"].startswith("infinitalk"):
                inp["resolution"] = p.get("resolution", "480p")
            urls, info = kie_task(p["lipsync"], inp, max_wait=int(p.get("max_wait", 5400)))
            vp = os.path.join(d, f"comp_v{k:02d}.mp4")
            with open(vp, "wb") as f:
                f.write(http_get(urls[0], timeout=300))
            credits[0] += float(info.get("credits") or 0)
            return vp

        def fetch(url, name):
            fp = os.path.join(work, name)
            with open(fp, "wb") as f:
                f.write(http_get(url, timeout=300))
            return fp

        lips = {k: p for k, p in enumerate(parts) if p.get("lipsync")}
        with TPE(max_workers=3) as ex:
            futs = {k: ex.submit(lip, k, p) for k, p in lips.items()}
            lip_files = {k: f.result() for k, f in futs.items()}
        with RENDER_LOCK:
            seq = []  # (path, offset, dur, push)
            for k, p in enumerate(parts):
                t0, t1 = float(p["t0"]), float(p["t1"])
                if k in lip_files:
                    seq.append((lip_files[k], 0.0, t1 - t0, False))
                elif p.get("video"):
                    seq.append((fetch(p["video"], f"v{k:02d}.mp4"), float(p.get("offset", 0)), t1 - t0, False))
                elif p.get("still"):  # still image shown for t1-t0 (optional slow push)
                    ext = p["still"].rsplit(".", 1)[-1].split("?")[0].lower()
                    ext = ext if ext in ("png", "jpg", "jpeg", "webp") else "png"
                    seq.append((fetch(p["still"], f"s{k:02d}.{ext}"), 0.0, t1 - t0, bool(p.get("push", True))))
                else:
                    clips = [fetch(u, f"c{k:02d}_{j:02d}.mp4") for j, u in enumerate(p["clips"])]
                    step = 60.0 / bpm * int(p.get("beats", 4))
                    b = phase
                    while b < t0 + 0.6:
                        b += step
                    bounds = [t0]
                    while b < t1 - 0.6:
                        bounds.append(b)
                        b += step
                    bounds.append(t1)
                    for j in range(len(bounds) - 1):
                        c = clips[j % len(clips)]
                        cd = probe_duration(c)
                        dur = bounds[j + 1] - bounds[j]
                        off = max(0.0, min(cd - dur - 0.2, (cd - dur) / 2))
                        seq.append((c, off, dur, j % 2 == 0))
            res = story.render_compose(seq, seg, os.path.join(d, "reel.mp4"), work,
                                       [tuple(x) for x in spec.get("texts", [])],
                                       pop_anim=bool(spec.get("pop", True)))
        prev_dir = os.path.join(d, "_preview")
        os.makedirs(prev_dir, exist_ok=True)
        previews = []
        for k, pth in enumerate(res["previews"]):
            dst = os.path.join(prev_dir, f"frame{k}.jpg")
            shutil.copy(pth, dst)
            previews.append(dst)
        return {"url": public_url(post, "reel.mp4"), "seconds": res["seconds"], "bpm": bpm,
                "credits": credits[0], "shots": len(seq), "previews": previews}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def do_transcribe(post, url, lang="ru", model="small"):
    """Word-level speech recognition with faster-whisper (installed on first use into a private dir)."""
    import sys as _sys
    lib = "/opt/carousel/pylib"
    if lib not in _sys.path:
        _sys.path.insert(0, lib)
    try:
        import faster_whisper  # noqa
    except ImportError:
        os.makedirs(lib, exist_ok=True)
        r = subprocess.run([_sys.executable, "-m", "pip", "install", "--break-system-packages", "-q",
                            "--target", lib, "faster-whisper"], capture_output=True, text=True, timeout=1800)
        if r.returncode != 0:
            raise RuntimeError("pip failed: " + r.stderr[-800:])
        import importlib
        importlib.invalidate_caches()
    from faster_whisper import WhisperModel
    post, d = post_dir(post)
    src = os.path.join(d, "stt_src" + os.path.splitext(url.split("?")[0])[1][:5])
    with open(src, "wb") as f:
        f.write(http_get(url, timeout=300))
    m = WhisperModel(model, device="cpu", compute_type="int8", cpu_threads=2)
    import numpy as _np
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True, check=True).stdout
    audio = _np.frombuffer(pcm, _np.int16).astype(_np.float32) / 32768.0
    segs, info = m.transcribe(audio, language=lang, word_timestamps=True, vad_filter=False, beam_size=5)
    words = []
    for sg in segs:
        for w in (sg.words or []):
            words.append([round(w.start, 3), round(w.end, 3), w.word.strip()])
    with open(os.path.join(d, "words.json"), "w") as f:
        json.dump(words, f, ensure_ascii=False)
    return {"url": public_url(post, "words.json"), "n": len(words), "words": words}


def tool_story(a):
    if isinstance(a.get("scenes"), str):
        a["scenes"] = json.loads(a["scenes"])
    first = (a.get("scenes") or [{}])[0]
    if first.get("mv"):  # music video: [{"mv":true,"music":url,"clips":[...],"bpm":128,"beats":4,"texts":[[t0,t1,text,style]]}]
        jid = start_job("reel", do_mv, a["post"], first)
        return text_result(f"job_id: {jid} — клип ~3–5 мин")
    if first.get("compose"):  # clip from parts: video / beat-cut b-roll / lip-sync, under one song
        jid = start_job("reel", do_compose, a["post"], first)
        return text_result(f"job_id: {jid} — клип из частей ~10–25 мин")
    if first.get("talk"):  # singing head: [{"talk":true,"music":url,"image":url,"start":0,"end":64,"prompt":"...","texts":[...]}]
        jid = start_job("reel", do_talk, a["post"], first)
        return text_result(f"job_id: {jid} — поющая голова ~5–15 мин")
    if first.get("transcribe"):  # scenes=[{"transcribe": audio_url, "lang": "ru", "model": "small"}]
        jid = start_job("stt", do_transcribe, a["post"], first["transcribe"], first.get("lang", "ru"),
                        first.get("model", "small"))
        return text_result(f"job_id: {jid} — распознавание речи ~3–10 мин")
    if first.get("zip"):  # [{"zip": {"dir/name.ext": url, ...}, "out": "kit.zip"}] -> /f/<post>/<out>
        import zipfile
        post, d = post_dir(a["post"])
        out = first.get("out", "kit.zip")
        with zipfile.ZipFile(os.path.join(d, out), "w", zipfile.ZIP_DEFLATED) as z:
            for name, url in first["zip"].items():
                z.writestr(name, http_get(url, timeout=120))
        return text_result(public_url(post, out))
    if first.get("botstatus"):  # [{"botstatus": true, "set": {"lesson_url": ...}}]
        import montage_bot
        if first.get("set"):
            montage_bot.set_cfg(**first["set"])
        if first.get("admin"):
            return text_result(json.dumps(montage_bot.admin(first["admin"], lambda u: http_get(u, timeout=120)),
                                          ensure_ascii=False))
        return text_result(json.dumps(montage_bot.status(), ensure_ascii=False))
    if first.get("botcheck"):  # [{"botcheck": "/opt/montage-bot/.env"}] — is a bot token there and valid? never returns it
        pth = first["botcheck"] if str(first["botcheck"]).startswith("/opt/") else "/opt/montage-bot/.env"
        try:
            tok = ""
            for line in open(pth):
                if line.startswith("BOT_TOKEN="):
                    tok = line.split("=", 1)[1].strip()
            if not tok:
                return text_result("файл есть, но BOT_TOKEN пустой")
            info = json.loads(http_get(f"https://api.telegram.org/bot{tok}/getMe", timeout=20))
            r = info.get("result", {})
            return text_result(f"ok={info.get('ok')} username=@{r.get('username')} name={r.get('first_name')}")
        except FileNotFoundError:
            return text_result("файла с токеном нет")
        except Exception as e:
            return text_result("ошибка проверки: " + type(e).__name__ + " " + str(e).replace(tok if 'tok' in dir() and tok else 'x', '***')[:200])
    if first.get("frames"):  # [{"frames": video_url, "times": [0.5, 1, 1.5]}]
        jid = start_job("frames", do_frames, a["post"], first["frames"], first.get("times", [0.5, 1.5, 3]))
        return text_result(f"job_id: {jid} — кадры ~20 с")
    if first.get("audio_build"):  # [{"audio_build": [pieces], "voice": "g31:Kore:Promo/Hype:lyuba", "speed": 1.05, "out": "voice.mp3"}]
        jid = start_job("voice", do_audio_build, a["post"], first["audio_build"], first.get("voice", "g31:Kore::lyuba"),
                        float(first.get("speed", 1.0)), first.get("out", "voice.mp3"))
        return text_result(f"job_id: {jid} — сборка озвучки ~1–3 мин")
    if first.get("crop"):  # [{"crop": [x,y,w,h], "src_file": "reel.mp4", "out": "reel_crop.mp4", "fade": false}]
        jid = start_job("reel", do_crop, a["post"], first.get("src_file", "reel.mp4"), first.get("out", "reel_crop.mp4"),
                        first["crop"], bool(first.get("fade", False)))
        return text_result(f"job_id: {jid} — кадрирование ~1–2 мин")
    if first.get("brand_cover"):  # [{"brand_cover": bg_url, "overlay": png_url, "out": "cover.png", "reel": "reel.mp4"}]
        jid = start_job("cover", do_brand_cover, a["post"], first["brand_cover"], first.get("overlay"),
                        first.get("out", "cover.png"), first.get("reel"), first.get("reel_out", first.get("reel")))
        return text_result(f"job_id: {jid} — обложка ~10 с (+ первый кадр рилса ~2 мин)")
    if first.get("mux"):  # [{"mux": video_url, "voice": "voice.mp3", "out": "reel.mp4"}]
        jid = start_job("reel", do_mux, a["post"], first["mux"], first.get("voice", "voice.mp3"), first.get("out", "reel.mp4"))
        return text_result(f"job_id: {jid} — склейка ~30 с")
    if first.get("batch_reels"):  # [{"batch_reels": spec_json_url}]
        jid = start_job("reel", do_batch_reels, first["batch_reels"])
        return text_result(f"job_id: {jid} — пакет рилсов ~1–2 мин на ролик")
    if first.get("audio_batch"):  # [{"audio_batch": spec_json_url}]
        jid = start_job("voice", do_audio_batch, first["audio_batch"])
        return text_result(f"job_id: {jid} — пакет озвучки ~1 мин на ролик")
    if first.get("remix"):  # scenes=[{"remix":true,"music":url,"vol":0.25}] — overlay music on existing reel.mp4
        jid = start_job("remix", do_remix, a["post"], first["music"], float(first.get("vol", 0.25)),
                        first.get("src_file", "reel.mp4"), first.get("out", "reel_music.mp4"),
                        first.get("mute"), first.get("sfx"))
        return text_result(f"job_id: {jid} — наложение музыки ~30 с")
    jid = start_job("reel", do_story, a["post"], a["scenes"], a.get("voice", "g31:Gacrux:Promo/Hype:loud"),
                    float(a.get("speed", 1.15)))
    return text_result(f"job_id: {jid} — сборка 3–8 минут")


def tool_status(_):
    du = shutil.disk_usage(FILES_DIR)
    mem = open("/proc/meminfo").read().split("\n")[:3]
    rev = subprocess.run(["git", "-C", REPO_DIR, "rev-parse", "--short", "HEAD"],
                         capture_output=True, text=True).stdout.strip()
    with JOBS_LOCK:
        running = [j["id"] + ":" + j["kind"] for j in JOBS.values() if j["state"] == "running"]
    return text_result(json.dumps({
        "version": VERSION, "repo": rev, "tts": "elevenlabs-direct" if ELEVEN_KEY else "kie", "eleven_models": eleven_models(), "pixabay": pixabay_check(), "domain": DOMAIN, "kie_key": bool(KIE_KEY),
        "disk_free_gb": round(du.free / 1e9, 1), "mem": mem, "running_jobs": running},
        ensure_ascii=False, indent=1))


def tool_update(_):
    out = subprocess.run(["git", "-C", REPO_DIR, "pull", "--ff-only"], capture_output=True, text=True)
    subprocess.Popen(["systemd-run", "--on-active=3", "/bin/systemctl", "restart", "carousel-mcp"])
    return text_result(f"git pull:\n{out.stdout}{out.stderr}\nСервис перезапустится через 3 секунды.")


def tool_logs(a):
    n = int(a.get("lines", 80))
    out = subprocess.run(["journalctl", "-u", "carousel-mcp", "-n", str(min(n, 400)), "--no-pager"],
                         capture_output=True, text=True)
    return text_result(out.stdout[-15000:] or out.stderr)


def tool_cover(a):
    jid = start_job("cover", do_cover, a["post"], a["prompt"], a.get("refs") or [],
                    a.get("aspect_ratio", "3:4"), a.get("resolution", "2K"), a.get("out", "01.png"))
    return text_result(f"job_id: {jid} — проверь через job через ~1 минуту")


def tool_voice_samples(a):
    jid = start_job("voice", do_voice_samples, a["text"], a["voices"], float(a.get("speed", 1.0)))
    return text_result(f"job_id: {jid}")


def tool_reel(a):
    if a.get("stock_q"):  # stock search mode
        return tool_stock({"q": a["stock_q"], "n": a.get("n", 8)})
    if a.get("scenes"):  # story mode (new tools may be hidden by the client's tool cache)
        return tool_story(a)
    base = a.get("slides_base") or f"{RAW_BASE}/posts/{a['post']}"
    jid = start_job("reel", do_reel, a["post"], a["lines"], a.get("voice", "g31:Gacrux:Promo/Hype"),
                    float(a.get("speed", 1.25)), float(a.get("gap", 0.2)), base, a.get("layout", "fit"))
    return text_result(f"job_id: {jid} — сборка занимает 2–5 минут")


def tool_job(a):
    with JOBS_LOCK:
        j = dict(JOBS.get(a["job_id"]) or {})
    if not j:
        return text_result("нет такой задачи (сервер мог перезапуститься)", True)
    content = []
    res = j.get("result") or {}
    if j["state"] == "done":
        if j["kind"] == "cover" and isinstance(res, dict) and res.get("file"):
            content.append({"type": "image", "mimeType": "image/jpeg", "data": preview_jpeg(res["file"])})
        if j["kind"] in ("reel", "frames") and isinstance(res, dict):
            for p in res.get("previews", []):
                content.append({"type": "image", "mimeType": "image/jpeg", "data": preview_jpeg(p, 600)})
    info = {k: v for k, v in j.items() if k != "result"}
    info["result"] = {k: v for k, v in res.items() if k not in ("previews", "file")} if isinstance(res, dict) else res
    content.insert(0, {"type": "text", "text": json.dumps(info, ensure_ascii=False, indent=1)})
    return {"content": content, "isError": j["state"] == "error"}


def tool_files(a):
    if "/" in a["post"]:  # "post/file.png" -> show the image (client schemas may be cached, so no extra param)
        pst, name = a["post"].split("/", 1)
        _, d = post_dir(pst)
        fp = os.path.join(d, os.path.basename(name))
        if not os.path.isfile(fp):
            return text_result("нет файла", True)
        return {"content": [{"type": "image", "mimeType": "image/jpeg", "data": preview_jpeg(fp, 700)}]}
    post, d = post_dir(a["post"])
    names = sorted(n for n in os.listdir(d) if not n.startswith("_"))
    return text_result("\n".join(public_url(post, n) for n in names) or "пусто")


def tool_put_file(a):
    """Download a file from a URL into the post folder (e.g. a slide or cover)."""
    post, d = post_dir(a["post"])
    name = os.path.basename(a["name"])
    with open(os.path.join(d, name), "wb") as f:
        f.write(http_get(a["url"]))
    return text_result(public_url(post, name))


def do_kie_raw(model, inp):
    urls, info = kie_task(model, inp, max_wait=600)
    return {"urls": urls, "info": info}


def tool_kie_raw(a):
    jid = start_job("raw", do_kie_raw, a["model"], a.get("input") or {})
    return text_result(f"job_id: {jid}")


def text_result(t, err=False):
    return {"content": [{"type": "text", "text": t}], "isError": err}


S = lambda **p: {"type": "object", "properties": p, "required": [k for k, v in p.items() if v.pop("_req", False)]}  # noqa: E731

TOOLS = {
    "status": (tool_status, "Состояние сервера: диск, память, версия, задачи.", S()),
    "update": (tool_update, "Обновить код сервера из GitHub (git pull) и перезапустить службу.", S()),
    "logs": (tool_logs, "Последние строки журнала службы.", S(lines={"type": "integer"})),
    "cover": (tool_cover, "Сгенерировать картинку в kie.ai (Nano Banana Pro). Возвращает job_id; результат — через job.",
              S(post={"type": "string", "_req": True}, prompt={"type": "string", "_req": True},
                refs={"type": "array", "items": {"type": "string"}, "description": "URL референсов"},
                aspect_ratio={"type": "string"}, resolution={"type": "string"},
                out={"type": "string", "description": "имя файла, по умолчанию 01.png"})),
    "voice_samples": (tool_voice_samples, "Пробная озвучка одной фразы несколькими голосами ElevenLabs (через kie.ai).",
                      S(text={"type": "string", "_req": True},
                        voices={"type": "array", "items": {"type": "string"}, "_req": True},
                        speed={"type": "number"})),
    "reel": (tool_reel, "Собрать рилс 9:16: слайды + озвучка + субтитры. lines = [{slide:'01'..'10' или имя файла без .png, say:'текст озвучки', sub?:'текст субтитров', nosub?:true, layout?:'fit'|'full'}]. layout fit — слайд с полями, субтитры под ним; full — слайд на всю ширину, субтитры поверх. Картинка 9:16 (обложка) — на весь экран. speed по умолчанию 1.25. Слайды берутся из папки поста на сервере, иначе из GitHub (posts/<post>/NN.png).",
             S(post={"type": "string", "_req": True},
               lines={"type": "array", "_req": True, "items": {"type": "object", "properties": {
                   "slide": {"type": "string"}, "say": {"type": "string"}, "sub": {"type": "string"},
                   "nosub": {"type": "boolean"}, "layout": {"type": "string"}},
                   "required": ["slide", "say"]}},
               voice={"type": "string"}, speed={"type": "number"}, gap={"type": "number"},
               slides_base={"type": "string"}, layout={"type": "string"})),
    "kie_raw": (tool_kie_raw, "Отладка: произвольная задача kie.ai (model + input), результат через job.",
                S(model={"type": "string", "_req": True}, input={"type": "object", "_req": True})),
    "job": (tool_job, "Статус фоновой задачи и результат (с превью картинок).", S(job_id={"type": "string", "_req": True})),
    "files": (tool_files, "Публичные ссылки на файлы поста.", S(post={"type": "string", "_req": True})),
    "story": (tool_story, "Сюжетный рилс без лица: стоковые видео Pixabay + эмоциональная озвучка + монтаж кодом "
                          "(смена кадра ~2.6 с, наезды, субтитры с подсветкой слова, счётчик цифр, звуки, полоса прогресса). "
                          "scenes = [{say, sub?, q (англ. запрос в сток) | clips:[url], title?, big?, count?, suffix?, hit?, n?}]",
              S(post={"type": "string", "_req": True},
                scenes={"type": "array", "_req": True, "items": {"type": "object"}},
                voice={"type": "string"}, speed={"type": "number"})),
    "stock": (tool_stock, "Поиск стоковых видео Pixabay (q на английском). Возвращает ссылки, размеры, длительность, теги.",
              S(q={"type": "string", "_req": True}, n={"type": "integer"})),
    "put_file": (tool_put_file, "Скачать файл по URL в папку поста (чтобы отдать его по ссылке сервера).",
                 S(post={"type": "string", "_req": True}, url={"type": "string", "_req": True},
                   name={"type": "string", "_req": True})),
}


# ---------------------------------------------------------------- MCP over HTTP

def handle_rpc(msg):
    method, mid, params = msg.get("method"), msg.get("id"), msg.get("params") or {}
    if mid is None:  # notification
        return None
    if method == "initialize":
        result = {"protocolVersion": params.get("protocolVersion", "2025-03-26"),
                  "capabilities": {"tools": {"listChanged": False}},
                  "serverInfo": {"name": "carousel-media", "version": VERSION}}
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": [{"name": n, "description": t[1], "inputSchema": t[2]} for n, t in TOOLS.items()]}
    elif method == "tools/call":
        name = params.get("name")
        if name not in TOOLS:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": f"unknown tool {name}"}}
        try:
            result = TOOLS[name][0](params.get("arguments") or {})
        except Exception as e:  # noqa: BLE001
            log("tool", name, "failed", traceback.format_exc())
            result = text_result(f"Ошибка: {e}", True)
    else:
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not found: {method}"}}
    return {"jsonrpc": "2.0", "id": mid, "result": result}


class Handler(BaseHTTPRequestHandler):
    def _authorized(self):
        return TOKEN and self.path.rstrip("/").split("?")[0] == f"/mcp/{TOKEN}"

    def do_POST(self):
        if not self._authorized():
            self.send_error(404)
            return
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)) or 0)
        try:
            msg = json.loads(body or b"{}")
        except ValueError:
            self.send_error(400)
            return
        if isinstance(msg, list):
            out = [r for r in (handle_rpc(m) for m in msg) if r]
        else:
            out = handle_rpc(msg)
        if not out:
            self.send_response(202)
            self.end_headers()
            return
        data = json.dumps(out, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
            return
        self.send_response(405)
        self.send_header("Allow", "POST")
        self.end_headers()

    def do_DELETE(self):
        self.send_response(405)
        self.end_headers()

    def log_message(self, fmt, *args):
        log(self.address_string(), fmt % args)


if __name__ == "__main__":
    os.makedirs(FILES_DIR, exist_ok=True)
    log("carousel-media", VERSION, "on port", PORT, "domain", DOMAIN)
    try:
        import montage_bot
        montage_bot.start(log)
    except Exception as e:
        log("bot start failed", type(e).__name__)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
