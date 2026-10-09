# Findings and suggested actions, ordered by ease

A decision document. Section 1 states what the analysis found. Section 2 lists every proposed action sorted by how hard it is to actually start — not by cost, and not by impact. Section 3 gives the honest caveats.

---

## 1. Findings

### F1 — The bottleneck is coupling, not sensing

Of **46 operational monitoring systems** inventoried across 8 layers (satellite greenhouse-gas observation, regulatory reporting, grid telemetry, urban sensing, hazard warning, buildings, mobility, climate finance), **25 publish open data** but only about **a dozen are connected to any actuator**. Thirty are connected to nothing — they produce a number and stop.

Detection has improved by orders of magnitude in a decade. What has not been built is the machinery that turns a detection into an obligated consequence. This is why most of the recommended actions are cheap: the sensing is already paid for.

### F2 — Four points in the harm chain are effectively unmeasured

Scoring each stage from emission to health outcome (`gap_matrix.csv`), four score 5/5:

| Stage | What is missing |
|---|---|
| Response to detection | We see the methane leak. No public, verified record of whether it was repaired or how fast. |
| Indoor heat | Heat kills indoors, at night, in bedrooms. No system measures indoor temperature in at-risk homes at scale. |
| Behaviour after warning | Nobody measures whether anyone acted on a heat warning. Plans cannot be improved by guesswork. |
| Adaptation spend | Cooling and greening projects are funded without before-and-after measurement at the site. |

Exposure and vulnerability score 4: we know the city's temperature, not the person's; registers of at-risk residents exist but are rarely linked to live hazard feeds.

### F3 — Warm nights have increased in every southern-European city studied

ERA5 reanalysis, 12 cities, 1950–2025, 333,108 city-days. Nights above 20 °C rose everywhere without exception. Athens: 61 → 83 per year. Rome tripled (2.8×), Madrid more than tripled (3.2×).

### F4 — Daytime is warming faster than nighttime, and the night case still holds

Summer maxima rise at **0.35 °C/decade** against **0.23 °C/decade** for minima, with daytime faster in **11 of 12 cities**. This contradicts the hypothesis the analysis set out to test and is reported as found.

The night case survives for a distributional reason rather than a rate reason: night minima sit close to the threshold at which the body cannot shed accumulated heat, so a slower warming rate crosses that threshold on far more nights than a faster daytime rate crosses 40 °C.

### F5 — The recovery gap is the sharpest and most neglected signal

The longest unbroken run of nights above 20 °C — consecutive nights with no physiological recovery — has grown in every city. **Athens 24 → 44 nights. Valletta now 105.** This maps more directly onto heat-mortality physiology than peak temperature does, and **no operational European warning system uses it as a trigger.**

---

## 2. Actions by ease

Ease is scored on what actually blocks a start: hardware to install, legal or data-protection agreements, institutional coordination, and whether the cost exceeds €1 per person per year. Lower burden means fewer things must go right before anything happens.

![Twelve actions ranked by deployment burden and time to first measurable result](../figures/actions_by_ease.png)

### Tier 1 — Do now. No permission, no hardware, no budget line.

**S11 · Carbon-aware scheduling of flexible compute and charging** — burden 0, result in ~2 weeks, ~€0
Shift deferrable work — model training, batch jobs, EV charging, water heating, building pre-cooling — to low-carbon grid hours using free marginal-emissions APIs. Nothing is computed less; the same work happens at a different hour. The pre-cooling variant also cuts heatwave peak demand. *This is the direct answer to "solve climate without stopping technology," and it is already wired to an actuator.* Evidence: high for grid-carbon reduction, medium for the pre-cooling variant.

**S5 · Cool-route mapping from open data** — burden 1, result in ~8 weeks, ~€0.05/person/yr
Compute shaded walking routes from free Landsat/Sentinel-3 thermal imagery, Copernicus tree cover, and OpenStreetMap footprints; publish them in the existing municipal routing app. Pure software on open inputs. Evidence: medium — the mapping method is mature, behavioural uptake is the uncertainty.

### Tier 2 — One agreement away. A single signature or partner unlocks it.

**S3 · Night-ventilation advisory** — burden 2, ~6 weeks, €0.63/person/yr
Tell a household the exact hour to open and close windows, from indoor temperature plus outdoor forecast, delivered by SMS so it works without a smartphone. Needs a met-service data feed and a delivery channel. Evidence: medium-high for the physics, low for delivery effectiveness.

**S1 · Indoor heat sentinel with escalation** — burden 3, ~8 weeks, €5.63/person/yr
A sub-€30 bedroom sensor in an at-risk home; two consecutive nights above the indoor threshold triggers an automated welfare call from the municipality — not a push notification to a phone the resident may not own. **The escalation loop is the part that exists nowhere at scale.** This is the highest-severity gap and the most directly falsifiable proposal. Evidence: medium — components proven, end-to-end loop rarely evaluated.

