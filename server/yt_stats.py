"""YouTube statistics for our channels (YouTube Data API v3 + YouTube Analytics API).

Secrets: /opt/carousel/yt.env (chmod 600): GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET (entered by the owner),
YT_<channelId>_REFRESH / YT_<channelId>_TITLE (written here after OAuth). Tokens are never returned.
OAuth redirect: https://<domain>/mcp/google/callback  (handled by app.py do_GET -> callback()).

Ops (via story [{"yt": op, ...}]):
  auth_url              -> link to open in the browser; pick the channel on Google's screen (repeat per channel)
  channels              -> connected channels (title, subscribers, videos)
  stats  channel|"all", [days=28], [limit=50] -> per-video metrics + CSV /f/yt/stats_<slug>.csv
  forget channel        -> remove a channel
Stats are collected automatically once a day (~07:10 MSK).
"""
import csv
import datetime
import json
import os
import re
import secrets
import sqlite3
import threading
import time
import urllib.parse
import urllib.request

ENV_FILE = os.environ.get("YT_ENV", "/opt/carousel/yt.env")
DB = "/var/lib/carousel/ig/yt.db"
MSK = datetime.timezone(datetime.timedelta(hours=3))
SCOPES = "https://www.googleapis.com/auth/youtube.readonly https://www.googleapis.com/auth/yt-analytics.readonly"
_files = {"dir": "/var/lib/carousel/files", "domain": "localhost"}
_states = {}
_lock = threading.Lock()
_log = print
_access = {}  # channel -> (token, expires)


def _env():
    d = {}
    try:
        for line in open(ENV_FILE):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                d[k.strip()] = v.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return d


def _write_env(d):
    tmp = ENV_FILE + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        for k, v in d.items():
            f.write(f"{k}={v}\n")
    os.replace(tmp, ENV_FILE)


def _redirect():
    return f"https://{_files['domain']}/mcp/google/callback"


def _http(url, data=None, headers=None, timeout=60):
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        txt = e.read().decode("utf-8", "replace")
        try:
            j = json.loads(txt)
            err = j.get("error")
            msg = err.get("message") if isinstance(err, dict) else f"{err}: {j.get('error_description', '')}"
        except Exception:
            msg = txt[:300]
        raise RuntimeError(f"HTTP {e.code} {msg}")


