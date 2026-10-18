import json, html, sys, os
M = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(M, "yt_postiz_media.json")))
INT = "cmve3cc4c0xhdr50y6pydhdal"
items = json.load(open(os.path.join(M, "yt_all_plan.json")))
TAGS = ["claude", "claude ai", "нейросети", "ии", "claude code"]
a, b = int(sys.argv[1]), int(sys.argv[2])
out = []
for it in items[a:b]:
    c = "".join(f"<p>{html.escape(l, quote=False)}</p>" for l in it["desc"].split("\n"))
    com = "".join(f"<p>{html.escape(l, quote=False)}</p>" for l in it["comment"].split("\n"))
    out.append({"integrationId": INT, "isPremium": False, "date": it["date"], "shortLink": False, "type": "schedule",
                "settings": [{"key": "title", "value": it["title"]}, {"key": "type", "value": "public"},
                             {"key": "selfDeclaredMadeForKids", "value": "no"},
                             {"key": "tags", "value": [{"value": t, "label": t} for t in TAGS]}],
                "postsAndComments": [{"content": c, "attachments": [f"https://uploads.postiz.com/{P[it['key']]}.mp4"]},
                                     {"content": com, "attachments": []}]})
missing = [it["key"] for it in items if it["key"] not in P]
sys.stderr.write(f"missing media: {len(missing)}\n")
print(json.dumps(out, ensure_ascii=False))
