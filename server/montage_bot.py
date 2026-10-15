"""@avtomontazh_ai_bot — gifts for Instagram code words + warm-up (stdlib only, long polling in a thread).

Token: /opt/montage-bot/.env (BOT_TOKEN=...), written by the owner. Never logged.
Gifts: <repo>/content/gifts/<slug>.md ; deep link t.me/avtomontazh_ai_bot?start=<slug>
DB: /var/lib/carousel/bot/bot.db (NOT under the public files dir).
"""
import html
import json
import os
import re
import sqlite3
import threading
import time
import urllib.parse
import urllib.request

ENV = "/opt/montage-bot/.env"
DB_DIR = "/var/lib/carousel/bot"
REPO = os.environ.get("REPO_DIR", "/opt/carousel/repo")
GIFTS = {  # start payload / typed code word -> gift file
    "skilly": "skilly", "скиллы": "skilly", "скилы": "skilly",
    "ofis": "ofis", "офис": "ofis",
    "klod": "klod", "клод": "klod",
    "razbor": "razbor", "разбор": "razbor",
    "poisk": "poisk", "поиск": "poisk",
    "klienty": "klienty", "клиенты": "klienty",
    "montazh": "montazh", "монтаж": "montazh",
    "kod": "kod", "код": "kod",
    "sait": "sait", "сайт": "sait",
    "arena": "arena", "арена": "arena",
}
TITLES = {"skilly": "5 скиллов", "ofis": "ИИ-офис", "klod": "Instagram на ИИ", "razbor": "REA",
          "poisk": "find-skills", "klienty": "Клиенты",
          "montazh": "Автомонтаж", "kod": "Сайт без кода", "sait": "Живые сайты", "arena": "Команда из Claude"}
ROLES = [("blog", "📱 Блогер"), ("expert", "🎓 Эксперт"), ("biz", "💼 Бизнес"), ("try", "👀 Просто интересно")]
CFG_FILE = os.path.join(DB_DIR, "config.json")  # {"admin_id":..., "lesson_url":..., "mini_url":..., "course_url":...}

_state = {"running": False, "error": None, "username": None}


def _token():
    try:
        for line in open(ENV):
            if line.startswith("BOT_TOKEN="):
                return line.split("=", 1)[1].strip()
    except FileNotFoundError:
        return None


def _cfg():
    try:
        return json.load(open(CFG_FILE))
    except Exception:
        return {}


def _save_cfg(c):
    json.dump(c, open(CFG_FILE, "w"), ensure_ascii=False, indent=1)


def api(tok, method, **params):
    data = json.dumps(params).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{tok}/{method}", data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=70) as r:
        return json.loads(r.read().decode())


def db():
    os.makedirs(DB_DIR, exist_ok=True)
    c = sqlite3.connect(os.path.join(DB_DIR, "bot.db"))
    c.execute("""create table if not exists users(id integer primary key, username text, name text,
                 source text, role text, created integer, last integer, gifts text default '')""")
    c.execute("create table if not exists events(ts integer, uid integer, kind text, data text)")
    return c


def md_to_tg(md):
    """Small markdown -> Telegram HTML (headings, bold, quotes, code blocks, lists)."""
    out, code = [], None
    for line in md.splitlines():
        if line.startswith("```"):
            if code is None:
                code = []
            else:
                out.append("<pre>" + html.escape("\n".join(code)) + "</pre>")
                code = None
            continue
        if code is not None:
            code.append(line)
            continue
        s = html.escape(line)
        s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        if line.startswith("#"):
            s = "<b>" + html.escape(line.lstrip("# ").strip()) + "</b>"
        elif line.startswith("> "):
            s = "<blockquote>" + s[5:] + "</blockquote>"
        elif line.strip() == "---":
            s = ""
        out.append(s)
    txt = "\n".join(out)
    txt = re.sub(r"</blockquote>\n<blockquote>", "\n", txt)
    return re.sub(r"\n{3,}", "\n\n", txt).strip()


