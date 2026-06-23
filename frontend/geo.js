// geo.js — render-only map helpers for the "Wasted wind" view.
//
// Why this file exists: per project convention (CLAUDE.md), render logic is kept
// separate from data-loading. The page fetches the committed TopoJSON and the
// panel JSON, then hands them to these helpers. Nothing here fetches or computes.
//
// Rendering stack: D3 (d3-geo / d3-selection / d3-scale) + topojson-client, both
// from CDN. The basemap is a committed, pre-simplified TopoJSON of the ~400 German
// Landkreise (NUTS-3) — there are NO map tiles and no runtime map service, so the
// page still opens as a static file (CLAUDE.md: stay static, no backend, no tiles).
//
// Projection: d3.geoMercator fitted to Germany. For a single country at this
// latitude the distortion is negligible; geoConicConformal is the only meaningfully
// nicer option and not worth the extra parameters at this scale.

const GeoMap = (function () {
  // ---- shared floating tooltip ------------------------------------------- //
  // A single styled div (re-used by every map) that hovers just above a dot on
  // mouseenter and shows caller-supplied HTML. Kept here so both views get an
  // identical, instant tooltip instead of the browser's slow native <title>.
  let _tip = null;
  function _tipEl() {
    if (_tip) return _tip;
    const style = document.createElement("style");
    style.textContent =
      ".geo-tip{position:fixed;z-index:9999;pointer-events:none;opacity:0;" +
      "transform:translate(-50%,-100%);transition:opacity .12s ease;" +
      "background:#2b2a33;color:#faf9f5;font:12px/1.45 system-ui,-apple-system,sans-serif;" +
      "padding:7px 10px;border-radius:7px;max-width:240px;white-space:normal;" +
      "box-shadow:0 4px 14px rgba(0,0,0,.28);}" +
      ".geo-tip::after{content:'';position:absolute;left:50%;top:100%;" +
      "transform:translateX(-50%);border:5px solid transparent;border-top-color:#2b2a33;}" +
      ".geo-tip b{color:#fff;}" +
      ".geo-tip .gt-sub{opacity:.72;font-size:11px;}";
    document.head.appendChild(style);
    _tip = document.createElement("div");
    _tip.className = "geo-tip";
    document.body.appendChild(_tip);
    return _tip;
  }
  function _showTip(html, x, y) {
    const t = _tipEl();
    t.innerHTML = html;
    t.style.left = x + "px";
    t.style.top = (y - 9) + "px";   // sit just above the dot; arrow points down to it
    t.style.opacity = "1";
  }
  function _hideTip() { if (_tip) _tip.style.opacity = "0"; }

  // Draw a choropleth of the Landkreise into `host`.
  //   host      : a DOM element to render into
  //   topo      : parsed TopoJSON (the committed basemap)
  //   object    : the TopoJSON object name (default "landkreise")
  //   width/height : SVG viewBox size; the SVG itself is width:100% (responsive)
  //   ariaLabel : accessible description of the map
  // Returns a handle: { svg, projection, path, features, recolor(fillFor) }.
  function choropleth(host, opts) {
    const { topo, object = "landkreise", width = 360, height = 460,
            ariaLabel = "Map", className = "lk", projection: projOpt, fitPoints } = opts;
    const fc = topojson.feature(topo, topo.objects[object]);
    // Fit to the basemap, optionally extended to include extra [lon,lat] points so they
    // aren't clipped — e.g. offshore wind sites that sit beyond the land boundary.
    const fitGeom = (fitPoints && fitPoints.length)
      ? { type: "FeatureCollection", features: [...fc.features,
          { type: "Feature", geometry: { type: "MultiPoint", coordinates: fitPoints } }] }
      : fc;
    // Default projection is Mercator (fine for Germany); a caller can pass a fitted-on
    // demand projection instance (e.g. d3.geoConicConformal for France) via opts.projection.
    const projection = (projOpt || d3.geoMercator()).fitSize([width, height], fitGeom);
    const path = d3.geoPath(projection);

    host.innerHTML = "";
    const svg = d3.select(host).append("svg")
      .attr("viewBox", `0 0 ${width} ${height}`)
      .attr("width", "100%")
      .attr("role", "img")
      .attr("aria-label", ariaLabel);

    const paths = svg.append("g").selectAll("path")
      .data(fc.features).join("path")
      .attr("class", className)
      .attr("d", path);

    // fillFor(props) -> colour string for that district, or a falsy value for the
    // "no data" state. A falsy result clears the inline fill so the path falls back
    // to the CSS `.lk` default colour — keeping "no data" visually distinct from a
    // real but low value (an acceptance criterion of Panel 1).
    function recolor(fillFor) {
      paths.attr("fill", (f) => fillFor(f.properties) || null);
    }

    return { svg, projection, path, features: fc.features, recolor };
  }

  // Plot lon/lat points over an existing map (plant points, demand centres).
  // Render-only; the page supplies colour / size / hover-title accessors. `r`,
  // `fill` and `stroke` may each be a constant or a per-item function. Returns the
  // <g> so the caller can clear/replace it (e.g. on metric toggle).
  //
  // Hover: `title(d)` sets the native <title> (kept for accessibility / fallback).
  // If `html(d)` is also given, the dot gets the rich floating tooltip above — an
  // instant styled card with the installation's context (capacity, units, type).
  function points(map, items, opts) {
    const o = opts || {};
    const asFn = (v) => (typeof v === "function" ? v : () => v);
    const r = asFn(o.r != null ? o.r : 4);
    const fill = asFn(o.fill != null ? o.fill : "#a32d2d");
    const stroke = asFn(o.stroke != null ? o.stroke : "#faf9f5");
    const strokeWidth = o.strokeWidth != null ? o.strokeWidth : 1;
    const title = o.title || (() => "");
    const g = map.svg.append("g").attr("class", o.className || "pts");
    const sel = g.selectAll("circle").data(items).join("circle")
      .attr("cx", (d) => map.projection([d.lon, d.lat])[0])
      .attr("cy", (d) => map.projection([d.lon, d.lat])[1])
      .attr("r", r).attr("fill", fill).attr("stroke", stroke).attr("stroke-width", strokeWidth);
    sel.append("title").text(title);
    if (o.html) {
      const htmlFn = o.html;
      sel.style("cursor", "pointer")
        .on("mouseenter", function (ev, d) {
          const box = this.getBoundingClientRect();
          _showTip(htmlFn(d), box.left + box.width / 2, box.top);
        })
        .on("mouseleave", _hideTip);
    }
    return g;
  }

  return { choropleth, points };
})();
