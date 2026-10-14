import json, sys
sys.path.insert(0, "/home/claude/montage/engine")
from planlib import build, bt, rel, dur
V = "v5"; ACC = "#FFB36B"; Q = "%23FFB36B"
SEGS = [
    (7.89, 10.03, "Есть сайты на которые ты смотришь", [], "hook"),
    (14.04, 16.56, "а есть сайты которые смотрят на тебя в ответ", ["смотрят", "тебя"], "hook"),
    (19.89, 21.53, "Вот такое сделал за 5 минут", ["5", "минут"], "demo"),
    (25.28, 27.11, "Двигаешь мышкой — сайт реагирует", ["реагирует"], "demo"),
    (29.49, 31.01, "Листаешь — всё оживает", ["оживает"], "demo"),
    (35.44, 38.33, "Раньше такое студия делала за сотни тысяч рублей", ["сотни", "тысяч"], "studio"),
    (44.14, 46.22, "А я просто описал Claude словами", ["словами"], "prompt"),
    (50.96, 53.95, "Кофейня — тёплый свет — зёрна разлетаются", ["зёрна"], "prompt"),
    (57.77, 59.01, "когда наводишь курсор", ["курсор"], "prompt"),
    (59.58, 60.95, "и получил готовый сайт", ["готовый", "сайт"], "prompt"),
    (65.18, 67.29, "Секрет не в нейросети — а в промте", ["промте"], "secret"),
    (81.26, 84.97, "Если написать «сделай красивый сайт» — получишь шаблон как у всех", ["шаблон"], "tmpl"),
    (98.29, 102.49, "Если написать настроение движение и детали — получишь вот это", ["настроение", "движение", "детали"], "tmpl2"),
    (102.49, 104.70, "", [], "demo2"),
    (110.15, 113.16, "Я собрал промты которыми делаю такие сайты", ["промты"], "ask"),
    (117.18, 119.36, "Напиши «сайт» в комментариях — пришлю", ["сайт"], "cta"),
]
E = f"/home/claude/montage/engine/out/{V}_"
SPEC = {"hook": {"mode": "full", "z": 1.45, "push": True, "cut_at": 2.3, "z2": 1.85},
        "demo": {"mode": "screen", "card": E + "demo.mp4", "pip_x": 750, "pip_y": 190, "pip_d": 270}, "demo2": {"mode": "screen", "card": E + "demo2.mp4", "pip_x": 750, "pip_y": 190, "pip_d": 270},
        "studio": {"mode": "full", "z": 1.85}, "secret": {"mode": "full", "z": 1.5, "push": True},
        "ask": {"mode": "full", "z": 1.45, "push": True}, "cta": {"mode": "full", "z": 1.8}}
for c in ["prompt", "tmpl", "tmpl2"]:
    SPEC[c] = {"mode": "split", "card": E + c + ".mp4"}
plan, B, total = build(SEGS, SPEC, f"/home/claude/montage/{V}/raw.mov", f"/home/claude/montage/{V}/edit.mp4",
                       face=(0.44, 0.52), hi_color=ACC)
O = "/home/claude/montage/engine/out/"
plan["overlays"] = [{"file": O + f"{V}_ov_hook.mov", "t0": 0.0}, {"file": O + f"{V}_ov_cta.mov", "t0": round(bt(B, "cta") + 0.3, 3)}]
dm = dur(B, "demo")
cards = {
    "prompt": (f"prompt&acc={Q}&b={rel(B,'prompt',1)}&c={rel(B,'prompt',2)}&d={rel(B,'prompt',3)}", dur(B, "prompt")),
    "tmpl": (f"tmpl&acc={Q}&b={rel(B,'tmpl',0,1.9)}", dur(B, "tmpl")),
    "tmpl2": (f"tmpl2&acc={Q}&b={rel(B,'tmpl2',0,3.3)}", dur(B, "tmpl2")),
}
sites = {"demo": (f"demo&d={dm}&sc={rel(B,'demo',2,-0.2)}", dm), "demo2": (f"demo2&d={dur(B,'demo2')}", dur(B, "demo2"))}
hook_d = round(bt(B, "hook", "t1", False), 2)
OVS = {"hook": [f"hook&a=САЙТ КОТОРЫЙ&sa=84&b=СМОТРИТ НА ТЕБЯ&acc={Q}&out={round(hook_d - 0.4, 2)}", hook_d],
       "cta": [f"cta&w=САЙТ&s=пришлю промты для таких сайтов&acc={Q}", round(total - bt(B, "cta") - 0.3, 2)]}
json.dump(plan, open(f"/home/claude/montage/{V}/plan.json", "w"), ensure_ascii=False, indent=1)
json.dump({"cards": cards, "sites": sites, "overlays": OVS, "total": total}, open(f"/home/claude/montage/{V}/aux.json", "w"), ensure_ascii=False, indent=1)
print("total", round(total, 2))
for b in B: print(b["blk"], round(b["t0"], 2), b["text"][:40])
print(json.dumps(cards, ensure_ascii=False), sites)
