"""YouTube «Долги без паники»: python3 yt_dolgi.py INT A B [first_msk HH:MM]"""
import json, sys, re
MEDIA = {"bk1-mfc":"PyCQMxpfyK","bk1-zaberut":"cp6yxVaIEM","bk1-posle":"gavMOr7zPZ","bk1-prezident":"PZv6ylKMvl",
 "bk1-stoimost":"K0zg8MBo5I","bk1-posledstviya":"9UiZue9dBp","bk1-neplatit":"tueNy76W4t","bk1-test":"Ac4qbz72Cj",
 "bk1-ipoteka":"KorHydaw5a","bk1-razbor":"NZJacYONYQ","f3-strakhovka":"XPagW9zrG9","f3-kollektory":"Aldd9KkWr0",
 "f3-zaym":"cX2Cr4Afck","f3-svadba":"0HW4in6q97","f3-pristavy":"SxdA4rhZ2u","f3-otkaz":"tQFtQJDLGu",
 "f3-drug":"o41axP5lNz","f3-bezopas":"t8DCpBYk7M"}
ORDER = ["bk1-prezident","bk1-mfc","f3-kollektory","bk1-zaberut","f3-bezopas","bk1-posle","bk1-neplatit","f3-strakhovka",
 "bk1-stoimost","f3-pristavy","bk1-test","bk1-ipoteka","f3-drug","bk1-posledstviya","f3-zaym","bk1-razbor","f3-otkaz","f3-svadba"]
TITLES = {"bk1-prezident":"Президент разрешил списать все долги? Разбираю","bk1-mfc":"Долги до миллиона можно списать бесплатно — но не всем",
 "f3-kollektory":"Коллекторы звонят маме и на работу. Имеют право?","bk1-zaberut":"Банкротство: что заберут, а что оставят",
 "f3-bezopas":"«Переведите деньги на безопасный счёт» — что делать","bk1-posle":"Дадут ли кредит после банкротства?",
 "bk1-neplatit":"Что будет, если просто перестать платить кредит","f3-strakhovka":"Навязали страховку к кредиту? Её можно вернуть",
 "bk1-stoimost":"Сколько на самом деле стоит банкротство через суд","f3-pristavy":"Карта, которую не видят приставы? Правда",
 "bk1-test":"Тест за 30 секунд: подходит ли тебе банкротство","bk1-ipoteka":"Банкротство и ипотека: заберут ли квартиру",
 "f3-drug":"Парень просит взять кредит на тебя. Что будет?","bk1-posledstviya":"Последствия банкротства, о которых молчат",
 "f3-zaym":"Займ 10 000 до зарплаты: сколько переплатишь","bk1-razbor":"Долг 600 000, зарплата 40 000 — что делать",
 "f3-otkaz":"Хорошая зарплата, а банк отказал. Почему","f3-svadba":"Свадьба в кредит: сколько стоит на самом деле"}
SLOTS = [("10:20","15:10","19:40"),("09:40","13:30","20:15"),("11:00","16:20","19:10"),("09:10","14:45","20:40"),
         ("10:40","13:50","19:25"),("08:50","15:40","20:00")]
SITE = "https://bankrotstvo-fizicheskih-lits.ru/?utm_source=youtube"
TAGS = ["банкротство физических лиц","списать долги","долги по кредитам","банкротство через мфц","кредиты"]
R = {'от двадцати пяти тысяч до миллиона рублей': 'от 25 000 до 1 000 000 ₽', 'шесть месяцев': '6 месяцев', 'с две тысячи пятнадцатого года': 'с 2015 года', 'Летом двадцать шестого года': 'Летом 2026 года', 'в июле двадцать седьмого': 'в июле 2027-го', 'Двадцать пять тысяч рублей': '25 000 ₽', 'от шестидесяти тысяч рублей': 'от 60 000 ₽', 'до двадцати процентов годовых': 'до 20% годовых', 'последние три года': 'последние 3 года', 'четыре или пять «да»': '4 или 5 «да»', 'С двадцать четвёртого года': 'С 2024 года', 'с восьми утра до десяти вечера': 'с 8:00 до 22:00', 'с девяти до восьми': 'с 9:00 до 20:00', 'десять тысяч на тридцать дней под ноль целых восемь десятых процента в день': '10 000 ₽ на 30 дней под 0,8% в день', 'двенадцать тысяч четыреста': '12 400 ₽', 'две тысячи четыреста': '2 400 ₽', 'Четыре месяца': '4 месяца', 'девять тысяч шестьсот': '9 600 ₽', 'пятьсот тысяч на пять лет под двадцать два процента годовых': '500 000 ₽ на 5 лет под 22% годовых', 'почти четырнадцать тысяч': 'почти 14 000 ₽', 'Шестьдесят месяцев': '60 месяцев', 'больше восьмисот двадцати восьми тысяч': 'больше 828 000 ₽', 'триста двадцать восемь тысяч': '328 000 ₽', 'с первого октября двадцать шестого года': 'с 1 октября 2026 года', 'полумиллиона': '500 000 ₽', 'Первый:': '1)', 'Второй:': '2)', 'Третий:': '3)', 'Четвёртый:': '4)', 'Пятый:': '5)'}
def clean(s):
    s = re.sub(r"\[[^\]]*\]\s*","",s).strip()
    for a,b in R.items(): s = s.replace(a,b)
    return s
S = {}
for d in ("bk1","f3"):
    for k,v in json.load(open(f"{d}/scripts.json")).items(): S[f"{d}-{k}"] = v["lines"]
def schedule(first):
    h,m = map(int, first.split(":")); out=[]
    for i in range(3): t=h*60+m+20*i; out.append(("10-18", f"{t//60:02d}:{t%60:02d}"))
    day, si = 19, 0
    while len(out) < len(ORDER):
        for s in SLOTS[si % len(SLOTS)]:
            out.append((f"10-{day:02d}", s))
        day += 1; si += 1
    return out[:len(ORDER)]
def p(lines): return "".join(f"<p>{l}</p>" for l in lines)
def build(INT, first):
    res=[]
    for key,(md,hm) in zip(ORDER, schedule(first)):
        L=S[key]; M,D=md.split("-"); h,mi=map(int,hm.split(":"))
        body=[clean(L[0]["say"]),""]+["• "+clean(x["say"]) for x in L[1:-1]]+["",
          "📌 Подходит ли вам банкротство — тест из 7 вопросов: "+SITE,
          "Бесплатная консультация юриста, без обещаний и гарантий.","",
          "Информация в ролике не является юридической консультацией. Условия зависят от вашей ситуации.","",
          "#банкротство #долги #кредиты #списатьдолги #shorts"]
        res.append({"integrationId":INT,"isPremium":False,"date":f"2026-{M}-{D}T{h-3:02d}:{mi:02d}:00Z","shortLink":False,"type":"schedule",
          "settings":[{"key":"title","value":TITLES[key]+" #shorts"},{"key":"type","value":"public"},{"key":"selfDeclaredMadeForKids","value":"no"},
                      {"key":"tags","value":[{"value":t,"label":t} for t in TAGS]}],
          "postsAndComments":[{"content":p(body),"attachments":[f"https://uploads.postiz.com/{MEDIA[key]}.mp4"]},
                              {"content":p(["📌 Тест: подходит ли вам банкротство → "+SITE,"Бесплатная консультация юриста"]),"attachments":[]}]})
    return res
if __name__=="__main__":
    INT,a,b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    first = sys.argv[4] if len(sys.argv)>4 else "21:00"
    print(json.dumps(build(INT,first)[a:b], ensure_ascii=False))
