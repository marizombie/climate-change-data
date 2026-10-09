"""Compute heat indicators and trends from the ERA5 daily series.

Inputs : data/era5_daily.parquet          (from 01_fetch_era5.py)
Outputs: data/heat_trends_annual.csv      per city-year indicators
         data/heat_trends.csv             OLS trends + period means per city
         data/decadal_summary.csv         decadal means across all cities
         data/recent_change_by_city.csv   2011-2025 vs 1996-2010

Indicator definitions
---------------------
days_over_35 / days_over_40   days with daily maximum above 35 / 40 C
tropical_nights_20            nights with daily minimum above 20 C
torrid_nights_25              nights with daily minimum above 25 C
longest_tn20_run              longest unbroken run of tropical nights in the
                              year - a proxy for consecutive nights without
                              physiological recovery
cdd_18                        cooling degree-days, base 18 C
mean_tmax_JJA / mean_tmin_JJA June-August means of daily max / min

Thresholds are the conventional European definitions, not physiological
constants; risk is continuous.

Usage:  python scripts/02_compute_indicators.py
"""
import numpy as np
import pandas as pd
from scipy import stats

METRICS = ["days_over_35", "days_over_40", "tropical_nights_20", "torrid_nights_25",
           "cdd_18", "mean_tmax_JJA", "mean_tmin_JJA", "longest_tn20_run"]


def longest_run(mask):
    """Longest run of consecutive True values."""
    best = cur = 0
    for v in mask:
        cur = cur + 1 if v else 0
        best = max(best, cur)
    return best


def annual_indicators(raw):
    raw = raw.copy()
    raw["year"] = raw.time.dt.year
    rows = []
    for (city, year), g in raw.groupby(["city", "year"]):
        tx, tn = g.temperature_2m_max.values, g.temperature_2m_min.values
        jja = g[g.time.dt.month.isin([6, 7, 8])]
        rows.append({
            "city": city, "year": year,
            "days_over_35": int((tx > 35).sum()),
            "days_over_40": int((tx > 40).sum()),
            "tropical_nights_20": int((tn > 20).sum()),
            "torrid_nights_25": int((tn > 25).sum()),
            "longest_hot_run_35": longest_run(tx > 35),
            "longest_tn20_run": longest_run(tn > 20),
            "cdd_18": float(np.clip(g.temperature_2m_mean.values - 18, 0, None).sum()),
            "mean_tmax_JJA": float(jja.temperature_2m_max.mean()),
            "mean_tmin_JJA": float(jja.temperature_2m_min.mean()),
        })
    return pd.DataFrame(rows)


def trends(ann):
    rows = []
    for city, g in ann.groupby("city"):
        r = {"city": city}
        for m in METRICS:
            sl = stats.linregress(g.year, g[m])
            r[f"{m}_per_decade"] = round(sl.slope * 10, 2)
            r[f"{m}_p"] = sl.pvalue
            r[f"{m}_1961_1990"] = round(g[g.year.between(1961, 1990)][m].mean(), 1)
            r[f"{m}_1996_2025"] = round(g[g.year.between(1996, 2025)][m].mean(), 1)
        rows.append(r)
    tr = pd.DataFrame(rows)
    tr["tn20_ratio"] = (tr.tropical_nights_20_1996_2025
                        / tr.tropical_nights_20_1961_1990).round(2)
    tr["over35_ratio"] = (tr.days_over_35_1996_2025
                          / tr.days_over_35_1961_1990.replace(0, np.nan)).round(2)
    return tr


def recent_change(ann):
    def win(y0, y1, col):
        return ann[ann.year.between(y0, y1)].groupby("city")[col].mean()
    acc = pd.DataFrame({
        "tn20_1996_2010": win(1996, 2010, "tropical_nights_20").round(1),
        "tn20_2011_2025": win(2011, 2025, "tropical_nights_20").round(1),
        "run_1996_2010": win(1996, 2010, "longest_tn20_run").round(1),
        "run_2011_2025": win(2011, 2025, "longest_tn20_run").round(1),
        "d35_1996_2010": win(1996, 2010, "days_over_35").round(1),
        "d35_2011_2025": win(2011, 2025, "days_over_35").round(1),
    })
    for k in ("tn20", "run", "d35"):
        acc[f"{k}_change"] = (acc[f"{k}_2011_2025"] - acc[f"{k}_1996_2010"]).round(1)
    return acc.sort_values("tn20_change", ascending=False)


def main():
    raw = pd.read_parquet("data/era5_daily.parquet")
    ann = annual_indicators(raw)
    ann.to_csv("data/heat_trends_annual.csv", index=False)

    trends(ann).to_csv("data/heat_trends.csv", index=False)

    ann["decade"] = (ann.year // 10) * 10
    dec = (ann[ann.decade >= 1960]
           .groupby("decade")[["tropical_nights_20", "days_over_35",
                               "longest_tn20_run", "torrid_nights_25", "cdd_18"]]
           .mean().round(1))
    dec.to_csv("data/decadal_summary.csv")
    recent_change(ann).to_csv("data/recent_change_by_city.csv")

    print(f"{len(ann)} city-years, {ann.city.nunique()} cities, "
          f"{ann.year.min()}-{ann.year.max()}")
    print(f"nights>25C, 2020s vs 1960s: "
          f"{dec.loc[2020, 'torrid_nights_25'] / dec.loc[1960, 'torrid_nights_25']:.1f}x")


if __name__ == "__main__":
    main()
