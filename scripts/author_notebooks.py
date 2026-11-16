"""Reproduce the original lesson sources. Run only when intentionally reauthoring content."""
import json
from pathlib import Path
from textwrap import dedent
from component_lessons import COMPONENT_LESSONS

ROOT = Path(__file__).resolve().parents[1]
REPO = "https://github.com/jltobias/JupyterLite-Destination-Earth-Digital-Twin"
LESSONS = [
    ("01-system", "A digital twin is a connected system", "Trace the roles of platform, data lake and twin engine; measure a small data pipeline.", '''
stages = {"generate": 0, "validate": 0, "analyze": 0}
cube = lab.synthetic_cube()
stages["generate"] = cube["temperature"].size
assert cube["temperature"].shape == (60, 25, 49)
assert np.isfinite(cube["temperature"]).all()
stages["validate"] = cube["temperature"].size
series = lab.global_mean(cube["temperature"], cube["lat"])
stages["analyze"] = series.size
fig, ax = plt.subplots(figsize=(8, 3))
ax.bar(stages.keys(), stages.values(), color=["#3f8eaa", "#3f8eaa", "#ebad55"])
ax.set(ylabel="Number of values", title="Synthetic pipeline: field to summary")
plt.show()
assert stages["analyze"] < stages["generate"]
print(f"Reduction ratio: {stages['generate'] / stages['analyze']:.0f}:1")
''', "Change the grid resolution and calculate the new reduction ratio. Explain why a summary cannot reconstruct the original field.", "A twin connects models, data and user workflows. This array pipeline illustrates interfaces; it does not run a production twin. The DestinE Platform is implemented by ESA, the Data Lake by EUMETSAT, and the Digital Twin Engine and initial twins by ECMWF, under an EU initiative.", "https://github.com/destination-earth/DestinE"),
    ("02-grids", "Coordinates, grids and units", "Inspect coordinate conventions; convert temperature units without losing metadata.", '''
cube = lab.synthetic_cube()
kelvin = cube["temperature"][0]
celsius = kelvin - 273.15
assert np.allclose(celsius + 273.15, kelvin)
assert np.all(np.diff(cube["lon"]) > 0)
assert cube["lon"].max() < 180
fig, ax = plt.subplots(figsize=(8, 3))
im = ax.pcolormesh(cube["lon"], cube["lat"], celsius, shading="auto", cmap="coolwarm")
fig.colorbar(im, ax=ax, label="Temperature (°C)")
ax.set(xlabel="Longitude (degrees east)", ylabel="Latitude (degrees north)", title="Synthetic regular grid, day 0")
plt.show()
print("Grid spacing:", np.diff(cube["lon"])[0], "degrees longitude")
''', "Plot the same field in kelvin. Check whether the pattern changes and whether a numeric threshold must change.", "Coordinate arrays describe cell centers on a regular teaching grid. Actual model meshes can be reduced, unstructured or rotated; do not infer a native grid from a rendered map.", "https://destine.ecmwf.int/digital-twin-engine/"),
    ("03-access", "Data access without credentials in the browser", "Describe discovery, selection and export; distinguish a query plan from a live request.", '''
cube = lab.synthetic_cube()
region = (cube["lat"] >= 30) & (cube["lat"] <= 60)
west_east = (cube["lon"] >= -20) & (cube["lon"] <= 40)
subset = cube["temperature"][:7, region, :][:, :, west_east]
plan = {"source": "local synthetic cube", "variable": "temperature", "units": "K", "days": 7,
        "latitude_bounds": [30, 60], "longitude_bounds": [-20, 40]}
assert subset.size > 0
assert subset.nbytes < cube["temperature"].nbytes
print(plan)
print(f"Local selection: {subset.nbytes:,} of {cube['temperature'].nbytes:,} bytes")
fig, ax = plt.subplots(figsize=(7, 3))
ax.plot(subset.mean(axis=(1, 2)) - 273.15, marker="o")
ax.set(xlabel="Synthetic day", ylabel="Regional mean (°C)", title="Synthetic selection, no service request")
plt.show()
''', "Expand the time range and compute the change in payload size. Draft a selection checklist including grid, units, license and time convention.", "A smaller selection reduces transfer and browser memory. Official catalog-generated requests, account permissions and applicable terms are needed for authentic data. This plan deliberately contains no invented service collection ID.", "https://polytope.readthedocs.io/en/stable/"),
    ("04-validation", "Validate a small authorized export", "Reject malformed values and missing provenance; keep real imports separate from synthetic examples.", '''
import copy
payload = {"schema_version": 1, "variable": "temperature", "units": "K",
           "lat": [40, 50], "lon": [-10, 10], "values": [[285, 286], [280, 281]],
           "provenance": {"source": "original synthetic example", "license": "CC BY 4.0",
                          "retrieved": "2026-11-15", "method": "hand-constructed teaching grid"}}
accepted = lab.validate_export(payload)
bad = copy.deepcopy(payload)
bad["units"] = "degC"
try:
    lab.validate_export(bad)
except ValueError as exc:
    print("Expected rejection:", exc)
else:
    raise AssertionError("Incompatible units were accepted")
assert accepted["values"].shape == (2, 2)
fig, ax = plt.subplots(figsize=(5, 3))
im = ax.pcolormesh(accepted["lon"], accepted["lat"], accepted["values"], shading="auto")
fig.colorbar(im, ax=ax, label="Temperature (K)")
ax.set(title="Validated synthetic interchange example", xlabel="Longitude", ylabel="Latitude")
plt.show()
# Optional authentic path, only after you upload an authorized compatible file:
# authorized = lab.load_export("my-authorized-export.json")
# Errors propagate: there is no automatic replacement with synthetic data.
''', "Try duplicate longitude, a missing license and a NaN value. Confirm each is rejected. Convert an authorized export into this local schema only after reviewing its terms.", "A schema proves structural consistency, not scientific truth or permission. A real adapter should document its source format, conversions, missing-value policy and coordinate system.", "https://data.destination-earth.eu/terms-and-conditions"),
    ("05-labelled-arrays", "Labeled arrays and regional selection", "Use xarray dimensions and units; avoid positional indexing mistakes.", '''
import xarray as xr
cube = lab.synthetic_cube()
da = xr.DataArray(cube["temperature"], dims=("day", "latitude", "longitude"),
                  coords={"day": cube["time"], "latitude": cube["lat"], "longitude": cube["lon"]},
                  name="temperature", attrs={"units": "K", "provenance": lab.PROVENANCE})
region = da.sel(latitude=slice(30, 60), longitude=slice(-20, 40))
regional = region.mean(("latitude", "longitude")) - 273.15
assert regional.dims == ("day",)
assert region.sizes["latitude"] < da.sizes["latitude"]
fig, ax = plt.subplots(figsize=(8, 3))
regional.plot(ax=ax)
ax.set(ylabel="Unweighted regional mean (°C)", title="Synthetic regional time series")
plt.show()
print(da.attrs)
''', "Transpose the array before selecting the same region. Verify named-dimension calculations still agree.", "Labels reduce ambiguity. An arithmetic regional mean is not automatically area weighted; the next lesson addresses that distinction.", "https://docs.xarray.dev/en/stable/"),
    ("06-area-means", "Area weighting changes the answer", "Calculate cosine-weighted means; test conservation for a constant field.", '''
cube = lab.synthetic_cube()
field = cube["temperature"][0]
weighted = lab.global_mean(field, cube["lat"])
unweighted = field.mean()
weights = lab.area_weights(cube["lat"])
assert np.isclose(weights.sum(), 1)
assert np.isclose(lab.global_mean(np.ones_like(field)*7, cube["lat"]), 7)
assert weighted > unweighted
fig, ax = plt.subplots(figsize=(7, 3))
ax.plot(cube["lat"], weights, marker="o")
ax.set(xlabel="Latitude (degrees)", ylabel="Normalized latitude weight", title="Synthetic regular-grid area approximation")
plt.show()
print(f"Weighted {weighted:.2f} K; unweighted {unweighted:.2f} K")
''', "Apply the same weights to precipitation. Explain why each latitude row has a different area even though it has the same number of grid points.", "Cosine latitude is a regular-grid approximation. Accurate production calculations should use cell areas supplied with the model grid, particularly near poles and on irregular meshes.", "https://destine.ecmwf.int/climate-digital-twin/"),
    ("07-climate", "Anomalies and baseline choices", "Compute a baseline anomaly; distinguish a demonstration trend from a climate projection.", '''
cube = lab.synthetic_cube()
series = lab.global_mean(cube["temperature"], cube["lat"])
baseline = series[:30].mean()
anomaly = series - baseline
slope, intercept = np.polyfit(cube["time"], anomaly, 1)
assert abs(anomaly[:30].mean()) < 1e-10
assert .015 < slope < .035
fig, ax = plt.subplots(figsize=(8, 3))
ax.plot(cube["time"], anomaly, label="Anomaly")
ax.plot(cube["time"], slope*cube["time"]+intercept, label="Linear fit")
ax.axhline(0, color="gray", lw=.7)
ax.set(xlabel="Synthetic day", ylabel="Anomaly (K)", title="Synthetic warming signal, 30-day baseline")
ax.legend(); plt.show()
print(f"Injected demonstration trend estimate: {slope:.4f} K/day")
''', "Use days 30–59 as the baseline. Check that the fitted slope stays the same while the intercept changes.", "A baseline changes the reference level. Sixty synthetic days cannot support an inference about real-world climate; real climate comparisons need appropriate periods, experiments and uncertainty analysis.", "https://destine.ecmwf.int/climate-digital-twin/"),
    ("08-extremes", "Thresholds and event duration", "Detect exceedance runs; compare absolute and percentile thresholds.", '''
cube = lab.synthetic_cube()
series = cube["temperature"][:, 12, 24] - 273.15
threshold = np.percentile(series[:30], 85)
exceed = series > threshold
padded = np.r_[False, exceed, False].astype(int)
starts = np.flatnonzero(np.diff(padded) == 1)
ends = np.flatnonzero(np.diff(padded) == -1)
durations = ends - starts
assert durations.sum() == exceed.sum()
assert np.all(durations > 0)
fig, ax = plt.subplots(figsize=(8, 3))
ax.plot(series, label="Synthetic temperature")
ax.axhline(threshold, color="tomato", label="Baseline 85th percentile")
ax.fill_between(cube["time"], threshold, series, where=exceed, color="tomato", alpha=.35)
ax.set(xlabel="Synthetic day", ylabel="Temperature (°C)", title="Synthetic threshold events")
ax.legend(); plt.show()
print("Run lengths (days):", durations)
''', "Require runs of at least three days. Compare retained event count with raw exceedance-day count.", "A hazard definition includes threshold, duration and reference period. Neither a percentile exceedance nor this toy series is an impact forecast.", "https://destine.ecmwf.int/weather-induced-extremes-digital-twin/"),
    ("09-water", "A water budget with a conservation check", "Implement a toy catchment bucket; close the mass balance.", '''
rain = np.array([0, 2, 5, 18, 20, 8, 1, 0, 0, 12, 3, 0], dtype=float)
storage, runoff, drainage = lab.flood_bucket(rain, capacity=12, drainage=.2)
delta = np.diff(np.r_[0, storage])
assert np.allclose(rain, delta + runoff + drainage)
assert storage.min() >= 0 and storage.max() <= 12
fig, ax = plt.subplots(figsize=(8, 3))
ax.bar(np.arange(len(rain)), rain, alpha=.4, label="Rain input")
ax.plot(storage, label="Storage")
ax.plot(runoff, label="Overflow")
ax.set(xlabel="Synthetic day", ylabel="Water depth (mm)", title="Synthetic bucket, not a river forecast")
ax.legend(); plt.show()
print(f"Budget residual: {(rain-delta-runoff-drainage).sum():.2e} mm")
''', "Double storage capacity and compare total overflow. Keep rainfall fixed so the scenario comparison has a clear cause.", "Conservation is necessary but not sufficient for realism. This bucket omits routing, soil heterogeneity, snow and infrastructure; overflow is not calibrated river discharge.", "https://destine.ecmwf.int/weather-induced-extremes-digital-twin/"),
    ("10-wind", "Vector fields and derived wind speed", "Calculate vector magnitude; inspect direction without confusing components with speed.", '''
cube = lab.synthetic_cube()
u, v = cube["wind_u"][0], cube["wind_v"][0]
speed = np.hypot(u, v)
assert np.all(speed >= np.abs(u)) and np.all(speed >= np.abs(v))
fig, ax = plt.subplots(figsize=(8, 3))
im = ax.pcolormesh(cube["lon"], cube["lat"], speed, shading="auto", cmap="viridis")
ax.quiver(cube["lon"][::3], cube["lat"][::3], u[::3, ::3], v[::3, ::3], color="white")
fig.colorbar(im, ax=ax, label="Speed (m s⁻¹)")
ax.set(xlabel="Longitude", ylabel="Latitude", title="Synthetic wind components and magnitude")
plt.show()
print("Maximum speed:", speed.max(), "m/s")
''', "Compare the magnitude of the mean vector with the mean of individual magnitudes. Explain the effect of cancellation.", "Arrows show local components on a longitude/latitude display. Vector rotation and projection must be handled explicitly for model grids and geographic map projections.", "https://destine.ecmwf.int/digital-twin-engine/"),
    ("11-interpolation", "Interpolation and its assumptions", "Sample between grid points; distinguish interpolation from new information.", '''
lat = np.array([30., 40., 50., 60.]); lon = np.array([-20., 0., 20., 40.])
x, y = np.meshgrid(lon, lat)
field = 280 + .1*y + .2*x
target_lat, target_lon = 43., 7.
estimated = lab.bilinear(field, lat, lon, target_lat, target_lon)
truth = 280 + .1*target_lat + .2*target_lon
assert np.isclose(estimated, truth)
fig, ax = plt.subplots(figsize=(6, 4))
im = ax.pcolormesh(lon, lat, field, shading="auto")
ax.scatter(target_lon, target_lat, marker="x", s=100, c="red", label=f"Interpolated {estimated:.1f} K")
fig.colorbar(im, ax=ax, label="Temperature (K)")
ax.set(xlabel="Longitude", ylabel="Latitude", title="Synthetic planar field")
ax.legend(); plt.show()
''', "Add a quadratic term to the field and measure interpolation error at the same target. Try an out-of-bounds target and confirm rejection.", "Bilinear interpolation reproduces this plane exactly. It does not preserve every integral, handle the dateline automatically, or recover sub-grid processes.", "https://docs.scipy.org/doc/scipy/tutorial/interpolate.html"),
    ("12-ensembles", "Ensembles and uncertainty bands", "Summarize member spread; distinguish uncertainty types.", '''
members = lab.ensemble()
mean = members.mean(axis=0)
low, high = np.quantile(members, [.1, .9], axis=0)
assert np.all(low <= high)
assert members.shape == (30, 60)
fig, ax = plt.subplots(figsize=(8, 3))
ax.plot(members[:5].T, color="gray", alpha=.2)
ax.fill_between(np.arange(60), low, high, alpha=.3, label="10–90% member interval")
ax.plot(mean, label="Ensemble mean")
ax.set(xlabel="Synthetic day", ylabel="Temperature (°C)", title="Synthetic ensemble spread")
ax.legend(); plt.show()
print("Average interval width:", (high-low).mean(), "°C")
''', "Generate ensembles with 10 and 100 members. Compare the stability of estimated quantiles using several random seeds.", "This interval summarizes generated members; it is not a calibrated probability statement about future observations. Structural model and scenario uncertainty are absent.", "https://destine.ecmwf.int/climate-digital-twin/"),
    ("13-verification", "Skill scores and reference forecasts", "Compute bias and RMSE; compare against a declared baseline.", '''
rng = np.random.default_rng(11)
truth = 10 + 2*np.sin(np.arange(60)/6)
forecast = truth + .4 + rng.normal(0, .5, 60)
baseline = np.full(60, truth.mean())
bias = (forecast-truth).mean()
rmse = np.sqrt(np.mean((forecast-truth)**2))
reference_rmse = np.sqrt(np.mean((baseline-truth)**2))
skill = 1-rmse/reference_rmse
assert rmse >= abs(bias)
assert 0 < skill < 1
fig, ax = plt.subplots(figsize=(5, 4))
ax.scatter(truth, forecast, s=15)
ax.plot([7, 13], [7, 13], color="gray")
ax.set(xlabel="Synthetic truth (°C)", ylabel="Synthetic forecast (°C)", title="Synthetic verification experiment")
plt.show()
print(dict(bias=bias, rmse=rmse, reference_rmse=reference_rmse, skill=skill))
''', "Add a constant 2 °C bias and recompute skill. Then subtract the estimated bias and assess the remaining error.", "A score depends on the reference, sample and event definition. Synthetic truth provides a controlled experiment; this is not an assessment of an operational twin.", "https://destine.ecmwf.int/weather-induced-extremes-digital-twin/"),
    ("14-maps", "Honest two-dimensional maps", "Use fixed color limits across time; separate rendering choices from physical change.", '''
cube = lab.synthetic_cube()
days = [0, 15]
fig, axes = plt.subplots(1, 2, figsize=(10, 3), constrained_layout=True)
for ax, day in zip(axes, days):
    field = cube["temperature"][day]-273.15
    im = ax.pcolormesh(cube["lon"], cube["lat"], field, vmin=-25, vmax=25, cmap="coolwarm", shading="auto")
    ax.set(title=f"Synthetic day {day}", xlabel="Longitude", ylabel="Latitude")
fig.colorbar(im, ax=axes, label="Temperature (°C)")
plt.show()
assert axes[0].collections[0].get_clim() == axes[1].collections[0].get_clim()
print("Both frames use the same -25 to 25 °C scale")
''', "Render each frame using automatic color limits and compare the story the two versions appear to tell.", "This equirectangular display stretches areas toward the poles. It is useful for coordinates but not for judging geographic area by eye.", "https://matplotlib.org/stable/users/explain/colors/colormaps.html"),
    ("15-projections", "From longitude and latitude to a projected plane", "Calculate a spherical Mercator projection; diagnose polar distortion.", '''
radius = lab.EARTH_RADIUS_M
lat = np.linspace(-80, 80, 41); lon = np.linspace(-180, 180, 73)
x = radius*np.deg2rad(lon)
y = radius*np.log(np.tan(np.pi/4+np.deg2rad(lat)/2))
recovered = np.rad2deg(2*np.arctan(np.exp(y/radius))-np.pi/2)
assert np.allclose(lat, recovered)
scale = 1/np.cos(np.deg2rad(lat))
assert scale.max() > 5
fig, axes = plt.subplots(1, 2, figsize=(9, 3))
for latitude_y in y[::4]: axes[0].plot(x/1e6, np.full_like(x, latitude_y)/1e6, color="teal", lw=.6)
for longitude_x in x[::6]: axes[0].plot(np.full_like(y, longitude_x)/1e6, y/1e6, color="teal", lw=.6)
axes[0].set(xlabel="x (million m)", ylabel="y (million m)", title="Synthetic Mercator graticule")
axes[1].plot(lat, scale)
axes[1].set(xlabel="Latitude", ylabel="Local scale factor", title="Distortion toward poles")
plt.tight_layout(); plt.show()
''', "Evaluate the scale factor at 0°, 45° and 75°. Explain why this projection is unsuitable for visual area comparisons.", "The spherical equations are a teaching approximation. Coordinate reference systems, ellipsoids and authoritative transformations matter for real spatial analysis.", "https://proj.org/en/stable/operations/projections/merc.html"),
    ("16-terrain", "A three-dimensional terrain scene", "Create a surface from a grid; describe vertical exaggeration explicitly.", '''
cube = lab.synthetic_cube(nlat=19, nlon=31)
x, y = np.meshgrid(cube["lon"], cube["lat"])
z = cube["elevation"]
assert np.all(z >= 0) and z.shape == x.shape
fig = plt.figure(figsize=(8, 5)); ax = fig.add_subplot(projection="3d")
ax.plot_surface(x, y, z, cmap="terrain", linewidth=0, antialiased=True)
ax.set(xlabel="Longitude (°)", ylabel="Latitude (°)", zlabel="Synthetic elevation (m)", title="Invented terrain; axes have different units")
ax.view_init(elev=28, azim=-55)
plt.show()
print("Height range (m):", z.min(), z.max())
''', "Change the viewing angle and box aspect ratio. Document how apparent steepness changes even though the numbers do not.", "This scene uses degrees horizontally and meters vertically, so it is a visual exploration rather than a physically scaled terrain model. No real elevation data are used.", "https://matplotlib.org/stable/users/explain/toolkits/mplot3d.html"),
    ("17-globe", "Put a field on a globe", "Transform spherical coordinates to Cartesian coordinates; verify radius.", '''
cube = lab.synthetic_cube(nlat=25, nlon=49)
lon, lat = np.meshgrid(cube["lon"], cube["lat"])
x, y, z = lab.globe_xyz(lat, lon)
assert np.allclose(x*x+y*y+z*z, 1)
field = cube["temperature"][0]-273.15
fig = plt.figure(figsize=(7, 5)); ax = fig.add_subplot(projection="3d")
elevation, azimuth = 20, -55
elev_rad, azim_rad = np.deg2rad([elevation, azimuth])
camera = np.array([np.cos(elev_rad)*np.cos(azim_rad), np.cos(elev_rad)*np.sin(azim_rad), np.sin(elev_rad)])
visible = x*camera[0] + y*camera[1] + z*camera[2] >= 0
assert 0 < visible.sum() < visible.size
points = ax.scatter(x[visible], y[visible], z[visible], c=field[visible], cmap="coolwarm", s=12, vmin=-25, vmax=25)
ax.set_proj_type("ortho"); ax.view_init(elev=elevation, azim=azimuth)
ax.set(xlim=(-1,1), ylim=(-1,1), zlim=(-1,1))
ax.set_box_aspect((1, 1, 1)); ax.set_axis_off()
ax.set_title("Synthetic field on a unit sphere")
fig.colorbar(points, ax=ax, shrink=.6, label="Temperature (°C)")
plt.show()
''', "Use radius 2 and confirm every point is twice as far from the origin. Change the viewing longitude to inspect the hidden hemisphere.", "A globe avoids a flat-map seam in geometry but still hides a hemisphere. This spherical point rendering is not an ellipsoidal Earth model or a basemap.", "https://destine.ecmwf.int/digital-twin-engine/"),
    ("18-time", "Time slices, animation and stable scales", "Build comparable frames; measure field change rather than relying on motion.", '''
cube = lab.synthetic_cube()
days = [0, 10, 20, 30]
fig, axes = plt.subplots(2, 2, figsize=(9, 5), constrained_layout=True)
for ax, day in zip(axes.flat, days):
    im = ax.pcolormesh(cube["lon"], cube["lat"], cube["precipitation"][day], shading="auto", vmin=0, vmax=8, cmap="Blues")
    ax.set(title=f"Synthetic day {day}", xlabel="Longitude", ylabel="Latitude")
fig.colorbar(im, ax=axes, label="Precipitation (mm day⁻¹)")
plt.show()
assert np.allclose(cube["precipitation"][0], cube["precipitation"][30])
change = np.abs(cube["precipitation"][10] - cube["precipitation"][0]).mean()
print(f"Mean absolute change after 10 days: {change:.2f} mm/day")
''', "Try days 5, 15, 25 and 35. Use the live gallery time slider to compare moving patterns with these static frames.", "The generator has a 30-day periodic precipitation cycle. Repetition follows an equation chosen for teaching; it is not a discovered atmospheric oscillation.", "https://matplotlib.org/stable/api/animation_api.html"),
    ("19-dashboard", "Build an analytical dashboard", "Coordinate a map, time series and distribution; retain units and provenance.", '''
cube = lab.synthetic_cube(); day = 15
field = cube["temperature"][day]-273.15
series = lab.global_mean(cube["temperature"], cube["lat"])-273.15
fig, axes = plt.subplots(1, 3, figsize=(12, 3), constrained_layout=True)
im = axes[0].pcolormesh(cube["lon"], cube["lat"], field, shading="auto", cmap="coolwarm", vmin=-25, vmax=25)
axes[0].set(title=f"Map · day {day}", xlabel="Longitude", ylabel="Latitude")
fig.colorbar(im, ax=axes[0], label="°C")
axes[1].plot(series); axes[1].axvline(day, color="tomato")
axes[1].set(title="Area-weighted mean", xlabel="Synthetic day", ylabel="°C")
counts, edges, _ = axes[2].hist(field.ravel(), bins=15)
axes[2].set(title="Unweighted cell distribution", xlabel="°C", ylabel="Cell count")
fig.suptitle("Original synthetic dashboard")
plt.show()
assert counts.sum() == field.size
''', "Change the selected day in all panels together. Explain why the cell histogram and area-weighted mean use different weighting conventions.", "A dashboard is meaningful when panels share a clear selection state. The gallery implements live variable, time and rendering controls for related synthetic views.", "https://matplotlib.org/stable/users/explain/axes/arranging_axes.html"),
    ("20-performance", "Browser memory and precision", "Estimate array costs; quantify float32 approximation error.", '''
cube = lab.synthetic_cube(); original = cube["temperature"]
compact = original.astype(np.float32)
error = np.max(np.abs(original - compact.astype(np.float64)))
assert compact.nbytes * 2 == original.nbytes
assert error < 5e-5
sizes = np.array([25*49*60, 180*360*365, 1800*3600*365], dtype=np.int64)
megabytes = sizes*8/1e6
fig, ax = plt.subplots(figsize=(7, 3))
ax.bar(["lesson", "1 degree / year", "0.1 degree / year"], megabytes)
ax.set_yscale("log")
ax.set(ylabel="One float64 variable (MB, log scale)", title="Estimated storage before overhead")
plt.show()
print(f"Lesson array {original.nbytes/1e6:.2f} MB; float32 error {error:.2e} K")
''', "Add ten variables and an ensemble of twenty members to the estimates. Propose a subset that fits a 100 MB working budget.", "Array storage is only part of memory use: temporary arrays, decompression, plotting and the browser add overhead. A lightweight lesson is not evidence that a full-resolution twin fits in a browser.", "https://numpy.org/doc/stable/reference/arrays.ndarray.html"),
    ("21-reproducibility", "Reproducible methods and provenance", "Test random seeds; record transformations and hash an artifact.", '''
import hashlib, json
a = lab.synthetic_cube(seed=42); b = lab.synthetic_cube(seed=42); c = lab.synthetic_cube(seed=43)
assert np.array_equal(a["temperature"], b["temperature"])
assert not np.array_equal(a["temperature"], c["temperature"])
summary = np.round(lab.global_mean(a["temperature"], a["lat"]), 6)
record = {"source": lab.PROVENANCE, "seed": 42, "method": "cosine-weighted mean; rounded to 6 decimals",
          "units": "K", "numpy_version": np.__version__, "values": summary.tolist()}
serialized = json.dumps(record, sort_keys=True).encode()
digest = hashlib.sha256(serialized).hexdigest()
print("Artifact SHA-256:", digest)
print({key: value for key, value in record.items() if key != "values"})
fig, ax = plt.subplots(figsize=(8, 3))
ax.plot(summary); ax.set(xlabel="Synthetic day", ylabel="Temperature (K)", title="Reproducible synthetic summary")
plt.show()
assert len(digest) == 64
''', "Change the seed or rounding precision and recompute the hash. Separate numerical reproducibility from byte-for-byte reproducibility.", "A hash detects changed bytes, not truth or licensing. Version and method records explain changes that a hash alone cannot; portable results should use documented tolerances.", "https://numpy.org/doc/stable/reference/random/"),
    ("22-capstone", "A transparent adaptation comparison", "Combine ensemble summaries, threshold exposure and a decision table; state limits.", '''
import pandas as pd
members = lab.ensemble(seed=21, members=40)
threshold = 16
rows = []
for label, cooling, cost in [("baseline", 0., 0.), ("scenario A", .5, 1.), ("scenario B", 1., 2.5)]:
    exposure = np.maximum(members-cooling-threshold, 0).sum(axis=1)
    rows.append({"scenario": label, "mean_degree_days": exposure.mean(),
                 "p10": np.quantile(exposure, .1), "p90": np.quantile(exposure, .9), "illustrative_cost": cost})
table = pd.DataFrame(rows).set_index("scenario")
assert np.all(np.diff(table.mean_degree_days) <= 0)
assert np.all(table.p10 <= table.p90)
fig, ax = plt.subplots(figsize=(8, 3))
ax.bar(table.index, table.mean_degree_days, color=["#557b8a", "#49a9a0", "#e4ac54"])
ax.vlines(np.arange(3), table.p10, table.p90, color="black", label="10–90% member range")
ax.set(ylabel="Exposure above 16 °C (°C·day)", title="Synthetic adaptation scenarios")
ax.legend(); plt.show()
print(table.round(2).to_string())
''', "Add a third scenario and a different threshold. Write a short recommendation that explains assumptions, uncertainty, provenance and missing impact information.", "The costs are arbitrary units and cooling is imposed uniformly. This comparison teaches transparent assumptions; it cannot select a real investment or substitute for locally validated impact models.", "https://destine.ecmwf.int/climate-digital-twin/"),
]

