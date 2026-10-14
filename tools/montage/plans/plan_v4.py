import json, sys
sys.path.insert(0, "/home/claude/montage/engine")
from planlib import build, bt, rel, dur
V = "v4"; ACC = "#FFC24D"; Q = "%23FFC24D"
SEGS = [
    (10.24, 12.87, "Я не программист — но за один день я сделал сайт", ["один", "день", "сайт"], "hook"),
    (24.41, 27.79, "который сам принимает заказы — сам выполняет их", ["заказы"], "site"),
    (33.96, 36.60, "с помощью нейросети и сам принимает оплату", ["оплату"], "site"),
    (42.52, 45.74, "Я не написал ни одной строчки кода — всё сделал Claude", ["ни", "одной", "строчки", "claude"], "nocode"),
    (52.71, 56.06, "Я просто объяснял ему словами как простому разработчику", ["словами"], "brief"),
    (65.23, 68.28, "Вот что должен делать сайт — вот как выглядит заказ", [], "brief"),
    (71.77, 73.21, "вот куда приходят деньги", ["деньги"], "brief"),
    (79.92, 82.80, "Он писал код — проверял — исправлял ошибки", ["исправлял"], "dev"),
    (89.21, 90.29, "Где было сложно?", ["сложно"], "q"),
    (91.89, 93.57, "Настроить сервер и оплату", ["сервер", "оплату"], "hard"),
    (98.54, 100.18, "Там я задавал много вопросов", ["вопросов"], "hard"),
    (105.67, 108.35, "но он объяснял так что разобрался даже я", ["даже", "я"], "hard"),
    (118.46, 123.55, "Раньше такой проект стоил бы сотни тысяч и работу целого штата программистов", ["сотни", "тысяч"], "cost"),
    (132.43, 135.02, "Сейчас — вечер и подписка на нейросети", ["вечер", "подписка"], "cost"),
    (142.49, 145.69, "Это называется вайб-кодинг — и это реально работает", ["вайб-кодинг"], "vibe"),
    (152.73, 154.50, "Хочешь промт с которого начинал?", ["промт"], "ask"),
    (157.62, 159.09, "Напиши «код» — пришлю", ["код"], "cta"),
]
E = f"/home/claude/montage/engine/out/{V}_"
SPEC = {"hook": {"mode": "full", "z": 1.45, "push": True, "cut_at": 1.25, "z2": 1.85},
        "nocode": {"mode": "full", "z": 1.85}, "q": {"mode": "full", "z": 1.5, "push": True},
        "vibe": {"mode": "full", "z": 1.5, "push": True}, "ask": {"mode": "full", "z": 1.85}, "cta": {"mode": "full", "z": 1.45}}
for c in ["site", "brief", "dev", "hard", "cost"]:
    SPEC[c] = {"mode": "split", "card": E + c + ".mp4"}
plan, B, total = build(SEGS, SPEC, f"/home/claude/montage/{V}/raw.mov", f"/home/claude/montage/{V}/edit.mp4",
                       face=(0.49, 0.52), hi_color=ACC)
O = "/home/claude/montage/engine/out/"
plan["overlays"] = [{"file": O + f"{V}_ov_hook.mov", "t0": 0.0},
                    {"file": O + f"{V}_ov_glitch.mov", "t0": round(bt(B, "nocode") + 0.2, 3)},
                    {"file": O + f"{V}_ov_cta.mov", "t0": round(bt(B, "cta") + 0.3, 3)}]
cards = {
    "site": (f"site&acc={Q}&b={rel(B,'site',0,1.75)}&c={rel(B,'site',1,1.5)}", dur(B, "site")),
    "brief": (f"brief&acc={Q}&b={rel(B,'brief',1)}&c={rel(B,'brief',1,1.9)}&d={rel(B,'brief',2)}", dur(B, "brief")),
    "dev": (f"dev&acc={Q}", dur(B, "dev")),
    "hard": (f"hard&acc={Q}&b={rel(B,'hard',1)}&c={rel(B,'hard',2)}", dur(B, "hard")),
    "cost": (f"cost&acc={Q}&b={rel(B,'cost',1)}", dur(B, "cost")),
}
hook_d = round(bt(B, "hook", "t1"), 2)
OVS = {"hook": [f"hook&a=Я НЕ ПРОГРАММИСТ&sa=84&b=САЙТ ЗА 1 ДЕНЬ&acc={Q}&out={hook_d - 0.3}", hook_d],
       "glitch": [f"glitch&g=0 строк кода&acc={Q}&out=2.6", 3.0],
       "cta": [f"cta&w=КОД&s=пришлю промт с которого начинал&acc={Q}", round(total - bt(B, "cta") - 0.3, 2)]}
json.dump(plan, open(f"/home/claude/montage/{V}/plan.json", "w"), ensure_ascii=False, indent=1)
json.dump({"cards": cards, "overlays": OVS, "total": total}, open(f"/home/claude/montage/{V}/aux.json", "w"), ensure_ascii=False, indent=1)
print("total", round(total, 2))
for b in B: print(b["blk"], round(b["t0"], 2), b["text"][:40])
print(json.dumps(cards, ensure_ascii=False))