def gift_text(slug):
    p = os.path.join(REPO, "content", "gifts", slug + ".md")
    md = open(p, encoding="utf-8").read()
    # the bridge line with the bot link placeholder is replaced by a button
    md = "\n".join(l for l in md.splitlines() if "[ссылка на бота]" not in l and not l.startswith("Кстати, ролик"))
    return md_to_tg(md)


def chunks(txt, n=3900):
    parts, cur = [], ""
    for para in txt.split("\n\n"):
        if len(cur) + len(para) + 2 > n and cur:
            parts.append(cur)
            cur = ""
        cur = (cur + "\n\n" + para) if cur else para
    if cur:
        parts.append(cur)
    return parts


def send(tok, chat, text, kb=None):
    for i, part in enumerate(chunks(text)):
        p = {"chat_id": chat, "text": part, "parse_mode": "HTML", "disable_web_page_preview": True}
        if kb and i == len(chunks(text)) - 1:
            p["reply_markup"] = {"inline_keyboard": kb}
        api(tok, "sendMessage", **p)


def lesson_kb():
    c = _cfg()
    if c.get("lesson_url"):
        return [[{"text": "🎬 Бесплатный урок по автомонтажу", "url": c["lesson_url"]}]]
    return [[{"text": "🎬 Хочу урок по автомонтажу", "callback_data": "lesson"}]]


def give(tok, con, uid, slug):
    send(tok, uid, gift_text(slug))
    row = con.execute("select gifts, role from users where id=?", (uid,)).fetchone()
    gifts = set((row[0] or "").split(",")) - {""} if row else set()
    gifts.add(slug)
    con.execute("update users set gifts=?, last=? where id=?", (",".join(sorted(gifts)), int(time.time()), uid))
    con.execute("insert into events values(?,?,?,?)", (int(time.time()), uid, "gift", slug))
    con.commit()
    bridge = ("Кстати, ролик, из которого ты пришёл, не монтировал человек: озвучку, анимации, субтитры "
              "и звуки собрал код вместе с Claude. Хочешь так же?")
    if row and row[1]:
        send(tok, uid, bridge, lesson_kb())
    else:
        send(tok, uid, bridge + "\n\nЧтобы прислать примеры под тебя — скажи, кто ты:",
             [[{"text": t, "callback_data": "role:" + k}] for k, t in ROLES])


def menu_text():
    return ("Привет! Я бот Руслана 👋\n\nЗдесь лежат подарки из рилсов. Напиши кодовое слово из ролика "
            "(например, <b>СКИЛЛЫ</b>) — и я сразу пришлю материал.")


def _remember_chat(ch):
    if ch and ch.get("type") == "channel":
        c = _cfg()
        chans = c.get("channels", {})
        chans[str(ch["id"])] = ch.get("title")
        c["channels"] = chans
        _save_cfg(c)


