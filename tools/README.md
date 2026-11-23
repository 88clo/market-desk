# Market Desk site tools

The site is a public copy of four claude.ai dashboards plus the Market Desk home page.

- `tools/update_prices.py` refreshes `data/prices.json`, which feeds the home page price chart.
- `tools/build.py` rebuilds `index.html`, `spx/`, `downturn/`, `etf/` and `regimes/` from the
  latest claude.ai versions placed in `sources/` (not committed: it holds private details such as a
  chat link and an example portfolio value that the build removes).

A scheduled Claude task runs both every day and pushes the result if anything changed.
