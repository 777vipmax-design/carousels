"""Build YouTube texts (title, description, comment) for the «Нейро на практике» shorts plan."""
import json, re, os

M = os.path.dirname(os.path.abspath(__file__))
G = os.path.join(M, "../../content/gifts")
BASE = "https://72-56-19-35.sslip.io/f"
BOT = "avtomontazh_ai_bot"

SCR = {}
for b, f in [("b1", "b1/scripts.json"), ("b2", "b2_scripts.json"), ("b3", "b3_scripts.json"),
             ("b4", "b4_scripts.json"), ("b5", "b5_scripts.json")]:
    for k, v in json.load(open(os.path.join(M, f))).items():
        SCR[f"{b}-{k}"] = v

FL = {
    "fl-rea": ("razbor", "РАЗБОР", "Этот ИИ разберёт на запчасти любую программу",
               ["Это REA — один из самых популярных проектов на GitHub, больше ста тысяч звёзд",
                "Даёшь ему приложение, сайт или файл — и спрашиваешь простыми словами, как это работает",
                "Он сам находит нужный кусок кода и показывает доказательства",
                "А потом может собрать такую же функцию в твоём проекте",
                "Работает с Claude Code и другими агентами. Бесплатно, открытый код",
                "По-честному: разбирай то, что твоё, или на что есть разрешение"]),
    "fl-find": ("poisk", "ПОИСК", "Скилл, который сам находит тебе нужный скилл",
                ["Скиллов для Claude уже тысячи — искать вручную долго",
                 "find-skills делает это за тебя: пишешь задачу обычными словами",
                 "Он ищет по каталогу, смотрит рейтинг и установки и предлагает лучший",
                 "И сразу ставит его одной командой",
                 "У него уже почти четыре миллиона установок"]),
    "fl-clients": ("klienty", "КЛИЕНТЫ", "Claude находит клиентов и пишет каждому личное предложение",
                   ["Говоришь: найди 20 компаний моей ниши в моём городе",
                    "Он изучает каждую: сайт, отзывы, соцсети",
                    "Находит, чего им не хватает",
                    "И пишет каждому предложение — не шаблон, а с конкретикой про их бизнес",
                    "Тебе остаётся проверить и отправить. Без спама — только тем, кому это правда нужно"]),
}
FACE = {"fl-face-v2": ("montazh", "МОНТАЖ", 2), "fl-face-v4": ("kod", "КОД", 4),
        "fl-face-v5": ("sait", "САЙТ", 5), "fl-face-v6": ("arena", "АРЕНА", 6)}
TITLES = {
    "fl-rea": "Этот ИИ разберёт любую программу на запчасти",
    "fl-find": "Скилл, который сам находит нужный скилл для Claude",
    "fl-clients": "Claude сам находит клиентов и пишет им предложения",
    "fl-face-v2": "Этот ролик смонтировал ИИ — я не открывал ни одной программы",
    "fl-face-v4": "Я не программист, но сделал сайт за 1 день с Claude",
    "fl-face-v5": "Сайт, который смотрит на тебя — сделал за 5 минут с Claude",
    "fl-face-v6": "Один запрос — целая команда из Claude: субагенты",
    "b1-limit": "Почему у тебя быстро сгорает лимит Claude: 5 привычек",
    "b1-dogovor": "Перед подписью договора я отдаю его Claude — вот что он находит",
    "b1-golos": "Надиктовал кашу из задач — Claude сделал план на день",
    "b1-novichok": "5 ошибок, из-за которых Claude отвечает плохо",
    "b1-konkurent": "Claude сам собирает цены конкурентов в таблицу",
    "b2-kak": "В какой программе я монтирую эти ролики? Ни в какой",
    "b2-skill": "Что такое скиллы Claude — простыми словами",
    "b2-vybor": "Claude или ChatGPT: что выбираю я и для чего",
    "b2-mcp": "Что такое MCP — за 30 секунд без сложных слов",
    "b3-obzor": "Весь Claude за 40 секунд — сохрани",
    "b3-tarif": "Какой тариф Claude брать, чтобы не переплачивать",
    "b3-schet": "Один забытый ключ — и счёт на сотни тысяч. Как защититься",
    "b3-kritik": "Попросил Claude оценить стартап «приложение-фонарик»",
    "b4-scenariy": "Почему твои рилсы листают на первой секунде — и как это исправить",
    "b5-terminal": "Claude Code без чёрного окна терминала",
    "b5-agent": "Чем ИИ-агент отличается от чата — на пальцах",
    "b5-skrin": "Непонятная ошибка на экране? Просто сфотографируй и отправь Claude",
}
WORDS = {"kak": "КАК", "vybor": "ВЫБОР", "skill": "СКИЛЛ", "mcp": "MCP", "obzor": "ОБЗОР", "tarif": "ТАРИФ",
         "schet": "СЧЁТ", "kritik": "КРИТИК", "scenariy": "СЦЕНАРИЙ", "terminal": "ТЕРМИНАЛ", "agent": "АГЕНТ", "skrin": "СКРИН"}
