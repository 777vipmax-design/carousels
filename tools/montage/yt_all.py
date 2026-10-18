"""Full plan for the new «Нейро на практике» channel: 61 shorts, 3 now + 3/day at varied times."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yt_neiro as Y
B = {"b1": "limit dogovor golos tablica preza proekt podkluchi svodka novichok konkurent",
     "b2": "ustanovka kak plaginy dyry pravila plan otkat skill vybor mcp",
     "b3": "tarif pamyat obzor schet zakon kritik dizain animaciya kniga magazin",
     "b4": "otchet audit otzyvy kp vakansiya idei scenariy kalkulyator bot formula",
     "b5": "issleduy kviz skrin terminal agent doverie posty vozrazheniya dashboard skolko"}
FIRST = ["fl-insta", "fl-office", "fl-skills5"]
REST = ["fl-rea", "fl-clients", "fl-find", "fl-face-v3", "fl-face-v2", "fl-face-v6", "fl-face-v4", "fl-face-v5",
        "b3-obzor", "b1-limit", "b2-vybor", "b1-dogovor", "b2-kak", "b5-terminal", "b1-golos", "b3-tarif",
        "b2-skill", "b1-novichok", "b5-agent", "b3-schet", "b1-konkurent", "b2-mcp", "b4-scenariy", "b3-kritik",
        "b5-skrin"]
allb = [f"{b}-{s}" for b, v in B.items() for s in v.split()]
REST += [k for k in allb if k not in REST]
SLOTS = [("09:10", "13:40", "19:20"), ("08:30", "14:15", "20:05"), ("10:00", "15:30", "19:45"),
         ("09:40", "12:50", "18:40"), ("08:50", "16:10", "20:30"), ("10:20", "14:40", "19:05"),
         ("09:25", "13:15", "21:00")]
import datetime as D
def utc(day, hm):
    h, m = map(int, hm.split(":"))
    t = D.datetime(2026, 10, day if isinstance(day, int) else 1, h, m) if False else None
    return t
plan = []
now = [D.datetime(2026, 10, 18, 20, 30), D.datetime(2026, 10, 18, 20, 50), D.datetime(2026, 10, 18, 21, 10)]
for k, t in zip(FIRST, now):
    plan.append((k, t))
d0 = D.datetime(2026, 10, 19)
for i, k in enumerate(REST):
    day, j = divmod(i, 3)
    hm = SLOTS[day % len(SLOTS)][j]
    h, m = map(int, hm.split(":"))
    plan.append((k, d0 + D.timedelta(days=day, hours=h, minutes=m)))
out = []
for k, t in plan:
    it = Y.item(k)
    it["msk"] = t.strftime("%d.%m %H:%M")
    it["date"] = (t - D.timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:00Z")
    out.append(it)
json.dump(out, open(os.path.join(Y.M, "yt_all_plan.json"), "w"), ensure_ascii=False, indent=1)
for o in out:
    print(o["msk"], o["key"], "|", o["title"])
print(len(out))
