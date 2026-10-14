"""Generic plan builder for talking-head montage.
SEGS: (src_start, src_end, text, highlight_words, block)
SHOTS: list of (block, spec) — spec: {"mode":"full","z":..,"push":..} or {"mode":"split","card":path}; consecutive
blocks with same name are merged into one shot. FULL blocks may be listed several times; order follows SEGS."""
import json, re

PAD0, PAD1, FPS = 0.08, 0.14, 30
SPLIT_Y, FULL_Y = 1035, 1420


def build(SEGS, SHOTSPEC, src, out, face=(0.47, 0.53), overlays=(), extra_sfx=(), hi_color=None):
    keep, out_t, blocks = [], 0.0, []
    for s, e, text, hi, blk in SEGS:
        s0, e1 = s - PAD0, e + PAD1
        keep.append([round(s0, 3), round(e1, 3)])
        d = round((e1 - s0) * FPS) / FPS
        blocks.append({"t0": out_t, "t1": out_t + d, "speech0": out_t + PAD0, "speech1": out_t + PAD0 + (e - s),
                       "text": text, "hi": hi, "blk": blk})
        out_t += d
    total = out_t
    # shots: merge consecutive same-block segments
    shots = []
    for b in blocks:
        if shots and shots[-1]["blk"] == b["blk"]:
            shots[-1]["t1"] = b["t1"]
        else:
            sp = dict(SHOTSPEC[b["blk"]])
            sp.update({"t0": b["t0"], "t1": b["t1"], "blk": b["blk"]})
            shots.append(sp)
    # allow a spec to split a full shot mid-way: {"cut_at": seconds after shot start, "z2": zoom}
    final = []
    for s in shots:
        if s.get("cut_at"):
            a = dict(s); bb = dict(s)
            m = s["t0"] + s["cut_at"]
            a["t1"] = m; bb["t0"] = m; bb["z"] = s.get("z2", s.get("z", 1.5)); bb["push"] = False
            final += [a, bb]
        else:
            final.append(s)
    shots = final
    for s in shots:
        s["t0"], s["t1"] = round(s["t0"], 3), round(s["t1"], 3)
    shots[-1]["t1"] = round(total, 3)
    subs = []
    for b in blocks:
        words = []
        for w in b["text"].split():
            if w in ("—", "-") and words:
                words[-1] += " —"
            else:
                words.append(w)
        chunks, cur = [], []
        for i, w in enumerate(words):
            cur.append(w)
            last = i == len(words) - 1
            if len(" ".join(cur)) >= 14 or w.endswith((",", ".", "?", "!", "—")):
                # do not end a chunk on a short preposition/conjunction — carry it to the next chunk
                if not last and len(cur) > 1 and len(cur[-1].strip(",.—")) <= 2 and not w.endswith(("—", ",", ".")):
                    nxt = [cur.pop()]
                    chunks.append(cur); cur = nxt
                else:
                    chunks.append(cur); cur = []
        if cur:
            if chunks and len(" ".join(cur)) < 6:
                chunks[-1] += cur
            else:
                chunks.append(cur)
        if not chunks:
            continue
        lens = [len(" ".join(c)) + 2 for c in chunks]
        tot = sum(lens); t = b["speech0"]; span = b["speech1"] - b["speech0"]
        mode = next(s["mode"] for s in shots if s["t0"] <= b["t0"] + 0.01 < s["t1"] + 0.01)
        y = FULL_Y if mode == "full" else SPLIT_Y
        for c, L in zip(chunks, lens):
            dt = span * L / tot
            txt = " ".join(c).upper()
            txt = re.sub(r"[.,;:«»?!]", "", txt).strip()
            txt = re.sub(r"\s*—\s*$", "", txt).strip()
            if len(txt) > 17 and " " in txt:
                ws = txt.split(); best = None
                for k in range(1, len(ws)):
                    a, bb = " ".join(ws[:k]), " ".join(ws[k:])
                    sc = max(len(a), len(bb))
                    if best is None or sc < best[0]:
                        best = (sc, a + " \\N " + bb)
                txt = best[1]
            subs.append([round(t, 3), round(t + dt, 3), txt, [h.lower() for h in b["hi"]], y])
            t += dt
    for i in range(len(subs) - 1):
        if subs[i + 1][0] - subs[i][1] < 0.35:
            subs[i][1] = subs[i + 1][0]
    sfx = [[0.0, "hit"]] + [[max(0, s["t0"] - 0.12), "whoosh"] for s in shots[1:]] + list(extra_sfx)
    plan = {"src": src, "face": list(face), "keep": keep, "shots": shots, "subs": subs, "sub_y": FULL_Y,
            "overlays": list(overlays), "sfx": sfx, "out": out}
    if hi_color:
        plan["hi_color"] = hi_color
    return plan, blocks, total


def bt(blocks, blk, which="t0", first=True):
    xs = [b for b in blocks if b["blk"] == blk]
    return xs[0][which] if first else xs[-1][which]


def rel(blocks, blk, k, add=0.0):
    xs = [b for b in blocks if b["blk"] == blk]
    return round(xs[k]["speech0"] - xs[0]["t0"] + add, 2)


def dur(blocks, blk):
    return round(bt(blocks, blk, "t1", False) - bt(blocks, blk) + 0.4, 2)