LESSONS += [
    ("23-dte-workflows", "Digital Twin Engine: workflow and HPC roles", "Model a dependency graph and its critical path; separate local orchestration patterns from HPC execution.", '''
tasks = {"discover": (2, []), "stage": (4, ["discover"]), "simulate": (20, ["stage"]),
         "extract": (3, ["simulate"]), "validate": (2, ["extract"]),
         "impact": (5, ["validate"]), "publish": (1, ["impact"])}
finish = {}
for name, (duration, parents) in tasks.items():
    assert all(parent in finish for parent in parents), "Tasks must be topologically ordered"
    finish[name] = max([finish[parent] for parent in parents] or [0]) + duration
assert finish["publish"] == 37
fig, ax = plt.subplots(figsize=(9, 3))
for row, (name, (duration, parents)) in enumerate(tasks.items()):
    ax.barh(name, duration, left=finish[name]-duration, color="#58a997")
ax.set(xlabel="Invented relative runtime units", title="Synthetic serial workflow; no job submitted")
plt.show()
print("Critical path:", finish["publish"], "relative units")
''', "Add a postprocessing branch that can run after extraction. Calculate when both branches finish and explain where extra workers help.", "The Digital Twin Engine connects workflows, data handling and simulation infrastructure. ECMWF develops it for use with initial twins on European supercomputing resources. The graph here only teaches dependencies; it has no scheduler, allocation, model executable or production connection.", "https://destine.ecmwf.int/digital-twin-engine/"),
    ("24-polytope", "Polytope: select a feature, not a whole cube", "Compare rectangular and trajectory-shaped selections; draft a catalog-grounded request plan.", '''
cube = lab.synthetic_cube()
track_lat = np.linspace(35, 55, 20); track_lon = np.linspace(-10, 30, 20)
values = np.array([lab.bilinear(cube["temperature"][day], cube["lat"], cube["lon"], lat, lon)
                   for day, (lat, lon) in enumerate(zip(track_lat, track_lon))])
assert values.size == 20 and np.isfinite(values).all()
print("Feature values:", values.size, "Full cube values:", cube["temperature"].size)
request_plan = {"catalog_collection": "SELECT FROM AUTHORIZED CATALOG — not a service ID",
                "feature": "trajectory", "coordinates": "longitude/latitude degrees", "units": "K",
                "time": "map actual valid times explicitly", "permission": "check before requesting"}
print(request_plan)
fig, axes = plt.subplots(1, 2, figsize=(9, 3))
axes[0].plot(track_lon, track_lat, marker=".")
axes[0].set(xlabel="Longitude", ylabel="Latitude", title="Synthetic trajectory")
axes[1].plot(values); axes[1].set(xlabel="Trajectory sample/day", ylabel="Temperature (K)")
plt.tight_layout(); plt.show()
''', "Compare the sampled trajectory with the enclosing spatial rectangle over the same days. Count transferred values for each strategy.", "Polytope provides feature-oriented extraction from multidimensional data. This interpolation exercise illustrates selection economics; it is not a Polytope client, endpoint or exact server sampling implementation. Generate actual requests from an authorized catalog and current client documentation.", "https://polytope.readthedocs.io/en/stable/"),
    ("25-earthkit-export", "Earthkit and a server-to-browser export boundary", "Design a small, explicit export contract; validate units and provenance after serialization.", '''
import json
cube = lab.synthetic_cube(nlat=5, nlon=7)
export = {"schema_version": 1, "variable": "temperature", "units": "K",
          "lat": cube["lat"].tolist(), "lon": cube["lon"].tolist(), "values": cube["temperature"][0].tolist(),
          "provenance": {"source": "original synthetic generator", "license": "CC BY 4.0",
                         "retrieved": "2026-11-15", "method": "selected day zero; native K retained"}}
wire = json.dumps(export, allow_nan=False)
validated = lab.validate_export(json.loads(wire))
assert np.array_equal(validated["values"], cube["temperature"][0])
assert len(wire.encode()) < 10000
fig, ax = plt.subplots(figsize=(6, 3))
im = ax.pcolormesh(validated["lon"], validated["lat"], validated["values"], shading="auto")
fig.colorbar(im, ax=ax, label="Temperature (K)")
ax.set(title="Synthetic JSON export after validation", xlabel="Longitude", ylabel="Latitude")
plt.show()
print("Small transfer size:", len(wire.encode()), "bytes")
''', "Add an explicit K-to-°C conversion and record it in metadata, then observe that the narrow schema rejects °C until you intentionally update the contract.", "Earthkit provides Python tools for Earth-system data, including GRIB-oriented workflows through associated native capabilities. Run authentic decoding and authorized retrieval on a suitable server or local environment, then export a small permitted subset. No Earthkit/GRIB decoding, authentication or official download runs in this browser exercise.", "https://earthkit-data.readthedocs.io/en/latest/"),
    ("26-data-lake", "Data Lake services: discovery, compute and hooks", "Connect HDA/STAC discovery concepts with a local manifest; validate an event-driven processing contract.", '''
catalog = [
    {"id": "synthetic-temperature", "variable": "temperature", "units": "K", "bbox": [-180,-84,180,84], "license": "CC BY 4.0"},
    {"id": "synthetic-rain", "variable": "precipitation", "units": "mm day-1", "bbox": [-180,-84,180,84], "license": "CC BY 4.0"}]
selected = [item for item in catalog if item["variable"] == "temperature"]
assert len(selected) == 1
events = [{"event_id": "demo-1", "item": selected[0]["id"]}, {"event_id": "demo-1", "item": selected[0]["id"]}]
seen, products = set(), []
for event in events:
    if event["event_id"] in seen: continue
    seen.add(event["event_id"])
    cube = lab.synthetic_cube()
    products.append(float(lab.global_mean(cube["temperature"][0], cube["lat"])))
assert len(products) == 1, "Duplicate delivery must not duplicate products"
fig, ax = plt.subplots(figsize=(6, 3))
ax.bar(["Received events", "Unique events", "Products"], [len(events),len(seen),len(products)])
ax.set(ylabel="Count", title="Synthetic idempotent processing pattern")
plt.show()
''', "Add a second unique event and test product count. Extend the local manifest with a retrieval timestamp and an explicit asset media type.", "The Data Lake documentation describes HDA for harmonized access and STAC discovery, plus services including Islet, Stack and Hook for connected user workflows. Consult each service's current interface and entitlement requirements. This plain Python manifest and duplicate-event check are conceptual exercises, not valid STAC records, a Hook client or cloud deployment.", "https://destine-data-lake-docs.data.destination-earth.eu/en/latest/"),
    ("27-ai-validation", "AI and ML: a time-aware baseline", "Fit a simple regression with held-out future samples; detect temporal leakage.", '''
rng = np.random.default_rng(23)
day = np.arange(120)
feature = np.sin(day/12)
target = 10 + .03*day + 2*feature + rng.normal(0, .2, len(day))
design = np.column_stack([np.ones(len(day)), day, feature])
split = 80
coef, *_ = np.linalg.lstsq(design[:split], target[:split], rcond=None)
pred = design[split:] @ coef
rmse = np.sqrt(np.mean((pred-target[split:])**2))
baseline_rmse = np.sqrt(np.mean((target[:split].mean()-target[split:])**2))
assert day[:split].max() < day[split:].min()
assert rmse < baseline_rmse
fig, ax = plt.subplots(figsize=(8, 3))
ax.plot(day, target, label="Synthetic target")
ax.plot(day[split:], pred, label="Held-out prediction")
ax.axvline(split, color="gray", linestyle="--", label="Training boundary")
ax.set(xlabel="Synthetic day", ylabel="Target (°C)", title="Original least-squares teaching model")
ax.legend(); plt.show()
print(f"Future RMSE {rmse:.3f}; training-mean baseline {baseline_rmse:.3f} °C")
''', "Remove the time feature and compare held-out error. Introduce a regime shift after day 80 and explain why training fit does not guarantee future skill.", "AI/ML tools can connect to digital-twin workflows, but validation must match the intended decision. This small least-squares model demonstrates time separation; it is not a trained DestinE AI model and makes no real forecast claim. MLOps Studio is separately described in the [official Data Lake documentation](https://destine-data-lake-docs.data.destination-earth.eu/en/latest/).", "https://destine.ecmwf.int/ai-in-destination-earth/"),
    ("28-regional-extremes", "Regional on-demand extremes and nested scales", "Compare coarse and fine sampling of a localized event; measure what a coarse grid misses.", '''
coarse = np.linspace(-100, 100, 11)
fine = np.linspace(-100, 100, 201)
def event(x): return 30*np.exp(-((x-13)/12)**2)
coarse_rain, fine_rain = event(coarse), event(fine)
interpolated = np.interp(fine, coarse, coarse_rain)
assert fine_rain.max() >= coarse_rain.max()
error = np.sqrt(np.mean((interpolated-fine_rain)**2))
assert error > 0
fig, ax = plt.subplots(figsize=(8, 3))
ax.plot(fine, fine_rain, label="Fine synthetic signal")
ax.plot(coarse, coarse_rain, "o--", label="Coarse samples")
ax.plot(fine, interpolated, label="Interpolated coarse samples")
ax.set(xlabel="Local distance (km)", ylabel="Rainfall rate (mm day⁻¹)", title="Synthetic localized event and sampling")
ax.legend(); plt.show()
print(f"Coarse interpolation error: {error:.3f} mm/day")
''', "Shift the event center onto a coarse grid point. Compare peak error and integrated rainfall; explain why a finer display cannot create missing dynamics.", "Weather-Induced Extremes DT includes global and regional on-demand capabilities described by ECMWF. Regional runs require model initialization, boundaries, configuration, compute allocations and authorized orchestration. This local resolution experiment neither downscales a real event nor submits a simulation.", "https://destine.ecmwf.int/weather-induced-extremes-digital-twin/"),
]

