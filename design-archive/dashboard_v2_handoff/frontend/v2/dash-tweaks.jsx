// Wattlas Dashboard v2 — Tweaks panel (React, mounts alongside the vanilla dashboard).
const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "density": "airy",
  "spreadStyle": "bars",
  "carbonStyle": "timeline",
  "pulseSplit": true
}/*EDITMODE-END*/;

function TweaksApp() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);

  React.useEffect(() => {
    document.body.classList.toggle("density-compact", t.density === "compact");
    if (window.S) {
      S.tweaks.density = t.density;
      S.tweaks.spreadStyle = t.spreadStyle === "calendar" ? "heatmap" : "bars";
      S.tweaks.carbonStyle = t.carbonStyle === "scatter" ? "scatter" : "time";
      S.tweaks.pulseSplit = !!t.pulseSplit;
      if (window.D && D.spread) {
        try { renderPulse(); renderSpread(); renderCarbon(); } catch (e) {}
      }
    }
  }, [t.density, t.spreadStyle, t.carbonStyle, t.pulseSplit]);

  return (
    <TweaksPanel>
      <TweakSection label="Layout" />
      <TweakRadio label="Density" value={t.density} options={["airy", "compact"]}
        onChange={(v) => setTweak("density", v)} />
      <TweakSection label="Chart styles" />
      <TweakRadio label="Spread" value={t.spreadStyle} options={["bars", "calendar"]}
        onChange={(v) => setTweak("spreadStyle", v)} />
      <TweakRadio label="Carbon" value={t.carbonStyle} options={["timeline", "scatter"]}
        onChange={(v) => setTweak("carbonStyle", v)} />
      <TweakToggle label="Pulse: weekday/weekend split" value={t.pulseSplit}
        onChange={(v) => setTweak("pulseSplit", v)} />
    </TweaksPanel>
  );
}

const tweaksRoot = document.createElement("div");
tweaksRoot.id = "tweaks-root";
document.body.appendChild(tweaksRoot);
ReactDOM.createRoot(tweaksRoot).render(<TweaksApp />);
