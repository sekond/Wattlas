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
  // Draw a choropleth of the Landkreise into `host`.
  //   host      : a DOM element to render into
  //   topo      : parsed TopoJSON (the committed basemap)
  //   object    : the TopoJSON object name (default "landkreise")
  //   width/height : SVG viewBox size; the SVG itself is width:100% (responsive)
  //   ariaLabel : accessible description of the map
  // Returns a handle: { svg, projection, path, features, recolor(fillFor) }.
  function choropleth(host, opts) {
    const { topo, object = "landkreise", width = 360, height = 460,
            ariaLabel = "Map of Germany by Landkreis" } = opts;
    const fc = topojson.feature(topo, topo.objects[object]);
    const projection = d3.geoMercator().fitSize([width, height], fc);
    const path = d3.geoPath(projection);

    host.innerHTML = "";
    const svg = d3.select(host).append("svg")
      .attr("viewBox", `0 0 ${width} ${height}`)
      .attr("width", "100%")
      .attr("role", "img")
      .attr("aria-label", ariaLabel);

    const paths = svg.append("g").selectAll("path")
      .data(fc.features).join("path")
      .attr("class", "lk")
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
    return g;
  }

  return { choropleth, points };
})();
