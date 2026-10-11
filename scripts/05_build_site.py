"""Publish the open dataset into site/data/ for the website.

Inputs : data/*.csv, data/climate_monitoring_dataset.xlsx, CITATION.cff,
         LICENSE-DATA, CITIES in scripts/01_fetch_era5.py

CITATION.cff is the single source for the title, version, release date,
authors and repository URL (`repository-code`) shown on the site.
Outputs: site/data/<name>.csv                 one file per table
         site/data/cities.csv                 the 12 cities and their coordinates
         site/data/datapackage.json           Frictionless Data Package: schema,
                                              units, column descriptions, headline
                                              numbers used on the home page
         site/data/climate_monitoring_dataset.xlsx
         site/data/climate-heat-monitoring-data.zip   everything above in one file

Standard library only, so the site can be rebuilt without the analysis stack.
Edit DATASETS below when a table or column is added; the explorer and the
catalogue on the home page are driven entirely by datapackage.json. In DATASETS,
`facets` maps a long-text column to a derived filter ("first-word": filter on
the leading Yes/No/Partly) and `ranges` lists numeric columns that get a range
filter by default; short categorical columns get a filter automatically.
`figure` names a chart from FIGURES that the explorer shows above the table; the
PNGs are copied into site/figures/ by scripts/04_build_report.py.

Usage:  python scripts/05_build_site.py
"""
import csv, importlib.util, io, json, os, re, shutil, zipfile

OUT = os.path.join("site", "data")
ZIP_NAME = "climate-heat-monitoring-data.zip"

THEMES = [
    ("monitoring", "Monitoring systems and gaps",
     "What is being watched, by whom, and whether anything happens when it detects a problem."),
    ("heat", "Heat exposure, 12 cities, 1950–2025",
     "Indicators computed from ERA5 daily temperature reanalysis for twelve southern European cities."),
    ("actions", "Actions and costs",
     "Twelve interventions with cost, evidence and what blocks a start, plus conventional benchmarks."),
    ("literature", "Research attention",
     "Publication counts and a sample of highly cited works per theme, from OpenAlex."),
]

# Charts from scripts/03_make_figures.py, with the caption used as alt text.
FIGURES = {
    "monitoring_landscape.png": "Left: monitoring systems by layer, split by whether the output triggers an action. "
                                "Right: severity of the observation gap at each stage of the chain from emission to health outcome.",
    "heat_exposure_figure.png": "Measured heat exposure, 1950–2025. (a) warm nights rising in every city; (b) the recovery gap: "
                                "consecutive warm nights; (c) day vs night warming rates; (d) hot-day burden then and now.",
    "what_changed.png": "Left: heat indicators by decade, relative to the 1960s. Middle: change in warm nights, last 15 years "
                        "against the 15 before. Right: annual publication counts by research theme (log scale).",
    "actions_by_ease.png": "Left: what blocks each action: hardware, legal agreements, coordination, budget. "
                           "Right: weeks until a first measurable result.",
    "solution_cost_impact.png": "Estimated annual cost per person covered, proposals against conventional measures, log scale.",
}

PERIODS = {"1961_1990": "mean over 1961–1990", "1996_2025": "mean over 1996–2025",
           "1996_2010": "mean over 1996–2010", "2011_2025": "mean over 2011–2025"}

# Base indicators, shared by the annual, trend, decadal and recent-change tables.
IND = {
    "days_over_35": ("days", "Days with daily maximum temperature above 35 °C"),
    "days_over_40": ("days", "Days with daily maximum temperature above 40 °C"),
    "tropical_nights_20": ("nights", "Nights with daily minimum temperature above 20 °C (tropical nights)"),
    "torrid_nights_25": ("nights", "Nights with daily minimum temperature above 25 °C (torrid nights)"),
    "longest_tn20_run": ("nights", "Longest unbroken run of nights above 20 °C in the year: consecutive nights without physiological recovery"),
    "longest_hot_run_35": ("days", "Longest unbroken run of days above 35 °C in the year"),
    "cdd_18": ("°C·days", "Cooling degree-days, base 18 °C"),
    "mean_tmax_JJA": ("°C", "Mean daily maximum temperature, June–August"),
    "mean_tmin_JJA": ("°C", "Mean daily minimum temperature, June–August"),
}
SHORT = {"tn20": "tropical_nights_20", "run": "longest_tn20_run", "d35": "days_over_35"}


