import pandas as pd, numpy as np, html as H

ART = {  # artifact_id for {{artifact:art_...}} markers
 "what_changed":"d7322787-7884-40b5-a9d2-f79bb806f72f",
 "landscape":"32a38fbc-4bcf-4e9f-b84d-a8cf78aad34a",
 "harm":"23a7c9a5-ba9a-40b6-84a8-c91410c7237e",
 "heat":"9899215b-ea35-4b97-98b0-599dc7de19a3",
 "ease":"89f64e48-8598-4ba6-ac95-b3619138afa5",
 "cost":"2d0fb790-deb3-41d5-99f1-75131c55ca85",
}
FILES = {  # filenames for static-site / repo builds
 "what_changed":"what_changed.png", "landscape":"monitoring_landscape.png",
 "harm":"how_heat_harms.png", "heat":"heat_exposure_figure.png",
 "ease":"actions_by_ease.png", "cost":"solution_cost_impact.png",
}
MODE = {"v": "relative"}   # "relative" for repo/site builds; "artifact" is host-internal

def img(k, cap):
    src = (f"{{{{artifact:art_{ART[k]}}}}}" if MODE["v"] == "artifact"
           else f"figures/{FILES[k]}")
    return (f'<figure><img src="{src}" alt="{H.escape(cap)}">'
            f'<figcaption>{cap}</figcaption></figure>')

def table(df, idx=False, cls=""):
    return df.to_html(index=idx, classes=f"tbl {cls}", border=0, escape=True,
                      na_rep="—", float_format=lambda v: f"{v:,.2f}".rstrip("0").rstrip("."))

