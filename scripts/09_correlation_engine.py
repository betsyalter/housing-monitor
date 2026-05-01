"""Pairwise correlation engine — universe tickers x housing macro indicators.

Per codex audit (2026-05-01):
- Monthly resampling (not weekly forward-fill — serial correlation in
  forward-filled FRED data inflates t/p stats; monthly is cleaner for
  a published artifact).
- Log-returns for tickers (ln(P_t / P_{t-1})).
- Bps first-difference for mortgage rates (level change × 100).
- Log-differences for sales / starts / permits / inventory / prices /
  Case-Shiller (volume-like or index-like series).
- Pearson primary, Spearman as a QA sidecar (catches outlier-driven
  spurious correlations).
- Trailing 1y / 3y / 5y windows. Min obs per window: 9 / 24 / 36.
- p-values are descriptive, not gates — running many pair tests, ranks
  matter more than nominal significance.

Outputs:
- data/correlation_matrix.csv: full long-format audit artifact.
- data/correlation_rankings.csv: top 30 + bottom 30 per indicator at 5y
  window, joined to tier/subsector/directional from the universe CSV.
"""

import sys, os, glob, math
sys.path.insert(0, os.path.dirname(__file__))
from config import DATA_DIR

import pandas as pd
import numpy as np
from datetime import datetime, timezone

PRICES_DIR = os.path.join(DATA_DIR, "fmp_prices")
FRED_CSV = os.path.join(DATA_DIR, "fred_housing.csv")
UNIVERSE_CSV = os.path.join(DATA_DIR, "fmp_tickers.csv")
OUT_MATRIX = os.path.join(DATA_DIR, "correlation_matrix.csv")
OUT_RANKINGS = os.path.join(DATA_DIR, "correlation_rankings.csv")

WINDOWS = [
    {"years": 1, "min_obs": 9},
    {"years": 3, "min_obs": 24},
    {"years": 5, "min_obs": 36},
]

# Forward-fill cap for monthly FRED data: 45 days = ~1.5 months
FFILL_DAYS_MONTHLY = 45
# Outlier flag threshold for ticker monthly returns
OUTLIER_MONTHLY_RET = 0.30
# Top/bottom N per indicator in the rankings file
RANKINGS_TOP_N = 30

INDICATORS = {
    "mortgage_rate_30yr":       {"group": "rate",   "transform": "diff_bps", "expected_sign": "negative", "lagged": False},
    "mortgage_rate_15yr":       {"group": "rate",   "transform": "diff_bps", "expected_sign": "negative", "lagged": False},
    "existing_home_sales_saar": {"group": "demand", "transform": "logdiff",  "expected_sign": "positive", "lagged": False},
    "housing_starts_total":     {"group": "supply", "transform": "logdiff",  "expected_sign": "positive", "lagged": False},
    "building_permits":         {"group": "supply", "transform": "logdiff",  "expected_sign": "positive", "lagged": False},
    "median_home_price":        {"group": "price",  "transform": "logdiff",  "expected_sign": "positive", "lagged": False},
    "existing_home_inventory":  {"group": "supply", "transform": "logdiff",  "expected_sign": "positive", "lagged": False},
    "case_shiller_national":    {"group": "price",  "transform": "logdiff",  "expected_sign": "positive", "lagged": True},
}

MATRIX_COLUMNS = [
    "ticker", "indicator", "indicator_group", "expected_thesis_sign",
    "window_years", "n_obs", "pearson_r", "pearson_t", "pearson_p", "spearman_r",
    "quality_flags", "last_updated",
]


# ── Helpers ────────────────────────────────────────────────────────────────

def _t_and_p(r: float, n: int) -> tuple[float, float]:
    """Compute t-stat and two-tailed p-value for Pearson correlation."""
    if n < 3 or pd.isna(r) or abs(r) >= 1.0:
        return float("nan"), float("nan")
    t = r * math.sqrt((n - 2) / max(1e-12, 1 - r * r))
    try:
        from scipy.stats import t as t_dist
        p = 2.0 * t_dist.sf(abs(t), df=n - 2)
    except ImportError:
        # Crude normal approx if scipy isn't available — for n>=20 close enough
        p = 2.0 * (1 - _norm_cdf(abs(t)))
    return float(t), float(p)


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _spearman(a: pd.Series, b: pd.Series) -> float:
    if len(a) < 3:
        return float("nan")
    return a.rank().corr(b.rank())


