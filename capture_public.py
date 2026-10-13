"""RASD Gate 7: isolated public-news screenshot proof.

No credentials, no private project code, no email sending, no scheduling.
Captures only two publicly accessible, previously verified publisher pages.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

TARGETS = (
    ("egypt_planning_official", "https://mped.gov.eg/singlenews?id=7248&lang=ar", {"mped.gov.eg", "www.mped.gov.eg"}),
    ("egypt_planning_coverage", "https://www.elwatannews.com/news/details/8375816", {"elwatannews.com", "www.elwatannews.com"}),
)

OUT = Path("evidence")
OUT.mkdir(parents=True, exist_ok=True)
results = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
    try:
        for label, url, allowed_hosts in TARGETS:
            result = {"label": label, "requested_url": url, "captured": False, "image": None}
            context = None
            try:
                context = browser.new_context(
                    viewport={"width": 1200, "height": 900},
                    device_scale_factor=1,
                    locale="ar-EG",
                    accept_downloads=False,
                    service_workers="block",
                    ignore_https_errors=False,
                )
                page = context.new_page()
                page.set_default_timeout(14000)
                response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
                if response is None or response.status >= 400:
                    raise RuntimeError("bad_http_status")
                final = urlsplit(page.url)
                if final.scheme != "https" or final.hostname not in allowed_hosts:
                    raise RuntimeError("redirected_outside_publisher")
                body = page.locator("body").inner_text(timeout=10000)
                title = page.title()
                if len(body) < 180 or ("التخطيط" not in (title + body) and "Planning" not in (title + body)):
                    raise RuntimeError("no_confirmed_news_article")
                low = body[:1200].lower()
                if any(phrase in low for phrase in ("verify you are human", "just a moment...", "captcha")):
                    raise RuntimeError("browser_challenge_detected")
                page.wait_for_timeout(1200)
                path = OUT / (label + ".jpg")
                page.screenshot(path=str(path), type="jpeg", quality=80, full_page=False)
                raw = path.read_bytes()
                if len(raw) < 8000 or raw[:2] != b"\\xff\\xd8":
                    path.unlink(missing_ok=True)
                    raise RuntimeError("screenshot_invalid")
                result.update({
                    "captured": True,
                    "final_url": page.url,
                    "page_title": title[:300],
                    "http_status": response.status,
                    "image": path.name,
                    "image_size_bytes": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "checked_at_utc": datetime.now(timezone.utc).isoformat(),
                })
            except Exception as exc:
                result["error"] = type(exc).__name__ + (": " + str(exc))[:125]
            finally:
                if context:
                    context.close()
            results.append(result)
            print(json.dumps(result, ensure_ascii=False), flush=True)
    finally:
        browser.close()

report = {
    "scope": "public_pages_only",
    "run_mode": "single_manual",
    "no_email_sent": True,
    "screenshots_captured": sum(bool(r["captured"]) for r in results),
    "results": results,
}
(OUT / "result.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
if not report["screenshots_captured"]:
    sys.exit("No verified publisher-page screenshot was captured")
