import json, sys
INT = "cmve3txlo0ygdlk0yfbc3dnjj"
SITE = "оживить-фотографии.рф"
V = [
 ("ar1982","https://uploads.postiz.com/JyULNl4iT1.mp4","Папе 19. Армия, 1982 год — фото ожило","Папе 19. Армия, зима 1982 года.",["Старое фото в трещинах","Реставрация и цвет","Пап, ты снова в строю"],"11-05 19:40"),
 ("vs1975","https://uploads.postiz.com/ijo8bJqL2z.mp4","Папе 23. Стройка, 1975 год — фото ожило","Папе 23. Монтажник на стройке, 1975 год.",["Снимок в заломах и пятнах","Реставрация и цвет","Пап, ты снова на стройке"],"11-06 10:40"),
 ("gs1981","https://uploads.postiz.com/vw2JwIfT7w.mp4","Маме 22. Гастроном, 1981 год — фото ожило","Маме 22. Продавщица в гастрономе, 1981 год.",["Выцветший снимок в пятнах","Реставрация и цвет","Мам, ты снова за прилавком"],"11-06 19:10"),
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