def load_fred_monthly() -> pd.DataFrame:
    """Load FRED CSV → monthly DataFrame, transforms applied per indicator."""
    raw = pd.read_csv(FRED_CSV)
    raw["date"] = pd.to_datetime(raw["date"])
    raw = raw.sort_values("date").set_index("date")

    out = pd.DataFrame(index=pd.date_range(
        start=raw.index.min().replace(day=1), end=raw.index.max(), freq="MS"
    ))

    for col, meta in INDICATORS.items():
        if col not in raw.columns:
            continue
        s = raw[col].dropna()
        if s.empty:
            continue

        # Resample to monthly: take last value in each month
        s_monthly = s.resample("MS").last()
        # Forward-fill with cap (~1.5 months)
        s_filled = s_monthly.ffill(limit=2)

        if meta["transform"] == "diff_bps":
            # First-difference in basis points (rate is in %, ×100 → bps)
            transformed = s_filled.diff() * 100.0
        elif meta["transform"] == "logdiff":
            # Log-difference, robust to zeros via small-eps guard
            transformed = np.log(s_filled.replace({0: np.nan})).diff()
        else:
            transformed = s_filled.diff()

        out[col] = out.index.map(lambda d: transformed.get(d, float("nan")))

    return out


def ticker_monthly_logreturns(path: str) -> pd.Series | None:
    """Load a single ticker's price CSV and return monthly log-returns series."""
    try:
        p = pd.read_csv(path)
        if "date" not in p.columns or "price" not in p.columns or p.empty:
            return None
        p["date"] = pd.to_datetime(p["date"])
        p = p.sort_values("date").set_index("date")
        # Resample to monthly: last price of each month
        m = p["price"].resample("MS").last().dropna()
        if len(m) < 4:
            return None
        return np.log(m).diff()
    except Exception:
        return None


def has_outlier(returns: pd.Series) -> bool:
    return bool((returns.abs() > OUTLIER_MONTHLY_RET).any())


def correlate_window(rets: pd.Series, ind: pd.Series, n_min: int) -> tuple:
    """Pairwise correlation on overlapping months only."""
    df = pd.concat([rets.rename("r"), ind.rename("i")], axis=1).dropna()
    n = len(df)
    if n < n_min:
        return None
    pearson = df["r"].corr(df["i"])
    spearman = _spearman(df["r"], df["i"])
    t, p = _t_and_p(pearson, n)
    return n, pearson, t, p, spearman


def build_matrix() -> pd.DataFrame:
    print("Loading FRED monthly indicators...")
    fred = load_fred_monthly()
    print(f"  FRED indicators: {[c for c in fred.columns if c in INDICATORS]}")
    print(f"  Date range: {fred.index.min().date()} to {fred.index.max().date()}")

    universe = pd.read_csv(UNIVERSE_CSV)
    tickers = sorted(universe["ticker"].dropna().unique())
    print(f"\nProcessing {len(tickers)} tickers...")

    now = datetime.now(timezone.utc).isoformat()
    rows = []
    skipped_no_file = 0
    skipped_short = 0

    for i, ticker in enumerate(tickers):
        path = os.path.join(PRICES_DIR, f"{ticker}.csv")
        if not os.path.exists(path):
            skipped_no_file += 1
            continue
        rets = ticker_monthly_logreturns(path)
        if rets is None or rets.dropna().empty:
            skipped_short += 1
            continue

        outlier_flag = has_outlier(rets)

        for ind_name, meta in INDICATORS.items():
            if ind_name not in fred.columns:
                continue
            ind_series = fred[ind_name]

            for win in WINDOWS:
                cutoff = fred.index.max() - pd.DateOffset(years=win["years"])
                rets_win = rets.loc[rets.index >= cutoff]
                ind_win = ind_series.loc[ind_series.index >= cutoff]

                result = correlate_window(rets_win, ind_win, win["min_obs"])
                if result is None:
                    continue
                n_obs, pearson, t_stat, p_val, spearman = result

                flags = []
                if outlier_flag:
                    flags.append("has_outlier_move")
                if n_obs < int(win["min_obs"] * 1.5):
                    flags.append("short_history")
                if meta["lagged"]:
                    flags.append("lagged_indicator")
                if meta["transform"] == "diff_bps":
                    flags.append("rate_bps_diff")
                else:
                    flags.append("logdiff")

                rows.append({
                    "ticker": ticker,
                    "indicator": ind_name,
                    "indicator_group": meta["group"],
                    "expected_thesis_sign": meta["expected_sign"],
                    "window_years": win["years"],
                    "n_obs": n_obs,
                    "pearson_r": round(pearson, 4) if not pd.isna(pearson) else None,
                    "pearson_t": round(t_stat, 3) if not pd.isna(t_stat) else None,
                    "pearson_p": round(p_val, 5) if not pd.isna(p_val) else None,
                    "spearman_r": round(spearman, 4) if not pd.isna(spearman) else None,
                    "quality_flags": "|".join(flags),
                    "last_updated": now,
                })

        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(tickers)} processed ({len(rows)} rows so far)")

    print(f"\nTotal pair-window observations: {len(rows)}")
    print(f"Skipped (no price file): {skipped_no_file}")
    print(f"Skipped (insufficient history): {skipped_short}")
    return pd.DataFrame(rows, columns=MATRIX_COLUMNS)


