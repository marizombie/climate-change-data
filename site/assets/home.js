/* Home page: headline numbers, dataset catalogue, code snippets, citation. */
(function () {
  "use strict";
  const { loadPackage, fmtBytes, esc, copyText } = window.CHM;

  const base = new URL(window.CHM.DATA, location.href).href;

  function kpis(h) {
    const items = [
      [h.systems, `monitoring systems inventoried across ${h.layers} layers`],
      [`${h.systems_coupled} of ${h.systems}`, "trigger any action; the rest only report"],
      [h.unmeasured_stages, "stages of the harm chain are effectively unmeasured"],
      [h.city_days.toLocaleString("en-GB"), `city-days of temperature, ${h.cities} cities, ${h.first_year}–${h.last_year}`],
      [`${h.torrid_nights_multiplier}×`, "more nights above 25 °C, 1960s to 2020s"],
      [`${h.actions_under_1_eur} of ${h.actions}`, "proposed actions cost under €1 per person per year"],
    ];
    document.getElementById("kpis").innerHTML = items
      .map(([n, l]) => `<div class="kpi"><div class="n">${esc(n)}</div><div class="l">${esc(l)}</div></div>`)
      .join("");
  }

  function catalogue(pkg) {
    const html = pkg.x_themes.map((t) => {
      const cards = pkg.resources.filter((r) => r.x_theme === t.id).map((r) => `
        <article class="card">
          <h4><a href="explore.html?d=${encodeURIComponent(r.name)}">${esc(r.title)}</a></h4>
          <p>${esc(r.description)}</p>
          <div class="stats">${r.x_rows.toLocaleString("en-GB")} rows · ${r.schema.fields.length} columns · ${fmtBytes(r.bytes)}</div>
          <div class="row">
            <a class="btn small primary" href="explore.html?d=${encodeURIComponent(r.name)}">Explore</a>
            <a class="btn small" href="data/${esc(r.path)}" download>CSV</a>
          </div>
        </article>`).join("");
      return `<div class="theme-group"><h3>${esc(t.title)}</h3><p>${esc(t.description)}</p><div class="cards">${cards}</div></div>`;
    }).join("");
    document.getElementById("catalogue").innerHTML = html;
    if (pkg.x_bundle.bytes) document.getElementById("zip-meta").textContent =
      `All ${pkg.resources.length} CSVs, the workbook, datapackage.json, licence and citation · ${fmtBytes(pkg.x_bundle.bytes)}`;
    if (pkg.x_workbook.bytes) document.getElementById("xlsx-meta").textContent =
      `Core tables as sheets in one .xlsx · ${fmtBytes(pkg.x_workbook.bytes)}`;
  }

  function snippets(pkg) {
    const u = (n) => base + n + ".csv";
    return {
      python: `import pandas as pd

base = "${base}"
annual = pd.read_csv(base + "heat_trends_annual.csv")
inventory = pd.read_csv(base + "monitoring_inventory.csv")

# warm nights per year in Athens since 2000
athens = annual.query("city == 'Athens' and year >= 2000")
print(athens[["year", "tropical_nights_20"]])

# or load the whole package with its schema
# pip install frictionless
from frictionless import Package
pkg = Package(base + "datapackage.json")`,
      r: `library(readr)

base <- "${base}"
annual    <- read_csv(paste0(base, "heat_trends_annual.csv"))
inventory <- read_csv(paste0(base, "monitoring_inventory.csv"))

# longest warm-night run per city, last 10 years
subset(annual, year >= 2016)[, c("city", "year", "longest_tn20_run")]`,
      shell: `# one table
curl -O ${u("heat_trends_annual")}

# everything, with schema, licence and citation
curl -O ${base}${pkg.x_bundle.path}

# list every table and column
curl -s ${base}datapackage.json | jq '.resources[] | {name, rows: .x_rows}'`,
    };
  }

  function codeTabs(pkg) {
    const snips = snippets(pkg);
    const code = document.getElementById("code-snippet");
    const tabs = document.querySelectorAll("#code-tabs [role=tab]");
    const show = (k) => {
      tabs.forEach((t) => t.setAttribute("aria-selected", String(t.dataset.tab === k)));
      code.textContent = snips[k];
    };
    tabs.forEach((t) => t.addEventListener("click", () => show(t.dataset.tab)));
    document.querySelector("#code-tabs .copy").addEventListener("click", () => copyText(code.textContent, "Code"));
    show("python");
  }

  function citation(pkg) {
    const year = (pkg.created || "").slice(0, 4);
    const who = window.CHM.authorList(pkg);
    const bibAuthors = pkg.contributors.map((c) => c.title).join(" and ");
    document.getElementById("cite-text").textContent =
      `${who} (${year}). ${pkg.title} (Version ${pkg.version}) [Data set]. ${pkg.homepage}`;
    document.getElementById("cite-bib").textContent =
`@misc{climate_heat_monitoring_${year},
  author       = {${bibAuthors}},
  title        = {${pkg.title}},
  year         = {${year}},
  version      = {${pkg.version}},
  howpublished = {\\url{${pkg.homepage}}},
  note         = {Dataset, CC BY 4.0}
}`;
    document.querySelectorAll("[data-copy]").forEach((b) =>
      b.addEventListener("click", () => copyText(document.getElementById(b.dataset.copy).textContent, b.dataset.label)));
  }

  loadPackage().then((pkg) => {
    kpis(pkg.x_highlights);
    catalogue(pkg);
    codeTabs(pkg);
    citation(pkg);
  }).catch((e) => {
    document.getElementById("catalogue").innerHTML =
      `<div class="err">Could not load the catalogue: ${esc(e.message)}. If you opened this file directly from disk, serve the folder instead: <code>python3 -m http.server -d site</code>.</div>`;
  });
})();
