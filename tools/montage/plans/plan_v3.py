import json, sys
sys.path.insert(0, "/home/claude/montage/engine")
from planlib import build, bt, rel, dur
V = "v3"; ACC = "#4FD1FF"; Q = "%234FD1FF"
SEGS = [
    (12.07, 14.70, "Если ты просто задаёшь Claude вопросы", ["вопросы"], "hook"),
    (20.28, 23.30, "ты используешь процентов 10 его возможностей", ["10"], "meter"),
    (27.43, 29.43, "Вот что он умеет на самом деле", ["самом", "деле"], "meter"),
    (34.80, 37.84, "Первое — делает готовые вещи а не текст", ["готовые", "вещи"], "make"),
    (61.65, 64.86, "Страницу калькулятор таблицу презентацию", [], "make"),
    (68.84, 70.64, "Сразу рабочие — по ссылке", ["рабочие"], "make"),
    (74.90, 76.05, "Второе — скиллы", ["скиллы"], "skill"),
    (80.77, 84.44, "Это как навыки сотрудника — один раз даёшь ему инструкцию", ["навыки", "инструкцию"], "skill"),
    (89.98, 91.09, "И он делает", [], "skill"),
    (94.28, 97.59, "задачу каждый раз одинаково хорошо", ["одинаково", "хорошо"], "skill"),
    (106.25, 107.72, "Третье — Claude Code", ["claude", "code"], "code"),
    (113.53, 116.54, "Он сам пишет программы и сайты прямо на компьютере", ["программы", "сайты"], "code"),
    (120.12, 122.06, "Ты объясняешь словами — он делает", ["словами", "делает"], "code"),
    (126.86, 128.39, "Четвёртое — подключения", ["подключения"], "connect"),
    (132.72, 134.75, "Почта календарь документы", [], "connect"),
    (138.50, 140.41, "Он сам в них заходит и работает", ["сам"], "connect"),
    (144.34, 145.36, "Пятое — браузер", ["браузер"], "browser"),
    (158.74, 162.20, "Он может сам заходить на сайт — кликать и заполнять формы", ["сам"], "browser"),
    (165.22, 166.47, "Пока ты пьёшь кофе", ["кофе"], "browser"),
    (170.40, 173.06, "Это уже не чат-бот — это сотрудник", ["сотрудник"], "emp"),
    (185.85, 188.39, "Хочешь инструкцию как начать каждое из пяти?", ["инструкцию"], "ask"),
    (191.16, 192.77, "Напиши «Клод» — пришлю", ["клод"], "cta"),
]
E = f"/home/claude/montage/engine/out/{V}_"
SPEC = {"hook": {"mode": "full", "z": 1.45, "push": True},
        "emp": {"mode": "full", "z": 1.85}, "ask": {"mode": "full", "z": 1.45, "push": True}, "cta": {"mode": "full", "z": 1.8}}
for c in ["meter", "make", "skill", "code", "connect", "browser"]:
    SPEC[c] = {"mode": "split", "card": E + c + ".mp4"}
plan, B, total = build(SEGS, SPEC, f"/home/claude/montage/{V}/raw.mov", f"/home/claude/montage/{V}/edit.mp4",
                       face=(0.44, 0.52), hi_color=ACC)
O = "/home/claude/montage/engine/out/"
plan["overlays"] = [{"file": O + f"{V}_ov_hook.mov", "t0": 0.0}, {"file": O + f"{V}_ov_cta.mov", "t0": round(bt(B, "cta") + 0.3, 3)}]
cards = {
    "meter": (f"meter&acc={Q}&b={rel(B,'meter',1)}", dur(B, "meter")),
    "make": (f"make&acc={Q}&b={rel(B,'make',1)}&c={rel(B,'make',1,1.75)}&d={rel(B,'make',2)}", dur(B, "make")),
    "skill": (f"skill&acc={Q}&b={rel(B,'skill',1,1.9)}&c={rel(B,'skill',2)}", dur(B, "skill")),
    "code": (f"code&acc={Q}&b={rel(B,'code',2)}", dur(B, "code")),
    "connect": (f"connect&acc={Q}&b={rel(B,'connect',1)}&c={rel(B,'connect',2)}", dur(B, "connect")),
    "browser": (f"browser&acc={Q}&b={rel(B,'browser',1)}&c={rel(B,'browser',2)}", dur(B, "browser")),
}
hook_d = round(bt(B, "hook", "t1"), 2)
OVS = {"hook": [f"hook&a=ТЫ ИСПОЛЬЗУЕШЬ&sa=80&b=CLAUDE НА 10%25&sb=84&yb=310&acc={Q}&out={hook_d - 0.4}", hook_d],
       "cta": [f"cta&w=КЛОД&s=пришлю инструкцию как начать&acc={Q}", round(total - bt(B, "cta") - 0.3, 2)]}
json.dump(plan, open(f"/home/claude/montage/{V}/plan.json", "w"), ensure_ascii=False, indent=1)
json.dump({"cards": cards, "overlays": OVS, "total": total}, open(f"/home/claude/montage/{V}/aux.json", "w"), ensure_ascii=False, indent=1)
print("total", round(total, 2))
for b in B: print(b["blk"], round(b["t0"], 2), b["text"][:40])
print(json.dumps(cards, ensure_ascii=False))
