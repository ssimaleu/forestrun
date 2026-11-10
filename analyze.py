"""Split 10y ETF prices into two 5-year windows and rank every ETF on
1) average monthly trend  = sum(monthly % returns) / number of months
2) 5D_SMA total gain      = (last 5D SMA / first 5D SMA - 1) * 100
"""

import os

import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data", "prices.csv")
OUT = os.path.join(BASE, "results")


def monthly_trend(close: pd.Series) -> tuple[float, int]:
    """Average of month-over-month % returns inside the window:
    sum(returns) / number of months."""
    month_end = close.resample("ME").last()
    rets = month_end.pct_change().dropna() * 100
    return rets.sum() / len(rets), len(rets)


def sma_gain(close: pd.Series) -> float:
    sma = close.rolling(5).mean().dropna()
    return (sma.iloc[-1] / sma.iloc[0] - 1) * 100


def window_metrics(prices: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    seg = prices.loc[(prices.index >= start) & (prices.index <= end)]
    rows = []
    for ticker in seg.columns:
        close = seg[ticker].dropna()
        trend, months = monthly_trend(close)
        rows.append(
            {
                "Ticker": ticker,
                "Avg monthly trend %": round(trend, 3),
                "Months": months,
                "5D SMA gain %": round(sma_gain(close), 1),
                "Total price gain %": round((close.iloc[-1] / close.iloc[0] - 1) * 100, 1),
            }
        )
    df = pd.DataFrame(rows).set_index("Ticker")
    df["Rank (monthly trend)"] = df["Avg monthly trend %"].rank(ascending=False).astype(int)
    df["Rank (5D SMA gain)"] = df["5D SMA gain %"].rank(ascending=False).astype(int)
    return df.sort_values("Avg monthly trend %", ascending=False)


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    prices = pd.read_csv(DATA, index_col=0, parse_dates=True).sort_index().dropna(how="all")

    idx = prices.index
    start, end = idx[0], idx[-1]
    split = idx[len(idx) // 2]          # roughly the 5-year mark (equal trading days)
    print(f"Full window : {start.date()} -> {end.date()}  ({len(idx)} trading days, {(end-start).days/365.25:.2f} years)")
    print(f"Split point : {split.date()}")
    print(f"Window A    : {start.date()} -> {idx[len(idx)//2 - 1].date()}  (study period, {len(idx)//2} days)")
    print(f"Window B    : {split.date()} -> {end.date()}  (check period, {len(idx) - len(idx)//2} days)\n")

    a = window_metrics(prices, start, idx[len(idx) // 2 - 1])
    b = window_metrics(prices, split, end)

    a.to_csv(os.path.join(OUT, "window_a_first_5y.csv"))
    b.to_csv(os.path.join(OUT, "window_b_second_5y.csv"))

    def show(title: str, df: pd.DataFrame) -> None:
        print(f"### {title}")
        cols = ["Avg monthly trend %", "Rank (monthly trend)", "5D SMA gain %", "Rank (5D SMA gain)", "Total price gain %"]
        print(df[cols].to_string())
        top_trend = df["Avg monthly trend %"].idxmax()
        top_sma = df["5D SMA gain %"].idxmax()
        print(f"-> top by avg monthly trend : {top_trend} ({df.loc[top_trend, 'Avg monthly trend %']:.3f} %/month)")
        print(f"-> top by 5D SMA gain       : {top_sma} ({df.loc[top_sma, '5D SMA gain %']:.1f} %)\n")

    show("Window A - first 5 years (study period)", a)
    show("Window B - second 5 years (check period)", b)

    # ---- consistency between the two 5-year periods ----
    comp = pd.DataFrame(
        {
            "A trend %": a["Avg monthly trend %"],
            "A trend rank": a["Rank (monthly trend)"],
            "B trend %": b["Avg monthly trend %"],
            "B trend rank": b["Rank (monthly trend)"],
            "Trend rank change": a["Rank (monthly trend)"] - b["Rank (monthly trend)"],
            "A 5D SMA gain %": a["5D SMA gain %"],
            "A SMA rank": a["Rank (5D SMA gain)"],
            "B 5D SMA gain %": b["5D SMA gain %"],
            "B SMA rank": b["Rank (5D SMA gain)"],
            "SMA rank change": a["Rank (5D SMA gain)"] - b["Rank (5D SMA gain)"],
        }
    ).sort_values("A trend rank")
    comp.to_csv(os.path.join(OUT, "consistency.csv"))

    print("### Consistency between the two 5-year periods")
    print(comp.to_string())

    n = len(comp)
    print("\n--- consistency summary ---")
    for metric, ra, rb in [("avg monthly trend", "A trend rank", "B trend rank"), ("5D SMA gain", "A SMA rank", "B SMA rank")]:
        corr = comp[ra].corr(comp[rb])  # Pearson on ranks == Spearman (no scipy needed)
        for k in (1, 3, 5):
            sa = set(comp[comp[ra] <= k].index)
            sb = set(comp[comp[rb] <= k].index)
            print(f"{metric}: Spearman rank corr = {corr:+.2f} | top-{k} overlap = {len(sa & sb)}/{k} ({sorted(sa & sb)})")
        stable = comp[(comp[ra] <= 5) & (comp[rb] <= 5)]
        print(f"{metric}: in top-5 in BOTH periods -> {list(stable.index) if len(stable) else 'none'}")
        print(f"{metric}: biggest fallers (A rank -> B rank) -> "
              f"{[f'{t} {int(r[ra])}->{int(r[rb])}' for t, r in comp.sort_values(rb, ascending=False).head(3).iterrows()]}")
        print(f"{metric}: biggest risers (A rank -> B rank) -> "
              f"{[f'{t} {int(r[ra])}->{int(r[rb])}' for t, r in comp.sort_values(rb).head(3).iterrows()]}\n")

    both_a = set(a[(a["Rank (monthly trend)"] == 1) | (a["Rank (5D SMA gain)"] == 1)].index)
    both_b = set(b[(b["Rank (monthly trend)"] == 1) | (b["Rank (5D SMA gain)"] == 1)].index)
    print(f"Top performer(s) window A: {sorted(both_a)}")
    print(f"Top performer(s) window B: {sorted(both_b)}")
    print(f"Same leader in both windows: {sorted(both_a & both_b) if both_a & both_b else 'NO - results are NOT consistent'}")
    print(f"ETFs rated: {n}")


if __name__ == "__main__":
    main()
