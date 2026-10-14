import json, sys
sys.path.insert(0, "/home/claude/montage/engine")
from render_cards import render
V = sys.argv[1]; aux = json.load(open(f"/home/claude/montage/{V}/aux.json"))
O = "/home/claude/montage/engine/out/"
only = sys.argv[2:] 
for name, (card, d) in aux["cards"].items():
    if only and name not in only: continue
    render(card, d, O + f"{V}_{name}.mp4", page_file="cards2.html"); print("card", name)
for name, (card, d) in aux.get("sites", {}).items():
    if only and name not in only: continue
    render(card, d, O + f"{V}_{name}.mp4", 1080, 1920, False, "site.html"); print("site", name)
for name, (card, d) in aux.get("overlays", {}).items():
    if only and name not in only: continue
    render(card, d, O + f"{V}_ov_{name}.mov", 1080, 1920, True, "overlay.html"); print("ov", name)
