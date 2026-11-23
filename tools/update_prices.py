"""Refresh data/prices.json with recent daily prices from Yahoo Finance.
Run by the GitHub Actions workflow in .github/workflows/prices.yml."""
import json, urllib.request, datetime as dt, sys
SYMS = ['VOO', 'NVDA', 'SMH', 'XLP', 'XBI']
NY = dt.timezone(dt.timedelta(hours=-5))
series = {}
for s in SYMS:
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{s}?range=6mo&interval=1d'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (market-desk updater)'})
    r = json.load(urllib.request.urlopen(req, timeout=30))['chart']['result'][0]
    q = r['indicators']['quote'][0]
    pts = [[dt.datetime.fromtimestamp(t, dt.timezone.utc).astimezone(NY).date().isoformat(), round(c, 2)]
           for t, c in zip(r['timestamp'], q['close']) if c is not None]
    last = r['meta'].get('regularMarketPrice')
    if last and pts:
        pts[-1][1] = round(last, 2)
    series[s] = pts[-90:]
out = {'asof': dt.datetime.now(NY).isoformat(timespec='minutes'),
       'note': 'Daily closes; last point is the latest price during market hours.', 'series': series}
json.dump(out, open('data/prices.json', 'w'), separators=(',', ':'))
print('updated', out['asof'])
