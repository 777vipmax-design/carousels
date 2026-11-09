import json, sys
INT = "cmve3txlo0ygdlk0yfbc3dnjj"
SITE = "оживить-фотографии.рф"
V = [
 ("ku1987","https://uploads.postiz.com/MCcJHRuFoW.mp4","Папе 18. Курсант, 1987 год — фото ожило","Папе 18. Курсант военного училища, 1987 год.",["Старое фото в трещинах","Реставрация и цвет","Пап, ты снова в строю"],"11-09 16:40"),
 ("fb1981","https://uploads.postiz.com/UNUWQKsNL5.mp4","Папе 21. Заводской футбол, 1981 — фото ожило","Папе 21. Футбольная команда завода, 1981 год.",["Снимок в заломах и пятнах","Реставрация и цвет","Пап, ты снова на поле"],"11-09 19:10"),
 ("kd1980","https://uploads.postiz.com/l7htHXNKoa.mp4","Маме 21. Кондуктор троллейбуса, 1980 — фото ожило","Маме 21. Кондуктор троллейбуса, 1980 год.",["Выцветший снимок","Реставрация и цвет","Мам, ты снова на маршруте"],"11-09 21:20"),
]
TAGS = ["оживить фото","старые фото","реставрация фото","фото оживают","нейросеть"]
def p(lines): return "".join(f"<p>{l}</p>" for l in lines)
out=[]
for k,m,t,hook,ls,when in V:
    mm,rest=when.split(" "); M,D=mm.split("-"); h,mi=map(int,rest.split(":"))
    date=f"2026-{M}-{D}T{h-3:02d}:{mi:02d}:00Z"
    body=[hook,""]+["• "+l for l in ls]+["","Хотите оживить своё фото? Ссылка на сайт — в шапке канала. Превью бесплатно, без регистрации. Реставрация, цвет и оживление за несколько минут.","","Подписывайтесь — каждый день оживляем старые снимки.","","#оживлениефото #старыефото #реставрацияфото #память #shorts"]
    out.append({"integrationId":INT,"isPremium":False,"date":date,"shortLink":False,"type":"schedule",
      "settings":[{"key":"title","value":t+" #shorts"},{"key":"type","value":"public"},{"key":"selfDeclaredMadeForKids","value":"no"},{"key":"tags","value":[{"value":x,"label":x} for x in TAGS]}],
      "postsAndComments":[{"content":p(body),"attachments":[m]},{"content":p(["📷 Оживить своё фото — ссылка в шапке канала","Превью бесплатно, без регистрации"]),"attachments":[]}]})
a,b=int(sys.argv[1]),int(sys.argv[2])
print(json.dumps(out[a:b],ensure_ascii=False))