**S10 · Cool-refuge network with occupancy sensing** — burden 3, ~10 weeks, €0.68/person/yr
Designate already-air-conditioned public buildings, publish hours in the warning feed, and put a €20 people-counter at the door so use is measured. Uses cooling capacity already paid for. Note the limitation: refuges close at night, when tropical nights are the risk.

**S12 · Instrument every adaptation project** — burden 3, ~12 weeks, €0.015/person/yr
Mandate that 1–2% of any publicly funded cooling or greening budget goes to before-and-after measurement at the site, published openly. Costs a rounding error and builds the evidence base whose absence forces everything else to be justified from research pilots. Evidence: high as a method — the gap is institutional, not technical.

### Tier 3 — Needs a budget line and a named owner.

**S6 · Opportunistic mobile sensing on public fleets** — burden 4, ~16 weeks, €0.005/person/yr
Shielded sensors on buses and waste vehicles cover more street kilometres per day than any static network a mid-sized city could afford. Watch for radiative heating when stationary and engine-heat contamination.

**S8 · Open heat-data schema and municipal API** — burden 4, ~26 weeks, €0.004/person/yr
A minimal published schema every city network must emit, modelled on the ENTSO-E transparency platform that made European electricity data usable. Prevents the recurring pattern of bespoke silos harmonised retrospectively. Standards without a procurement hook get ignored — pair it with one.

**S2 · Smart-meter heat-vulnerability screening** — burden 4, ~30 weeks, €0.20/person/yr
Households showing no cooling-load signature during a heatwave, in poor-quality dwellings, with an occupant over 75, become priority visits. **No new hardware — the data is already collected.** The data-protection agreement with the distribution operator is the entire project; start the legal work early.

**S9 · Heat-triggered welfare call roster** — burden 5, ~20 weeks, €12.80/person/yr
Pre-agreed roster linking the national warning feed to a call list of registered at-risk residents. The technology is a spreadsheet and an API subscription; the work is the pre-agreement and the volunteer base.

**S7 · Calibration-as-a-service for low-cost sensors** — burden 5, ~26 weeks, €0.04/person/yr
A regional reference station where any citizen or municipal sensor gets two weeks of co-location and a correction certificate. **Highest leverage per euro in the catalogue** — it converts thousands of already-deployed untrusted sensors into usable public data. High burden only because it needs an institutional home that outlives the founding grant. Evidence: high.

### Tier 4 — Programme-scale.

**S4 · Shade-first retrofit protocol** — burden 6, ~24 weeks, €43.75/person/yr
Prioritise external shading and reflective roof coatings over deep envelope retrofits or AC subsidies: external shading blocks solar gain before it enters, at roughly one-tenth the cost. Still an order of magnitude cheaper than the €600/person-yr deep-retrofit alternative. Blockers are heritage and facade rules, and the landlord–tenant split incentive in rental stock. Evidence: high for the building physics.

---

## 3. If you only do three things

1. **Start S11 this month.** Zero cost, zero permission, measurable in a fortnight, and it cuts emissions without reducing any output.
2. **Put S12 into the next funding round's terms.** One clause. It is the only way the missing evidence base ever gets built, and every later decision depends on it.
3. **Begin the S2 data-protection negotiation now, in parallel.** It has the longest lead time (~30 weeks) and the shortest technical path — the delay is entirely legal, so it should be running in the background while faster items deliver.

---

## 4. Caveats

**Cost figures are engineering estimates, not procurement quotes.** They are built from component prices and coverage assumptions; the coverage denominators (people per sensor, people per city network) carry more uncertainty than the numerators. Use them to separate items differing by two orders of magnitude, not by 30%.

**Ease scores are judgements, not measurements.** The four burden components are equally weighted, which is a simplification — in a specific municipality, a data-protection agreement may be trivial or may be fatal. Re-score locally before committing.

**Time-to-result assumes a willing institution.** The week counts measure technical and procedural lead time, not the time to persuade anyone.

**What would falsify the central claim.** If a well-instrumented city with a mature heat plan showed no residual preventable mortality, the coupling diagnosis would be wrong. Current European evidence points the other way — plans are widespread and excess deaths persist. The indoor-measurement claim (F2, S1) is testable directly and cheaply: deploy a few hundred sensors and check whether indoor night minima predict health events better than the outdoor forecast that currently drives warnings. If they do not, the household tier collapses and the cross-cutting tier still stands.

**On health.** This document concerns population-level risk and monitoring design. It is not clinical guidance, and decisions about any individual's care — including anyone a system of this kind flags as at risk — rest with qualified health professionals who have the full context.