def build(d, counts):
    inv, gm, sol, ez, tr, dec, acc, lit, cost = (d[k] for k in
        ["inv","gm","sol","ez","tr","dec","acc","lit","cost"])
    P = []
    A = P.append
    site = MODE["v"] == "relative"
    A(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Digital climate monitoring — consolidated data report</title>""")
    if site:
        A('<link rel="stylesheet" href="assets/style.css">\n<script src="assets/common.js"></script>')
    A(f"""<style>
:root{{--bg:#fbfaf8;--surface-2:#f3f1ed;--ink:#1b1a19;--ink-2:#4a4744;--muted:#6e6a65;--line:#e4e0da;
--line-2:#d4cfc7;--accent:#b9381b;--amber:#b7791f;--amber-soft:#fbf1e1;--ok:#1a7046;--cool:#1f5f8b;color-scheme:light}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#151413;--surface-2:#262422;--ink:#f1eeea;
--ink-2:#cdc8c1;--muted:#9d978f;--line:#34312e;--line-2:#45413c;--accent:#f0714f;--amber:#e8a33d;--amber-soft:#33280f;
--ok:#6cc596;--cool:#7fb6dc;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#151413;--surface-2:#262422;--ink:#f1eeea;--ink-2:#cdc8c1;--muted:#9d978f;--line:#34312e;
--line-2:#45413c;--accent:#f0714f;--amber:#e8a33d;--amber-soft:#33280f;--ok:#6cc596;--cool:#7fb6dc;color-scheme:dark}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink)}}
.report a{{color:var(--cool)}}
.report{{font:15px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
max-width:1120px;margin:0 auto;padding:40px 16px 90px}}
@media (min-width:720px){{.report{{padding:40px 28px 90px}}}}
.report h1{{font-size:30px;line-height:1.25;margin:0 0 6px;letter-spacing:-.4px}}
.report h2{{font-size:21px;margin:46px 0 8px;padding-top:18px;border-top:2px solid var(--ink)}}
.report h3{{font-size:16px;margin:28px 0 6px;color:var(--ink-2)}}
.report .sub{{color:var(--muted);font-size:14px;margin:0 0 26px}}
.report p{{margin:10px 0}}
.report figure{{margin:22px 0}} .report figure img{{width:100%;border:1px solid var(--line);border-radius:5px}}
.report figcaption{{font-size:12.5px;color:var(--muted);margin-top:7px;line-height:1.5}}
.report table.tbl{{border-collapse:collapse;width:100%;font-size:12.5px;margin:12px 0 6px}}
.report .tbl th{{text-align:left;background:var(--surface-2);padding:7px 9px;border-bottom:2px solid var(--line-2);
font-weight:600;vertical-align:bottom}}
.report .tbl td{{padding:6px 9px;border-bottom:1px solid var(--line);vertical-align:top}}
.report .tbl tr:hover td{{background:var(--surface-2)}}
.report .tbl-wrap{{overflow-x:auto;margin:12px 0}}
.report .kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:12px;margin:22px 0}}
.report .kpi{{background:transparent;border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:4px;padding:11px 13px}}
.report .kpi .n{{font-size:25px;font-weight:650;letter-spacing:-.5px}}
.report .kpi .l{{font-size:11.5px;color:var(--muted);line-height:1.4;margin-top:3px}}
.report .kpi.g{{border-left-color:var(--ok)}} .report .kpi.a{{border-left-color:var(--amber)}}
.report .note{{background:var(--surface-2);color:var(--ink);border-left:3px solid var(--line-2);border-radius:0;
padding:11px 15px;margin:18px 0;font-size:13.5px}}
.report .warn{{background:var(--amber-soft);border-left:3px solid var(--amber)}}
.report .lede{{font-size:16.5px;line-height:1.6}}
.report footer{{margin-top:54px;padding-top:16px;border-top:1px solid var(--line);font-size:12px;color:var(--muted)}}
.report code{{background:var(--surface-2);padding:1px 5px;border-radius:3px;font-size:12.5px}}
</style></head><body>""")
    if site:
        A("""<header class="site-header">
  <div class="wrap">
    <a class="brand" href="./"><span class="brand-mark" aria-hidden="true"></span>Climate Heat Monitoring</a>
    <nav class="site-nav" aria-label="Main">
      <a href="./#datasets">Datasets</a>
      <a href="explore.html">Explore</a>
      <a href="report.html" aria-current="page">Report</a>
      <a href="./#use">Use &amp; cite</a>
      <a href="./#maintenance">Maintenance</a>
      <a data-link="repo" href="#">GitHub</a>
    </nav>
    <button class="theme-toggle" type="button" aria-label="Toggle theme">☾</button>
  </div>
</header>""")
    A('<main class="report">')
    if not site:
        A('<nav class="sub"><a href="./">Open dataset home</a> · <a href="explore.html">Explore and download the data</a></nav>')
    A("<h1>Digital climate monitoring: consolidated data report</h1>")
    A('<p class="sub">Every dataset gathered in this project, what it shows, how it changed over time, '
      'and what follows from it. Nine tables, six figures, 12 costed actions.</p>')

    A(f"""<div class="kpis">
<div class="kpi"><div class="n">{counts['n_sys']}</div><div class="l">monitoring systems inventoried across {counts['n_layer']} layers</div></div>
<div class="kpi"><div class="n">{counts['n_coupled']} of {counts['n_sys']}</div><div class="l">are connected to an action; the rest produce data only</div></div>
<div class="kpi"><div class="n">{counts['n_blind']}</div><div class="l">stages of the harm chain are effectively unmeasured</div></div>
<div class="kpi g"><div class="n">{counts['n_days']:,}</div><div class="l">daily temperature records analysed, 12 cities, 1950–2025</div></div>
<div class="kpi a"><div class="n">{counts['torrid_mult']}×</div><div class="l">increase in nights above 25 °C, 1960s to 2020s</div></div>
<div class="kpi g"><div class="n">{counts['n_cheap']} of 12</div><div class="l">proposed actions cost under €1 per person per year</div></div>
</div>""")

    A('<div class="note"><strong>How to read this.</strong> Sections 1–3 are evidence: what exists, '
      'what it misses, and how the climate signal moved. Sections 4–5 are response: what to do, ranked by '
      'how hard it is to start. Section 6 states what would prove the argument wrong. Every table here can be '
      'searched, filtered and downloaded as CSV in the <a href="explore.html">data explorer</a>, and the whole '
      'set is bundled in <a href="data/climate-heat-monitoring-data.zip">one zip</a>.</div>')

    # ---- 1 landscape
    A("<h2>1. What is being monitored</h2>")
    A("<p>Forty-six operational systems were inventoried across eight layers, each scored on resolution, "
      "latency, openness, funding model, and — the column that turned out to matter most — whether the "
      "output is wired to any actuator that changes a physical outcome without a human choosing to act.</p>")
    A(img("landscape","Left: monitoring systems by layer, split by whether the output triggers an action. "
          "Right: severity of the observation gap at each stage of the chain from emission to health outcome."))
    A(f"<p>The split is the finding. Space-based greenhouse-gas observation and urban environmental sensing — "
      f"{counts['n_space']+counts['n_urban']} systems between them — trigger nothing at all. The layers that do act "
      f"(regulatory reporting, grid telemetry, hazard warning) act because a regulation or a market obliges them to, "
      f"not because the sensing is better.</p>")
    A("<h3>Table 1 — Monitoring systems by layer</h3>")
    A('<div class="tbl-wrap">'+table(d["lay"], idx=True)+"</div>")
    A("<h3>Table 2 — Full inventory (46 systems)</h3>")
    A('<div class="tbl-wrap">'+table(inv.drop(columns=["coupled"], errors="ignore"))+"</div>")

    # ---- 2 gaps
    A("<h2>2. What the monitoring misses</h2>")
    A("<p>Walking the causal chain from emission to health outcome and scoring how well each stage is "
      "observed produces four stages at severity 5 — essentially unmeasured.</p>")
    A(img("harm","The harm pathway in plain language. Green: well observed. Red: not observed. "
          "The blind band sits exactly where a person could still be helped."))
    A("<h3>Table 3 — Gap matrix</h3>")
    A('<div class="tbl-wrap">'+table(gm)+"</div>")
    A('<div class="note"><strong>Updated October 2026.</strong> Two rows changed. Indoor heat monitoring is no '
      'longer unproven — 2026 brought a Dutch crowdsourced study (<em>QJRMS</em>), work on Boulder mobile homes '
      '(<em>Environ. Res. Commun.</em>), a New Zealand household study, and a municipal sensor programme in Miami. '
      'And on methane, a UN satellite alert programme reports 40+ super-emitters curbed since 2023. Both gaps remain '
      'open — feasibility is now demonstrated, deployment and coupling are not — so the severity scores are unchanged '
      'while the evidence column is rewritten.</div>')

    # ---- 3 change
    A("<h2>3. How it changed</h2>")
    A("<p>Daily maximum and minimum temperatures were pulled from ERA5 reanalysis for twelve southern European "
      f"cities over 1950–2025 ({counts['n_days']:,} city-days), and indicators computed per city-year.</p>")
    A(img("what_changed","Left: heat indicators by decade, relative to the 1960s. Middle: change in warm nights, "
          "last 15 years against the 15 before. Right: annual publication counts by research theme (log scale)."))
    A("<h3>3.1 The extremes moved faster than the averages</h3>")
    A(f"<p>Between the 1960s and the 2020s, nights above 20 °C rose {counts['tn_mult']}× while nights above "
      f"<em>25 °C</em> rose {counts['torrid_mult']}× and days above 35 °C {counts['d35_mult']}×. The further into the "
      "tail you look, the faster the growth — which is why averages understate the change people actually feel. "
      "The 2020s row covers 2020–2025 only.</p>")
    A("<h3>Table 4 — Decadal means across all twelve cities</h3>")
    A(table(dec, idx=True))
    A("<h3>3.2 The last fifteen years</h3>")
    A(f"<p>Comparing 2011–2025 against 1996–2010: warm nights increased in {counts['tn_up']} of 12 cities "
      f"(mean +{counts['tn_mean']} nights/year), the longest unbroken warm-night run in {counts['run_up']} of 12, "
      f"and days above 35 °C in {counts['d35_up']} of 12. "
      f"{counts['down_cities']} are the exceptions on warm nights, both slightly down. Rome (+20.5 nights) and "
      "Madrid (+19.0) moved most — both starting from a historically low base, which is why a tripling there still "
      "leaves them below Valletta's absolute level.</p>")
    A("<h3>Table 5 — Change by city, last 15 years vs the previous 15</h3>")
    A(table(acc, idx=True))
    A("<h3>3.3 The full trend record</h3>")
    A(img("heat","Measured heat exposure, 1950–2025. (a) warm nights rising in every city; (b) the recovery gap — "
          "consecutive warm nights; (c) day vs night warming rates; (d) hot-day burden then and now."))
    A('<div class="warn note"><strong>A result that contradicted our expectation.</strong> We set out expecting '
      f"nights to be warming faster than days. They are not: summer maxima rise at {counts['tmax_rate']} °C/decade "
      f"against {counts['tmin_rate']} for minima, with days faster in {counts['faster_day']} of 12 cities. We report "
      "it as found. The case for focusing on nights survives on distribution rather than rate — night minima sit "
      "close to the threshold at which the body cannot recover, so the slower trend crosses that line on far more "
      "nights than the faster daytime trend crosses 40 °C.</div>")
    A("<h3>Table 6 — Trends and period means by city</h3>")
    A('<div class="tbl-wrap">'+table(tr)+"</div>")
    A("<h3>3.4 Research attention</h3>")
    A("<p>Publication counts per theme, 2015–2025, from a structured bibliographic query. Every theme grew; the "
      "newest ones grew from near-zero bases, which says more about when a term entered use than about how much "
      "is known. Carbon-aware computing went from single digits to a few hundred papers a year; low-cost urban "
      "temperature sensing grew roughly tenfold.</p>")
    A("<h3>Table 7 — Publications per year by theme</h3>")
    A('<div class="tbl-wrap">'+table(lit)+"</div>")
    A('<div class="warn note"><strong>Not refreshed.</strong> These counts run to 2025. The intended refresh '
      "through 2026 could not run because the bibliographic API credential was not approved for this session. "
      "No finding in this report depends on them.</div>")

    # ---- 4 actions
    A("<h2>4. What we can do</h2>")
    A("<p>Twelve interventions, each specified with capital and running cost, deploying institution, expected "
      "effect, evidence strength, and explicit failure modes. All twelve are compatible with continued "
      "technological development; one of them consists of running more computation, scheduled differently.</p>")
    A(img("ease","Left: what blocks each action — hardware, legal agreements, coordination, budget. "
          "Right: weeks until a first measurable result."))
    A(f"<p>Ranking by ease rather than cost reorders the list substantially. The cheapest item in the catalogue "
      f"(€0.004 per person per year) sits in the third tier because it needs a mandate; the item with zero cost "
      "and zero permission requirements sits first.</p>")
    A("<h3>Table 8 — Actions ranked by ease of deployment</h3>")
    A('<div class="tbl-wrap">'+table(ez)+"</div>")
    A("<h3>Table 9 — Full solution catalogue</h3>")
    A('<div class="tbl-wrap">'+table(sol)+"</div>")

    # ---- 5 cost
    A("<h2>5. What it costs</h2>")
    A(img("cost","Estimated annual cost per person covered, proposals against conventional measures, log scale."))
    A(f"<p>{counts['n_cheap']} of the 12 proposals cost under €1 per person per year with capital amortised over "
      "five years, against roughly €120 for room air-conditioner subsidies and €600 for deep envelope retrofit. "
      "The two most expensive proposals remain well below the conventional measures they partly substitute for.</p>")
    A("<h3>Table 10 — Cost comparison including conventional benchmarks</h3>")
    A(table(cost))
    A('<div class="note"><strong>These are engineering estimates, not procurement quotes.</strong> They are built '
      "from component prices and coverage assumptions; the coverage denominators carry more uncertainty than the "
      "numerators. Use them to separate options differing by two orders of magnitude, not by 30%.</div>")

    # ---- 6 limits
    A("<h2>6. Problems, limits, and what would prove this wrong</h2>")
    A("""<h3>Problems in the evidence</h3><ul>
<li><strong>Reanalysis is modelled, not observed.</strong> ERA5 assimilates observations into a physical model on a
grid of roughly 30 km. It represents the climate signal at a city's location well; it does not represent the street
the person lives on, and it cannot represent their bedroom.</li>
<li><strong>Thresholds are conventions.</strong> 20 °C for a warm night and 35 °C for a hot day are the standard
European definitions, not physiological constants. Risk is continuous, and the real threshold varies with humidity,
age, medication, and acclimatisation.</li>
<li><strong>Summer-2026 mortality figures are early press estimates</strong> and will be revised as official
statistics catch up. They agree on order of magnitude, which is the only claim made from them here.</li>
<li><strong>Publication counts measure attention, not knowledge.</strong> A theme growing from 7 papers to 209
reflects a term entering circulation as much as a field maturing.</li>
<li><strong>The inventory is a considered sample, not a census.</strong> Forty-six systems chosen for coverage
across layers; the actuator-coupling score is a judgement applied consistently, not a measured quantity.</li>
<li><strong>Ease scores weight four components equally.</strong> In any specific municipality a data-protection
agreement may be trivial or fatal. Re-score locally before committing.</li></ul>""")
    A("""<h3>What would falsify the central claim</h3>
<p>The argument is that the binding constraint is coupling — acting on information — rather than sensing. It would
be wrong if a well-instrumented city with a mature heat plan showed no residual preventable mortality. Current
European evidence points the other way: heat plans are widespread and excess deaths persist through recent summers.</p>
<p>The cheapest falsifiable piece is the indoor-sensor claim. Deploy a few hundred bedroom sensors and test whether
indoor night minima predict individual health events better than the outdoor forecast that currently drives warnings.
If they do not, the household tier of the catalogue collapses and the cross-cutting tier still stands.</p>""")
    A("""<div class="note"><strong>On health.</strong> This report concerns population-level risk and monitoring
design. It is not clinical guidance. Decisions about any individual's care — including anyone a system of this kind
flags as at risk — rest with qualified health professionals who have the full context.</div>""")

    A("""<footer>Sources: ERA5 reanalysis via the Open-Meteo archive (1950–2025, 12 cities); OpenAlex bibliographic
queries (2015–2025); operational documentation for 46 monitoring systems; peer-reviewed and press sources listed in
<em>plain_language_guide.md</em>. Analysis in Python (pandas, scipy, matplotlib). Every table is available as a
standalone CSV in the <a href="explore.html">data explorer</a>, licensed CC BY 4.0. <a href="./">Dataset home</a>.</footer></main></body></html>""")
    return "\n".join(P)


# ---------------------------------------------------------------------------
# Standalone entry point: load every table from data/, derive the inline
# counts, and write site/report.html with relative figure paths.
# ---------------------------------------------------------------------------

def load_tables():
    """Read the committed CSVs into the dict shape build() expects."""
    names = {"inv": "monitoring_inventory", "gm": "gap_matrix",
             "sol": "solutions_catalogue", "ez": "actions_by_ease",
             "tr": "heat_trends", "cost": "solution_cost_impact"}
    d = {k: pd.read_csv(f"data/{v}.csv") for k, v in names.items()}
    d["dec"] = pd.read_csv("data/decadal_summary.csv", index_col=0)
    d["acc"] = pd.read_csv("data/recent_change_by_city.csv", index_col=0)
    d["lit"] = pd.read_csv("data/literature_counts_by_year.csv").rename(
        columns={"Unnamed: 0": "year"})

    inv = d["inv"].copy()
    inv["coupled"] = inv.coupled_to_actuator.astype(str).str.strip().str.startswith("Yes")
    lay = (inv.groupby("layer")
           .agg(Systems=("system", "size"),
                **{"Connected to an action": ("coupled", "sum")})
           .sort_values("Systems", ascending=False))
    lay["Data only"] = lay["Systems"] - lay["Connected to an action"]
    lay.index.name = "Layer"
    d["lay"] = lay
    return d


def derive_counts(d):
    """Every number interpolated into the report prose, computed from the data."""
    inv, gm, tr = d["inv"].copy(), d["gm"], d["tr"]
    dec, acc, cost, lay = d["dec"], d["acc"], d["cost"], d["lay"]
    inv["coupled"] = inv.coupled_to_actuator.astype(str).str.strip().str.startswith("Yes")
    ann = pd.read_csv("data/heat_trends_annual.csv")
    prop = cost[cost.kind == "proposed"]
    down = acc.index[acc.tn20_change <= 0].tolist()
    return dict(
        n_sys=len(inv), n_layer=inv.layer.nunique(),
        n_coupled=int(inv.coupled.sum()),
        n_blind=int((gm.gap_severity_0to5 == 5).sum()),
        n_days=int(len(ann) * 365.25),
        torrid_mult=round(dec.loc[2020, "torrid_nights_25"] / dec.loc[1960, "torrid_nights_25"], 1),
        tn_mult=round(dec.loc[2020, "tropical_nights_20"] / dec.loc[1960, "tropical_nights_20"], 1),
        d35_mult=round(dec.loc[2020, "days_over_35"] / dec.loc[1960, "days_over_35"], 1),
        n_cheap=int((prop.eur_per_person_year < 1).sum()),
        n_space=int(lay.loc["Space-based GHG", "Systems"]),
        n_urban=int(lay.loc["Urban and environmental", "Systems"]),
        tn_up=int((acc.tn20_change > 0).sum()),
        run_up=int((acc.run_change > 0).sum()),
        d35_up=int((acc.d35_change > 0).sum()),
        tn_mean=round(float(acc.tn20_change.mean()), 1),
        down_cities=" and ".join(down) if down else "none",
        tmax_rate=round(float(tr.mean_tmax_JJA_per_decade.mean()), 2),
        tmin_rate=round(float(tr.mean_tmin_JJA_per_decade.mean()), 2),
        faster_day=int((tr.mean_tmax_JJA_per_decade > tr.mean_tmin_JJA_per_decade).sum()),
    )


def main():
    import os
    d = load_tables()
    counts = derive_counts(d)
    os.makedirs("site/figures", exist_ok=True)
    html = build(d, counts)
    with open("site/report.html", "w") as fh:
        fh.write(html)
    for name in FILES.values():
        src, dst = f"figures/{name}", f"site/figures/{name}"
        if os.path.exists(src):
            with open(src, "rb") as a, open(dst, "wb") as b:
                b.write(a.read())
    print(f"wrote site/report.html  ({len(html):,} chars, "
          f"{html.count('<table')} tables, {html.count('<figure')} figures)")


if __name__ == "__main__":
    main()
