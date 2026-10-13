"""Public RSS discovery proof. Public publisher metadata only, no login or mail."""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import build_opener, HTTPRedirectHandler, Request
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

SOURCE = "https://hapijournal.com/feed/"
OUTPUT = Path("evidence/feed_probe.json")
KEYWORDS = ("وزارة التخطيط", "وزير التخطيط", "وزيرة التخطيط",
            "التخطيط والتنمية الاقتصادية")

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise ValueError("RSS_redirect_refused")

def publisher_url(url):
    try:
        parts = urlsplit(url)
        return parts.scheme == "https" and parts.hostname in {
            "hapijournal.com", "www.hapijournal.com"
        } and (parts.port is None or parts.port == 443) and not parts.username
    except (ValueError, AttributeError):
        return False

def fetch():
    opener = build_opener(NoRedirect)
    req = Request(SOURCE, headers={"User-Agent": "RASD-RSS-Probe/1.0"})
    with opener.open(req, timeout=25) as response:
        if response.status != 200 or response.geturl() != SOURCE:
            raise RuntimeError("feed_response_or_redirect_invalid")
        data = response.read(1_500_001)
        if len(data) > 1_500_000:
            raise RuntimeError("rss_too_large")
    root = ET.fromstring(data)
    if root.tag.rsplit("}", 1)[-1] != "rss":
        raise RuntimeError("not_an_rss_feed")
    parsed = []
    for el in root.findall("./channel/item"):
        title = (el.findtext("title") or "").strip()
        url = (el.findtext("link") or "").strip()
        if not title or not publisher_url(url):
            continue
        parsed.append({"title": title, "url": url,
                       "published": (el.findtext("pubDate") or "").strip()})
    matching = [a for a in parsed if any(word in a["title"] for word in KEYWORDS)]
    result = {
        "status": "feed_checked",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "feed": SOURCE,
        "direct_publisher_entries": len(parsed),
        "matched_headlines": len(matching),
        "news_alerts_sent": 0,
        "email_sent": False,
        "automatic_schedule_active": False,
        "note": "A zero-match probe does not demonstrate comprehensive media coverage.",
        "matches": matching[:5],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    try:
        fetch()
    except Exception as exc:
        print("FAIL: " + type(exc).__name__ + ": " + str(exc), file=sys.stderr)
        raise