PLAN = [  # order of publication
    "fl-rea", "fl-clients", "fl-find",
    "fl-face-v2", "b1-limit", "b2-vybor",
    "fl-face-v6", "b3-obzor", "b1-dogovor",
    "fl-face-v4", "b2-kak", "b5-terminal",
    "b1-golos", "b3-tarif", "fl-face-v5",
    "b2-skill", "b1-novichok", "b5-agent",
    "b3-schet", "b1-konkurent", "b2-mcp",
    "b4-scenariy", "b3-kritik", "b5-skrin",
]


def gift_title(slug):
    t = open(os.path.join(G, slug + ".md")).readline().strip("# \n")
    return t


def clean(s):
    s = re.sub(r"\[[^\]]+\]", "", s).strip()
    return re.sub(r"\s+", " ", s)


def face_lines(n):
    src = open(os.path.join(M, f"plans/plan_v{n}.py")).read()
    return [m.group(1) for m in re.finditer(r'\(\s*[\d.]+,\s*[\d.]+,\s*"([^"]+)"', src)]


def item(key):
    if key in FL:
        slug, word, hook, pts = FL[key]
        url = f"{BASE}/{key}/reel_music.mp4"
    elif key in FACE:
        slug, word, n = FACE[key]
        ls = face_lines(n)
        merged = []
        for l in ls:
            if merged and (l[:1].islower() or len(merged[-1]) < 25):
                merged[-1] = merged[-1].rstrip(" —") + (" — " if l[:1].isupper() else " ") + l
            else:
                merged.append(l)
        hook, pts = merged[0], [l for l in merged[1:] if not re.search(r"напиши|комментар|хочешь|пришлю", l, re.I)]
        url = f"{BASE}/{key}/reel_music.mp4"
    else:
        s = SCR[key]
        slug = key.split("-", 1)[1]
        word = s.get("word") or WORDS[slug]
        lines = [clean(l["say"]) for l in s["lines"]]
        hook = lines[0]
        pts = [l for l in lines[1:] if not re.search(r"напиши|комментар|сохрани", l, re.I)]
        url = f"{BASE}/{key}/reel_music.mp4"
    gt = gift_title(slug)
    title = TITLES[key]
    if len(title) + 8 <= 100:
        title += " #shorts"
    body = [hook, ""]
    body += [f"• {p.rstrip('.')}" for p in pts]
    body += ["", f"🎁 {gt} — забери бесплатно: найди в тг бота {BOT} и напиши ему слово {word}",
             "", "Подписывайся — каждый день показываю, как Claude делает реальную работу за тебя.",
             "", "#claude #нейросети #ии #claudecode #shorts"]
    desc = "\n".join(body)
    comment = f"🎁 {gt}\nНайди в тг бота {BOT} и напиши ему слово {word} — пришлёт бесплатно"
    tags = ["claude", "claude ai", "нейросети", "ии", "искусственный интеллект", "claude code", "нейросеть для работы"]
    return {"key": key, "url": url, "title": title, "desc": desc, "comment": comment, "tags": tags, "word": word}


if __name__ == "__main__":
    out = [item(k) for k in PLAN]
    json.dump(out, open(os.path.join(M, "yt_neiro_plan.json"), "w"), ensure_ascii=False, indent=1)
    for o in out:
        print(o["key"], len(o["title"]), len(o["desc"]), "|", o["title"])
    print(out[3]["desc"])
