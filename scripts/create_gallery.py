"""Generate standalone gallery routes from one accessible shell."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
VIEWS = {
    "map": ("Read a field, one layer at a time.", "A regular longitude/latitude map. Areas are distorted toward the poles; color scales stay fixed as time changes.", "14-maps"),
    "terrain": ("Give a synthetic landscape some height.", "An invented terrain scene colored by the selected field. Vertical height is exaggerated, and the scene is not a scaled geographic model.", "16-terrain"),
    "globe": ("A different perspective on the same field.", "Rotate a spherical point grid. The hidden hemisphere is omitted; no real basemap, terrain or satellite imagery is used.", "17-globe"),
    "dashboard": ("Connect the field to the bigger picture.", "The map, area-weighted time series and summaries share your selection. The vertical line marks the selected day.", "19-dashboard"),
    "flow": ("Find direction in a moving field.", "Arrows show synthetic eastward and northward wind components. Change the underlying color variable while the wind vectors remain explicit.", "10-wind"),
    "compare": ("Compare time without changing the scale.", "Day zero stays on the left; the selected day appears on the right. Both panels use exactly the same variable and color limits.", "18-time"),
}

def main():
    for mode, (title, description, lesson) in VIEWS.items():
        options = "".join(f'<option value="{v}">{label}</option>' for v, label in [("temperature", "Temperature"), ("precipitation", "Precipitation"), ("wind", "Wind speed")])
        page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{mode.title()} — Earth / Lab</title><link rel="stylesheet" href="../../styles.css"></head>
<body data-view="{mode}"><a class="skip" href="#main">Skip to visualization</a><header><div class="wrap"><a class="brand" href="../../">EARTH <span>/ LAB</span></a><nav aria-label="Main"><a href="../../#explore">All experiences</a><a href="../../book/">Book</a><a href="../../lab/index.html?path={lesson}.ipynb">Run the notebook ↗</a></nav></div></header>
<main id="main" class="wrap"><div class="gallery-title"><span class="eyebrow">Interactive gallery / {mode}</span><h1>{title}</h1><p class="lead">{description}</p><span class="synthetic">ORIGINAL SYNTHETIC DATA</span></div>
<div class="controls"><div class="control"><label for="variable">Field</label><select id="variable">{options}</select></div><div class="control"><label for="time">Synthetic day <output id="day-value">0</output> / 59</label><input id="time" type="range" min="0" max="59" value="0"></div><button id="play" aria-pressed="false">Play time</button><div class="control"><label for="render">Rendering</label><select id="render"><option value="surface">Surface cells</option><option value="points">Points</option></select></div><div class="control" {'hidden style="display:none"' if mode not in ('globe','terrain') else ''}><label for="rotation">View rotation</label><input id="rotation" type="range" min="-180" max="180" value="-25"></div></div>
<div class="visual"><canvas id="visualization" role="img" aria-label="Interactive synthetic visualization" aria-describedby="summary"></canvas><div class="legend"><span id="legend-low"></span><span class="gradient"></span><span id="legend-high"></span></div><p id="summary" aria-live="polite"></p></div>
<div class="stats"><div class="stat"><span>Area-weighted mean</span><strong id="mean"></strong></div><div class="stat"><span>Grid minimum</span><strong id="min"></strong></div><div class="stat"><span>Grid maximum</span><strong id="max"></strong></div></div>
<details><summary>Inspect tabular values and provenance</summary><p>Original deterministic trigonometric equations, evaluated locally in JavaScript. The gallery omits the notebook generator's seeded temperature noise; both are synthetic demonstrations. Sample units: <span id="unit"></span>. These values are not observations or Destination Earth outputs.</p><div class="table-scroll"><table><caption>Selected field at representative coordinates</caption><thead><tr><th scope="col">Latitude</th><th scope="col">Longitude</th><th scope="col">Value</th></tr></thead><tbody id="sample-values"></tbody></table></div><div class="table-scroll"><table id="view-table" hidden><caption id="view-caption"></caption><thead><tr id="view-head"></tr></thead><tbody id="view-values"></tbody></table></div><p>Grid summaries use cosine latitude weights. All time points are synthetic day numbers, not dates. Source and equations: <a href="https://github.com/jltobias/JupyterLite-Destination-Earth-Digital-Twin/blob/main/web/gallery.js">gallery.js</a> (MIT); generated values (CC BY 4.0).</p></details>
<aside class="banner"><h2>Make the experiment your own.</h2><p>Use the matching notebook for the equations, numerical checks, exercises and interpretation.</p><a class="button" href="../../lab/index.html?path={lesson}.ipynb">Open {lesson}.ipynb ↗</a></aside></main><footer><div class="wrap">Independent educational project · No official imagery or authentic model output · <a href="../../">Back to Earth / Lab</a></div></footer><script src="../../gallery.js"></script></body></html>'''
        destination = ROOT / "web" / "gallery" / mode
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "index.html").write_text(page, encoding="utf-8")
    print(f"Created {len(VIEWS)} gallery routes")

if __name__ == "__main__": main()
