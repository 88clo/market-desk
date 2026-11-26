"""Refresh data/prices.json: the home page chart series plus the four headline numbers.
Run from the repo root. Used by .github/workflows/prices.yml (every 30 minutes in US market hours)."""
import json, urllib.request, urllib.parse, datetime as dt, os

CHART = ['VOO', 'NVDA', 'SMH', 'XLP', 'XBI']
NY = dt.timezone(dt.timedelta(hours=-5))
OUT = 'data/prices.json'

def fetch(sym, rng):
    url = 'https://query1.finance.yahoo.com/v8/finance/chart/%s?range=%s&interval=1d' % (urllib.parse.quote(sym), rng)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (market-desk updater)'})
    r = json.load(urllib.request.urlopen(req, timeout=30))['chart']['result'][0]
    q = r['indicators']['quote'][0]
    pts = [[dt.datetime.fromtimestamp(t, dt.timezone.utc).astimezone(NY).date().isoformat(), round(c, 4)]
           for t, c in zip(r['timestamp'], q['close']) if c is not None]
    last = r['meta'].get('regularMarketPrice')
    if last and pts:
        pts[-1][1] = round(last, 4)
    return pts, r['meta']

old = {}
if os.path.exists(OUT):
    try: old = json.load(open(OUT))
    except Exception: old = {}

series = dict(old.get('series', {}))
for s in CHART:
    try:
        pts, _ = fetch(s, '6mo')
        series[s] = [[d, round(v, 2)] for d, v in pts][-130:]
    except Exception as e:
        print('chart fetch failed', s, e)

pulse = dict(old.get('pulse', {}))
def back(pts, n):  # value n sessions ago
    return pts[-1 - n][1] if len(pts) > n else pts[0][1]
try:
    p, m = fetch('^GSPC', '1y')
    rec = max(p, key=lambda x: x[1])
    pulse['spx'] = {'last': round(p[-1][1], 2), 'date': p[-1][0], 'chg1d': round((p[-1][1] / back(p, 1) - 1) * 100, 2),
                    'record': round(rec[1], 2), 'record_date': rec[0], 'from_record': round((p[-1][1] / rec[1] - 1) * 100, 2)}
except Exception as e: print('spx failed', e)
try:
    p, _ = fetch('^VIX', '1mo'); pulse['vix'] = {'last': round(p[-1][1], 2), 'prev': round(back(p, 1), 2)}
except Exception as e: print('vix failed', e)
try:
    p, _ = fetch('^TNX', '1mo'); pulse['tnx'] = {'last': round(p[-1][1], 3), 'wk_ago': round(back(p, 5), 3)}
except Exception as e: print('tnx failed', e)
try:
    p, _ = fetch('CL=F', '3mo'); pulse['oil'] = {'last': round(p[-1][1], 2), 'chg4w': round((p[-1][1] / back(p, 20) - 1) * 100, 1)}
except Exception as e: print('oil failed', e)

out = {'asof': dt.datetime.now(NY).isoformat(timespec='minutes'),
       'note': 'Daily closes; the last point is the latest price during market hours.',
       'series': series, 'pulse': pulse}
json.dump(out, open(OUT, 'w'), separators=(',', ':'))
print('updated', out['asof'], json.dumps(pulse))
