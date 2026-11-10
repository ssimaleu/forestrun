"""Fetch 10 years of daily ETF closes and cache them to data/prices.csv."""

import os
import sys
import time
import json

import pandas as pd
import yfinance as yf

TICKERS = [
    "SPY", "QQQ", "IWM", "DIA", "VTI", "VOO", "EFA", "EEM", "GLD", "TLT",
    "HYG", "XLE", "XLK", "XLF", "XLV", "XLY", "XLP", "XLI", "XLB", "XLRE",
    "XLU", "VNQ", "SMH", "ARKK",
]

START = "2016-10-22"
END = "2026-10-22"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def fetch(ticker: str) -> pd.Series | None:
    for attempt in range(4):
        try:
            df = yf.download(
                ticker,
                start=START,
                end=END,
                interval="1d",
                auto_adjust=True,
                progress=False,
                threads=False,
            )
            if df is None or df.empty:
                raise RuntimeError("empty frame")
            close = df["Close"]
            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]
            close = close.dropna()
            close.index = pd.to_datetime(close.index).tz_localize(None).normalize()
            close.name = ticker
            return close
        except Exception as exc:  # noqa: BLE001
            print(f"  {ticker} attempt {attempt + 1} failed: {exc}", file=sys.stderr)
            time.sleep(3 * (attempt + 1))
    return None


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    csv_path = os.path.join(OUT_DIR, "prices.csv")
    series = {}
    if os.path.exists(csv_path):
        existing = pd.read_csv(csv_path, index_col=0, parse_dates=True)
        for ticker in existing.columns:
            s = existing[ticker].dropna()
            s.index = pd.to_datetime(s.index).normalize()
            series[ticker] = s
        print(f"cached: {list(series)}")

    for ticker in TICKERS:
        if ticker in series:
            continue
        close = fetch(ticker)
        if close is None:
            print(f"SKIP {ticker}", file=sys.stderr)
            continue
        series[ticker] = close
        print(f"OK {ticker}: {len(close)} rows {close.index.min().date()} -> {close.index.max().date()}")
        time.sleep(4)

    if not series:
        raise SystemExit("no data downloaded")

    prices = pd.concat(series, axis=1).sort_index()
    prices = prices.ffill()
    prices.to_csv(os.path.join(OUT_DIR, "prices.csv"))
    with open(os.path.join(OUT_DIR, "coverage.json"), "w") as fh:
        json.dump({t: [str(s.index.min().date()), str(s.index.max().date()), int(s.notna().sum())] for t, s in series.items()}, fh, indent=2)
    print(f"\nSaved {prices.shape[0]} rows x {prices.shape[1]} tickers -> data/prices.csv")


if __name__ == "__main__":
    main()
