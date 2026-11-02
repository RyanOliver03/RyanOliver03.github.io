"""Fetch USD FX rates from Yahoo Finance with yfinance and write fx.json.

Every rate is local currency per 1 USD (Yahoo's "XXX=X" tickers).
The file is only rewritten when a rate changes, so weekends make no commits.
"""
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import yfinance as yf

PAIRS = {
    "JPY": "JPY=X", "CNY": "CNY=X", "TWD": "TWD=X", "HKD": "HKD=X",
    "KRW": "KRW=X", "INR": "INR=X", "EUR": "EUR=X", "GBP": "GBP=X",
}
OUT = Path(__file__).resolve().parent.parent / "fx.json"


def last_close(ticker: str):
    for interval, period in (("5m", "1d"), ("30m", "5d"), ("1d", "1mo")):
        try:
            h = yf.Ticker(ticker).history(period=period, interval=interval)
            h = h.dropna(subset=["Close"])
            if not h.empty:
                v = float(h["Close"].iloc[-1])
                if v > 0 and math.isfinite(v):
                    return round(v, 6), h.index[-1].to_pydatetime().astimezone(timezone.utc)
        except Exception as e:  # keep going with the next interval
            print(f"{ticker} {interval}: {e}")
    return None, None


def main():
    old = json.loads(OUT.read_text()) if OUT.exists() else {}
    rates, as_of = dict(old.get("rates", {})), None
    for ccy, tk in PAIRS.items():
        v, ts = last_close(tk)
        if v is None:
            print(f"{ccy}: no data, keeping previous value")
            continue
        rates[ccy] = v
        as_of = ts if as_of is None or ts > as_of else as_of
        print(f"{ccy}: {v} ({ts:%Y-%m-%d %H:%M} UTC)")

    if not rates:
        raise SystemExit("No FX data fetched")
    if rates == old.get("rates"):
        print("Rates unchanged, fx.json left as is")
        return

    out = {
        "base": "USD",
        "source": "Yahoo Finance (yfinance)",
        "asOf": (as_of or datetime.now(timezone.utc)).isoformat(timespec="seconds"),
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rates": rates,
    }
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
