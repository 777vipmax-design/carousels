import json, sys
INT = "cmve3txlo0ygdlk0yfbc3dnjj"
SITE = "оживить-фотографии.рф"
V = [
 ("pl1986","https://uploads.postiz.com/ztTqyQM71U.mp4","Папе 20. Подводник, 1986 год — фото ожило","Папе 20. Подводный флот, 1986 год. Бескозырка, тельняшка и северное море.",["Снимок в трещинах и пятнах","Реставрация и цвет","Пап, ты снова на пирсе"],"10-31 10:40"),
 ("sv1983","https://uploads.postiz.com/vRa9V4qGw3.mp4","Папе 23. Сварщик, 1983 год — фото ожило","Папе 23. Сварщик, 1983 год. Маска на лбу, рукавицы и стройка за спиной.",["Надорванное фото в пятнах","Реставрация и цвет","И папа снова улыбается"],"10-31 15:10"),
 ("tf1978","https://uploads.postiz.com/jqQbjn12VZ.mp4","Маме 21. Телефонистка, 1978 — фото ожило","Маме 21. Телефонистка, 1978 год. Наушники, бантик и коммутатор.",["Снимок в трещинах и пятнах","Реставрация и цвет","Мам, ты снова на связи"],"10-31 19:40"),
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
