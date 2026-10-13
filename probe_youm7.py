"""Manual, public Youm7 economy RSS feed acceptance; no mail, cron or secrets."""
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import build_opener, HTTPRedirectHandler, Request
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

SOURCE = 'https://www.youm7.com/rss/SectionRss?SectionID=297'

class StopRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise ValueError('redirect_refused')

request = Request(SOURCE, headers={'User-Agent':'RASD-RSS-Probe/1.0'})
with build_opener(StopRedirect).open(request, timeout=25) as response:
    if response.status != 200 or response.geturl() != SOURCE:
        raise RuntimeError('unexpected_response')
    xml = response.read(1_500_001)
    if len(xml) > 1_500_000:
        raise RuntimeError('oversize_feed')

root = ET.fromstring(xml)
items = root.findall('./channel/item')
if not items:
    raise RuntimeError('not_an_rss_feed_with_items')
accepted = []
for item in items:
    title = (item.findtext('title') or '').strip()
    link = (item.findtext('link') or '').strip()
    parts = urlsplit(link)
    if title and parts.scheme == 'https' and parts.hostname in {'www.youm7.com', 'youm7.com'} and not parts.username and (parts.port is None or parts.port == 443):
        accepted.append({'title':title,'url':link})
if not accepted:
    raise RuntimeError('no_verified_direct_article_links')
matches = [a for a in accepted if 'التخطيط' in a['title']]
result = {'checked_at_utc':datetime.now(timezone.utc).isoformat(),
          'source': SOURCE,'rss_item_count':len(items),
          'verified_publisher_links':len(accepted),'planning_headline_matches':len(matches),
          'match_samples':matches[:3], 'email_sent':False, 'automatic_schedule_active':False}
Path('evidence').mkdir(exist_ok=True)
Path('evidence/youm7_rss_probe.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
