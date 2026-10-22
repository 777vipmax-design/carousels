"""Свой трекер позиций: Google (Search Console) + Яндекс (Вебмастер API v4).

Каждый день (~07:20 МСК) сохраняет по каждому сайту: день, запрос, страница (только Google), показы, клики, средняя позиция.
Таблица /var/lib/carousel/ig/seo.db -> pos(engine, site, day, query, page, clicks, impr, position).

Секреты — /opt/carousel/yt.env (600): YANDEX_CLIENT_ID, YANDEX_CLIENT_SECRET (вписывает владелец),
YA_TOKEN / YA_REFRESH / YA_EXPIRES (пишутся здесь после OAuth). Токены наружу не отдаются.
OAuth Яндекса: redirect https://<domain>/mcp/yandex/callback (app.py do_GET -> ya_callback()).

Ops (story [{"seo": op, ...}]):
  ya_auth_url                          -> ссылка «Разрешить» для Яндекса
  sites                                -> сайты в Google и Яндексе
  collect [days=4] [engine]            -> собрать сейчас (days=28 — история)
  report  [site] [engine] [days=7]     -> сравнение периода с предыдущим: рост/падение, почти топ, топ-3/10
"""
import csv
import datetime
import json
import os
import secrets
import sqlite3
import threading
import time
import urllib.parse
import urllib.request

import yt_stats

DB = "/var/lib/carousel/ig/seo.db"
MSK = datetime.timezone(datetime.timedelta(hours=3))
YA_API = "https://api.webmaster.yandex.net/v4"
_states = {}
_lock = threading.Lock()
_log = print
_files = yt_stats._files


def _db():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    c = sqlite3.connect(DB, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("""create table if not exists pos(engine text, site text, day text, query text, page text,
        clicks real, impr real, position real, primary key(engine, site, day, query, page))""")
    c.execute("create index if not exists pos_sd on pos(site, day)")
    return c


def _key(site):
    """Единое имя сайта для Google и Яндекса: домен в punycode без www."""
    s = site.lower().replace("sc-domain:", "").replace("https://", "").replace("http://", "")
    if s.startswith("https:") or s.startswith("http:"):  # яндексовый host_id https:domain:443
        s = s.split(":")[1]
    s = s.split("/")[0].split(":")[0]
    if s.startswith("www."):
        s = s[4:]
    return s


def _human(k):
    try:
        return k.encode().decode("idna")
    except Exception:
        return k


# ------------------------------------------------------------------ yandex oauth
def _ya_redirect():
    return f"https://{_files['domain']}/mcp/yandex/callback"


def _ya_client():
    e = yt_stats._env()
    for k in ("YANDEX_CLIENT_ID", "YANDEX_CLIENT_SECRET"):
        if not e.get(k) and os.environ.get(k):
            e[k] = os.environ[k]
    return e


def ya_auth_url():
    e = _ya_client()
    if not e.get("YANDEX_CLIENT_ID") or not e.get("YANDEX_CLIENT_SECRET"):
        raise ValueError("нет YANDEX_CLIENT_ID / YANDEX_CLIENT_SECRET (setenv.sh)")
    st = secrets.token_urlsafe(16)
    _states[st] = time.time()
    q = {"response_type": "code", "client_id": e["YANDEX_CLIENT_ID"], "redirect_uri": _ya_redirect(),
         "state": st, "force_confirm": "yes"}
    return "https://oauth.yandex.ru/authorize?" + urllib.parse.urlencode(q)


def _ya_token_req(data):
    e = _ya_client()
    data = {**data, "client_id": e["YANDEX_CLIENT_ID"], "client_secret": e["YANDEX_CLIENT_SECRET"]}
    return yt_stats._http("https://oauth.yandex.ru/token", data)


def _ya_save(tok):
    with yt_stats._lock:
        e = yt_stats._env()
        e["YA_TOKEN"] = tok["access_token"]
        if tok.get("refresh_token"):
            e["YA_REFRESH"] = tok["refresh_token"]
        e["YA_EXPIRES"] = str(int(time.time() + int(tok.get("expires_in", 31536000))))
        yt_stats._write_env(e)


def ya_callback(query):
    q = urllib.parse.parse_qs(query)
    st = (q.get("state") or [""])[0]
    t0 = _states.pop(st, None)
    if not t0 or time.time() - t0 > 1800:
        return 400, "Ссылка устарела. Попросите новую ссылку подключения."
    if q.get("error"):
        return 400, "Яндекс вернул ошибку: " + q["error"][0]
    tok = _ya_token_req({"grant_type": "authorization_code", "code": (q.get("code") or [""])[0]})
    if not tok.get("access_token"):
        return 400, "Яндекс не выдал доступ. Откройте ссылку ещё раз."
    _ya_save(tok)
    try:
        n = len(ya_hosts())
    except Exception as ex:  # noqa: BLE001
        return 200, f"Яндекс подключён, но сайты не прочитались: {str(ex)[:150]}"
    _log("yandex webmaster connected", n)
    return 200, f"Яндекс.Вебмастер подключён: сайтов — {n}. Окно можно закрыть."


def _ya_tok():
    e = yt_stats._env()
    if not e.get("YA_TOKEN"):
        raise ValueError("Яндекс.Вебмастер не подключён: нужна ссылка ya_auth_url")
    if e.get("YA_REFRESH") and int(e.get("YA_EXPIRES", "0")) - time.time() < 14 * 86400:
        try:
            _ya_save(_ya_token_req({"grant_type": "refresh_token", "refresh_token": e["YA_REFRESH"]}))
            e = yt_stats._env()
        except Exception as ex:  # noqa: BLE001
            _log("yandex refresh", str(ex)[:150])
    return e["YA_TOKEN"]


def _ya(path, params=None):
    url = YA_API + path
    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True)
    return yt_stats._http(url, headers={"Authorization": "OAuth " + _ya_tok()}, timeout=90)


