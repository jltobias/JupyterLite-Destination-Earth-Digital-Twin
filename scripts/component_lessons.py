"""Original process exercises that orient readers to ECMWF's ML components.

These deliberately small equations are not implementations of the official models.
"""

COMPONENT_LESSONS = [
    ("29-land", "Land processes: snow storage and melt", "Partition precipitation; track snow storage; close a water budget.", '''
rng = np.random.default_rng(29)
day = np.arange(120)
temperature = -8 + 15*np.sin(np.pi*day/119)
precipitation = rng.gamma(1.5, 2, len(day))
snowfall = np.where(temperature < 0, precipitation, 0)
rain = precipitation - snowfall
snow = np.zeros(len(day)+1)
melt = np.zeros(len(day))
for i in range(len(day)):
    available = snow[i] + snowfall[i]
    # A chosen teaching coefficient: 3 mm per day per positive degree C.
    melt[i] = min(available, 3*max(temperature[i], 0))
    snow[i+1] = available - melt[i]
liquid = rain + melt
assert np.all(snow >= 0)
assert np.allclose(precipitation, liquid + np.diff(snow))
assert np.isclose(precipitation.sum(), liquid.sum()+snow[-1]-snow[0])
fig, axes = plt.subplots(2, 1, figsize=(9, 5), constrained_layout=True)
axes[0].plot(day, temperature, color="tomato")
axes[0].axhline(0, color="gray", linestyle="--")
axes[0].set(ylabel="Temperature (°C)", title="Original synthetic snow experiment")
axes[1].plot(np.arange(len(snow)), snow, label="Snow water equivalent (mm)")
axes[1].plot(day, liquid, label="Liquid release (mm per daily interval)")
axes[1].set(xlabel="Synthetic day", ylabel="Water equivalent (mm)")
axes[1].legend(); plt.show()
print(f"Input {precipitation.sum():.2f} mm; liquid {liquid.sum():.2f} mm; final snow {snow[-1]:.2f} mm")
''', "Change the melt coefficient and the temperature sequence. Check the budget again, then compare the timing of liquid release with total water input.", "ECMWF's land ML component addresses land-surface processes. This original degree-day bucket illustrates one storage mechanism only: it omits soil, vegetation, radiation, sublimation and refreezing. Liquid release is not routed river discharge. The model is not aiLand or a trained ML emulator. Lesson 09 supplies a separate hydrological storage exercise, and lesson 27 introduces held-out ML validation.", "https://destine.ecmwf.int/ml-earth-system-components/"),
    ("30-waves", "Waves: forcing, response time and memory", "Drive a response model with wind; distinguish an equilibrium target from a delayed state.", '''
hour = np.arange(0, 240, 6)
wind = 5 + 10*np.exp(-((hour-90)/30)**2)
# Invented coefficient 0.02 s²/m maps wind squared to a target height in m.
# It is chosen for this exercise, not fitted to observations or a wave model.
target = .02*wind**2
dt_hours, response_hours = 6., 18.
fraction = dt_hours/response_hours
height = np.zeros(len(hour)+1)
height[0] = target[0]
for i in range(len(hour)):
    height[i+1] = height[i] + fraction*(target[i]-height[i])
assert 0 < fraction <= 1
assert np.all(height >= 0) and height.max() <= target.max()
assert np.allclose(np.diff(height), fraction*(target-height[:-1]))
constant_response = np.zeros(41)
for i in range(40):
    constant_response[i+1] = constant_response[i]+fraction*(2-constant_response[i])
analytic = 2*(1-(1-fraction)**np.arange(41))
assert np.allclose(constant_response, analytic)
assert abs(2-constant_response[-1]) < abs(2-constant_response[0])
fig, axes = plt.subplots(2, 1, figsize=(9, 5), constrained_layout=True)
axes[0].plot(hour, wind, color="#557b8a")
axes[0].set(ylabel="Wind speed (m s⁻¹)", title="Original synthetic forcing and wave-height response")
axes[1].plot(hour, target, "--", label="Invented equilibrium target")
axes[1].plot(np.r_[hour, hour[-1]+6], height, label="Delayed response")
axes[1].set(xlabel="Synthetic hour", ylabel="Height (m)")
axes[1].legend(); plt.show()
print(f"Wind maximum at {hour[np.argmax(wind)]} h; height maximum at {6*np.argmax(height)} h")
''', "Try response times of 6, 18 and 48 hours. Compare the peak and delay. Explain why the condition dt/response_time ≤ 1 matters for this update.", "ECMWF's wave ML component connects atmospheric forcing with wave dynamics. This scalar relaxation equation only illustrates memory and forcing: it has no spectrum, propagation, fetch, bathymetry or wave-current interaction. Its coefficients are invented, and its height is not a validated significant-wave-height forecast. It neither runs the official AI wave model nor retrieves AIFS output.", "https://destine.ecmwf.int/ml-earth-system-components/"),
    ("31-sea-ice", "Sea ice: bounded fractions and seasonal response", "Evolve a bounded concentration; verify its discrete budget; handle masked regions explicitly.", '''
day = np.arange(365)
# Dimensionless invented thermal driver: positive means a melt tendency.
driver = np.sin(2*np.pi*day/365)
freeze_rate = .04*np.maximum(-driver, 0)
melt_rate = .06*np.maximum(driver, 0)
concentration = np.zeros(len(day)+1)
concentration[0] = .8
formation, loss = np.zeros(len(day)), np.zeros(len(day))
for i in range(len(day)):
    formation[i] = freeze_rate[i]*(1-concentration[i])
    loss[i] = melt_rate[i]*concentration[i]
    concentration[i+1] = concentration[i]+formation[i]-loss[i]
assert np.all((concentration >= 0) & (concentration <= 1))
assert np.allclose(np.diff(concentration), formation-loss)
# A missing land cell is not a zero-ice ocean cell.
ocean_mask = np.array([True, True, False])
field = np.where(ocean_mask, [.4, .8, 0.], np.nan)
assert np.isclose(np.nanmean(field), .6)
assert np.nanmean(field) != np.nan_to_num(field).mean()
fig, axes = plt.subplots(2, 1, figsize=(9, 5), constrained_layout=True)
axes[0].plot(day, driver, color="#557b8a")
axes[0].axhline(0, color="gray", linestyle="--")
axes[0].set(ylabel="Driver (dimensionless)", title="Original synthetic sea-ice fraction experiment")
axes[1].plot(np.arange(len(concentration)), concentration)
axes[1].set(xlabel="Synthetic day", ylabel="Ice-covered fraction", ylim=(0, 1))
plt.show()
print(f"Fraction range {concentration.min():.3f}–{concentration.max():.3f}; masked ocean mean {np.nanmean(field):.2f}")
''', "Change the forcing phase and initial concentration. Preserve the fraction bounds, then explain why masked land must remain distinct from open water.", "ECMWF's sea-ice ML component studies changing sea-ice and surface-ocean conditions under atmospheric forcing. This original one-cell recurrence is only a bounded-state exercise. It omits ice thickness, transport, salinity, thermodynamics and coupling, and uses no real forcing, reanalysis or trained parameters. Its dimensionless driver is not a physical freezing-point rule.", "https://destine.ecmwf.int/ml-earth-system-components/"),
    ("32-ocean", "Ocean layers: heat exchange and conservation", "Couple two heat reservoirs; account for surface forcing; test energy conservation.", '''
day = np.arange(120)
dt = 86400.  # seconds per daily interval
heat_capacity = 4e6  # chosen volumetric heat capacity, J m⁻³ K⁻¹
upper_capacity, lower_capacity = heat_capacity*20, heat_capacity*80
exchange = 5.  # chosen exchange coefficient, W m⁻² K⁻¹
surface_flux = 20*np.sin(2*np.pi*day/60)  # original forcing, W m⁻²
upper, lower = np.zeros(len(day)+1), np.zeros(len(day)+1)
upper[0], lower[0] = 15., 8.
for i in range(len(day)):
    transfer = exchange*(upper[i]-lower[i])
    upper[i+1] = upper[i] + dt*(surface_flux[i]-transfer)/upper_capacity
    lower[i+1] = lower[i] + dt*transfer/lower_capacity
change = upper_capacity*np.diff(upper) + lower_capacity*np.diff(lower)
assert np.allclose(change, dt*surface_flux, rtol=1e-9, atol=1e-6)
assert dt*exchange*(1/upper_capacity+1/lower_capacity) < 1
energy_anomaly = upper_capacity*(upper-upper[0]) + lower_capacity*(lower-lower[0])
assert np.allclose(energy_anomaly, np.r_[0, np.cumsum(dt*surface_flux)], atol=2e-6)
fig, axes = plt.subplots(2, 1, figsize=(9, 5), constrained_layout=True)
axes[0].plot(np.arange(len(upper)), upper, label="Upper 20 m")
axes[0].plot(np.arange(len(lower)), lower, label="Lower 80 m")
axes[0].set(ylabel="Temperature (°C)", title="Original synthetic two-layer heat budget")
axes[0].legend()
axes[1].plot(np.arange(len(energy_anomaly)), energy_anomaly/1e6)
axes[1].set(xlabel="Synthetic day", ylabel="Energy anomaly (MJ m⁻²)")
plt.show()
print(f"Largest daily energy-budget residual: {np.max(np.abs(change-dt*surface_flux)):.2e} J m⁻²")
''', "Double the upper-layer depth and compare response amplitude. Change the exchange coefficient while checking both energy conservation and time-step stability.", "ECMWF's ocean ML component targets evolving ocean fields through depth, including temperature, salinity, currents and sea-surface-height anomalies. This original two-reservoir model illustrates heat exchange only. It has no circulation, salinity, sea-level dynamics, assimilation or trained ML model. Chosen parameters are teaching assumptions; the curves cannot be interpreted as ocean projections.", "https://destine.ecmwf.int/ml-earth-system-components/"),
]
