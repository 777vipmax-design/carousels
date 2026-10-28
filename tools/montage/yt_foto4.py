import json, sys
INT = "cmve3txlo0ygdlk0yfbc3dnjj"
SITE = "оживить-фотографии.рф"
V = [
 ("k1987","https://uploads.postiz.com/bPgKkVbGjh.mp4","Папе 24. Дальнобой, 1987 год — фото ожило","Папе 24. Дальнобой, 1987 год. Усы, грузовик и пыльная дорога через степь.",["Снимок в заломах и пятнах","Реставрация и цвет","Пап, а ты снова в рейсе"],"10-30 10:40"),
 ("zd1962","https://uploads.postiz.com/mazm93VNpM.mp4","Деду 22. Машинист паровоза, 1962 — фото ожило","Деду 22. Машинист паровоза, 1962 год. Фуражка, ватник и пар из-под колёс.",["Надорванное фото в пятнах","Реставрация и цвет","И дед снова улыбается"],"10-30 15:10"),
 ("g1985","https://uploads.postiz.com/ck4n2SdZTJ.mp4","Папе 25. Геолог, 1985 год — фото ожило","Папе 25. Геолог, 1985 год. Борода, рюкзак и палатка в тайге.",["Снимок в сгибах и разводах","Реставрация и цвет","Папа снова в экспедиции"],"10-30 19:40"),
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