_ya_uid = {}


def _uid():
    if "id" not in _ya_uid:
        _ya_uid["id"] = _ya("/user")["user_id"]
    return _ya_uid["id"]


def ya_hosts():
    hs = _ya(f"/user/{_uid()}/hosts").get("hosts", [])
    return [{"host_id": h["host_id"], "site": _key(h.get("ascii_host_url") or h["host_id"]),
             "verified": h.get("verified"), "url": h.get("unicode_host_url") or h.get("ascii_host_url")} for h in hs]


# ------------------------------------------------------------------ collect
def _gsc_day(site, day):
    enc = urllib.parse.quote(site, safe="")
    rows, start = [], 0
    while True:
        r = yt_stats._gsc("POST", f"/sites/{enc}/searchAnalytics/query", {
            "startDate": day, "endDate": day, "dimensions": ["query", "page"], "rowLimit": 25000,
            "startRow": start, "dataState": "all"})
        got = r.get("rows", [])
        rows += got
        if len(got) < 25000:
            return rows
        start += 25000


def collect_google(days=4):
    out = {}
    today = datetime.date.today()
    for s in yt_stats.gsc_sites():
        site = s["site"]
        k = _key(site)
        n = 0
        try:
            for i in range(1, int(days) + 1):
                day = (today - datetime.timedelta(days=i)).isoformat()
                rows = _gsc_day(site, day)
                with _lock, _db() as c:
                    c.execute("delete from pos where engine='google' and site=? and day=?", (k, day))
                    c.executemany("insert or replace into pos values('google',?,?,?,?,?,?,?)",
                                  [(k, day, x["keys"][0], x["keys"][1], x["clicks"], x["impressions"], x["position"])
                                   for x in rows])
                n += len(rows)
            out[k] = n
        except Exception as ex:  # noqa: BLE001
            out[k] = "ошибка: " + str(ex)[:120]
    return out


