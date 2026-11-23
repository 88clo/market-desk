"""Build the Market Desk site from the latest dashboard sources.

Inputs (filled by whoever runs the sync, usually the scheduled Claude task):
  sources/hub.html              Market Desk page as published on claude.ai (its file content)
  sources/spx.html              S&P 500 Stock Returns, as published on claude.ai
  sources/downturn.html         Downturn Ledger (full saved HTML from an Artifact read)
  sources/etf.html              ETF Allocation Outlook (full saved HTML from an Artifact read)
  sources/regimes/files/*.json  Regimes dashboard store: index.html, app.js, style.css documents
  sources/regimes/datasets/*.json and sources/regimes/blobs/<id>.json   its data
Outputs: index.html, spx/, downturn/, etf/, regimes/ at the repo root.
Run from the repo root:  python3 tools/build.py
"""
import json, os, re, glob, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'sources')
T = os.path.join(ROOT, 'tools')
exec(open(os.path.join(T, 'navbar.py')).read())
CLAUDE = {'spx': 'https://claude.ai/artifact/JNH69umZsfKm4sHRSQur3L', 'downturn': 'https://claude.ai/artifact/Ep32oqGTBW1zKGeiFrzJx1',
          'etf': 'https://claude.ai/artifact/S752kVNvG6bgcR89S9vr9M', 'regimes': 'https://claude.ai/artifact/RES9qxbEVNfhyAbiMiPZcv',
          'home': 'https://claude.ai/artifact/2yY1iHHgi5zwjYHRerFkuV'}
SITE = {'home': '../', 'spx': '../spx/', 'downturn': '../downturn/', 'etf': '../etf/', 'regimes': '../regimes/'}
NOI = '<meta name="robots" content="noindex, nofollow">'
LIGHT = '<meta name="color-scheme" content="light"><script>document.documentElement.setAttribute("data-theme","light")</script>'
RESET = '<style>:root{color-scheme:light;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}html{scroll-padding-top:env(safe-area-inset-top,0px)}body{margin:0;padding:0;font:14px -apple-system,BlinkMacSystemFont,sans-serif;background:#fff;color:#000}img{max-width:100%}[hidden]:not([hidden=until-found i]){display:none!important}</style>'
SK = '<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">' + NOI + LIGHT + RESET + '</head><body>\n'

def read(p): return open(p, encoding='utf-8').read()
def write(rel, s):
    p = os.path.join(ROOT, rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'w', encoding='utf-8').write(s)
def as_fragment(s):
    """Accept either a published fragment or a full saved document; return the body content."""
    if '<!doctype html>' in s.lower()[:4000]:
        s = s[s.lower().index('<!doctype html>'):]
        m = re.search(r'<body[^>]*>', s); s = s[m.end():] if m else s
        s = re.sub(r'</body>\s*</html>\s*$', '', s.strip())
    return s
def remove_navbar(s):
    """Drop a Market Desk nav bar (and the collapse helper) that the claude.ai copies carry."""
    while '<style>.mdnav{' in s:
        a = s.index('<style>.mdnav{'); d = s.index('<div class="mdnav">', a); e = s.index('</script>', d) + 9
        s = s[:a] + s[e:]
    while '<style>.mdc-btn{' in s:
        a = s.index('<style>.mdc-btn{'); e = s.index('</script>', a) + 9; s = s[:a] + s[e:]
    return s
def page(frag, cur, extra_head=''):
    frag = remove_navbar(frag)
    return SK.replace('</head>', extra_head + '</head>') + strip(cur, SITE) + '\n' + frag + collapse_js(cur) + '\n</body></html>\n'

# home page
hub = remove_navbar(as_fragment(read(os.path.join(SRC, 'hub.html'))))
for k in ('spx', 'downturn', 'etf'):
    hub = hub.replace(CLAUDE[k], k + '/')
hub = hub.replace('href="%s" target="_blank" rel="noopener"' % CLAUDE['regimes'], 'href="regimes/"').replace('Open on claude.ai ↗', 'Open dashboard →')
write('index.html', SK + hub + '\n</body></html>\n')
# S&P 500
write('spx/index.html', page(as_fragment(read(os.path.join(SRC, 'spx.html'))), 'spx'))
# Downturn Ledger (keep the example portfolio generic)
d = as_fragment(read(os.path.join(SRC, 'downturn.html')))
d = d.replace('value="500,000"', 'value="100,000"').replace('amt: 500000', 'amt: 100000')
write('downturn/index.html', page(d, 'downturn'))
# ETF Allocation Outlook (no private chat link; open in Quick view)
e = as_fragment(read(os.path.join(SRC, 'etf.html')))
e = re.sub(r'"chat":"https://claude\.ai/code/session_[A-Za-z0-9]+"', '"chat":""', e)
e = e.replace("v=localStorage.getItem('etf-outlook-view')||'full'", "v=localStorage.getItem('etf-outlook-view')||'quick'")
write('etf/index.html', page(e, 'etf'))
# Regimes: standalone rebuild of a claude.ai Dashboard-type page
RG = os.path.join(SRC, 'regimes')
def doc(p):
    j = json.load(open(p)); return j.get('data', j)
data = {}
for f in glob.glob(os.path.join(RG, 'datasets', '*.json')):
    ds = doc(f); src = ds.get('source', {})
    if src.get('kind') != 'file': continue
    bid = src['url'].split('/')[-1]
    data[os.path.basename(f)[:-5]] = json.load(open(os.path.join(RG, 'blobs', bid + '.json')))
files = {os.path.basename(f)[:-5]: doc(f)['text'] for f in glob.glob(os.path.join(RG, 'files', '*.json'))}
html = files['index.html'].replace('<meta name="dash-one-writer">', '')
html = re.sub(r'<link rel="stylesheet" href="[^"]+">', '', html)
css = ''.join(v for k, v in files.items() if k.endswith('.css'))
js = ''.join(v for k, v in sorted(files.items()) if k.endswith('.js'))
shim = read(os.path.join(T, 'regimes_shim.js')).replace('__RAW__', json.dumps(data, separators=(',', ':')))
reg = ('<title>Two Centuries of Regimes, Industry &amp; Opportunity</title>\n<style>' + read(os.path.join(T, 'regimes_tokens.css')) + '\n' + css + '</style>\n'
       '<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>\n<script>' + shim + '</script>\n<div id="dash-root">' + html + '</div>\n<script>' + js + '</script>\n<script>window.__dashRenderAll();</script>\n')
write('regimes/index.html', page(reg, 'regimes'))
print('built: index.html spx downturn etf regimes')
