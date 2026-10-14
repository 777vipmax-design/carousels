import json, sys
sys.path.insert(0, "/home/claude/montage/engine")
from planlib import build, bt
ACC = "#B388FF"
ACCQ = "%23B388FF"
SEGS = [
    (7.26, 12.25, "Я не открывал ни одной программы для монтажа — этот ролик смонтировал Claude", ["монтажа", "claude"], "hook"),
    (19.78, 22.94, "Я просто записал себя на телефон лёжа в кровати", ["телефон"], "raw"),
    (27.19, 29.12, "Со всеми оговорками и паузами", ["оговорками", "паузами"], "raw"),
    (32.64, 33.49, "И отдал ему", [], "raw"),
    (39.32, 42.61, "Он сам нашёл где я споткнулся и вырезал лишнее", ["вырезал", "лишнее"], "cut"),
    (47.80, 49.19, "Сам сделал субтитры", ["субтитры"], "subs"),
    (55.50, 60.00, "Сам добавил вот эти вставки — сделал музыку и добавил анимацию", ["вставки", "музыку", "анимацию"], "fx"),
    (67.74, 70.80, "Раньше на монтаж одного ролика у меня уходил вечер", ["вечер"], "before"),
    (76.49, 79.71, "Или полторы-две тысячи монтажёру — и так каждый раз", ["тысячи", "каждый", "раз"], "before"),
    (87.03, 90.45, "А теперь я снимаю и иду заниматься своими делами", ["своими", "делами"], "now"),
    (102.18, 106.06, "Самое смешное — большинство людей Claude используют как чат", ["чат"], "chat"),
    (118.02, 122.27, "Чтобы спросить что-то — а он за тебя может уже делать целую работу", ["целую", "работу"], "work"),
    (126.98, 128.84, "Хочешь узнать как я это настроил?", ["настроил"], "ask"),
    (133.59, 136.16, "Напиши в комментариях «монтаж» — пришлю", ["монтаж"], "cta"),
]
E = "/home/claude/montage/engine/out/v2_"
SPEC = {
    "hook": {"mode": "full", "z": 1.45, "push": True, "cut_at": 2.95, "z2": 1.85},
    "raw": {"mode": "split", "card": E + "raw.mp4"}, "cut": {"mode": "split", "card": E + "cut.mp4"},
    "subs": {"mode": "split", "card": E + "subs.mp4"}, "fx": {"mode": "split", "card": E + "fx.mp4"},
    "before": {"mode": "split", "card": E + "before.mp4"},
    "now": {"mode": "full", "z": 1.5, "push": True}, "chat": {"mode": "full", "z": 1.85},
    "work": {"mode": "split", "card": E + "work.mp4"},
    "ask": {"mode": "full", "z": 1.45, "push": True}, "cta": {"mode": "full", "z": 1.8},
}
plan, blocks, total = build(SEGS, SPEC, "/home/claude/montage/v2/raw.mov", "/home/claude/montage/v2/edit.mp4",
                            face=(0.44, 0.52), hi_color=ACC)
O = "/home/claude/montage/engine/out/"
plan["overlays"] = [{"file": O + "v2_ov_hook.mov", "t0": 0.0}, {"file": O + "v2_ov_cta.mov", "t0": round(bt(blocks, "cta") + 0.3, 3)}]
# card params: speech starts of later segments relative to card start
def rel(blk, k):
    xs = [b for b in blocks if b["blk"] == blk]; return round(xs[k]["speech0"] - xs[0]["t0"], 2)
def dur(blk):
    return round(bt(blocks, blk, "t1", False) - bt(blocks, blk) + 0.4, 2)
fx = [b for b in blocks if b["blk"] == "fx"][0]
cards = {
    "raw": (f"raw&acc={ACCQ}&b={rel('raw',1)}&c={rel('raw',2)}", dur("raw")),
    "cut": (f"cut&acc={ACCQ}&b=2.2", dur("cut")),
    "subs": (f"subs&acc={ACCQ}", dur("subs")),
    "fx": (f"fx&acc={ACCQ}&b=2.25&c=3.5", dur("fx")),
    "before": (f"before&acc={ACCQ}&b={rel('before',1)}&c={round(rel('before',1)+2.05,2)}", dur("before")),
    "work": (f"work&acc={ACCQ}&b=1.65", dur("work")),
}
json.dump(plan, open("/home/claude/montage/v2/plan.json", "w"), ensure_ascii=False, indent=1)
OVS = {"hook": ["hook&a=ЭТОТ РОЛИК&b=СМОНТИРОВАЛ CLAUDE&sb=66&yb=322&acc=%23B388FF&out=4.7", 5.2],
       "cta": ["cta&w=МОНТАЖ&s=пришлю как я это настроил&acc=%23B388FF", round(total - bt(blocks, "cta") - 0.3, 2)]}
json.dump({"cards": cards, "overlays": OVS, "cta_dur": round(total - bt(blocks, "cta") - 0.3, 2), "hook_dur": 5.2, "total": total},
          open("/home/claude/montage/v2/aux.json", "w"), ensure_ascii=False, indent=1)
print("total", round(total, 2))
for b in blocks: print(b["blk"], round(b["t0"], 2), round(b["speech0"], 2), b["text"][:40])
