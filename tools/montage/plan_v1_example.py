import json, subprocess, sys
sys.path.insert(0, "/home/claude/montage/engine")

PAD0, PAD1 = 0.08, 0.14
# (src_start, src_end, text, highlight words, block)
SEGS = [
    (16.53, 23.63, "У меня в команде 5 сотрудников, и никому я не плачу зарплату. Это нейросети, и вот кого они заменили.",
     ["5", "сотрудников", "зарплату", "нейросети"], "hook"),
    (26.72, 28.03, "Первый — копирайтер.", ["копирайтер"], "copy"),
    (36.11, 39.33, "Объявления, посты, тексты для сайта — за минуту.", ["минуту"], "copy"),
    (42.12, 43.55, "Раньше я ждал день.", ["день"], "copy"),
    (46.46, 47.38, "Второй — дизайнер.", ["дизайнер"], "design"),
    (56.19, 58.99, "Обложки, баннеры, картинки для рекламы.", [], "design"),
    (63.20, 64.38, "По одному описанию.", ["описанию"], "design"),
    (68.86, 70.11, "Третий — монтажёр.", ["монтажёр"], "edit"),
    (74.26, 76.57, "Кстати, этот ролик смонтировал не человек.", ["не", "человек"], "meta"),
    (80.67, 82.06, "Четвёртый — аналитик.", ["аналитик"], "anal"),
    (87.83, 92.56, "Загружаю отчёт по рекламе, а он показывает, где сливается бюджет.", ["сливается", "бюджет"], "anal"),
    (97.08, 98.20, "Пятый — помощник.", ["помощник"], "asst"),
    (105.26, 109.41, "Разбирает почту, пишет ответы клиентам, строит планы на день.", [], "asst"),
    (117.66, 120.42, "Но важно: ИИ не заменяет голову.", ["голову"], "warn"),
    (123.34, 124.70, "Задачу ставишь ты.", ["ты"], "head"),
    (126.97, 128.38, "Проверяешь тоже ты.", ["ты"], "head"),
    (134.87, 140.33, "Зато рутину, на которую уходили часы, он теперь собирает за минуту.", ["часы", "минуту"], "head"),
    (150.37, 152.50, "Хочешь список нейросетей под", ["список"], "ask"),
    (160.86, 164.15, "каждую роль и промты к ним?", ["промты"], "ask"),
    (171.75, 175.12, "Напиши в комментариях «команда» — и пришлю.", ["команда"], "cta"),
]

keep, out_t, blocks = [], 0.0, []
for s, e, text, hi, blk in SEGS:
    s0, e1 = s - PAD0, e + PAD1
    keep.append([round(s0, 3), round(e1, 3)])
    d = e1 - s0
    blocks.append({"t0": out_t, "t1": out_t + d, "speech0": out_t + PAD0, "speech1": out_t + PAD0 + (e - s),
                   "text": text, "hi": hi, "blk": blk})
    out_t += d
total = out_t
print("total", round(total, 2))

# subtitle chunks: proportional timing by characters within each speech island
SPLIT_Y = 1035
FULL_Y = 1420
subs = []
mode_of = {"hook": "full", "meta": "full", "warn": "full", "ask": "full", "cta": "full"}
for b in blocks:
    words = b["text"].split()
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        if len(" ".join(cur)) >= 14 or w.endswith((",", ".", "?", "!", "—")):
            chunks.append(cur); cur = []
    if cur:
        chunks.append(cur)
    lens = [len(" ".join(c)) + 2 for c in chunks]
    tot = sum(lens); t = b["speech0"]; span = b["speech1"] - b["speech0"]
    y = FULL_Y if mode_of.get(b["blk"]) == "full" else SPLIT_Y
    for c, L in zip(chunks, lens):
        dt = span * L / tot
        subs.append([round(t, 3), round(t + dt, 3), " ".join(c).upper(), [h.lower() for h in b["hi"]], y])
        t += dt
# stretch each sub to next start
for i in range(len(subs) - 1):
    if subs[i + 1][0] - subs[i][1] < 0.35:
        subs[i][1] = subs[i + 1][0]

# shots
def bt(blk, which="t0", first=True):
    xs = [b for b in blocks if b["blk"] == blk]
    return xs[0][which] if first else xs[-1][which]

E = "/home/claude/montage/engine/out/"
hook0, hook1 = bt("hook"), bt("hook", "t1", False)
mid = blocks[0]["speech0"] + 3.55  # "Это нейросети" ~ halfway of hook
shots = [
    {"t0": 0, "t1": mid, "mode": "full", "z": 1.45, "push": True},
    {"t0": mid, "t1": hook1, "mode": "full", "z": 1.85},
    {"t0": bt("copy"), "t1": bt("copy", "t1", False), "mode": "split", "card": E + "copywriter.mp4"},
    {"t0": bt("design"), "t1": bt("design", "t1", False), "mode": "split", "card": E + "designer.mp4"},
    {"t0": bt("edit"), "t1": bt("edit", "t1", False), "mode": "split", "card": E + "editor.mp4"},
    {"t0": bt("meta"), "t1": bt("meta", "t1", False), "mode": "full", "z": 1.95},
    {"t0": bt("anal"), "t1": bt("anal", "t1", False), "mode": "split", "card": E + "analyst.mp4"},
    {"t0": bt("asst"), "t1": bt("asst", "t1", False), "mode": "split", "card": E + "assistant.mp4"},
    {"t0": bt("warn"), "t1": bt("warn", "t1", False), "mode": "full", "z": 1.5, "push": True},
    {"t0": bt("head"), "t1": bt("head", "t1", False), "mode": "split", "card": E + "head_v1.mp4"},
    {"t0": bt("ask"), "t1": bt("ask", "t1", False), "mode": "full", "z": 1.45, "push": True},
    {"t0": bt("cta"), "t1": total, "mode": "full", "z": 1.8},
]
for s in shots:
    s["t0"], s["t1"] = round(s["t0"], 3), round(s["t1"], 3)
# head card timings relative to its shot
hb = [b for b in blocks if b["blk"] == "head"]
h0 = hb[0]["t0"]
head_params = f"head&a={hb[0]['speech0'] - h0:.2f}&b={hb[1]['speech0'] - h0:.2f}&c={hb[2]['speech0'] - h0:.2f}"
head_dur = hb[-1]["t1"] - h0 + 0.5

sfx = [[0.0, "hit"]]
for s in shots[1:]:
    sfx.append([max(0, s["t0"] - 0.12), "whoosh"])
sfx.append([bt("meta") + 0.05, "hit"])

plan = {"src": "/home/claude/montage/v1/raw.mov", "face": [0.47, 0.53], "keep": keep, "shots": shots,
        "subs": subs, "sub_y": FULL_Y,
        "overlays": [{"file": E + "ov_hook.mov", "t0": 0.0},
                     {"file": E + "ov_glitch.mov", "t0": round(bt("meta") + 0.1, 3)},
                     {"file": E + "ov_cta.mov", "t0": round(bt("cta") + 0.3, 3)}],
        "sfx": sfx, "out": "/home/claude/montage/v1/edit.mp4"}
json.dump(plan, open("/home/claude/montage/v1/plan.json", "w"), ensure_ascii=False, indent=1)
json.dump({"head_params": head_params, "head_dur": head_dur, "cta_dur": total - bt("cta") - 0.3},
          open("/home/claude/montage/v1/aux.json", "w"))
print(head_params, round(head_dur, 2))
