"""Own Instagram publisher (Instagram API with Instagram Login) — replaces Postiz.

Secrets: /opt/carousel/ig.env (chmod 600): META_APP_ID, META_APP_SECRET, IG_<acc>_ID, IG_<acc>_TOKEN.
Tokens are never returned by any function here.
Queue: /var/lib/carousel/ig/ig.db. Worker thread publishes due posts, refreshes tokens every ~20 days.

Ops (via story [{"ig": op, ...}]):
  accounts                       -> list accounts (username check through /me)
  schedule  account, kind (reel|image|carousel), media [urls], caption, at (ISO, MSK if no tz; "now"),
            trial (bool, reels only), share_to_feed (bool, default true), cover (url, reel cover), thumb_offset (ms)
  list      [account], [limit]
  cancel    id
  retry     id
"""
import datetime
import json
import os
import sqlite3
import subprocess
import threading
import time
import urllib.parse
import urllib.request

ENV_FILE = os.environ.get("IG_ENV", "/opt/carousel/ig.env")
DB_DIR = "/var/lib/carousel/ig"
DB = os.path.join(DB_DIR, "ig.db")
API = "https://graph.instagram.com/v23.0"
MSK = datetime.timezone(datetime.timedelta(hours=3))
REFRESH_DAYS = 20
_lock = threading.Lock()
_log = print
_files = {"dir": "/var/lib/carousel/files", "domain": "localhost"}
ALIAS = {"zina": "babazina_rocknroll", "foto": "foto_ozhivayut", "ozhiv": "foto_ozhivayut", "alina": "alina_poyot",
         "lyuba": "matrica_ot_lyuby", "main": "vip_malakh", "malakh": "vip_malakh"}


# ------------------------------------------------------------------ env / tokens
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
    os.chmod(tmp, 0o600)
    os.replace(tmp, ENV_FILE)


def accounts_raw():
    e = _env()
    accs = {}
    for k, v in e.items():
        if k.startswith("IG_") and k.endswith("_TOKEN"):
            name = k[3:-6].lower()
            accs[name] = {"id": e.get(f"IG_{name.upper()}_ID", ""), "token": v}
    return accs


def _acc(name):
    name = ALIAS.get(name.lower(), name.lower()).replace(".", "_")
    a = accounts_raw().get(name)
    if not a:
        raise ValueError(f"нет аккаунта {name}")
    return name, a


def _scrub(s, tok):
    return str(s).replace(tok, "***") if tok else str(s)


# ------------------------------------------------------------------ http
def _call(method, path, tok, params=None, timeout=120):
    params = dict(params or {})
    params["access_token"] = tok
    url = path if path.startswith("http") else API + path
    data = None
    if method == "GET":
        url += "?" + urllib.parse.urlencode(params)
    else:
        data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method=method, headers={"User-Agent": "carousel-ig"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            err = json.loads(body).get("error", {})
            msg = f"{err.get('code')}/{err.get('error_subcode')}: {err.get('error_user_msg') or err.get('message')}"
        except Exception:
            msg = body[:300]
        raise RuntimeError(_scrub(f"HTTP {e.code} {msg}", tok))


# ------------------------------------------------------------------ db
def _db():
    os.makedirs(DB_DIR, exist_ok=True)
    c = sqlite3.connect(DB, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("""create table if not exists posts(
        id integer primary key, account text, kind text, media text, caption text, opts text,
        publish_at integer, status text, container text, media_id text, permalink text, error text,
        created integer, updated integer)""")
    c.execute("create table if not exists tokens(account text primary key, refreshed integer)")
    return c


def _row(r):
    d = dict(r)
    d["media"] = json.loads(d["media"] or "[]")
    d["opts"] = json.loads(d["opts"] or "{}")
    d["publish_at_msk"] = datetime.datetime.fromtimestamp(d["publish_at"], MSK).strftime("%d.%m %H:%M")
    return d


def _parse_at(at):
    if not at or at == "now":
        return int(time.time())
    if isinstance(at, (int, float)):
        return int(at)
    dt = datetime.datetime.fromisoformat(str(at).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=MSK)
    return int(dt.timestamp())


# ------------------------------------------------------------------ media prep
def _jpeg(url, pid, n):
    """IG accepts only JPEG images — convert anything else to JPEG on our file server."""
    if url.lower().split("?")[0].endswith((".jpg", ".jpeg")):
        return url
    d = os.path.join(_files["dir"], "ig")
    os.makedirs(d, exist_ok=True)
    src = os.path.join(d, f"{pid}_{n}.src")
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "carousel-ig"}), timeout=120) as r:
        open(src, "wb").write(r.read())
    out = os.path.join(d, f"{pid}_{n}.jpg")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-q:v", "2", out], check=True)
    os.remove(src)
    return f"https://{_files['domain']}/f/ig/{pid}_{n}.jpg"


