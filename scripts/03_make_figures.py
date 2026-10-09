"""Regenerate every figure in figures/ from the CSVs in data/.

Usage:  python scripts/03_make_figures.py
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.lines import Line2D

FIG = "figures"
CITY = {"Athens": "#c1121f", "Seville": "#e07a00", "Rome": "#1d4e89"}
GREY, DARK = "#c0c0c0", "#3a3a3a"
TIER = {"1 · Do now": "#1a7f37", "2 · One agreement away": "#3d7ea6",
        "3 · Needs a budget line": "#d08c1c", "4 · Programme-scale": "#a8332a"}


def style(sizes=(9, 8, 7)):
    base, mid, small = sizes
    plt.rcParams.update({
        "figure.facecolor": "white", "axes.facecolor": "white",
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.titlesize": base, "axes.labelsize": base,
        "legend.fontsize": mid, "xtick.labelsize": small, "ytick.labelsize": small,
        "axes.titlelocation": "left", "axes.titlepad": 8,
        "font.size": base, "savefig.bbox": None,
    })


def load():
    d = {n: pd.read_csv(f"data/{n}.csv") for n in
         ["heat_trends", "heat_trends_annual", "monitoring_inventory", "gap_matrix",
          "actions_by_ease", "solution_cost_impact"]}
    d["decadal"] = pd.read_csv("data/decadal_summary.csv", index_col=0)
    d["recent"] = pd.read_csv("data/recent_change_by_city.csv", index_col=0)
    d["lit"] = pd.read_csv("data/literature_counts_by_year.csv").rename(
        columns={"Unnamed: 0": "year"})
    return d


def fig_heat_exposure(d):
    """Four-panel measured heat exposure, ERA5 1950-2025."""
    ann, tr = d["heat_trends_annual"], d["heat_trends"]
    n_day = int((tr.mean_tmax_JJA_per_decade > tr.mean_tmin_JJA_per_decade).sum())
    fig = plt.figure(figsize=(11.5, 7.4))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.35, 1], hspace=0.45, wspace=0.30)

    ax = fig.add_subplot(gs[0, 0])
    for c in sorted(ann.city.unique()):
        g = ann[ann.city == c].sort_values("year")
        s = g.tropical_nights_20.rolling(11, center=True, min_periods=6).mean()
        f = c in CITY
        ax.plot(g.year, s, lw=2.0 if f else 1.0, color=CITY.get(c, GREY),
                zorder=3 if f else 2)
    for c, col in list(CITY.items()) + [("Valletta", "#8a8a8a")]:
        g = ann[ann.city == c].sort_values("year")
        y = g.tropical_nights_20.rolling(11, center=True, min_periods=6).mean().iloc[-6]
        ax.text(2026, y, c, color=col, va="center", ha="left", fontsize=7)
    ax.set_xlim(1950, 2038)
    ax.set_xlabel("Year"); ax.set_ylabel("Nights above 20 °C per year")
    ax.set_title("a  Warm nights are increasing in every city (11-year running mean)")

    axb = fig.add_subplot(gs[0, 1])
    s = tr.sort_values("longest_tn20_run_1996_2025"); y = np.arange(len(s))
    axb.hlines(y, s.longest_tn20_run_1961_1990, s.longest_tn20_run_1996_2025,
               color="#dcdcdc", lw=2.4, zorder=1)
    axb.scatter(s.longest_tn20_run_1961_1990, y, s=26, facecolor="white",
                edgecolor="#8a8a8a", lw=1.1, zorder=3, label="1961–1990")
    axb.scatter(s.longest_tn20_run_1996_2025, y, s=32,
                color=[CITY.get(c, DARK) for c in s.city], zorder=3, label="1996–2025")
    axb.set_yticks(y); axb.set_yticklabels(s.city)
    axb.set_xlabel("Longest unbroken run of nights above 20 °C (days)")
    axb.set_title("b  Recovery gap: consecutive warm nights")
    axb.legend(frameon=False, loc="lower right", fontsize=7)

    axc = fig.add_subplot(gs[1, 0])
    s2 = tr.sort_values("mean_tmax_JJA_per_decade"); yy = np.arange(len(s2)); h = 0.36
    axc.barh(yy + h / 2, s2.mean_tmax_JJA_per_decade, height=h, color="#d8a15a",
             label="Daytime maximum")
    axc.barh(yy - h / 2, s2.mean_tmin_JJA_per_decade, height=h, color="#4a4a4a",
             label="Nighttime minimum")
    axc.set_yticks(yy); axc.set_yticklabels(s2.city)
    axc.set_xlabel("Summer (JJA) warming rate, °C per decade")
    axc.set_title(f"c  Daytime warms faster in {n_day} of 12 cities — "
                  "but nights start nearer the harm threshold")
    axc.legend(frameon=False, loc="lower right", fontsize=7)

    axd = fig.add_subplot(gs[1, 1])
    s3 = tr.sort_values("days_over_35_1996_2025"); y3 = np.arange(len(s3))
    axd.hlines(y3, s3.days_over_35_1961_1990, s3.days_over_35_1996_2025,
               color="#dcdcdc", lw=2.4, zorder=1)
    axd.scatter(s3.days_over_35_1961_1990, y3, s=26, facecolor="white",
                edgecolor="#8a8a8a", lw=1.1, zorder=3)
    axd.scatter(s3.days_over_35_1996_2025, y3, s=32,
                color=[CITY.get(c, DARK) for c in s3.city], zorder=3)
    axd.set_yticks(y3); axd.set_yticklabels(s3.city)
    axd.set_xlabel("Days above 35 °C per year")
    axd.set_title("d  Hot-day burden: 1961–1990 vs 1996–2025")

    for a in fig.axes:
        a.margins(y=0.05)
    fig.suptitle("Southern European cities: measured heat exposure, ERA5 1950–2025",
                 x=0.008, ha="left", fontsize=10)
    fig.subplots_adjust(left=0.09, right=0.985, top=0.90, bottom=0.085)
    fig.savefig(f"{FIG}/heat_exposure_figure.png", dpi=300)
    plt.close(fig)


def fig_what_changed(d):
    """Decadal growth, recent change per city, and research attention."""
    dec, acc, lit = d["decadal"], d["recent"], d["lit"]
    ind = {"torrid_nights_25": ("Nights >25 °C", "#7d1128"),
           "days_over_35": ("Days >35 °C", "#c1121f"),
           "longest_tn20_run": ("Longest run", "#e07a00"),
           "tropical_nights_20": ("Nights >20 °C", "#1d4e89"),
           "cdd_18": ("Cooling demand", "#6a8ca8")}
    fig = plt.figure(figsize=(13.2, 4.9))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.05, 1, 1.05], wspace=0.42)

    ax = fig.add_subplot(gs[0, 0])
    rel = dec / dec.loc[1960]
    for col, (lab, c) in ind.items():
        ax.plot(rel.index, rel[col], marker="o", ms=4, lw=1.9, color=c)
    prev = None
    for v, col in sorted([(rel[c].iloc[-1], c) for c in ind], reverse=True):
        yv = v if prev is None or prev - v >= 0.42 else prev - 0.42
        ax.text(2021.0, yv, " " + ind[col][0], color=ind[col][1], fontsize=6.8,
                va="center", ha="left")
        prev = yv
    ax.axhline(1, color="#bbbbbb", lw=0.9, ls="--")
    ax.set_xlim(1958, 2033); ax.set_ylim(0.5, 7.2)
    ax.set_xticks(dec.index)
    ax.set_xticklabels([f"{i}s" for i in dec.index], rotation=45, ha="right")
    ax.set_ylabel("Change relative to the 1960s (×)")
    ax.set_title("a  Extreme-heat indicators grew fastest")

    axb = fig.add_subplot(gs[0, 1])
    o = acc.sort_values("tn20_change"); yb = np.arange(len(o))
    axb.barh(yb, o.tn20_change, height=0.66,
             color=["#8a8a8a" if v < 0 else "#c1121f" for v in o.tn20_change])
    axb.axvline(0, color="#555555", lw=0.9)
    axb.set_yticks(yb); axb.set_yticklabels(o.index, fontsize=7.6)
    for i, v in enumerate(o.tn20_change):
        axb.text(v + (0.5 if v >= 0 else -0.5), i, f"{v:+.1f}", va="center",
                 ha="left" if v >= 0 else "right", fontsize=6.8, color="#444444")
    axb.set_xlim(-4.5, 26)
    axb.set_xlabel("Change in warm nights per year")
    n_up = int((acc.tn20_change > 0).sum())
    axb.set_title(f"b  Last 15 years vs the 15 before:\n    up in {n_up} of "
                  f"{len(acc)} cities")

    axc = fig.add_subplot(gs[0, 2])
    foc = {"carbon_aware_computing": "#1a7f37", "indoor_overheating": "#c1121f",
           "low_cost_urban_temperature": "#e07a00",
           "heat_health_early_warning": "#1d4e89"}
    for col in lit.columns:
        if col == "year":
            continue
        f = col in foc
        axc.plot(lit.year, lit[col].clip(lower=1), lw=2.0 if f else 1.0,
                 color=foc.get(col, "#cccccc"), zorder=3 if f else 2)
    axc.set_yscale("log"); axc.set_xlim(2015, 2032)
    for col, c in foc.items():
        axc.text(2025.3, lit[col].iloc[-1], " " + col.replace("_", " "),
                 color=c, fontsize=6.8, va="center")
    axc.set_ylabel("Publications per year"); axc.set_xlabel("Year")
    axc.set_title("c  Research attention is growing,\n    newest topics fastest")

    fig.suptitle("What changed: heat exposure and research attention over time",
                 x=0.006, ha="left", fontsize=10.5)
    fig.subplots_adjust(left=0.062, right=0.99, top=0.80, bottom=0.17)
    fig.savefig(f"{FIG}/what_changed.png", dpi=300)
    plt.close(fig)


def fig_landscape(d):
    """Inventory coupling by layer, and gap severity by stage."""
    inv, gm = d["monitoring_inventory"].copy(), d["gap_matrix"]
    inv["coupled"] = inv.coupled_to_actuator.astype(str).str.strip().str.startswith("Yes")
    lay = (inv.groupby("layer").agg(total=("system", "size"), coupled=("coupled", "sum"))
           .sort_values("total"))
    lay["rest"] = lay.total - lay.coupled
    short = {
        "Emission - large point sources": "Big emission sources",
        "Emission - diffuse and small sources": "Small/diffuse emissions",
        "Emission - response to detection": "Was the leak fixed?",
        "Concentration and climate state": "Atmosphere & climate state",
        "Hazard - outdoor heat forecast": "Outdoor heat forecast",
        "Hazard - intra-urban heat": "Heat within a city",
        "Hazard - indoor heat": "Heat inside homes",
        "Exposure": "Who is exposed", "Vulnerability": "Who is vulnerable",
        "Intervention - passive": "Passive measures in place",
        "Intervention - active": "Active measures in place",
        "Behaviour": "Did anyone act on warnings",
        "Outcome - mortality": "Deaths", "Outcome - morbidity": "Illness",
        "Accountability - adaptation spend": "Did the spending work"}

    fig = plt.figure(figsize=(12.4, 5.9))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.12, 1], wspace=0.34)
    ax = fig.add_subplot(gs[0, 0]); y = np.arange(len(lay))
    ax.barh(y, lay.coupled, height=0.64, color="#1a7f37", label="Connected to an action")
    ax.barh(y, lay.rest, left=lay.coupled, height=0.64, color="#d9d9d9",
            edgecolor="#b0b0b0", lw=0.7, label="Produces data only")
    ax.set_yticks(y); ax.set_yticklabels(lay.index, fontsize=8)
    for i, (c, t) in enumerate(zip(lay.coupled, lay.total)):
        ax.text(t + 0.18, i, f"{c}/{t}", va="center", fontsize=7.2, color="#444444")
    ax.set_xlabel("Number of monitoring systems"); ax.set_xlim(0, 11.6)
    ax.set_title(f"a  Most monitoring is not wired to anything\n"
                 f"    {int(lay.coupled.sum())} of {int(lay.total.sum())} "
                 "systems trigger an action")
    ax.legend(frameon=False, loc="lower right", fontsize=7.4)

    axb = fig.add_subplot(gs[0, 1])
    g = gm.sort_values("gap_severity_0to5"); y2 = np.arange(len(g))
    cols = ["#1a7f37" if v <= 1 else "#d08c1c" if v <= 3 else "#b3261e"
            for v in g.gap_severity_0to5]
    axb.barh(y2, g.gap_severity_0to5, height=0.66, color=cols)
    for i, v in enumerate(g.gap_severity_0to5):
        if v == 0:
            axb.plot([0], [i], marker="|", ms=8, color="#1a7f37")
    axb.set_yticks(y2)
    axb.set_yticklabels([short.get(s, s) for s in g.stage], fontsize=7.8)
    axb.set_xlabel("Gap severity (0 = well observed, 5 = unmeasured)")
    axb.set_xlim(-0.08, 5.6); axb.set_xticks(range(6))
    n5 = int((gm.gap_severity_0to5 == 5).sum())
    axb.set_title(f"b  {n5} stages of the harm chain\n    are effectively unmeasured")
    axb.legend(handles=[Line2D([], [], marker="s", ls="", color=c, label=l) for c, l in
                        [("#1a7f37", "Well observed"), ("#d08c1c", "Partial"),
                         ("#b3261e", "Blind spot")]],
               frameon=False, loc="lower right", fontsize=7.4)
    axb.margins(y=0.025)
    fig.suptitle("The monitoring landscape: 46 systems, and where the chain breaks",
                 x=0.006, ha="left", fontsize=10.5)
    fig.subplots_adjust(left=0.145, right=0.985, top=0.82, bottom=0.12)
    fig.savefig(f"{FIG}/monitoring_landscape.png", dpi=300)
    plt.close(fig)


def fig_harm_chain(d):
    """Plain-language harm pathway plus the warm-night change."""
    tr = d["heat_trends"]
    steps = [
        ("The weather turns hot", "Satellites and weather services track this very well", "w"),
        ("A heat warning is issued", "Every southern EU country has a warning system", "w"),
        ("The warning reaches the person", "Nobody checks whether it arrived or was understood", "b"),
        ("Their home heats up", "Almost nobody measures temperature inside at-risk homes", "b"),
        ("The home stays hot all night", "Night after night, the body never gets to cool down", "b"),
        ("They become ill, or die", "Counted weeks or months later — too late to act on", "p"),
    ]
    col = {"w": "#1a7f37", "p": "#d08c1c", "b": "#b3261e"}
    lab = {"w": "We watch this well", "p": "We count it, but too late",
           "b": "We are not watching"}
    fig = plt.figure(figsize=(12.8, 6.8))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.45, 1], wspace=0.16)
    ax = fig.add_subplot(gs[0, 0]); ax.axis("off")
    ax.set_xlim(0, 10); ax.set_ylim(-0.25, len(steps))
    for i, (title, sub, kind) in enumerate(steps):
        yb = len(steps) - 1 - i
        ax.add_patch(FancyBboxPatch((0.3, yb + 0.16), 9.1, 0.68,
                     boxstyle="round,pad=0.02,rounding_size=0.07",
                     facecolor=col[kind], alpha=0.12, edgecolor=col[kind], lw=1.4))
        ax.add_patch(plt.Rectangle((0.3, yb + 0.16), 0.12, 0.68,
                                   facecolor=col[kind], edgecolor="none"))
        ax.text(0.66, yb + 0.64, f"{i + 1}.  {title}", fontsize=10.5, va="center",
                fontweight="bold", color="#1a1a1a")
        ax.text(0.66, yb + 0.34, sub, fontsize=8.6, va="center", color="#454545")
        if i < len(steps) - 1:
            ax.annotate("", xy=(0.9, yb + 0.12), xytext=(0.9, yb - 0.02),
                        arrowprops=dict(arrowstyle="-|>", color="#a0a0a0", lw=1.4))
    ax.set_title("How heat actually kills — and where we stop watching", fontsize=12, pad=12)
    ax.legend(handles=[Line2D([], [], marker="s", ls="", ms=9, color=col[k], label=lab[k])
                       for k in ("w", "p", "b")],
              frameon=False, loc="lower left", bbox_to_anchor=(0.0, -0.045),
              ncol=3, fontsize=8.6)

    axb = fig.add_subplot(gs[0, 1])
    s = tr.sort_values("tropical_nights_20_1996_2025"); y = np.arange(len(s))
    axb.hlines(y, s.tropical_nights_20_1961_1990, s.tropical_nights_20_1996_2025,
               color="#e2e2e2", lw=3, zorder=1)
    axb.scatter(s.tropical_nights_20_1961_1990, y, s=40, facecolor="white",
                edgecolor="#777777", lw=1.3, zorder=3, label="1961–1990")
    axb.scatter(s.tropical_nights_20_1996_2025, y, s=46, color="#b3261e", zorder=3,
                label="1996–2025 (today)")
    axb.set_yticks(y); axb.set_yticklabels(s.city, fontsize=9)
    axb.set_xlabel("Nights per year too warm to cool down (above 20 °C)")
    axb.set_title("Hot nights are what changed most", fontsize=12, pad=12)
    axb.legend(frameon=False, loc="lower right", fontsize=8.4)
    axb.margins(y=0.04)
    fig.subplots_adjust(left=0.012, right=0.985, top=0.885, bottom=0.115)
    fig.savefig(f"{FIG}/how_heat_harms.png", dpi=300)
    plt.close(fig)


def fig_actions(d):
    """Deployment burden and time-to-result per action."""
    ez = d["actions_by_ease"].sort_values(
        ["ease_burden", "weeks_to_first_result"]).iloc[::-1].reset_index(drop=True)
    y = np.arange(len(ez))
    fig, (ax, axr) = plt.subplots(1, 2, figsize=(12.2, 5.9), width_ratios=[1.9, 1],
                                  gridspec_kw=dict(wspace=0.04))
    for c, lab, colr in [("hardware", "Hardware to install", "#5b7c99"),
                         ("legal", "Legal or data agreement", "#9c6b98"),
                         ("coordination", "Institutional coordination", "#c98b4b"),
                         ("money", "Budget above 1 EUR/person/yr", "#8a8a8a")]:
        left = ez[["hardware", "legal", "coordination", "money"]].loc[
            :, :c].iloc[:, :-1].sum(axis=1)
        ax.barh(y, ez[c], left=left, height=0.6, color=colr, label=lab,
                edgecolor="white", lw=0.6)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{r.id}  {r.solution[:42]}" for _, r in ez.iterrows()],
                       fontsize=7.4)
    for t, (_, r) in zip(ax.get_yticklabels(), ez.iterrows()):
        t.set_color(TIER[r.ease_tier])
    ax.set_xlim(0, 7.4); ax.set_xticks(range(0, 7))
    ax.set_xlabel("Deployment burden (count of blocking conditions)")
    ax.set_title("a  What actually blocks each action")
    ax.legend(frameon=False, loc="upper right", bbox_to_anchor=(1.0, 0.34), fontsize=7)

    axr.barh(y, ez.weeks_to_first_result, height=0.6,
             color=[TIER[t] for t in ez.ease_tier])
    for i, v in enumerate(ez.weeks_to_first_result):
        axr.text(v + 0.7, i, f"{v}", va="center", fontsize=7, color="#444444")
    axr.set_yticks(y); axr.set_yticklabels([])
    axr.set_xlim(0, 42); axr.set_xlabel("Weeks to first measurable result")
    axr.set_title("b  Time to evidence")
    axr.legend(handles=[Line2D([], [], marker="s", ls="", color=TIER[t], label=t)
                        for t in sorted(TIER)],
               frameon=False, loc="upper right", bbox_to_anchor=(1.01, 1.0), fontsize=7)
    for a in (ax, axr):
        a.margins(y=0.03)
    fig.suptitle("Twelve actions ranked by ease of deployment, not by cost",
                 x=0.006, ha="left", fontsize=10.5)
    fig.subplots_adjust(left=0.30, right=0.985, top=0.885, bottom=0.10)
    fig.savefig(f"{FIG}/actions_by_ease.png", dpi=300)
    plt.close(fig)


def fig_cost(d):
    """Cost per person covered, proposals against conventional measures."""
    c2 = d["solution_cost_impact"].sort_values("eur_per_person_year").reset_index(drop=True)
    ev = {2.0: "#f0c3c3", 2.5: "#dd7070", 3.0: "#c1121f"}
    bn = {2.0: "#d6d6d6", 2.5: "#a8a8a8", 3.0: "#5a5a5a"}
    fig, ax = plt.subplots(figsize=(9.8, 5.8))
    for i, r in c2.iterrows():
        prop = r["kind"] == "proposed"
        v = max(r.eur_per_person_year, 0.0025)
        ax.hlines(i, 0.0025, v, color="#e4e4e4", lw=1.3, zorder=1)
        ax.scatter(v, i, s=110, marker="o" if prop else "s",
                   color=(ev if prop else bn)[r.evidence_score],
                   edgecolor="none" if prop else "#333333", lw=0.9, zorder=3)
        txt = ("≈0" if r.eur_per_person_year < 0.005
               else (f"{r.eur_per_person_year:.3f}".rstrip("0").rstrip(".")
                     if r.eur_per_person_year < 1 else f"{r.eur_per_person_year:,.0f}"))
        ax.text(v * 1.55, i, txt, va="center", fontsize=6.6, color="#444444")
    ax.set_yticks(np.arange(len(c2)))
    ax.set_yticklabels([r.label + ("" if r["kind"] == "proposed" else "  (conventional)")
                        for _, r in c2.iterrows()])
    for t, (_, r) in zip(ax.get_yticklabels(), c2.iterrows()):
        t.set_color("#c1121f" if r["kind"] == "proposed" else "#3a3a3a")
    ax.set_xscale("log"); ax.set_xlim(0.0025, 4000)
    ax.set_xticks([0.01, 0.1, 1, 10, 100, 1000])
    ax.set_xticklabels(["0.01", "0.1", "1", "10", "100", "1,000"])
    ax.set_xlabel("Estimated annual cost per person covered "
                  "(EUR, log scale) — lower is better")
    n = int((c2[c2.kind == "proposed"].eur_per_person_year < 1).sum())
    ax.set_title(f"{n} of 12 proposals cost under 1 EUR per person per year")
    ax.invert_yaxis(); ax.margins(y=0.03)
    ax.legend(handles=[
        Line2D([], [], marker="o", ls="", color=ev[3.0], label="Proposed — high evidence"),
        Line2D([], [], marker="o", ls="", color=ev[2.5], label="Proposed — medium-high"),
        Line2D([], [], marker="o", ls="", color=ev[2.0], label="Proposed — medium"),
        Line2D([], [], marker="s", ls="", mfc=bn[3.0], mec="#333333",
               label="Conventional measure")],
        frameon=False, loc="upper right", bbox_to_anchor=(0.995, 0.30), fontsize=7.2)
    fig.tight_layout()
    fig.savefig(f"{FIG}/solution_cost_impact.png", dpi=300)
    plt.close(fig)


def main():
    os.makedirs(FIG, exist_ok=True)
    style()
    d = load()
    for fn in (fig_heat_exposure, fig_what_changed, fig_landscape,
               fig_harm_chain, fig_actions, fig_cost):
        fn(d)
        print(f"ok {fn.__name__}")


if __name__ == "__main__":
    main()