def ind_field(name):
    """Describe a heat-indicator column from its name, e.g. cdd_18_per_decade."""
    if name in IND:
        return {"unit": IND[name][0], "description": IND[name][1] + " (annual count or mean)."}
    for base, (unit, desc) in IND.items():
        if name == f"{base}_per_decade":
            return {"unit": f"{unit} per decade",
                    "description": f"Linear (OLS) trend, 1950–2025. {desc}."}
        if name == f"{base}_p":
            return {"unit": "p-value", "description": f"p-value of the OLS trend for {base}."}
        for p, pdesc in PERIODS.items():
            if name == f"{base}_{p}":
                return {"unit": unit, "description": f"{desc}, {pdesc}."}
    m = re.match(r"(tn20|run|d35)_(\d{4}_\d{4}|change)$", name)
    if m:
        unit, desc = IND[SHORT[m.group(1)]]
        if m.group(2) == "change":
            return {"unit": unit, "description": f"{desc}: 2011–2025 mean minus 1996–2010 mean."}
        return {"unit": unit, "description": f"{desc}, {PERIODS[m.group(2)]}."}
    return {}


DATASETS = [
    # ---- monitoring
    dict(name="monitoring_inventory", theme="monitoring", figure="monitoring_landscape.png",
         title="Monitoring systems inventory",
         facets={"coupled_to_actuator": "first-word"},
         description="46 operational digital climate-monitoring systems across 8 layers, each scored on "
                     "resolution, latency, openness, funding and whether the output is wired to any actuator.",
         fields={
             "layer": "Layer of the monitoring stack the system belongs to.",
             "system": "System or programme name.",
             "operator": "Organisation that runs it.",
             "geographic_scope": "Area covered.",
             "what_it_measures": "Quantities observed.",
             "spatial_resolution": "Finest spatial unit reported.",
             "revisit_or_latency": "How often it observes and how fast data appears.",
             "open_data": "Whether outputs are openly published.",
             "funding_model": "Who pays for it.",
             "coupled_to_actuator": "Whether the output triggers a physical action without a person choosing to act. The column that drives the central finding.",
             "maturity": "Operational status.",
             "notes_and_provenance": "Notes and source links.",
         }),
    dict(name="gap_matrix", theme="monitoring", figure="monitoring_landscape.png",
         title="Gap matrix: the emission-to-harm chain",
         facets={"coupled_to_action": "first-word"},
         description="15 stages from emission to health outcome, each scored 0–5 on how badly it is observed. "
                     "Four stages score 5: effectively unmeasured.",
         fields={
             "stage": "Stage of the causal chain.",
             "question_the_data_should_answer": "The operational question monitoring at this stage should answer.",
             "observation_density": "How densely the stage is observed.",
             "latency": "Delay between event and data.",
             "who_can_see_it": "Who has access to the data.",
             "coupled_to_action": "Whether observation at this stage triggers action.",
             "gap_severity_0to5": ("score 0–5", "0 = well observed and acted on; 5 = effectively unmeasured."),
             "evidence_for_the_gap": "Evidence and sources behind the score, including 2026 revisions.",
         }),
    # ---- heat
    dict(name="heat_trends_annual", theme="heat", figure="heat_exposure_figure.png",
         title="Annual heat indicators by city",
         description="One row per city-year, 12 cities × 1950–2025 (912 rows), computed from ERA5 daily "
                     "maximum, minimum and mean 2 m temperature.",
         primaryKey=["city", "year"], ranges=["year"],
         fields={"city": "City name; see cities.csv for coordinates.", "year": "Calendar year."}),
    dict(name="heat_trends", theme="heat", figure="heat_exposure_figure.png",
         title="Trends and period means by city",
         description="Per city: OLS trend per decade with p-value for each indicator, and means for "
                     "1961–1990 versus 1996–2025.",
         primaryKey=["city"],
         fields={
             "city": "City name.",
             "tn20_ratio": ("ratio", "Tropical nights, 1996–2025 mean divided by 1961–1990 mean."),
             "over35_ratio": ("ratio", "Days above 35 °C, 1996–2025 mean divided by 1961–1990 mean. Empty where the baseline is zero."),
         }),
    dict(name="decadal_summary", theme="heat", figure="what_changed.png",
         title="Decadal means across all cities",
         description="Mean of the twelve cities per decade, 1960s–2020s. The 2020s row covers 2020–2025 only.",
         primaryKey=["decade"],
         fields={"decade": "First year of the decade."}),
    dict(name="recent_change_by_city", theme="heat", figure="what_changed.png",
         title="Recent change by city",
         description="The last 15 years (2011–2025) against the 15 before (1996–2010) for warm nights, "
                     "the longest warm-night run and hot days.",
         primaryKey=["city"],
         fields={"city": "City name."}),
    dict(name="cities", theme="heat", generated=True,
         title="Cities and coordinates",
         description="The twelve cities analysed and the grid point queried from the Open-Meteo ERA5 archive.",
         primaryKey=["city"],
         fields={"city": "City name.", "country": "Country.",
                 "latitude": ("degrees", "Latitude of the point queried (WGS84)."),
                 "longitude": ("degrees", "Longitude of the point queried (WGS84).")}),
    # ---- actions
    dict(name="solutions_catalogue", theme="actions", figure="actions_by_ease.png",
         title="Solutions catalogue",
         description="Twelve interventions, each with mechanism, capital and running cost, who deploys it, "
                     "expected effect, evidence strength and failure modes.",
         primaryKey=["id"],
         fields={
             "id": "Solution identifier, S1–S12.", "solution": "Short name.",
             "tier": "Scale at which it operates.", "gap_closed": "Which monitoring gap it closes.",
             "mechanism": "How it works.",
             "capex_eur_per_unit": ("EUR", "Capital cost per deployment unit."),
             "opex_eur_per_unit_per_year": ("EUR per year", "Running cost per unit per year."),
             "unit": "Deployment unit the costs refer to.", "who_deploys": "Institution that would deploy it.",
             "expected_effect": "Expected effect.", "evidence_strength": "Strength of evidence, in words.",
             "failure_modes": "Ways it can fail.",
             "stops_tech_development": "Whether it requires slowing technological development.",
         }),
    dict(name="actions_by_ease", theme="actions", figure="actions_by_ease.png",
         title="Actions ranked by ease of starting",
         description="The twelve solutions scored on what blocks a start: hardware, legal agreements, "
                     "coordination and money. Lower burden means fewer things must go right first.",
         primaryKey=["id"],
         fields={
             "id": "Solution identifier.",
             "hardware": ("count 0–2", "Blocking conditions from hardware that must be installed."),
             "legal": ("count 0–2", "Blocking conditions from legal or data-protection agreements."),
             "coordination": ("count 0–2", "Blocking conditions from institutions that must coordinate."),
             "money": ("count 0–2", "Blocking conditions from budget; 0 when cost is under €1 per person per year."),
             "weeks_to_first_result": ("weeks", "Estimated weeks until a first measurable result."),
             "ease_burden": ("count", "Deployment burden: hardware + legal + coordination + money. Lower means fewer things must go right first."),
             "solution": "Short name.", "tier": "Scale at which it operates.",
             "gap_closed": "Which monitoring gap it closes.", "evidence_strength": "Strength of evidence, in words.",
             "evidence_score": ("score 1–3", "Evidence strength as a number."),
             "eur_per_person_year": ("EUR per person per year", "Annual cost per person covered, capital amortised over five years."),
             "ease_tier": "Ease tier: 1 Do now, 2 One agreement away, 3 Needs a budget line, 4 Programme-scale.",
         }),
    dict(name="solution_cost_impact", theme="actions", figure="solution_cost_impact.png",
         title="Cost per person, proposals against benchmarks",
         description="Annual cost per person covered for the twelve proposals and four conventional measures. "
                     "Engineering estimates, not procurement quotes.",
         fields={
             "id": "Solution identifier; empty for benchmarks.", "label": "Name.",
             "eur_per_person_year": ("EUR per person per year", "Annual cost per person covered."),
             "evidence_score": ("score 1–3", "Evidence strength."),
             "tier": "Scale at which it operates.",
             "kind": "proposed = one of the twelve; benchmark = conventional measure for comparison.",
         }),
    # ---- literature
    dict(name="literature_counts_by_year", theme="literature", figure="what_changed.png",
         title="Publications per year by theme",
         description="OpenAlex publication counts per research theme, 2015–2025. Measures attention, not knowledge.",
         primaryKey=["year"], ranges=["year"],
         fields={"year": "Publication year.", "*": ("papers", "Publications matching this theme's query.")}),
    dict(name="literature_corpus", theme="literature",
         title="Literature corpus",
         description="200 works from OpenAlex, 25 per theme, ordered by citation count.",
         ranges=["year", "citations"],
         fields={
             "theme": "Research theme the work was retrieved under.",
             "work_id": "OpenAlex work identifier.", "title": "Title.", "year": "Publication year.",
             "citations": ("citations", "Citation count in OpenAlex at retrieval."),
             "venue": "Journal or venue.", "is_oa": "Whether the work is open access.",
             "doi": "DOI link.", "type": "Work type.",
         }),
]

