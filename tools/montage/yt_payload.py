import json, html, sys
P = {"fl-rea":"HpxsoUrkJE","fl-clients":"Pj4sQwGy7M","fl-find":"PE9he3shHx","fl-face-v2":"QxE88cBCJ0","b1-limit":"2XcmX349BC","b2-vybor":"zJNHCDIZe3","fl-face-v6":"3Ub8njP70Z","b3-obzor":"ASFdZmI10P","b1-dogovor":"fKA9IUwjVi","fl-face-v4":"csuwgDdeks","b2-kak":"5FM5aM0Xj8","b5-terminal":"qlh3xmuhjv","b1-golos":"LjxBYbgUiX","b3-tarif":"K1BjFIlfED","fl-face-v5":"8sr9s7rLdJ","b2-skill":"2zwSaufPyO","b1-novichok":"Mr2jncA6AX","b5-agent":"7QdgOvmSrb","b3-schet":"wzajNI7FBP","b1-konkurent":"VQRQAf4cpf","b2-mcp":"kd1BGx7UZq","b4-scenariy":"NKl31X4DGd","b3-kritik":"hFgdOoLlbI","b5-skrin":"NVv26TyR1p"}
items = json.load(open("yt_neiro_plan.json"))
dates = ["2026-10-18T16:40:00Z","2026-10-18T17:00:00Z","2026-10-18T17:20:00Z"] + [f"2026-10-{d}T{h}:00Z" for d in range(19,26) for h in ("06:00","10:00","16:00")]
posts=[]
for it,dt in zip(items,dates):
    c="".join(f"<p>{html.escape(l, quote=False)}</p>" for l in it["desc"].split("\n"))
    com="".join(f"<p>{html.escape(l, quote=False)}</p>" for l in it["comment"].split("\n"))
    posts.append({"integrationId":"cmve1fuaq0wnvlk0yrylpt7lf","isPremium":False,"date":dt,"shortLink":False,"type":"schedule",
      "settings":[{"key":"title","value":it["title"]},{"key":"type","value":"public"},{"key":"selfDeclaredMadeForKids","value":"no"},
                  {"key":"tags","value":[{"value":t,"label":t} for t in it["tags"]]}],
      "postsAndComments":[{"content":c,"attachments":[f"https://uploads.postiz.com/{P[it['key']]}.mp4"]},{"content":com,"attachments":[]}]})
a,b=int(sys.argv[1]),int(sys.argv[2])
print(json.dumps(posts[a:b],ensure_ascii=False))
