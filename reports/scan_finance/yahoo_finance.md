# Scan — yahoo_finance

_kind=filesystem · provenance=offline-baseline · model_reviewed=False · bands={'low': 27, 'medium': 27, 'high': 0, 'critical': 0}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical.

## Inferred domain profile

- **mcp_kind**: filesystem
- **asset_meaning**: a class of file the server can read or write, by type
- **blast_radius_meaning**: from reading one file to overwriting or destroying many
- **worked_example**: write_file on a .pem = critical: clobbers key material irreversibly

## Tool impact

| tool | impact |
| --- | --- |
| `get_historical_stock_prices` | 1 |
| `get_stock_info` | 1 |
| `get_yahoo_finance_news` | 1 |
| `get_stock_actions` | 1 |
| `get_financial_statement` | 1 |
| `get_holder_info` | 1 |
| `get_option_expiration_dates` | 1 |
| `get_option_chain` | 1 |
| `get_recommendations` | 1 |

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

| asset \ tool | get_historical_stock_prices | get_stock_info | get_yahoo_finance_news | get_stock_actions | get_financial_statement | get_holder_info | get_option_expiration_dates | get_option_chain | get_recommendations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `.txt` | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 |
| `.csv` | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 |
| `.json` | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 |
| `.md` | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 |
| `.png` | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 |
| `.py` | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 |