def handle(tok, con, upd):
    now = int(time.time())
    if "channel_post" in upd:
        _remember_chat(upd["channel_post"].get("chat"))
        return
    if "my_chat_member" in upd:
        _remember_chat(upd["my_chat_member"].get("chat"))
        return
    if "callback_query" in upd:
        q = upd["callback_query"]
        uid, data = q["from"]["id"], q.get("data", "")
        api(tok, "answerCallbackQuery", callback_query_id=q["id"])
        if data.startswith("role:"):
            con.execute("update users set role=?, last=? where id=?", (data[5:], now, uid))
            con.execute("insert into events values(?,?,?,?)", (now, uid, "role", data[5:]))
            con.commit()
            send(tok, uid, "Принял 👌 Буду присылать примеры под тебя.", lesson_kb())
        elif data == "lesson":
            con.execute("insert into events values(?,?,?,?)", (now, uid, "lesson_wait", ""))
            con.commit()
            send(tok, uid, "Записал тебя 🙌 Бесплатный урок по автомонтажу выйдет совсем скоро — пришлю сюда первым.")
        return
    m = upd.get("message")
    if not m:
        return
    if m.get("forward_from_chat"):
        _remember_chat(m["forward_from_chat"])
    fo = m.get("forward_origin") or {}
    if fo.get("type") == "channel":
        _remember_chat(fo.get("chat"))
        send(tok, m["chat"]["id"], "Канал запомнил ✅")
        return
    if "text" not in m:
        return
    uid, txt = m["from"]["id"], m["text"].strip()
    u = m["from"]
    if not con.execute("select 1 from users where id=?", (uid,)).fetchone():
        con.execute("insert into users(id,username,name,source,created,last) values(?,?,?,?,?,?)",
                    (uid, u.get("username"), u.get("first_name"), "", now, now))
        con.commit()
    if txt.startswith("/start"):
        payload = txt[6:].strip().lower()
        con.execute("update users set source=coalesce(nullif(source,''),?) where id=?", (payload or "direct", uid))
        con.commit()
        if payload in GIFTS:
            give(tok, con, uid, GIFTS[payload])
        else:
            send(tok, uid, menu_text())
        return
    c = _cfg()
    if txt.startswith("/claim_admin") and not c.get("admin_id"):
        c["admin_id"] = uid
        _save_cfg(c)
        send(tok, uid, "Ты админ бота ✅ Команды: /stats")
        return
    if txt == "/stats" and c.get("admin_id") == uid:
        n = con.execute("select count(*) from users").fetchone()[0]
        by = con.execute("select source, count(*) from users group by source order by 2 desc").fetchall()
        rl = con.execute("select role, count(*) from users group by role").fetchall()
        lw = con.execute("select count(distinct uid) from events where kind='lesson_wait'").fetchone()[0]
        send(tok, uid, f"<b>Всего:</b> {n}\n<b>Источники:</b> " + ", ".join(f"{a or '—'}: {b}" for a, b in by) +
             "\n<b>Кто:</b> " + ", ".join(f"{a or '—'}: {b}" for a, b in rl) + f"\n<b>Ждут урок:</b> {lw}")
        return
    key = re.sub(r"[^a-zа-яё]", "", txt.lower())
    if key in GIFTS:
        give(tok, con, uid, GIFTS[key])
    else:
        send(tok, uid, menu_text())


def loop(log):
    tok = _token()
    if not tok:
        _state["error"] = "no token"
        return
    con = db()
    try:
        me = api(tok, "getMe")
        _state["username"] = me["result"]["username"]
        api(tok, "setMyCommands", commands=[{"command": "start", "description": "Начать"}])
    except Exception as e:
        _state["error"] = "getMe: " + type(e).__name__
        return
    _state["running"] = True
    off = 0
    while True:
        try:
            r = api(tok, "getUpdates", offset=off, timeout=50, allowed_updates=["message", "callback_query", "channel_post", "my_chat_member"])
            for upd in r.get("result", []):
                off = upd["update_id"] + 1
                try:
                    handle(tok, con, upd)
                except Exception as e:
                    log("bot handle error", type(e).__name__, str(e)[:200])
            _state["error"] = None
        except Exception as e:
            _state["error"] = type(e).__name__
            time.sleep(5)


def start(log):
    if _token() and not _state["running"]:
        threading.Thread(target=loop, args=(log,), daemon=True).start()


def status():
    out = dict(_state)
    try:
        con = db()
        out["users"] = con.execute("select count(*) from users").fetchone()[0]
        out["by_source"] = dict(con.execute("select source, count(*) from users group by source").fetchall())
    except Exception as e:
        out["db_error"] = str(e)[:100]
    c = _cfg()
    out["admin_set"] = bool(c.get("admin_id"))
    out["lesson_url"] = c.get("lesson_url")
    out["channels"] = c.get("channels", {})
    return out


def set_cfg(**kw):
    c = _cfg()
    for k, v in kw.items():
        if k in ("lesson_url", "mini_url", "course_url") and v:
            c[k] = v
    _save_cfg(c)
    return {k: c.get(k) for k in ("lesson_url", "mini_url", "course_url")}


