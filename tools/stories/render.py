import json, sys, urllib.parse, pathlib, asyncio
from playwright.async_api import async_playwright
spec = json.load(open(sys.argv[1])); out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
base = pathlib.Path(sys.argv[1]).resolve().parent
tpl = pathlib.Path(__file__).resolve().parent / (sys.argv[3] if len(sys.argv) > 3 else "story.html")
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width":1080,"height":1920})
        for i, f in enumerate(spec, 1):
            for k in ("img","old","new"):
                if k in f and not f[k].startswith(("http","file:")): f[k] = (base / f[k]).resolve().as_uri()
            for bl in f.get("blocks", []):
                if "img" in bl and not bl["img"].startswith(("http","file:")): bl["img"] = (base / bl["img"]).resolve().as_uri()
            await pg.goto(tpl.as_uri() + f"?n={i}#" + urllib.parse.quote(json.dumps(f, ensure_ascii=False)))
            await pg.wait_for_timeout(500)
            await pg.screenshot(path=str(out / f"{i:02d}.jpg"), type="jpeg", quality=92)
        await b.close()
asyncio.run(main())