def build_rankings(matrix: pd.DataFrame) -> pd.DataFrame:
    """Top N + bottom N per indicator at the 5y window, joined to universe metadata."""
    universe = pd.read_csv(UNIVERSE_CSV)[["ticker", "tier", "subsector", "directional"]]
    sub = matrix[matrix["window_years"] == 5].copy()
    sub = sub.merge(universe, on="ticker", how="left")
    sub = sub.dropna(subset=["pearson_r"])

    out = []
    for ind in sorted(sub["indicator"].unique()):
        rows = sub[sub["indicator"] == ind].copy()
        if rows.empty:
            continue
        rows = rows.sort_values("pearson_r", ascending=False)
        top = rows.head(RANKINGS_TOP_N).assign(
            rank=range(1, min(RANKINGS_TOP_N, len(rows)) + 1),
            rank_side="top",
        )
        bot = rows.tail(RANKINGS_TOP_N).iloc[::-1].assign(
            rank=range(1, min(RANKINGS_TOP_N, len(rows)) + 1),
            rank_side="bottom",
        )
        out.append(top)
        out.append(bot)

    if not out:
        return pd.DataFrame()

    df = pd.concat(out, ignore_index=True)
    return df[[
        "indicator", "rank_side", "rank", "ticker", "pearson_r",
        "tier", "subsector", "directional", "n_obs", "quality_flags",
    ]]


def main():
    if not os.path.isdir(PRICES_DIR):
        raise SystemExit(f"Price directory not found: {PRICES_DIR}. Run scripts/04_fmp_prices.py first.")
    if not os.path.exists(FRED_CSV):
        raise SystemExit(f"FRED CSV not found: {FRED_CSV}. Run scripts/01_fred_pull.py first.")
    if not os.path.exists(UNIVERSE_CSV):
        raise SystemExit(f"Universe CSV not found: {UNIVERSE_CSV}. Run scripts/03_fmp_universe.py first.")

    matrix = build_matrix()
    matrix.to_csv(OUT_MATRIX, index=False)
    print(f"\nWrote correlation matrix: {len(matrix)} rows -> {OUT_MATRIX}")

    rankings = build_rankings(matrix)
    if not rankings.empty:
        rankings.to_csv(OUT_RANKINGS, index=False)
        print(f"Wrote rankings: {len(rankings)} rows -> {OUT_RANKINGS}")
    else:
        print("No rankings produced (matrix may be empty at 5y window).")

    # Sanity-check summary
    if not matrix.empty:
        print("\nSanity check — correlation distribution by indicator (5y window):")
        sub = matrix[matrix["window_years"] == 5]
        for ind in INDICATORS.keys():
            if ind not in sub["indicator"].values:
                continue
            r = sub[sub["indicator"] == ind]["pearson_r"].dropna()
            if len(r) == 0:
                continue
            print(f"  {ind:30s} n={len(r):3d}  median r={r.median():+.3f}  "
                  f"|r|>0.3: {(r.abs() > 0.3).sum():3d}  |r|>0.5: {(r.abs() > 0.5).sum():3d}")


if __name__ == "__main__":
    main()
