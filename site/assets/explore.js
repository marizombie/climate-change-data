/* Data explorer: search, facet and range filters, multi-column sort, column
   visibility, pagination, filtered downloads. The whole view lives in the URL
   (?d=dataset&q=…&s=col:asc&f.col=a|b&r.col=min..max&h=col,col) so it can be shared. */
(function () {
  "use strict";
  const { loadPackage, loadTable, fmtNum, fmtBytes, esc, toast, copyText, download } = window.CHM;
  const $ = (id) => document.getElementById(id);

  let pkg, res, table, cols, colBy, items;
  let st = freshState();
  let filtered = [];

  function freshState() {
    return { q: "", sort: [], sets: {}, ranges: {}, hidden: new Set(), page: 0, size: 50 };
  }

  // ---------- URL state
  function readState(params) {
    const s = freshState();
    s.q = params.get("q") || "";
    (params.get("s") || "").split(",").filter(Boolean).forEach((p) => {
      const [col, dir] = p.split(":");
      if (colBy[col]) s.sort.push({ col, dir: dir === "desc" ? "desc" : "asc" });
    });
    for (const [k, v] of params) {
      if (k.startsWith("f.") && colBy[k.slice(2)]) s.sets[k.slice(2)] = new Set(v.split("|"));
      if (k.startsWith("r.") && colBy[k.slice(2)]) {
        const [a, b] = v.split("..");
        s.ranges[k.slice(2)] = { min: a === "" ? null : Number(a), max: b === "" || b == null ? null : Number(b) };
      }
    }
    (params.get("h") || "").split(",").filter((c) => colBy[c]).forEach((c) => s.hidden.add(c));
    (res.x_ranges || []).forEach((c) => { if (colBy[c] && !s.ranges[c]) s.ranges[c] = { min: null, max: null }; });
    return s;
  }

  function writeState() {
    const p = new URLSearchParams();
    p.set("d", res.name);
    if (st.q) p.set("q", st.q);
    if (st.sort.length) p.set("s", st.sort.map((s) => s.col + ":" + s.dir).join(","));
    for (const [c, set] of Object.entries(st.sets)) if (set.size) p.set("f." + c, [...set].join("|"));
    for (const [c, r] of Object.entries(st.ranges))
      if (r.min != null || r.max != null) p.set("r." + c, (r.min ?? "") + ".." + (r.max ?? ""));
    if (st.hidden.size) p.set("h", [...st.hidden].join(","));
    history.replaceState(null, "", "?" + p.toString().replace(/%3A/g, ":").replace(/%2C/g, ",").replace(/%7C/g, "|"));
  }

  // ---------- columns
  function firstWord(v) {
    if (v == null || v === "") return "(empty)";
    const m = String(v).match(/^[A-Za-z]+/);
    return m ? m[0][0].toUpperCase() + m[0].slice(1).toLowerCase() : String(v);
  }

  function setupCols() {
    const n = table.rows.length;
    cols = table.fields.map((f) => {
      const isNum = f.type === "integer" || f.type === "number";
      const vals = table.rows.map((r) => r[f.name]);
      const distinct = new Set(vals.map((v) => (v == null ? "" : String(v))));
      const maxLen = vals.reduce((m, v) => Math.max(m, v == null ? 0 : String(v).length), 0);
      let facet = (res.x_facets || {})[f.name] || null;
      if (!facet && distinct.size > 1 && distinct.size < n) {
        if (f.type === "boolean") facet = "value";
        else if (!isNum && distinct.size <= 15 && maxLen <= 48) facet = "value";
        else if (f.type === "integer" && distinct.size <= 7 && !/year|decade/.test(f.name)) facet = "value";
      }
      const key = facet === "first-word" ? firstWord : (v) => (v == null || v === "" ? "(empty)" : String(v));
      const nums = isNum ? vals.filter((v) => v != null) : [];
      return {
        ...f, isNum, facet, key, long: !isNum && maxLen > 90,
        distinct: distinct.size, nulls: vals.filter((v) => v == null).length,
        min: nums.length ? Math.min(...nums) : null, max: nums.length ? Math.max(...nums) : null,
      };
    });
    colBy = Object.fromEntries(cols.map((c) => [c.name, c]));
    items = table.rows.map((r, i) => ({
      r, i, t: cols.map((c) => (r[c.name] == null ? "" : String(r[c.name]))).join(" \u0001 ").toLowerCase(),
    }));
  }

  // ---------- filtering & sorting
  const terms = () => st.q.toLowerCase().split(/\s+/).filter(Boolean);

  function passes(it, skipFacet) {
    const r = it.r;
    for (const c in st.sets) {
      if (c === skipFacet || !st.sets[c].size) continue;
      if (!st.sets[c].has(colBy[c].key(r[c]))) return false;
    }
    for (const c in st.ranges) {
      const g = st.ranges[c], v = r[c];
      if (g.min != null && (v == null || v < g.min)) return false;
      if (g.max != null && (v == null || v > g.max)) return false;
    }
    for (const t of terms()) if (!it.t.includes(t)) return false;
    return true;
  }

  function cmp(a, b) {
    for (const s of st.sort) {
      const va = a.r[s.col], vb = b.r[s.col];
      if (va == null && vb == null) continue;
      if (va == null) return 1;                    // empty values always last
      if (vb == null) return -1;
      const d = typeof va === "number" && typeof vb === "number"
        ? va - vb
        : String(va).localeCompare(String(vb), "en", { numeric: true, sensitivity: "base" });
      if (d) return s.dir === "asc" ? d : -d;
    }
    return a.i - b.i;
  }

  function update(opts = {}) {
    filtered = items.filter((it) => passes(it));
    if (st.sort.length) filtered.sort(cmp);
    if (!opts.keepPage) st.page = 0;
    const pages = Math.max(1, Math.ceil(filtered.length / (st.size || filtered.length || 1)));
    if (st.page >= pages) st.page = pages - 1;
    writeState();
    renderFacetCounts();
    renderTable();
    renderStatus();
    renderPager();
  }

  // ---------- rendering: dataset header & navigation
  function renderNav() {
    const byTheme = pkg.x_themes.map((t) => [t, pkg.resources.filter((r) => r.x_theme === t.id)]);
    $("ds-nav").innerHTML = byTheme.map(([t, rs]) =>
      `<h2>${esc(t.title)}</h2>` + rs.map((r) =>
        `<a href="?d=${encodeURIComponent(r.name)}" data-ds="${esc(r.name)}"><span class="n">${r.x_rows}</span>${esc(r.title)}</a>`).join("")
    ).join("");
    $("ds-select").innerHTML = byTheme.map(([t, rs]) =>
      `<optgroup label="${esc(t.title)}">` + rs.map((r) => `<option value="${esc(r.name)}">${esc(r.title)} (${r.x_rows} rows)</option>`).join("") + "</optgroup>"
    ).join("");
    $("ds-nav").addEventListener("click", (e) => {
      const a = e.target.closest("a[data-ds]");
      if (!a || e.metaKey || e.ctrlKey) return;
      e.preventDefault();
      go(a.dataset.ds);
    });
    $("ds-select").addEventListener("change", (e) => go(e.target.value));
  }

  function go(name) {
    history.pushState(null, "", "?d=" + encodeURIComponent(name));
    open(new URLSearchParams(location.search));
    window.scrollTo({ top: 0 });
  }

  function renderHead() {
    document.title = res.title + " · Data Explorer";
    document.querySelectorAll("#ds-nav a").forEach((a) => a.setAttribute("aria-current", String(a.dataset.ds === res.name)));
    $("ds-select").value = res.name;
    const key = res.schema.primaryKey ? ` · key: <code>${res.schema.primaryKey.map(esc).join(", ")}</code>` : "";
    const fig = res.x_figure ? `
      <figure class="ds-fig">
        <a href="${esc(res.x_figure.path)}" title="Open full size"><img src="${esc(res.x_figure.path)}" alt="${esc(res.x_figure.title)}"></a>
        <figcaption>${esc(res.x_figure.title)}</figcaption>
      </figure>` : "";
    $("ds-head").innerHTML = `
      <h1>${esc(res.title)}</h1>
      <p>${esc(res.description)}</p>${fig}
      <div class="meta"><code>${esc(res.path)}</code> · ${res.x_rows.toLocaleString("en-GB")} rows · ${res.schema.fields.length} columns · ${fmtBytes(res.bytes)}${key} · CC BY 4.0</div>
      <div class="row">
        <a class="btn small primary" href="data/${esc(res.path)}" download>Download CSV</a>
        <a class="btn small" href="#dict">Data dictionary</a>
        <button class="btn small ghost" type="button" id="copy-view">Copy link to this view</button>
      </div>`;
    $("copy-view").addEventListener("click", () => copyText(location.href, "Link"));
  }

  // ---------- filters
  function renderFilters() {
    const box = $("filters");
    box.innerHTML = "";
    cols.filter((c) => c.facet).forEach((c) => {
      const values = [...new Set(table.rows.map((r) => c.key(r[c.name])))]
        .sort((a, b) => a.localeCompare(b, "en", { numeric: true }));
      const el = document.createElement("div");
      el.className = "filter";
      el.dataset.col = c.name;
      el.innerHTML = `
        <div class="fl"><span title="${esc(c.description || "")}">${esc(c.name)}${c.facet === "first-word" ? " (first word)" : ""}</span></div>
        <details class="pop"><summary class="btn small" style="width:100%;justify-content:space-between"><span class="sum">All</span><span aria-hidden="true">▾</span></summary>
          <div class="pop-body">
            ${values.map((v) => `<label><input type="checkbox" value="${esc(v)}"> <span>${esc(v)}</span> <span class="meta" data-n="${esc(v)}"></span></label>`).join("")}
            <div class="pop-actions"><button class="linkish" type="button" data-act="clear">Clear</button></div>
          </div></details>`;
      el.querySelectorAll("input").forEach((cb) => {
        cb.checked = !!(st.sets[c.name] && st.sets[c.name].has(cb.value));
        cb.addEventListener("change", () => {
          const set = st.sets[c.name] || (st.sets[c.name] = new Set());
          cb.checked ? set.add(cb.value) : set.delete(cb.value);
          update();
        });
      });
      el.querySelector("[data-act=clear]").addEventListener("click", () => { delete st.sets[c.name]; syncFilterInputs(); update(); });
      box.appendChild(el);
    });
    Object.keys(st.ranges).forEach(addRangeCard);
    renderRangeSelect();
  }

  function addRangeCard(name) {
    const c = colBy[name];
    if (!c || $("filters").querySelector(`[data-range="${CSS.escape(name)}"]`)) return;
    const g = st.ranges[name] || (st.ranges[name] = { min: null, max: null });
    const isDefault = (res.x_ranges || []).includes(name);
    const el = document.createElement("div");
    el.className = "filter";
    el.dataset.range = name;
    el.innerHTML = `
      <div class="fl"><span title="${esc(c.description || "")}">${esc(name)}${c.unit ? ` <span class="meta">(${esc(c.unit)})</span>` : ""}</span>
        ${isDefault ? "" : `<button class="linkish clear-one" type="button" aria-label="Remove ${esc(name)} filter">remove</button>`}</div>
      <div class="range">
        <input type="number" step="any" inputmode="decimal" aria-label="${esc(name)} minimum" placeholder="min ${esc(fmtNum(c.min))}" value="${g.min ?? ""}">
        <input type="number" step="any" inputmode="decimal" aria-label="${esc(name)} maximum" placeholder="max ${esc(fmtNum(c.max))}" value="${g.max ?? ""}">
      </div>`;
    const [lo, hi] = el.querySelectorAll("input");
    let t;
    const onInput = () => {
      clearTimeout(t);
      t = setTimeout(() => {
        g.min = lo.value === "" ? null : Number(lo.value);
        g.max = hi.value === "" ? null : Number(hi.value);
        el.classList.toggle("active", g.min != null || g.max != null);
        update();
      }, 250);
    };
    lo.addEventListener("input", onInput);
    hi.addEventListener("input", onInput);
    el.classList.toggle("active", g.min != null || g.max != null);
    const rm = el.querySelector(".clear-one");
    if (rm) rm.addEventListener("click", () => { delete st.ranges[name]; el.remove(); renderRangeSelect(); update(); });
    $("filters").appendChild(el);
  }

  function renderRangeSelect() {
    const sel = $("add-range");
    const avail = cols.filter((c) => c.isNum && !st.ranges[c.name]);
    sel.hidden = !avail.length;
    sel.innerHTML = `<option value="">+ Filter by number…</option>` + avail.map((c) => `<option value="${esc(c.name)}">${esc(c.name)}</option>`).join("");
  }

  function syncFilterInputs() {
    document.querySelectorAll("#filters .filter[data-col]").forEach((el) => {
      const set = st.sets[el.dataset.col];
      el.querySelectorAll("input").forEach((cb) => { cb.checked = !!(set && set.has(cb.value)); });
    });
    document.querySelectorAll("#filters .filter[data-range]").forEach((el) => {
      const g = st.ranges[el.dataset.range] || {};
      const [lo, hi] = el.querySelectorAll("input");
      lo.value = g.min ?? ""; hi.value = g.max ?? "";
      el.classList.toggle("active", g.min != null || g.max != null);
    });
    $("q").value = st.q;
  }

  function renderFacetCounts() {
    document.querySelectorAll("#filters .filter[data-col]").forEach((el) => {
      const c = colBy[el.dataset.col];
      const counts = {};
      items.forEach((it) => { if (passes(it, c.name)) { const k = c.key(it.r[c.name]); counts[k] = (counts[k] || 0) + 1; } });
      el.querySelectorAll("[data-n]").forEach((s) => { s.textContent = counts[s.dataset.n] || 0; });
      const set = st.sets[c.name];
      const n = set ? set.size : 0;
      el.classList.toggle("active", n > 0);
      el.querySelector(".sum").textContent = n === 0 ? "All" : n <= 2 ? [...set].join(", ") : n + " selected";
    });
  }

  // ---------- table
  function highlight(text) {
    const ts = terms();
    // split out URLs so they can be linked without breaking the markup
    const parts = String(text).split(/(https?:\/\/[^\s<>"]+[^\s<>".,;:)])/g);
    return parts.map((p, i) => {
      let h = esc(p);
      if (ts.length) {
        const re = new RegExp("(" + ts.map((t) => esc(t).replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|") + ")", "gi");
        h = h.replace(re, "<mark>$1</mark>");
      }
      return i % 2 ? `<a href="${esc(p)}" target="_blank" rel="noopener">${h}</a>` : h;
    }).join("");
  }

  function visibleCols() { return cols.filter((c) => !st.hidden.has(c.name)); }

  function renderTable() {
    const vc = visibleCols();
    const start = st.size ? st.page * st.size : 0;
    const pageRows = st.size ? filtered.slice(start, start + st.size) : filtered;
    const sortIdx = Object.fromEntries(st.sort.map((s, i) => [s.col, { ...s, i }]));
    const head = vc.map((c) => {
      const s = sortIdx[c.name];
      const aria = s ? (s.dir === "asc" ? "ascending" : "descending") : "none";
      const arrow = s ? (s.dir === "asc" ? "▲" : "▼") + (st.sort.length > 1 ? `<sup>${s.i + 1}</sup>` : "") : "";
      const tip = [c.description, c.unit ? `Unit: ${c.unit}` : "", "Click to sort, shift-click to add a secondary sort."].filter(Boolean).join("\n");
      return `<th class="${c.isNum ? "num" : ""}" aria-sort="${aria}" scope="col"><button type="button" data-sort="${esc(c.name)}" title="${esc(tip)}">${esc(c.name)}<span class="arrow" aria-hidden="true">${arrow}</span></button></th>`;
    }).join("");
    let body;
    if (!pageRows.length) {
      body = `<tr><td colspan="${vc.length}"><div class="empty">No rows match these filters. <button class="linkish" type="button" data-act="reset">Clear all filters</button></div></td></tr>`;
    } else {
      body = pageRows.map(({ r }) => "<tr>" + vc.map((c) => {
        const v = r[c.name];
        if (v == null) return `<td class="null${c.isNum ? " num" : ""}">—</td>`;
        if (c.isNum) return `<td class="num">${highlight(fmtNum(v, c))}</td>`;
        const shown = typeof v === "boolean" ? (v ? "Yes" : "No") : v;
        return c.long && String(v).length > 90
          ? `<td class="long" title="Click to expand"><div class="clamp">${highlight(shown)}</div></td>`
          : `<td>${highlight(shown)}</td>`;
      }).join("") + "</tr>").join("");
    }
    $("table-wrap").innerHTML = `<table class="data"><caption class="visually-hidden">${esc(res.title)}</caption><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
  }

  function renderStatus() {
    const total = items.length, n = filtered.length;
    const start = st.size ? st.page * st.size : 0;
    const end = st.size ? Math.min(start + st.size, n) : n;
    $("count").innerHTML = n === total
      ? `<strong>${n.toLocaleString("en-GB")}</strong> rows`
      : `<strong>${n.toLocaleString("en-GB")}</strong> of ${total.toLocaleString("en-GB")} rows match`;
    if (n > (st.size || n)) $("count").innerHTML += ` · showing ${start + 1}–${end}`;

    const chips = [];
    if (st.q) chips.push(["q", `search: “${st.q}”`]);
    for (const [c, set] of Object.entries(st.sets)) if (set.size) chips.push(["f." + c, `${c}: ${[...set].join(", ")}`]);
    for (const [c, g] of Object.entries(st.ranges)) if (g.min != null || g.max != null)
      chips.push(["r." + c, `${c}: ${g.min ?? "…"} – ${g.max ?? "…"}`]);
    st.sort.forEach((s) => chips.push(["s." + s.col, `sorted by ${s.col} ${s.dir === "asc" ? "↑" : "↓"}`]));
    $("chips").innerHTML = chips.map(([k, l]) => `<button class="chip" type="button" data-chip="${esc(k)}" aria-label="Remove ${esc(l)}">${esc(l)}<span aria-hidden="true">×</span></button>`).join("")
      + (chips.length > 1 ? `<button class="linkish" type="button" data-act="reset">Clear all</button>` : "");
  }

  function renderPager() {
    const n = filtered.length;
    const pages = st.size ? Math.max(1, Math.ceil(n / st.size)) : 1;
    $("pager").innerHTML = `
      <div class="pg">
        <label for="ps">Rows per page</label>
        <select id="ps">${[25, 50, 100, 250, 0].map((s) => `<option value="${s}" ${s === st.size ? "selected" : ""}>${s || "All"}</option>`).join("")}</select>
      </div>
      <div class="pg">
        <button class="btn small" type="button" data-pg="prev" ${st.page <= 0 ? "disabled" : ""}>← Previous</button>
        <span>Page ${st.page + 1} of ${pages}</span>
        <button class="btn small" type="button" data-pg="next" ${st.page >= pages - 1 ? "disabled" : ""}>Next →</button>
      </div>`;
    $("ps").addEventListener("change", (e) => { st.size = Number(e.target.value); update(); });
  }

  function renderColumns() {
    const body = $("cols-body");
    body.innerHTML = cols.map((c) => `<label><input type="checkbox" value="${esc(c.name)}" ${st.hidden.has(c.name) ? "" : "checked"}> ${esc(c.name)}</label>`).join("")
      + `<div class="pop-actions"><button class="linkish" type="button" data-act="all">Show all</button><button class="linkish" type="button" data-act="none">Hide all</button></div>`;
    const sum = () => { $("cols-summary").textContent = `Columns ${cols.length - st.hidden.size}/${cols.length}`; };
    body.querySelectorAll("input").forEach((cb) => cb.addEventListener("change", () => {
      cb.checked ? st.hidden.delete(cb.value) : st.hidden.add(cb.value);
      sum(); writeState(); renderTable();
    }));
    body.querySelector("[data-act=all]").addEventListener("click", () => { st.hidden.clear(); renderColumns(); writeState(); renderTable(); });
    body.querySelector("[data-act=none]").addEventListener("click", () => {
      cols.slice(1).forEach((c) => st.hidden.add(c.name)); renderColumns(); writeState(); renderTable();
    });
    sum();
  }

  function renderDownloads() {
    $("dl-body").innerHTML = `
      <label><a href="data/${esc(res.path)}" download>Full table, CSV (${fmtBytes(res.bytes)})</a></label>
      <label><button class="linkish" type="button" data-dl="csv">Matching rows, CSV</button></label>
      <label><button class="linkish" type="button" data-dl="json">Matching rows, JSON</button></label>
      <label><a href="data/${esc(pkg.x_bundle.path)}" download>Every table, zip (${fmtBytes(pkg.x_bundle.bytes)})</a></label>
      <label><a href="data/datapackage.json" target="_blank">Schema: datapackage.json</a></label>
      <p class="meta" style="margin:8px 0 0">Matching rows keep every column, in the current sort order, with the original values.</p>`;
    $("dl-body").querySelectorAll("[data-dl]").forEach((b) => b.addEventListener("click", () => {
      const suffix = filtered.length === items.length ? "" : "_filtered";
      if (b.dataset.dl === "csv") {
        const q = (s) => (/[",\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s);
        const lines = [table.header.map(q).join(",")].concat(filtered.map((it) => table.raw[it.i].map(q).join(",")));
        download(`${res.name}${suffix}.csv`, lines.join("\n") + "\n", "text/csv");
      } else {
        download(`${res.name}${suffix}.json`, JSON.stringify(filtered.map((it) => it.r), null, 2), "application/json");
      }
      toast(`Downloaded ${filtered.length} rows`);
    }));
  }

  function renderDict() {
    $("dict").innerHTML = `
      <h2 id="dict-h">Data dictionary</h2>
      <p>Every column in <code>${esc(res.path)}</code>, as declared in <a href="data/datapackage.json">datapackage.json</a>.</p>
      <div class="table-wrap"><table class="data">
        <thead><tr><th scope="col"><button type="button" tabindex="-1">Column</button></th><th scope="col"><button type="button" tabindex="-1">Type</button></th><th scope="col"><button type="button" tabindex="-1">Unit</button></th><th scope="col"><button type="button" tabindex="-1">Description</button></th><th scope="col"><button type="button" tabindex="-1">Values</button></th></tr></thead>
        <tbody>${cols.map((c) => `<tr>
          <td class="name">${esc(c.name)}</td>
          <td class="type">${esc(c.type)}</td>
          <td class="type">${esc(c.unit || "")}</td>
          <td>${esc(c.description || "")}</td>
          <td class="stat">${c.isNum && c.min != null ? `${esc(fmtNum(c.min, c))} – ${esc(fmtNum(c.max, c))}` : `${c.distinct} distinct`}${c.nulls ? ` · ${c.nulls} empty` : ""}</td>
        </tr>`).join("")}</tbody></table></div>`;
  }

  // ---------- events (bound once)
  function bind() {
    let t;
    $("q").addEventListener("input", (e) => { clearTimeout(t); t = setTimeout(() => { st.q = e.target.value.trim(); update(); }, 150); });
    $("add-range").addEventListener("change", (e) => {
      const name = e.target.value;
      if (!name) return;
      st.ranges[name] = { min: null, max: null };
      addRangeCard(name);
      renderRangeSelect();
      const card = $("filters").querySelector(`[data-range="${CSS.escape(name)}"] input`);
      if (card) card.focus();
    });
    $("table-wrap").addEventListener("click", (e) => {
      const sb = e.target.closest("[data-sort]");
      if (sb) {
        const col = sb.dataset.sort;
        const cur = st.sort.find((s) => s.col === col);
        const next = !cur ? "asc" : cur.dir === "asc" ? "desc" : null;
        if (e.shiftKey) {
          if (!cur) st.sort.push({ col, dir: "asc" });
          else if (next) cur.dir = next;
          else st.sort = st.sort.filter((s) => s.col !== col);
        } else st.sort = next ? [{ col, dir: next }] : [];
        update();
        const again = $("table-wrap").querySelector(`[data-sort="${CSS.escape(col)}"]`);
        if (again) again.focus();
        return;
      }
      const td = e.target.closest("td.long");
      if (td && !e.target.closest("a")) td.classList.toggle("expanded");
    });
    document.addEventListener("click", (e) => {
      if (e.target.closest("[data-act=reset]")) { resetAll(); return; }
      const chip = e.target.closest("[data-chip]");
      if (chip) {
        const k = chip.dataset.chip;
        if (k === "q") st.q = "";
        else if (k.startsWith("f.")) delete st.sets[k.slice(2)];
        else if (k.startsWith("r.")) { const g = st.ranges[k.slice(2)]; g.min = g.max = null; }
        else if (k.startsWith("s.")) st.sort = st.sort.filter((s) => s.col !== k.slice(2));
        syncFilterInputs(); update();
        return;
      }
      const pg = e.target.closest("[data-pg]");
      if (pg) {
        st.page += pg.dataset.pg === "next" ? 1 : -1;
        update({ keepPage: true });
        $("table-wrap").scrollTop = 0;
        return;
      }
      // close any open popover the click was outside of
      document.querySelectorAll("details.pop[open]").forEach((d) => { if (!d.contains(e.target)) d.open = false; });
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") document.querySelectorAll("details.pop[open]").forEach((d) => { d.open = false; });
      if (e.key === "/" && !/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)) { e.preventDefault(); $("q").focus(); }
    });
    window.addEventListener("popstate", () => open(new URLSearchParams(location.search)));
  }

  function resetAll() {
    const keep = { hidden: st.hidden, size: st.size };
    st = readState(new URLSearchParams());
    Object.assign(st, keep);
    renderFilters();
    syncFilterInputs();
    update();
  }

  // ---------- open a dataset
  async function open(params) {
    const name = params.get("d");
    res = pkg.resources.find((r) => r.name === name) || pkg.resources[0];
    renderHead();
    $("table-wrap").innerHTML = `<div class="empty">Loading ${esc(res.title)}…</div>`;
    try {
      table = await loadTable(res);
    } catch (e) {
      $("table-wrap").innerHTML = `<div class="err">${esc(e.message)}. If you opened this page straight from disk, serve the folder instead: <code>python3 -m http.server -d site</code>.</div>`;
      return;
    }
    setupCols();
    st = readState(params);
    $("q").value = st.q;
    renderFilters();
    renderColumns();
    renderDownloads();
    renderDict();
    update();
  }

  loadPackage().then((p) => {
    pkg = p;
    renderNav();
    bind();
    open(new URLSearchParams(location.search));
  }).catch((e) => {
    $("ds-head").innerHTML = `<div class="err">Could not load the dataset index: ${esc(e.message)}. Serve the folder over HTTP: <code>python3 -m http.server -d site</code>.</div>`;
  });
})();