def collect_yandex(days=7):
    out = {}
    today = datetime.date.today()
    ind = ["TOTAL_SHOWS", "TOTAL_CLICKS", "AVG_SHOW_POSITION"]
    for h in ya_hosts():
        if not h.get("verified"):
            out[h["site"]] = "не подтверждён"
            continue
        hid = urllib.parse.quote(h["host_id"], safe="")
        n = 0
        try:
            for i in range(1, int(days) + 1):
                day = (today - datetime.timedelta(days=i)).isoformat()
                rows, off = [], 0
                while True:
                    r = _ya(f"/user/{_uid()}/hosts/{hid}/search-queries/popular", {
                        "order_by": "TOTAL_SHOWS", "query_indicator": ind, "date_from": day, "date_to": day,
                        "limit": 500, "offset": off})
                    q = r.get("queries", [])
                    rows += q
                    if len(q) < 500 or off >= 2500:
                        break
                    off += 500
                vals = []
                for x in rows:
                    d = x.get("indicators", {})
                    if not d.get("TOTAL_SHOWS"):
                        continue
                    vals.append((h["site"], day, x["query_text"], "", d.get("TOTAL_CLICKS") or 0,
                                 d.get("TOTAL_SHOWS") or 0, d.get("AVG_SHOW_POSITION") or 0))
                with _lock, _db() as c:
                    c.execute("delete from pos where engine='yandex' and site=? and day=?", (h["site"], day))
                    c.executemany("insert or replace into pos values('yandex',?,?,?,?,?,?,?)", vals)
                n += len(vals)
            out[h["site"]] = n
        except Exception as ex:  # noqa: BLE001
            out[h["site"]] = "ошибка: " + str(ex)[:120]
    return out


def collect(days=None, engine=None):
    res = {}
    if engine in (None, "google"):
        try:
            res["google"] = collect_google(days or 4)
        except Exception as ex:  # noqa: BLE001
            res["google"] = "ошибка: " + str(ex)[:150]
    if engine in (None, "yandex"):
        try:
            res["yandex"] = collect_yandex(days or 7)
        except Exception as ex:  # noqa: BLE001
            res["yandex"] = "ошибка: " + str(ex)[:150]
    return res


# ------------------------------------------------------------------ report
def _agg(c, engine, site, d0, d1):
    """По запросу за период: показы, клики, средняя позиция (взвешенная по показам), лучшая страница."""
    rows = c.execute("""select query, sum(impr) i, sum(clicks) cl, sum(position*impr)/sum(impr) p
        from pos where engine=? and site=? and day between ? and ? and impr>0 group by query""",
                     (engine, site, d0, d1)).fetchall()
    res = {r["query"]: {"impr": int(r["i"]), "clicks": int(r["cl"]), "pos": round(r["p"], 1)} for r in rows}
    if engine == "google":
        for r in c.execute("""select query, page, sum(impr) i from pos where engine=? and site=? and day between ? and ?
                group by query, page order by i""", (engine, site, d0, d1)):
            if r["query"] in res:
                res[r["query"]]["page"] = r["page"]
    return res


def _last_day(c, engine, site):
    r = c.execute("select max(day) d from pos where engine=? and site=? and impr>0", (engine, site)).fetchone()
    return r["d"]