def _multipart(fields, files):
    bnd = "----bot" + str(int(time.time() * 1000))
    body = b""
    for k, v in fields.items():
        body += f"--{bnd}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    for k, (name, data, ctype) in files.items():
        body += (f"--{bnd}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{name}\"\r\n"
                 f"Content-Type: {ctype}\r\n\r\n").encode() + data + b"\r\n"
    return body + f"--{bnd}--\r\n".encode(), "multipart/form-data; boundary=" + bnd


def api_file(tok, method, fields, files):
    body, ct = _multipart(fields, files)
    req = urllib.request.Request(f"https://api.telegram.org/bot{tok}/{method}", data=body, headers={"Content-Type": ct})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def admin(action, get_bytes):
    """action dict: {"op": "describe", "description":..., "short":...}
    {"op": "channel_photo", "url":...} {"op": "channel_desc", "text":...}
    {"op": "post", "html":..., "pin": bool, "photo_url": optional}  (channel = only known channel)"""
    tok = _token()
    c = _cfg()
    chans = list(c.get("channels", {}).keys())
    op = action.get("op")
    if op == "describe":
        out = {}
        if action.get("description"):
            out["d"] = api(tok, "setMyDescription", description=action["description"])["ok"]
        if action.get("short"):
            out["s"] = api(tok, "setMyShortDescription", short_description=action["short"])["ok"]
        if action.get("name"):
            out["n"] = api(tok, "setMyName", name=action["name"])["ok"]
        return out
    if not chans:
        return {"error": "канал неизвестен: опубликуй любое сообщение в канале (бот должен быть админом)"}
    ch = action.get("chat_id") or chans[0]
    if op == "channel_photo":
        data = get_bytes(action["url"])
        return api_file(tok, "setChatPhoto", {"chat_id": ch}, {"photo": ("p.png", data, "image/png")})
    if op == "channel_desc":
        return api(tok, "setChatDescription", chat_id=ch, description=action["text"])
    if op == "post":
        if action.get("photo_url"):
            data = get_bytes(action["photo_url"])
            r = api_file(tok, "sendPhoto", {"chat_id": ch, "caption": action["html"], "parse_mode": "HTML"},
                         {"photo": ("p.png", data, "image/png")})
        else:
            r = api(tok, "sendMessage", chat_id=ch, text=action["html"], parse_mode="HTML",
                    disable_web_page_preview=True)
        mid = r.get("result", {}).get("message_id")
        if action.get("pin") and mid:
            api(tok, "pinChatMessage", chat_id=ch, message_id=mid, disable_notification=True)
        return {"ok": r.get("ok"), "message_id": mid}
    if op == "md":  # photo (caption) + full text of a repo markdown file
        ids = {}
        if action.get("photo_url"):
            r = api_file(tok, "sendPhoto", {"chat_id": ch, "caption": action.get("caption", ""), "parse_mode": "HTML"},
                         {"photo": ("p.png", get_bytes(action["photo_url"]), "image/png")})
            ids["photo"] = r.get("result", {}).get("message_id")
        md = open(os.path.join(REPO, action["path"]), encoding="utf-8").read()
        ids["text"] = []
        for part in chunks(md_to_tg(md)):
            r = api(tok, "sendMessage", chat_id=ch, text=part, parse_mode="HTML", disable_web_page_preview=True)
            ids["text"].append(r.get("result", {}).get("message_id"))
        return ids
    if op == "doc":
        data = get_bytes(action["url"])
        r = api_file(tok, "sendDocument", {"chat_id": ch, "caption": action.get("caption", ""), "parse_mode": "HTML"},
                     {"document": (action.get("filename", "file.zip"), data, "application/octet-stream")})
        return {"ok": r.get("ok"), "message_id": r.get("result", {}).get("message_id")}
    if op == "edit":
        r = api(tok, "editMessageText" if not action.get("caption") else "editMessageCaption", chat_id=ch,
                message_id=int(action["message_id"]), parse_mode="HTML",
                **({"caption": action["html"]} if action.get("caption") else {"text": action["html"], "disable_web_page_preview": True}))
        return {"ok": r.get("ok")}
    if op == "delete":
        return api(tok, "deleteMessage", chat_id=ch, message_id=int(action["message_id"]))
    return {"error": "unknown op"}