LESSONS += COMPONENT_LESSONS

SETUP = '''import sys
if sys.platform == "emscripten":
    import piplite
    await piplite.install(["numpy", "matplotlib", "pandas", "xarray", "ipywidgets"])
import numpy as np
import matplotlib.pyplot as plt
import earthlab as lab
plt.rcParams.update({"figure.dpi": 100, "axes.spines.top": False, "axes.spines.right": False})
print(lab.PROVENANCE)
'''

def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}

def code(text):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": dedent(text).strip().splitlines(keepends=True)}

def main():
    out = ROOT / "content"
    out.mkdir(exist_ok=True)
    manifest = []
    for index, (slug, title, objectives, experiment, exercise, interpretation, ref) in enumerate(LESSONS):
        source = f"{REPO}/blob/main/content/{slug}.ipynb"
        prev = f"[Previous]({LESSONS[index-1][0]}.ipynb) · " if index else ""
        next_link = f" · [Next]({LESSONS[index+1][0]}.ipynb)" if index+1 < len(LESSONS) else ""
        cells = [
            md(f"![Original abstract globe and synthetic weather streamlines](assets/splash.png)\n\n# {title}\n\n**Lesson {index+1:02d} · Original synthetic data · Independent educational project**"),
            md(f"## Objectives\n\n{objectives}\n\n{prev}[Notebook source]({source}){next_link}\n\n[Open this notebook in JupyterLite](https://jltobias.github.io/JupyterLite-Destination-Earth-Digital-Twin/lab/index.html?path={slug}.ipynb) — public deployment pending until verified. For a local build, open the matching filename from the Lab file browser.\n\nRun every code cell in order. The first run in JupyterLite downloads browser packages; it needs an internet connection. No account or credentials are used. The interactive visual lessons use ipywidgets, and the gallery provides additional live controls."),
            md("## Prepare the browser-sized environment\n\nThe shared `earthlab.py` helper lives beside every notebook. The same source notebook is used by the book and Lab."),
            code(SETUP), md("## Worked experiment\n\nRun this original experiment and inspect both its figure and numerical checks."), code(experiment),
            md(f"## Exercise\n\n{exercise}\n\nAdd a code cell with your modification and at least one assertion that would catch an incorrect result. Keep the original experiment as a reference."),
            md(f"## Interpretation and limits\n\n{interpretation}\n\n**Check your reasoning:** identify one result the code establishes and one conclusion the demonstration cannot establish."),
            md(f"## References and provenance\n\n- [Conceptual or software reference]({ref}) — linked for background; no text, external notebook code or data were copied.\n- [Destination Earth initiative source index](https://github.com/destination-earth/DestinE).\n- Generated arrays and equations: original project teaching material, CC BY 4.0; helper code: MIT. No authentic DestinE outputs or observational datasets are used.\n- The abstract splash was generated for this project. See the repository's [attribution record]({REPO}/blob/main/ATTRIBUTIONS.md)."),
        ]
        if slug in {"14-maps", "16-terrain", "17-globe", "18-time", "19-dashboard"}:
            interactive = '''import ipywidgets as widgets
from IPython.display import display
interactive_cube = lab.synthetic_cube(nlat=19, nlon=31)
def explore(day=0, variable="temperature", azimuth=-55):
    units = interactive_cube["units"][variable]
    field = interactive_cube[variable][day]
    bounds = (245, 300) if variable == "temperature" else (0, 8)
    fig = plt.figure(figsize=(8, 4))
'''
            if slug == "16-terrain":
                interactive += '''    ax = fig.add_subplot(projection="3d")
    xx, yy = np.meshgrid(interactive_cube["lon"], interactive_cube["lat"])
    norm = plt.Normalize(*bounds)
    ax.plot_surface(xx, yy, interactive_cube["elevation"], facecolors=plt.cm.viridis(norm(field)))
    ax.view_init(elev=28, azim=azimuth)
    ax.set(xlabel="Longitude", ylabel="Latitude", zlabel="Synthetic elevation (m)")
    fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap="viridis"), ax=ax, shrink=.6, label=units)
'''
            elif slug == "17-globe":
                interactive += '''    ax = fig.add_subplot(projection="3d")
    lo, la = np.meshgrid(interactive_cube["lon"], interactive_cube["lat"])
    xx, yy, zz = lab.globe_xyz(la, lo)
    elev_rad, azim_rad = np.deg2rad([20, azimuth])
    camera = np.array([np.cos(elev_rad)*np.cos(azim_rad), np.cos(elev_rad)*np.sin(azim_rad), np.sin(elev_rad)])
    visible = xx*camera[0] + yy*camera[1] + zz*camera[2] >= 0
    im = ax.scatter(xx[visible], yy[visible], zz[visible], c=field[visible], cmap="viridis", s=15, vmin=bounds[0], vmax=bounds[1])
    ax.set_proj_type("ortho"); ax.set(xlim=(-1,1), ylim=(-1,1), zlim=(-1,1))
    ax.view_init(elev=20, azim=azimuth); ax.set_box_aspect((1,1,1))
    fig.colorbar(im, ax=ax, shrink=.6, label=units)
'''
            elif slug == "19-dashboard":
                interactive += '''    ax = fig.add_subplot(121)
    im = ax.pcolormesh(interactive_cube["lon"], interactive_cube["lat"], field, shading="auto", vmin=bounds[0], vmax=bounds[1])
    ax.set(xlabel="Longitude", ylabel="Latitude")
    fig.colorbar(im, ax=ax, label=units)
    other = fig.add_subplot(122)
    other.plot(lab.global_mean(interactive_cube[variable], interactive_cube["lat"]))
    other.axvline(day, color="tomato"); other.set(xlabel="Synthetic day", ylabel=units)
'''
            else:
                interactive += '''    ax = fig.add_subplot()
    im = ax.pcolormesh(interactive_cube["lon"], interactive_cube["lat"], field, shading="auto", vmin=bounds[0], vmax=bounds[1])
    fig.colorbar(im, ax=ax, label=units)
    ax.set(xlabel="Longitude", ylabel="Latitude")
'''
            interactive += '''    fig.suptitle(f"Synthetic {variable}, day {day}")
    plt.tight_layout(); plt.show()
controls = widgets.interactive(explore, day=widgets.IntSlider(min=0,max=59,value=0),
                               variable=["temperature", "precipitation"], azimuth=(-180,180,5))
display(controls)
'''
            if slug not in {"16-terrain", "17-globe"}:
                interactive = interactive.replace("azimuth=(-180,180,5)", "azimuth=widgets.fixed(-55)")
            cells.insert(-2, md("## Interactive Lab experiment\n\nMove the time slider, change the variable or rotate the 3D view. This widget runs in a Python kernel in Lab; the published book preserves a static output. Explain which control changes the data and which only changes its display."))
            cells.insert(-2, code(interactive))
        nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3 (ipykernel)", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.13"}, "earthlab": {"synthetic": True, "lesson": index+1}}, "nbformat": 4, "nbformat_minor": 5}
        for n, cell in enumerate(cells): cell["id"] = f"lesson-{index+1:02d}-cell-{n:02d}"
        (out / f"{slug}.ipynb").write_text(json.dumps(nb, indent=1, ensure_ascii=False)+"\n", encoding="utf-8")
        manifest.append({"slug": slug, "title": title, "objectives": objectives, "reference": ref})
    (out / "lessons.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    print(f"Authored {len(manifest)} canonical notebooks")

if __name__ == "__main__": main()