COUNTRIES = {"Athens": "Greece", "Thessaloniki": "Greece", "Rome": "Italy", "Naples": "Italy",
             "Palermo": "Italy", "Madrid": "Spain", "Seville": "Spain", "Cordoba": "Spain",
             "Barcelona": "Spain", "Lisbon": "Portugal", "Marseille": "France", "Valletta": "Malta"}


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    return rows[0], rows[1:]


def infer_type(values):
    vals = [v for v in values if v != ""]
    if not vals:
        return "string"
    if all(v in ("True", "False") for v in vals):
        return "boolean"
    if all(re.fullmatch(r"-?\d+", v) for v in vals):
        return "integer"
    try:
        [float(v) for v in vals]
        return "number"
    except ValueError:
        return "string"


def cities_table():
    spec = importlib.util.spec_from_file_location("fetch", os.path.join("scripts", "01_fetch_era5.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    header = ["city", "country", "latitude", "longitude"]
    return header, [[c, COUNTRIES.get(c, ""), str(lat), str(lon)] for c, (lat, lon) in mod.CITIES.items()]


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def citation_meta():
    """Read the top-level fields the site needs from CITATION.cff (no YAML dependency)."""
    text = open("CITATION.cff", encoding="utf-8").read()
    get = lambda k: (re.search(rf'^{k}:\s*"?([^"\n]+?)"?\s*$', text, re.M) or [None, ""])[1]
    block = re.search(r"^authors:\s*\n((?:[ \t-].*\n?)*)", text, re.M)
    authors = []
    for entry in re.split(r"^\s*-\s+", block.group(1) if block else "", flags=re.M)[1:]:
        f = dict(re.findall(r'([\w-]+):\s*"?([^"\n]+?)"?\s*$', "  " + entry, re.M))
        name = f.get("name") or " ".join(x for x in (f.get("given-names"), f.get("family-names")) if x)
        if name:
            authors.append(name)
    meta = {"title": get("title"), "version": get("version"), "released": get("date-released"),
            "repo": get("repository-code").rstrip("/"), "authors": authors}
    missing = [k for k in ("title", "version", "released", "repo", "authors") if not meta[k]]
    if missing:
        raise SystemExit(f"CITATION.cff is missing: {', '.join(missing)}")
    if "YOUR-USERNAME" in meta["repo"]:
        print("   warning: repository-code in CITATION.cff is still a placeholder")
    return meta


def highlights(tables):
    inv_h, inv = tables["monitoring_inventory"]
    gm_h, gm = tables["gap_matrix"]
    dec_h, dec = tables["decadal_summary"]
    ann_h, ann = tables["heat_trends_annual"]
    cost_h, cost = tables["solution_cost_impact"]
    col = lambda h, rows, c: [r[h.index(c)] for r in rows]
    coupled = [v.strip().startswith("Yes") for v in col(inv_h, inv, "coupled_to_actuator")]
    dec_by = {r[0]: r for r in dec}
    t25 = dec_h.index("torrid_nights_25")
    proposed = [float(r[cost_h.index("eur_per_person_year")]) for r in cost
                if r[cost_h.index("kind")] == "proposed"]
    years = [int(y) for y in col(ann_h, ann, "year")]
    return {
        "systems": len(inv), "layers": len(set(col(inv_h, inv, "layer"))),
        "systems_coupled": sum(coupled),
        "unmeasured_stages": sum(1 for v in col(gm_h, gm, "gap_severity_0to5") if v == "5"),
        "cities": len(set(col(ann_h, ann, "city"))), "first_year": min(years), "last_year": max(years),
        "city_days": int(len(ann) * 365.25),
        "torrid_nights_multiplier": round(float(dec_by["2020"][t25]) / float(dec_by["1960"][t25]), 1),
        "actions": len(proposed), "actions_under_1_eur": sum(1 for v in proposed if v < 1),
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    cite = citation_meta()
    repo = cite["repo"]
    tables, resources = {}, []
    for ds in DATASETS:
        name = ds["name"]
        if ds.get("generated"):
            header, rows = cities_table()
            src = "scripts/01_fetch_era5.py (CITIES)"
        else:
            header, rows = read_csv(os.path.join("data", f"{name}.csv"))
            src = f"data/{name}.csv"
        tables[name] = (header, rows)
        dest = os.path.join(OUT, f"{name}.csv")
        if ds.get("generated"):
            write_csv(dest, header, rows)
        else:
            shutil.copyfile(src, dest)   # byte-identical to the repo copy

        fields = []
        for i, col in enumerate(header):
            meta = ds["fields"].get(col) or ds["fields"].get("*") or ind_field(col)
            if isinstance(meta, tuple):
                meta = {"unit": meta[0], "description": meta[1]}
            elif isinstance(meta, str):
                meta = {"description": meta}
            f = {"name": col, "type": infer_type([r[i] for r in rows if i < len(r)])}
            f.update({k: v for k, v in meta.items() if v})
            fields.append(f)
        undocumented = [f["name"] for f in fields if "description" not in f]
        if undocumented:
            print(f"   warning: {name}: no description for {', '.join(undocumented)}")

        fig = ds.get("figure")
        if fig and not os.path.exists(os.path.join("figures", fig)):
            print(f"   warning: {name}: figures/{fig} not found")

        schema = {"fields": fields}
        if ds.get("primaryKey"):
            schema["primaryKey"] = ds["primaryKey"]
        resources.append({
            "name": name, "path": f"{name}.csv", "title": ds["title"], "description": ds["description"],
            "format": "csv", "mediatype": "text/csv", "encoding": "utf-8",
            "bytes": os.path.getsize(dest), "x_theme": ds["theme"], "x_rows": len(rows),
            "x_source": src, "x_facets": ds.get("facets", {}), "x_ranges": ds.get("ranges", []),
            "schema": schema,
        })
        if fig:
            resources[-1]["x_figure"] = {"path": f"figures/{fig}", "title": FIGURES[fig]}

    package = {
        "profile": "tabular-data-package",
        "name": "climate-heat-monitoring",
        "id": repo,
        "title": cite["title"],
        "description": "An inventory of 46 operational digital climate-monitoring systems scored on whether their "
                       "output is coupled to any actuator, a 15-stage map of gaps in the emission-to-harm chain, "
                       "heat exposure indicators for twelve southern European cities from ERA5 reanalysis "
                       "1950–2025, and twelve costed interventions ranked by deployment burden.",
        "version": cite["version"],
        "created": cite["released"],
        "homepage": repo,
        "licenses": [{"name": "CC-BY-4.0", "title": "Creative Commons Attribution 4.0",
                      "path": "https://creativecommons.org/licenses/by/4.0/"}],
        "contributors": [{"title": a, "role": "author"} for a in cite["authors"]],
        "sources": [
            {"title": "ERA5 hourly data on single levels, Copernicus Climate Change Service (C3S)",
             "path": "https://cds.climate.copernicus.eu/", "x_via": "Open-Meteo archive API"},
            {"title": "OpenAlex", "path": "https://openalex.org/"},
            {"title": "Operational documentation for 46 monitoring systems; see notes_and_provenance",
             "path": f"{repo}/blob/main/data/monitoring_inventory.csv"},
        ],
        "keywords": ["climate monitoring", "urban heat", "heat mortality", "climate adaptation",
                     "ERA5", "southern Europe"],
        "x_themes": [{"id": t, "title": ti, "description": de} for t, ti, de in THEMES],
        "x_highlights": highlights(tables),
        "x_issues": f"{repo}/issues",
        "x_bundle": {"path": ZIP_NAME},
        "x_workbook": {"path": "climate_monitoring_dataset.xlsx"},
        "resources": resources,
    }

    shutil.copyfile(os.path.join("data", "climate_monitoring_dataset.xlsx"),
                    os.path.join(OUT, "climate_monitoring_dataset.xlsx"))
    pkg_json = json.dumps(package, indent=2, ensure_ascii=False)

    # Zip first so its size can go into the package that the site reads.
    zpath = os.path.join(OUT, ZIP_NAME)
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for r in resources:
            z.write(os.path.join(OUT, r["path"]), f"climate-heat-monitoring/{r['path']}")
        z.write(os.path.join(OUT, "climate_monitoring_dataset.xlsx"),
                "climate-heat-monitoring/climate_monitoring_dataset.xlsx")
        z.writestr("climate-heat-monitoring/datapackage.json", pkg_json)
        for f in ("LICENSE-DATA", "CITATION.cff"):
            z.write(f, f"climate-heat-monitoring/{f}")
    package["x_bundle"]["bytes"] = os.path.getsize(zpath)
    package["x_workbook"]["bytes"] = os.path.getsize(os.path.join(OUT, "climate_monitoring_dataset.xlsx"))

    with open(os.path.join(OUT, "datapackage.json"), "w", encoding="utf-8") as fh:
        fh.write(json.dumps(package, indent=2, ensure_ascii=False))
    print(f"wrote {OUT}/  {len(resources)} tables, "
          f"{sum(r['x_rows'] for r in resources):,} rows, bundle {package['x_bundle']['bytes']:,} bytes")


if __name__ == "__main__":
    main()