def _db():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    c = sqlite3.connect(DB, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("""create table if not exists yt_stats(channel text, video_id text, day text, title text, published text,
        data text, primary key(channel, video_id, day))""")
    c.execute("create table if not exists yt_channel(channel text, day text, data text, primary key(channel, day))")
    return c


# ------------------------------------------------------------------ oauth
def auth_url():
    e = _env()
    if not e.get("GOOGLE_CLIENT_ID") or not e.get("GOOGLE_CLIENT_SECRET"):
        raise ValueError("нет GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET в /opt/carousel/yt.env")
    st = secrets.token_urlsafe(16)
    _states[st] = time.time()
    q = {"client_id": e["GOOGLE_CLIENT_ID"], "redirect_uri": _redirect(), "response_type": "code",
         "scope": SCOPES, "access_type": "offline", "prompt": "consent select_account",
         "include_granted_scopes": "true", "state": st}
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(q)


def callback(query):
    """Called from app.py for GET /mcp/google/callback. Returns (status, html)."""
    q = urllib.parse.parse_qs(query)
    st = (q.get("state") or [""])[0]
    if st not in _states or time.time() - _states.pop(st) > 1800:
        return 400, "Ссылка устарела. Попросите новую ссылку подключения."
    if q.get("error"):
        return 400, "Google вернул ошибку: " + q["error"][0]
    code = (q.get("code") or [""])[0]
    e = _env()
    tok = _http("https://oauth2.googleapis.com/token", {
        "code": code, "client_id": e["GOOGLE_CLIENT_ID"], "client_secret": e["GOOGLE_CLIENT_SECRET"],
        "redirect_uri": _redirect(), "grant_type": "authorization_code"})
    if not tok.get("refresh_token"):
        return 400, "Google не выдал постоянный доступ. Откройте ссылку подключения ещё раз."
    ch = _http("https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true",
               headers={"Authorization": "Bearer " + tok["access_token"]})
    items = ch.get("items") or []
    if not items:
        return 400, "У выбранного аккаунта нет YouTube-канала. Откройте ссылку снова и выберите канал."
    cid, title = items[0]["id"], items[0]["snippet"]["title"]
    with _lock:
        e = _env()
        e[f"YT_{cid}_REFRESH"] = tok["refresh_token"]
        e[f"YT_{cid}_TITLE"] = title.replace("\n", " ")
        _write_env(e)
    _log("yt connected", title)
    return 200, f"Канал «{title}» подключён. Окно можно закрыть."


def _channels():
    e = _env()
    out = {}
    for k, v in e.items():
        m = re.match(r"YT_(.+)_REFRESH$", k)
        if m:
            out[m.group(1)] = {"refresh": v, "title": e.get(f"YT_{m.group(1)}_TITLE", m.group(1))}
    return out


def _token(cid):
    t = _access.get(cid)
    if t and t[1] > time.time() + 60:
        return t[0]
    e = _env()
    ch = _channels()[cid]
    r = _http("https://oauth2.googleapis.com/token", {
        "client_id": e["GOOGLE_CLIENT_ID"], "client_secret": e["GOOGLE_CLIENT_SECRET"],
        "refresh_token": ch["refresh"], "grant_type": "refresh_token"})
    _access[cid] = (r["access_token"], time.time() + int(r.get("expires_in", 3600)))
    return r["access_token"]


def _get(cid, url, params):
    return _http(url + "?" + urllib.parse.urlencode(params), headers={"Authorization": "Bearer " + _token(cid)})


def _find(name):
    chs = _channels()
    if name in chs:
        return name
    for cid, c in chs.items():
        if name.lower() in c["title"].lower():
            return cid
    raise ValueError(f"нет канала {name}")


def _slug(s):
    s = re.sub(r"[^a-zA-Zа-яА-Я0-9]+", "_", s).strip("_").lower()
    return s[:40] or "channel"


# ------------------------------------------------------------------ stats
def channel_stats(cid, days=28, limit=50):
    ch = _get(cid, "https://www.googleapis.com/youtube/v3/channels",
              {"part": "snippet,statistics,contentDetails", "id": cid})["items"][0]
    title = ch["snippet"]["title"]
    uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, page = [], None
    while len(ids) < limit:
        p = {"part": "contentDetails", "playlistId": uploads, "maxResults": 50}
        if page:
            p["pageToken"] = page
        try:
            r = _get(cid, "https://www.googleapis.com/youtube/v3/playlistItems", p)
        except RuntimeError as ex:
            if "404" in str(ex):
                break
            raise
        ids += [i["contentDetails"]["videoId"] for i in r.get("items", [])]
        page = r.get("nextPageToken")
        if not page:
            break
    ids = ids[:limit]
    vids = {}
    for i in range(0, len(ids), 50):
        r = _get(cid, "https://www.googleapis.com/youtube/v3/videos",
                 {"part": "snippet,statistics,contentDetails", "id": ",".join(ids[i:i + 50])})
        for v in r.get("items", []):
            s = v.get("statistics", {})
            vids[v["id"]] = {"title": v["snippet"]["title"][:80], "published": v["snippet"]["publishedAt"][:16],
                             "views": int(s.get("viewCount", 0)), "likes": int(s.get("likeCount", 0)),
                             "comments": int(s.get("commentCount", 0)), "url": f"https://youtu.be/{v['id']}"}
    end = datetime.date.today()
    start = end - datetime.timedelta(days=int(days))
    analytics_err = ""
    try:
        r = _get(cid, "https://youtubeanalytics.googleapis.com/v2/reports", {
            "ids": "channel==MINE", "startDate": start.isoformat(), "endDate": end.isoformat(),
            "metrics": "views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,likes,shares,subscribersGained",
            "dimensions": "video", "sort": "-views", "maxResults": "200"})
        cols = [h["name"] for h in r.get("columnHeaders", [])]
        for row in r.get("rows", []):
            d = dict(zip(cols, row))
            v = vids.setdefault(d["video"], {"title": "", "published": "", "url": f"https://youtu.be/{d['video']}"})
            v.update({"views_period": d.get("views"), "avg_view_sec": d.get("averageViewDuration"),
                      "avg_view_pct": round(d.get("averageViewPercentage") or 0, 1), "shares": d.get("shares"),
                      "subs_gained": d.get("subscribersGained"), "minutes": d.get("estimatedMinutesWatched")})
    except Exception as ex:
        analytics_err = str(ex)[:200]
    summary = {"title": title, "subscribers": int(ch["statistics"].get("subscriberCount", 0)),
               "videos": int(ch["statistics"].get("videoCount", 0)), "views_total": int(ch["statistics"].get("viewCount", 0))}
    day = datetime.datetime.now(MSK).strftime("%Y-%m-%d")
    with _lock, _db() as c:
        c.execute("insert or replace into yt_channel values(?,?,?)", (cid, day, json.dumps(summary)))
        for vid, v in vids.items():
            c.execute("insert or replace into yt_stats values(?,?,?,?,?,?)",
                      (cid, vid, day, v.get("title", ""), v.get("published", ""), json.dumps(v)))
    rows = sorted(vids.values(), key=lambda v: v.get("published", ""), reverse=True)
    d = os.path.join(_files["dir"], "yt")
    os.makedirs(d, exist_ok=True)
    slug = _slug(title)
    keys = ["published", "title", "views", "likes", "comments", "views_period", "avg_view_sec", "avg_view_pct",
            "shares", "subs_gained", "url"]
    with open(os.path.join(d, f"stats_{slug}.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(keys)
        for r_ in rows:
            w.writerow([r_.get(k, "") for k in keys])
    res = {**summary, "csv": f"https://{_files['domain']}/f/yt/stats_{slug}.csv", "videos_list": rows}
    if analytics_err:
        res["analytics_error"] = analytics_err
    return res


def collect_all():
    out = {}
    for cid, c in _channels().items():
        try:
            r = channel_stats(cid)
            out[c["title"]] = {k: r[k] for k in ("subscribers", "videos", "views_total")}
        except Exception as ex:
            out[c["title"]] = {"error": str(ex)[:200]}
    return out


def _loop():
    last = ""
    while True:
        try:
            now = datetime.datetime.now(MSK)
            day = now.strftime("%Y-%m-%d")
            if now.hour == 7 and now.minute >= 10 and day != last and _channels():
                last = day
                _log("yt stats", collect_all())
        except Exception as ex:
            _log("yt loop", str(ex)[:200])
        time.sleep(120)


def start(log, files_dir, domain):
    global _log
    _log = log
    _files.update(dir=files_dir, domain=domain)
    threading.Thread(target=_loop, daemon=True, name="yt-stats").start()


def op(a):
    o = a.get("yt")
    if o == "auth_url":
        return {"url": auth_url(), "redirect_uri": _redirect()}
    if o == "channels":
        out = []
        for cid, c in _channels().items():
            try:
                s = _get(cid, "https://www.googleapis.com/youtube/v3/channels", {"part": "statistics", "id": cid})["items"][0]["statistics"]
                out.append({"id": cid, "title": c["title"], "subscribers": s.get("subscriberCount"), "videos": s.get("videoCount")})
            except Exception as ex:
                out.append({"id": cid, "title": c["title"], "error": str(ex)[:200]})
        return out
    if o == "stats":
        ch = a.get("channel", "all")
        cids = list(_channels()) if ch == "all" else [_find(ch)]
        res = []
        for cid in cids:
            try:
                r = channel_stats(cid, int(a.get("days", 28)), int(a.get("limit", 50)))
                if not a.get("full"):
                    r["videos_list"] = r["videos_list"][:int(a.get("show", 10))]
                res.append(r)
            except Exception as ex:
                res.append({"channel": cid, "error": str(ex)[:300]})
        return res
    if o == "forget":
        cid = _find(a["channel"])
        with _lock:
            e = _env()
            e.pop(f"YT_{cid}_REFRESH", None)
            e.pop(f"YT_{cid}_TITLE", None)
            _write_env(e)
        return "ok"
    raise ValueError("yt: auth_url | channels | stats | forget")
