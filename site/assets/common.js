/* Shared helpers: data package loading, CSV parsing, formatting, theme, copy. */
(function () {
  "use strict";

  const DATA = "data/";
  let pkgPromise = null;

  function loadPackage() {
    if (!pkgPromise) {
      pkgPromise = fetch(DATA + "datapackage.json").then((r) => {
        if (!r.ok) throw new Error("Could not load datapackage.json (" + r.status + ")");
        return r.json();
      });
    }
    return pkgPromise;
  }

  // RFC 4180: quoted fields, doubled quotes, CRLF or LF.
  function parseCSV(text) {
    const rows = [];
    let row = [], field = "", i = 0, q = false;
    if (text.charCodeAt(0) === 0xfeff) i = 1;
    for (; i < text.length; i++) {
      const c = text[i];
      if (q) {
        if (c === '"') {
          if (text[i + 1] === '"') { field += '"'; i++; } else q = false;
        } else field += c;
      } else if (c === '"') q = true;
      else if (c === ",") { row.push(field); field = ""; }
      else if (c === "\n" || c === "\r") {
        if (c === "\r" && text[i + 1] === "\n") i++;
        row.push(field); rows.push(row); row = []; field = "";
      } else field += c;
    }
    if (field !== "" || row.length) { row.push(field); rows.push(row); }
    return rows;
  }

  function cast(v, type) {
    if (v === "" || v == null) return null;
    if (type === "integer" || type === "number") { const n = Number(v); return Number.isFinite(n) ? n : null; }
    if (type === "boolean") return v === "True" || v === "true";
    return v;
  }

  const tableCache = {};
  function loadTable(res) {
    if (!tableCache[res.name]) {
      tableCache[res.name] = fetch(DATA + res.path)
        .then((r) => { if (!r.ok) throw new Error("Could not load " + res.path); return r.text(); })
        .then((text) => {
          const raw = parseCSV(text).filter((r) => r.length > 1 || r[0] !== "");
          const header = raw.shift();
          const fields = res.schema.fields;
          const rows = raw.map((r) => {
            const o = {};
            header.forEach((h, j) => { o[h] = cast(r[j], (fields[j] || {}).type); });
            return o;
          });
          return { header, rows, raw, fields };   // raw keeps the original strings for exports
        });
    }
    return tableCache[res.name];
  }

  function fmtNum(v, field) {
    if (v == null) return "";
    if (typeof v !== "number") return String(v);
    if (field && field.unit === "p-value") return v === 0 ? "0" : v < 0.001 ? v.toExponential(1) : v.toFixed(3);
    const a = Math.abs(v);
    if (a !== 0 && a < 0.001) return v.toExponential(2);
    return v.toLocaleString("en-GB", { maximumFractionDigits: a < 1 ? 3 : 2, useGrouping: a >= 10000 });
  }

  function fmtBytes(b) {
    if (b == null) return "";
    if (b < 1024) return b + " B";
    if (b < 1024 * 1024) return (b / 1024).toFixed(b < 10240 ? 1 : 0) + " KB";
    return (b / 1024 / 1024).toFixed(1) + " MB";
  }

  function fmtDate(iso) {
    if (!iso) return "";
    const d = new Date(iso + "T00:00:00");
    return isNaN(d) ? iso : d.toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" });
  }

  // "A", "A & B", "A, B & C"
  function authorList(pkg) {
    const n = (pkg.contributors || []).map((c) => c.title);
    return n.length > 1 ? n.slice(0, -1).join(", ") + " & " + n[n.length - 1] : n[0] || "";
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  function toast(msg) {
    let t = document.querySelector(".toast");
    if (!t) { t = document.createElement("div"); t.className = "toast"; t.setAttribute("role", "status"); document.body.appendChild(t); }
    t.textContent = msg;
    t.classList.add("show");
    clearTimeout(t._h);
    t._h = setTimeout(() => t.classList.remove("show"), 1800);
  }

  function copyText(text, label) {
    const done = () => toast((label || "Text") + " copied");
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(done, () => fallback());
    } else fallback();
    function fallback() {
      const ta = document.createElement("textarea");
      ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
      document.body.appendChild(ta); ta.select();
      try { document.execCommand("copy"); done(); } catch (e) { toast("Copy failed"); }
      ta.remove();
    }
  }

  function download(name, text, type) {
    const blob = new Blob([text], { type: type || "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }

  // ---- theme
  function getTheme() { try { return localStorage.getItem("theme"); } catch (e) { return null; } }
  function setTheme(t) {
    if (t) document.documentElement.setAttribute("data-theme", t); else document.documentElement.removeAttribute("data-theme");
    try { t ? localStorage.setItem("theme", t) : localStorage.removeItem("theme"); } catch (e) { /* storage blocked */ }
  }
  const saved = getTheme();
  if (saved) document.documentElement.setAttribute("data-theme", saved);

  function isDark() {
    const t = document.documentElement.getAttribute("data-theme");
    return t ? t === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  }

  document.addEventListener("DOMContentLoaded", () => {
    const btn = document.querySelector(".theme-toggle");
    if (btn) {
      const paint = () => { btn.textContent = isDark() ? "☀" : "☾"; btn.setAttribute("aria-label", isDark() ? "Switch to light theme" : "Switch to dark theme"); };
      paint();
      btn.addEventListener("click", () => { setTheme(isDark() ? "light" : "dark"); paint(); });
    }
    loadPackage().then((pkg) => {
      document.querySelectorAll("[data-link]").forEach((a) => {
        const k = a.getAttribute("data-link");
        if (k === "repo") a.href = pkg.homepage;
        if (k === "issues") a.href = pkg.x_issues;
        if (k === "new-issue") a.href = pkg.x_issues + "/new";
      });
      document.querySelectorAll("[data-pkg]").forEach((el) => {
        const k = el.getAttribute("data-pkg");
        if (k === "version") el.textContent = "v" + pkg.version;
        if (k === "released") el.textContent = fmtDate(pkg.created);
        if (k === "maintainer") el.textContent = authorList(pkg);
      });
    }).catch(() => {});
  });

  window.CHM = { authorList, loadPackage, loadTable, parseCSV, fmtNum, fmtBytes, fmtDate, esc, toast, copyText, download, DATA };
})();
