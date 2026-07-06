# Scan — ccxt

_kind=filesystem · provenance=offline-baseline · model_reviewed=False · bands={'low': 57, 'medium': 72, 'high': 15, 'critical': 0}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical.

## Inferred domain profile

- **mcp_kind**: filesystem
- **asset_meaning**: a class of file the server can read or write, by type
- **blast_radius_meaning**: from reading one file to overwriting or destroying many
- **worked_example**: write_file on a .pem = critical: clobbers key material irreversibly

## Tool impact

| tool | impact |
| --- | --- |
| `cache-stats` | 1 |
| `clear-cache` | 1 |
| `set-log-level` | 2 |
| `list-exchanges` | 1 |
| `get-ticker` | 1 |
| `batch-get-tickers` | 1 |
| `get-orderbook` | 1 |
| `get-ohlcv` | 1 |
| `get-trades` | 1 |
| `get-markets` | 1 |
| `get-exchange-info` | 1 |
| `get-leverage-tiers` | 1 |
| `get-funding-rates` | 1 |
| `get-market-types` | 1 |
| `account-balance` | 1 |
| `place-market-order` | 1 |
| `set-leverage` | 2 |
| `set-margin-mode` | 2 |
| `place-futures-market-order` | 1 |
| `get-proxy-config` | 1 |
| `set-proxy-config` | 2 |
| `test-proxy-connection` | 1 |
| `clear-exchange-cache` | 1 |
| `set-market-type` | 2 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `.txt` | 2 |
| `.csv` | 4 |
| `.json` | 4 |
| `.md` | 2 |
| `.png` | 2 |
| `.py` | 4 |

## Risk matrix (score · band)

| asset \ tool | cache-stats | clear-cache | set-log-level | list-exchanges | get-ticker | batch-get-tickers | get-orderbook | get-ohlcv | get-trades | get-markets | get-exchange-info | get-leverage-tiers | get-funding-rates | get-market-types | account-balance | place-market-order | set-leverage | set-margin-mode | place-futures-market-order | get-proxy-config | set-proxy-config | test-proxy-connection | clear-exchange-cache | set-market-type |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `.txt` | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 8 🟡 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 8 🟡 |
| `.csv` | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 24 🟠 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 24 🟠 |
| `.json` | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 24 🟠 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 24 🟠 |
| `.md` | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 8 🟡 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 8 🟡 |
| `.png` | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 8 🟡 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 8 🟡 |
| `.py` | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 24 🟠 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 24 🟠 |
