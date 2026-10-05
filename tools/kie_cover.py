"""Generate carousel covers with kie.ai (Nano Banana Pro).

Runs inside GitHub Actions. For every posts/<name>/cover_job.json that has no
matching cover file yet, it sends the prompt and reference images to kie.ai,
waits for the result and saves it next to the slides as 01.png.

cover_job.json:
{
  "prompt": "...",
  "refs": ["templates/B_derzhit.png"],   # repo paths or full https URLs
  "aspect_ratio": "3:4",
  "resolution": "2K",
  "model": "nano-banana-pro",
  "out": "01.png"                         # optional
}
Delete 01.png (or change "out") to generate again.
"""
import glob
import json
import os
import sys
import time
import urllib.request

API = "https://api.kie.ai/api/v1/jobs"
KEY = os.environ["KIE_API_KEY"]
REPO = os.environ["GITHUB_REPOSITORY"]
SHA = os.environ["GITHUB_SHA"]


def call(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def ref_url(ref):
    if ref.startswith("http"):
        return ref
    return f"https://raw.githubusercontent.com/{REPO}/{SHA}/{ref}"


def generate(job_path):
    folder = os.path.dirname(job_path)
    job = json.load(open(job_path, encoding="utf-8"))
    out = os.path.join(folder, job.get("out", "01.png"))
    if os.path.exists(out):
        return None
    body = {
        "model": job.get("model", "nano-banana-pro"),
        "input": {
            "prompt": job["prompt"],
            "image_input": [ref_url(r) for r in job.get("refs", [])],
            "aspect_ratio": job.get("aspect_ratio", "3:4"),
            "resolution": job.get("resolution", "2K"),
            "output_format": "png",
        },
    }
    res = call("POST", f"{API}/createTask", body)
    task = (res.get("data") or {}).get("taskId")
    status = {"job": job_path, "taskId": task, "create": res}
    if not task:
        status["state"] = "fail"
        return status
    for _ in range(90):  # up to ~15 minutes
        time.sleep(10)
        info = call("GET", f"{API}/recordInfo?taskId={task}").get("data") or {}
        state = info.get("state")
        if state in ("success", "fail"):
            status.update(state=state, failMsg=info.get("failMsg"),
                          credits=info.get("creditsConsumed"))
            if state == "success":
                urls = json.loads(info.get("resultJson") or "{}").get("resultUrls") or []
                if urls:
                    urllib.request.urlretrieve(urls[0], out)
                    status["file"] = out
                else:
                    status["state"] = "fail"
                    status["failMsg"] = "no resultUrls"
            return status
    status["state"] = "timeout"
    return status


def main():
    results = []
    for job in sorted(glob.glob("posts/*/cover_job.json")):
        try:
            r = generate(job)
        except Exception as e:  # keep going with other jobs
            r = {"job": job, "state": "error", "error": str(e)}
        if r:
            results.append(r)
            json.dump(r, open(os.path.join(os.path.dirname(job), "cover_status.json"), "w",
                              encoding="utf-8"), ensure_ascii=False, indent=1)
            print(json.dumps(r, ensure_ascii=False))
    if any(r.get("state") != "success" for r in results):
        sys.exit(0)  # statuses are committed; Claude reads cover_status.json


if __name__ == "__main__":
    main()
