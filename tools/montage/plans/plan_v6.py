import json, sys
sys.path.insert(0, "/home/claude/montage/engine")
from planlib import build, bt, rel, dur
V = "v6"; ACC = "#FF5FD2"; Q = "%23FF5FD2"
SEGS = [
    (6.13, 9.39, "Большинство людей Claude пишут один запрос", ["один", "запрос"], "hook"),
    (10.00, 11.50, "и получают один ответ", ["один", "ответ"], "hook"),
    (16.97, 20.85, "А можно сделать так чтобы он работал как целая команда", ["целая", "команда"], "hook2"),
    (32.60, 34.47, "В Claude Code есть субагенты", ["субагенты"], "agents"),
    (54.74, 60.41, "Это его помощники — каждому даёшь отдельную команду и они работают одновременно", ["помощники", "одновременно"], "agents"),
    (66.16, 67.29, "Один пишет текст", ["текст"], "team"),
    (67.57, 68.94, "второй проверяет факты", ["факты"], "team"),
    (73.46, 74.74, "третий ищет ошибки", ["ошибки"], "team"),
    (78.57, 81.31, "А главный собирает из этого лучший результат", ["лучший", "результат"], "team"),
    (91.96, 92.86, "Как с командой", [], "speed"),
    (93.17, 95.37, "один делает работу за целый день", ["день"], "speed"),
    (95.68, 97.30, "а команда делает за час", ["час"], "speed"),
    (106.54, 109.06, "Главный вопрос в комментариях всегда один", [], "limq"),
    (109.65, 110.81, "А лимиты не сгорят?", ["лимиты"], "limq"),
    (115.98, 118.04, "Сгорят — если запускать бездумно", ["бездумно"], "limit"),
    (125.01, 129.05, "Поэтому важно сколько помощников и какие задачи им давать", ["сколько", "задачи"], "limit"),
    (139.26, 143.16, "Хочешь мою настройку — как запустить команду и не спалить лимит?", ["настройку"], "ask"),
    (147.60, 149.46, "Напиши «арена» — пришлю", ["арена"], "cta"),
]
E = f"/home/claude/montage/engine/out/{V}_"
SPEC = {"hook": {"mode": "full", "z": 1.45, "push": True}, "hook2": {"mode": "full", "z": 1.85},
        "limq": {"mode": "full", "z": 1.5, "push": True, "cut_at": 2.6, "z2": 1.95},
        "ask": {"mode": "full", "z": 1.45, "push": True}, "cta": {"mode": "full", "z": 1.8}}
for c in ["agents", "team", "speed", "limit"]:
    SPEC[c] = {"mode": "split", "card": E + c + ".mp4"}
plan, B, total = build(SEGS, SPEC, f"/home/claude/montage/{V}/raw.mov", f"/home/claude/montage/{V}/edit.mp4",
                       face=(0.45, 0.50), hi_color=ACC)
O = "/home/claude/montage/engine/out/"
plan["overlays"] = [{"file": O + f"{V}_ov_hook.mov", "t0": 0.0}, {"file": O + f"{V}_ov_cta.mov", "t0": round(bt(B, "cta") + 0.3, 3)}]
cards = {
    "agents": (f"agents&acc={Q}&b={rel(B,'agents',1)}&c={rel(B,'agents',1,3.95)}", dur(B, "agents")),
    "team": (f"team&acc={Q}&b={rel(B,'team',1)}&c={rel(B,'team',2)}&d={rel(B,'team',3)}", dur(B, "team")),
    "speed": (f"speed&acc={Q}&b={rel(B,'speed',1)}&c={rel(B,'speed',2)}", dur(B, "speed")),
    "limit": (f"limit&acc={Q}&b={rel(B,'limit',1)}", dur(B, "limit")),
}
hook_d = round(bt(B, "hook", "t1", False), 2)
OVS = {"hook": [f"hook&a=1 ЗАПРОС = 1 ОТВЕТ&sa=84&b=А МОЖНО КОМАНДУ&sb=68&acc={Q}&out={round(hook_d - 0.3, 2)}", hook_d],
       "cta": [f"cta&w=АРЕНА&s=пришлю мою настройку агентов&acc={Q}", round(total - bt(B, "cta") - 0.3, 2)]}
json.dump(plan, open(f"/home/claude/montage/{V}/plan.json", "w"), ensure_ascii=False, indent=1)
json.dump({"cards": cards, "overlays": OVS, "total": total}, open(f"/home/claude/montage/{V}/aux.json", "w"), ensure_ascii=False, indent=1)
print("total", round(total, 2))
for b in B: print(b["blk"], round(b["t0"], 2), b["text"][:40])
print(json.dumps(cards, ensure_ascii=False))
