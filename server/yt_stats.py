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
GSC_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"


def auth_url(kind="yt"):
    e = _env()
    if not e.get("GOOGLE_CLIENT_ID") or not e.get("GOOGLE_CLIENT_SECRET"):
        raise ValueError("нет GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET в /opt/carousel/yt.env")
    st = secrets.token_urlsafe(16)
    _states[st] = (time.time(), kind)
    q = {"client_id": e["GOOGLE_CLIENT_ID"], "redirect_uri": _redirect(), "response_type": "code",
         "scope": GSC_SCOPE if kind == "gsc" else SCOPES, "access_type": "offline", "prompt": "consent select_account",
         "include_granted_scopes": "true", "state": st}
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(q)


def callback(query):
    """Called from app.py for GET /mcp/google/callback. Returns (status, html)."""
    q = urllib.parse.parse_qs(query)
    st = (q.get("state") or [""])[0]
    if st not in _states:
        return 400, "Ссылка устарела. Попросите новую ссылку подключения."
    t0, kind = _states.pop(st)
    if time.time() - t0 > 1800:
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
    if kind == "gsc":
        sites = _http("https://www.googleapis.com/webmasters/v3/sites",
                      headers={"Authorization": "Bearer " + tok["access_token"]}).get("siteEntry", [])
        with _lock:
            e = _env()
            e["GSC_REFRESH"] = tok["refresh_token"]
            _write_env(e)
        _log("gsc connected", len(sites))
        return 200, f"Search Console подключён: сайтов в доступе — {len(sites)}. Окно можно закрыть."
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
    refresh = e.get("GSC_REFRESH") if cid == "__gsc__" else _channels()[cid]["refresh"]
    if not refresh:
        raise ValueError("Search Console не подключён: нужна ссылка gsc_auth_url")
    r = _http("https://oauth2.googleapis.com/token", {
        "client_id": e["GOOGLE_CLIENT_ID"], "client_secret": e["GOOGLE_CLIENT_SECRET"],
        "refresh_token": refresh, "grant_type": "refresh_token"})
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


# ------------------------------------------------------------------ search console
def _gsc(method, path, body=None):
    url = "https://www.googleapis.com/webmasters/v3" + path if not path.startswith("http") else path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + _token("__gsc__"), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} {e.read().decode('utf-8', 'replace')[:300]}")


def gsc_sites():
    return [{"site": x["siteUrl"], "level": x.get("permissionLevel")} for x in _gsc("GET", "/sites").get("siteEntry", [])]


def _site(name):
    sites = [x["site"] for x in gsc_sites()]
    if name in sites:
        return name
    n = name.lower().replace("https://", "").replace("http://", "").strip("/")
    try:
        n_idna = n.encode("idna").decode()
    except Exception:
        n_idna = n
    for s_ in sites:
        if n in s_.lower() or n_idna in s_.lower():
            return s_
    raise ValueError(f"нет сайта {name} в Search Console (доступны: {', '.join(sites)})")


def gsc_report(site, days=28, dims=("query",), limit=50, page_filter=None):
    site = _site(site)
    end = datetime.date.today() - datetime.timedelta(days=2)  # GSC data lags ~2 days
    start = end - datetime.timedelta(days=int(days) - 1)
    body = {"startDate": start.isoformat(), "endDate": end.isoformat(), "dimensions": list(dims),
            "rowLimit": int(limit), "dataState": "final"}
    if page_filter:
        body["dimensionFilterGroups"] = [{"filters": [{"dimension": "page", "operator": "contains", "expression": page_filter}]}]
    enc = urllib.parse.quote(site, safe="")
    r = _gsc("POST", f"/sites/{enc}/searchAnalytics/query", body)
    rows = [{**dict(zip(dims, x["keys"])), "clicks": x["clicks"], "impressions": x["impressions"],
             "ctr": round(x["ctr"] * 100, 2), "position": round(x["position"], 1)} for x in r.get("rows", [])]
    tot = _gsc("POST", f"/sites/{enc}/searchAnalytics/query", {k: v for k, v in body.items() if k != "dimensions"} | {"rowLimit": 1})
    t = (tot.get("rows") or [{}])[0]
    summary = {"site": site, "period": f"{start}..{end}", "clicks": t.get("clicks", 0), "impressions": t.get("impressions", 0),
               "ctr": round(t.get("ctr", 0) * 100, 2), "position": round(t.get("position", 0), 1)}
    d = os.path.join(_files["dir"], "gsc")
    os.makedirs(d, exist_ok=True)
    slug = _slug(site.replace("sc-domain:", "").replace("https://", "")) + "_" + "_".join(dims)
    with open(os.path.join(d, f"{slug}.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        keys = list(dims) + ["clicks", "impressions", "ctr", "position"]
        w.writerow(keys)
        for r_ in rows:
            w.writerow([r_.get(k, "") for k in keys])
    return {"summary": summary, "rows": rows, "csv": f"https://{_files['domain']}/f/gsc/{slug}.csv"}


def gsc_sitemaps(site):
    site = _site(site)
    r = _gsc("GET", f"/sites/{urllib.parse.quote(site, safe='')}/sitemaps")
    return [{"path": x.get("path"), "submitted": x.get("lastSubmitted", "")[:10], "downloaded": x.get("lastDownloaded", "")[:10],
             "errors": x.get("errors"), "warnings": x.get("warnings"),
             "urls": [(c.get("type"), c.get("submitted"), c.get("indexed")) for c in x.get("contents", [])]}
            for x in r.get("sitemap", [])]


def gsc_inspect(site, url):
    site = _site(site)
    r = _gsc("POST", "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect",
             {"inspectionUrl": url, "siteUrl": site, "languageCode": "ru"})
    ir = r.get("inspectionResult", {}).get("indexStatusResult", {})
    return {k: ir.get(k) for k in ("verdict", "coverageState", "indexingState", "lastCrawlTime", "pageFetchState",
                                   "googleCanonical", "userCanonical", "robotsTxtState")}


def op(a):
    o = a.get("yt")
    if o == "gsc_auth_url":
        return {"url": auth_url("gsc")}
    if o == "gsc_sites":
        return gsc_sites()
    if o == "gsc":
        dims = a.get("dims") or ["query"]
        return gsc_report(a["site"], int(a.get("days", 28)), tuple(dims), int(a.get("limit", 50)), a.get("page"))
    if o == "gsc_sitemaps":
        return gsc_sitemaps(a["site"])
    if o == "gsc_inspect":
        return gsc_inspect(a["site"], a["url"])
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
    raise ValueError("yt: auth_url | channels | stats | forget | gsc_auth_url | gsc_sites | gsc | gsc_sitemaps | gsc_inspect")