def report(site=None, engine=None, days=7, show=10):
    days = int(days)
    out = []
    with _db() as c:
        pairs = c.execute("select distinct engine, site from pos").fetchall()
        for p in pairs:
            eng, s = p["engine"], p["site"]
            if engine and eng != engine:
                continue
            if site and _key(site) not in s and site.lower() not in _human(s).lower():
                continue
            last = _last_day(c, eng, s)
            if not last:
                continue
            l = datetime.date.fromisoformat(last)
            cur0, cur1 = (l - datetime.timedelta(days=days - 1)).isoformat(), last
            prv0 = (l - datetime.timedelta(days=2 * days - 1)).isoformat()
            prv1 = (l - datetime.timedelta(days=days)).isoformat()
            cur, prv = _agg(c, eng, s, cur0, cur1), _agg(c, eng, s, prv0, prv1)
            ti, tc = sum(v["impr"] for v in cur.values()), sum(v["clicks"] for v in cur.values())
            pi, pc = sum(v["impr"] for v in prv.values()), sum(v["clicks"] for v in prv.values())
            moves = []
            for q, v in cur.items():
                if q in prv and v["impr"] >= 3 and prv[q]["impr"] >= 3:
                    moves.append({"query": q, "was": prv[q]["pos"], "now": v["pos"], "impr": v["impr"],
                                  "delta": round(prv[q]["pos"] - v["pos"], 1)})
            up = sorted([m for m in moves if m["delta"] >= 1], key=lambda m: (-m["delta"] * m["impr"]))[:show]
            down = sorted([m for m in moves if m["delta"] <= -1], key=lambda m: (m["delta"] * m["impr"]))[:show]
            near = sorted([{"query": q, **v} for q, v in cur.items() if 3.5 < v["pos"] <= 20 and v["impr"] >= 5],
                          key=lambda x: -x["impr"])[:show]
            new = sorted([{"query": q, **v} for q, v in cur.items() if q not in prv],
                         key=lambda x: -x["impr"])[:show]
            out.append({
                "engine": eng, "site": _human(s), "period": f"{cur0}..{cur1}", "prev": f"{prv0}..{prv1}",
                "impr": ti, "impr_prev": pi, "clicks": tc, "clicks_prev": pc, "queries": len(cur),
                "top3": sum(1 for v in cur.values() if v["pos"] <= 3.5),
                "top10": sum(1 for v in cur.values() if v["pos"] <= 10.5),
                "top3_prev": sum(1 for v in prv.values() if v["pos"] <= 3.5),
                "top10_prev": sum(1 for v in prv.values() if v["pos"] <= 10.5),
                "up": up, "down": down, "near_top": near, "new": new})
            d = os.path.join(_files["dir"], "seo")
            os.makedirs(d, exist_ok=True)
            fn = f"pos_{eng}_{s.replace('.', '_')}.csv"
            with open(os.path.join(d, fn), "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(["query", "pos_now", "pos_prev", "impr_now", "impr_prev", "clicks_now", "page"])
                for q, v in sorted(cur.items(), key=lambda kv: -kv[1]["impr"]):
                    w.writerow([q, v["pos"], prv.get(q, {}).get("pos", ""), v["impr"], prv.get(q, {}).get("impr", ""),
                                v["clicks"], v.get("page", "")])
            out[-1]["csv"] = f"https://{_files['domain']}/f/seo/{fn}"
    out.sort(key=lambda x: -x["impr"])
    return out


def sites():
    res = {"google": [], "yandex": []}
    try:
        res["google"] = [_human(_key(s["site"])) for s in yt_stats.gsc_sites()]
    except Exception as ex:  # noqa: BLE001
        res["google"] = "ошибка: " + str(ex)[:120]
    try:
        res["yandex"] = [{"site": _human(h["site"]), "verified": h["verified"]} for h in ya_hosts()]
    except Exception as ex:  # noqa: BLE001
        res["yandex"] = str(ex)[:150]
    return res


# ------------------------------------------------------------------ yandex metrika
METRIKA = {"рассчитать-матрицу-судьбы.рф": 113592122, "zaymikredit.ru": 113659152, "записка-матроне.рф": 113591512,
           "sostavim-dogovor.ru": 113657171, "claudekurs.ru": 113657180, "bankrotstvo-fizicheskih-lits.ru": 113658803,
           "песни-ии.рф": 106821116, "оживить-фотографии.рф": 113592069, "rusifikaciya-avto.ru": 112126918,
           "za-rubezhom.ru": 113690451, "ии-ветеринар.рф": 113703144, "авто-из-азии.рф": 113703135,
           "оценка-внешности.рф": 113702617,
           "история-фамилии.рф": 113727398, "где-подработать.рф": 113727407}


def _mk(path, params, timeout=40):
    url = "https://api-metrika.yandex.net" + path + "?" + urllib.parse.urlencode(params, doseq=True)
    return yt_stats._http(url, headers={"Authorization": "OAuth " + _ya_tok()}, timeout=timeout)


def ya_ping():
    out = {}
    for name, fn in (("webmaster", lambda: _ya("/user")), ("metrika", lambda: _mk("/management/v1/counters", {"per_page": 1}, 20))):
        t = time.time()
        try:
            fn()
            out[name] = f"ok {time.time() - t:.1f}s"
        except Exception as ex:  # noqa: BLE001
            out[name] = f"ошибка {time.time() - t:.1f}s: {str(ex)[:150]}"
    return out


def counters():
    r = _mk("/management/v1/counters", {"per_page": 1000})
    return [{"id": c.get("id"), "site": c.get("site2", {}).get("site") or c.get("site"), "name": c.get("name")}
            for c in r.get("counters", [])]


def metrika(site=None, days=7):
    res = []
    for name, cid in METRIKA.items():
        if site and site.lower() not in name.lower():
            continue
        p = {"ids": cid, "date1": f"{int(days)}daysAgo", "date2": "today",
             "metrics": "ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:sumGoalReachesAny"}
        try:
            tot = _mk("/stat/v1/data", p).get("totals", [0, 0, 0, 0])
            src = _mk("/stat/v1/data", {**p, "metrics": "ym:s:visits", "dimensions": "ym:s:lastTrafficSource",
                                        "limit": 10}).get("data", [])
            eng = _mk("/stat/v1/data", {**p, "metrics": "ym:s:visits,ym:s:sumGoalReachesAny",
                                        "dimensions": "ym:s:lastSearchEngineRoot", "limit": 10}).get("data", [])
            res.append({"site": name, "counter": cid, "visits": int(tot[0]), "users": int(tot[1]),
                        "bounce": round(tot[2], 1), "goals": int(tot[3]),
                        "sources": {r["dimensions"][0]["name"]: int(r["metrics"][0]) for r in src},
                        "search_engines": {(r["dimensions"][0].get("name") or "?"): [int(r["metrics"][0]), int(r["metrics"][1])]
                                           for r in eng}})
        except Exception as ex:  # noqa: BLE001
            res.append({"site": name, "counter": cid, "error": str(ex)[:150]})
    return res


def op(a):
    o = a.get("seo")
    if o == "ya_auth_url":
        return {"url": ya_auth_url(), "redirect_uri": _ya_redirect()}
    if o == "sites":
        return sites()
    if o == "ya_ping":
        return ya_ping()
    if o == "counters":
        return counters()
    if o == "metrika":
        return metrika(a.get("site"), a.get("days", 7))
    if o == "collect":
        return collect(a.get("days"), a.get("engine"))
    if o == "report":
        return report(a.get("site"), a.get("engine"), a.get("days", 7), int(a.get("show", 10)))
    raise ValueError("seo: неизвестная операция " + str(o))


def _loop():
    last = ""
    while True:
        try:
            now = datetime.datetime.now(MSK)
            day = now.strftime("%Y-%m-%d")
            if now.hour == 7 and now.minute >= 20 and day != last:
                last = day
                _log("seo collect", json.dumps(collect(), ensure_ascii=False)[:300])
        except Exception as ex:  # noqa: BLE001
            _log("seo loop", str(ex)[:200])
        time.sleep(120)


def start(log):
    global _log
    _log = log
    threading.Thread(target=_loop, daemon=True, name="seo-pos").start()