def _wait(cid, tok, limit=900):
    t0 = time.time()
    while time.time() - t0 < limit:
        st = _call("GET", f"/{cid}", tok, {"fields": "status_code,status"})
        code = st.get("status_code")
        if code == "FINISHED":
            return
        if code in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"контейнер {code}: {st.get('status')}")
        time.sleep(10)
    raise RuntimeError("контейнер не обработался за 15 мин")


def _publish(p):
    name, a = _acc(p["account"])
    tok, uid = a["token"], a["id"]
    o, media, kind = p["opts"], p["media"], p["kind"]
    cap = p["caption"] or ""
    if kind == "reel":
        prm = {"media_type": "REELS", "video_url": media[0], "caption": cap,
               "share_to_feed": "true" if o.get("share_to_feed", True) else "false"}
        if o.get("cover"):
            prm["cover_url"] = _jpeg(o["cover"], p["id"], "cover")
        if o.get("thumb_offset") is not None:
            prm["thumb_offset"] = str(int(o["thumb_offset"]))
        if o.get("trial"):
            prm["trial_params"] = json.dumps({"graduation_strategy": o.get("graduation", "MANUAL")})
        cid = _call("POST", f"/{uid}/media", tok, prm)["id"]
    elif kind == "image":
        cid = _call("POST", f"/{uid}/media", tok, {"image_url": _jpeg(media[0], p["id"], 0), "caption": cap})["id"]
    elif kind == "carousel":
        kids = []
        for i, u in enumerate(media[:10]):
            if u.lower().split("?")[0].endswith((".mp4", ".mov")):
                k = _call("POST", f"/{uid}/media", tok, {"media_type": "VIDEO", "video_url": u, "is_carousel_item": "true"})["id"]
            else:
                k = _call("POST", f"/{uid}/media", tok, {"image_url": _jpeg(u, p["id"], i), "is_carousel_item": "true"})["id"]
            kids.append(k)
        for k in kids:
            _wait(k, tok)
        cid = _call("POST", f"/{uid}/media", tok, {"media_type": "CAROUSEL", "children": ",".join(kids), "caption": cap})["id"]
    else:
        raise ValueError("kind: reel | image | carousel")
    _upd(p["id"], status="processing", container=cid)
    _wait(cid, tok)
    mid = _call("POST", f"/{uid}/media_publish", tok, {"creation_id": cid})["id"]
    link = ""
    try:
        link = _call("GET", f"/{mid}", tok, {"fields": "permalink"}).get("permalink", "")
    except Exception:
        pass
    return mid, link


def _upd(pid, **kw):
    kw["updated"] = int(time.time())
    with _lock, _db() as c:
        c.execute("update posts set " + ",".join(f"{k}=?" for k in kw) + " where id=?", (*kw.values(), pid))


# ------------------------------------------------------------------ token refresh
def refresh_tokens(force=False):
    out = {}
    e = _env()
    with _db() as c:
        seen = {r["account"]: r["refreshed"] for r in c.execute("select * from tokens")}
    changed = False
    for name, a in accounts_raw().items():
        last = seen.get(name)
        if last is None:  # first sight: tokens were issued 18.10.2026
            last = int(datetime.datetime(2026, 10, 18, tzinfo=MSK).timestamp())
            with _db() as c:
                c.execute("insert or ignore into tokens values(?,?)", (name, last))
        if not force and time.time() - last < REFRESH_DAYS * 86400:
            out[name] = "ok"
            continue
        try:
            r = _call("GET", "https://graph.instagram.com/refresh_access_token", a["token"],
                      {"grant_type": "ig_refresh_token"})
            if r.get("access_token"):
                e[f"IG_{name.upper()}_TOKEN"] = r["access_token"]
                changed = True
                with _db() as c:
                    c.execute("insert or replace into tokens values(?,?)", (name, int(time.time())))
                out[name] = f"продлён на {int(r.get('expires_in', 0)) // 86400} дн."
        except Exception as ex:
            out[name] = "ошибка продления: " + _scrub(ex, a["token"])[:200]
    if changed:
        _write_env(e)
    return out


