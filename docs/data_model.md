# Data Model

## Price Data

| Field | Description | Frequency |
|---|---|---|
| ticker | Stock ticker symbol | static |
| date | Trading date | daily |
| open | Opening price | daily |
| high | Daily high | daily |
| low | Daily low | daily |
| close | Closing price | daily |
| adjusted_close | Adjusted closing price | daily |
| volume | Trading volume | daily |

## Company Data

| Field | Description | Frequency |
|---|---|---|
| ticker | Stock ticker symbol | static |
| company_name | Full company name | static |
| sector | Economic sector | static |
| industry | Industry classification | static |
| country | Country of headquarters | static |

## Fundamental Data

| Field | Description | Frequency |
|---|---|---|
| ticker | Stock ticker symbol | static |
| period_end | End of the reporting period | quarterly/yearly |
| filing_date | Date when the information became publicly available | quarterly/yearly |
| revenue | Company revenue | quarterly/yearly |
| net_income | Net income | quarterly/yearly |
| eps | Earnings per share | quarterly/yearly |
| free_cash_flow | Free cash flow | quarterly/yearly |
| total_assets | Total assets | quarterly/yearly |
| total_debt | Total debt | quarterly/yearly |
| cash | Cash and equivalents | quarterly/yearly |
| equity | Shareholders' equity | quarterly/yearly |

## Market Data

| Field | Description | Frequency |
|---|---|---|
| ticker | Stock ticker symbol | static |
| market_cap | Market capitalization | daily/periodic |
| shares_outstanding | Shares outstanding | periodic |