# ------------------------------------------------------------------ worker
def _loop():
    last_refresh = 0
    while True:
        try:
            if time.time() - last_refresh > 6 * 3600:
                last_refresh = time.time()
                r = refresh_tokens()
                if any(v != "ok" for v in r.values()):
                    _log("ig tokens", r)
            with _db() as c:
                due = [_row(r) for r in c.execute(
                    "select * from posts where status='pending' and publish_at<=? order by publish_at limit 1",
                    (int(time.time()),))]
            for p in due:
                _upd(p["id"], status="processing")
                try:
                    mid, link = _publish(p)
                    _upd(p["id"], status="published", media_id=mid, permalink=link, error="")
                    _log("ig published", p["id"], p["account"], link)
                except Exception as ex:
                    _upd(p["id"], status="error", error=str(ex)[:500])
                    _log("ig error", p["id"], p["account"], str(ex)[:200])
        except Exception as ex:
            _log("ig loop", type(ex).__name__, str(ex)[:200])
        time.sleep(20)


def start(log, files_dir, domain):
    global _log
    _log = log
    _files.update(dir=files_dir, domain=domain)
    with _db() as c:  # posts interrupted by a restart go back to the queue
        c.execute("update posts set status='pending' where status='processing'")
    threading.Thread(target=_loop, daemon=True, name="ig-pub").start()
    log("ig publisher started")


# ------------------------------------------------------------------ ops
def op(a):
    o = a.get("ig")
    if o == "accounts":
        res = {}
        for name, acc in accounts_raw().items():
            try:
                me = _call("GET", "/me", acc["token"], {"fields": "user_id,username,account_type,media_count,followers_count"})
                res[name] = {k: me.get(k) for k in ("username", "account_type", "media_count", "followers_count")}
            except Exception as ex:
                res[name] = {"error": _scrub(ex, acc["token"])[:200]}
        return res
    if o == "schedule":
        name, _ = _acc(a["account"])
        media = a["media"] if isinstance(a["media"], list) else [a["media"]]
        opts = {k: a[k] for k in ("trial", "graduation", "share_to_feed", "cover", "thumb_offset") if k in a}
        now = int(time.time())
        with _lock, _db() as c:
            cur = c.execute("insert into posts(account,kind,media,caption,opts,publish_at,status,created,updated) "
                            "values(?,?,?,?,?,?,?,?,?)",
                            (name, a.get("kind", "reel"), json.dumps(media), a.get("caption", ""), json.dumps(opts),
                             _parse_at(a.get("at")), "pending", now, now))
            pid = cur.lastrowid
        return _get(pid)
    if o == "list":
        q, args = "select * from posts", []
        if a.get("account"):
            q += " where account=?"
            args.append(_acc(a["account"])[0])
        q += " order by publish_at desc limit ?"
        args.append(int(a.get("limit", 30)))
        with _db() as c:
            return [{k: v for k, v in _row(r).items() if k not in ("caption",)} | {"caption": (r["caption"] or "")[:60]}
                    for r in c.execute(q, args)]
    if o == "cancel":
        with _lock, _db() as c:
            c.execute("update posts set status='cancelled' where id=? and status in ('pending','error')", (a["id"],))
        return _get(a["id"])
    if o == "retry":
        with _lock, _db() as c:
            c.execute("update posts set status='pending', error='' where id=? and status='error'", (a["id"],))
        return _get(a["id"])
    if o == "get":
        return _get(a["id"])
    if o == "refresh":
        return refresh_tokens(force=bool(a.get("force")))
    raise ValueError("ig: accounts | schedule | list | get | cancel | retry | refresh")


def _get(pid):
    with _db() as c:
        r = c.execute("select * from posts where id=?", (pid,)).fetchone()
    return _row(r) if r else None
