import copy
import sys
from pathlib import Path
import numpy as np
import pytest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "content"))
import earthlab as lab

def test_generator_reproducible_and_bounded():
    a, b = lab.synthetic_cube(), lab.synthetic_cube()
    assert np.array_equal(a["temperature"], b["temperature"])
    assert a["temperature"].shape == (60, 25, 49)
    assert np.all(a["precipitation"] >= 0)
    assert np.allclose(a["precipitation"][0], a["precipitation"][30])
    assert a["lon"][-1] < 180

def test_area_mean_constant_and_latitude_signal():
    lat = np.linspace(-80, 80, 21)
    field = np.broadcast_to(280-30*np.sin(np.deg2rad(lat))[:,None]**2, (21, 40))
    assert lab.global_mean(field, lat) > field.mean()
    assert np.isclose(lab.global_mean(np.ones((21, 40))*8, lat), 8)
    with pytest.raises(ValueError): lab.global_mean(np.ones((2, 4)), lat)

def test_mass_balance():
    rain = np.random.default_rng(5).uniform(0, 20, 100)
    storage, runoff, drainage = lab.flood_bucket(rain)
    assert np.allclose(rain, np.diff(np.r_[0, storage])+runoff+drainage)
    assert np.all((storage >= 0) & (storage <= 12))
    with pytest.raises(ValueError): lab.flood_bucket([-1, 2])

def test_interpolation_plane_and_bounds():
    lat, lon = np.array([-10.,0.,10.]), np.array([0.,10.,20.])
    x, y = np.meshgrid(lon, lat)
    assert np.isclose(lab.bilinear(3*x+2*y, lat, lon, 2, 7), 25)
    with pytest.raises(ValueError): lab.bilinear(x, lat, lon, 30, 2)

def test_globe_radius():
    x,y,z = lab.globe_xyz(np.arange(-90,91,10), np.arange(-90,91,10), radius=2)
    assert np.allclose(x*x+y*y+z*z, 4)

@pytest.fixture
def payload():
    return dict(schema_version=1, variable="temperature", units="K", lat=[20,30], lon=[10,20], values=[[280,281],[279,280]],
                provenance=dict(source="synthetic",license="CC BY 4.0",retrieved="2026-11-15",method="test"))

def test_export_roundtrip(payload):
    assert lab.validate_export(payload)["values"].shape == (2,2)

@pytest.mark.parametrize("key,value", [("units","C"),("lat",[30,20]),("lon",[10,10]),("lon",[10,180]),("values",[[280],[281]]),("values",[[280,float('nan')],[280,281]]),("provenance",{}),("schema_version",2),("values",[[20,21],[22,23]])])
def test_export_rejects_invalid_input(payload,key,value):
    payload[key] = value
    with pytest.raises(ValueError): lab.validate_export(payload)

def test_missing_file_never_synthetic_fallback():
    path = ROOT / "content" / "__nonexistent_authorized_export__.json"
    assert not path.exists()
    with pytest.raises(FileNotFoundError): lab.load_export(path)

@pytest.mark.parametrize("lat", [[], [-90, 90], [90], [float("nan"), 10]])
def test_area_weights_reject_empty_or_zero_area(lat):
    with pytest.raises(ValueError): lab.area_weights(lat)

@pytest.mark.parametrize("shape,lat", [((2, 0), [-10, 10]), ((0, 3), []), ((3, 2, 0), [-10, 10])])
def test_global_mean_rejects_empty_spatial_dimensions(shape, lat):
    with pytest.raises(ValueError): lab.global_mean(np.empty(shape), lat)

@pytest.mark.parametrize("capacity", [float("nan"), float("inf"), -1, 0, [1, 2]])
def test_bucket_rejects_invalid_capacity(capacity):
    with pytest.raises(ValueError): lab.flood_bucket([1, 2], capacity=capacity)

@pytest.mark.parametrize("dimension", [0, -1, 2.5, float("nan"), True])
@pytest.mark.parametrize("name", ["members", "days"])
def test_ensemble_requires_positive_integer_dimensions(name, dimension):
    with pytest.raises(ValueError): lab.ensemble(**{name: dimension})

@pytest.mark.parametrize("field,lat,lon,target_lat,target_lon", [
    ([[1, 2]], [0], [0, 1], 0, .5),
    ([], [], [0, 1], 0, .5),
    ([[1], [2]], [0, 1], [0], .5, 0),
    ([[1, 2], [3, 4]], [[0, 1]], [0, 1], .5, .5),
    ([[1, 2], [3, 4]], [0, float("nan")], [0, 1], .5, .5),
    ([[1, 2], [3, float("inf")]], [0, 1], [0, 1], .5, .5),
    ([[1, 2], [3, 4]], [0, 1], [0, 1], float("nan"), .5),
    ([[1, 2], [3, 4]], [0, 1], [0, 1], .5, float("inf")),
    ([[1, 2], [3, 4]], ["a", "b"], [0, 1], .5, .5),
])
def test_bilinear_rejects_malformed_grids(field, lat, lon, target_lat, target_lon):
    with pytest.raises(ValueError): lab.bilinear(field, lat, lon, target_lat, target_lon)

@pytest.mark.parametrize("version", [True, 1.0, "1", np.int64(1)])
def test_export_version_requires_exact_int(payload, version):
    payload["schema_version"] = version
    with pytest.raises(ValueError): lab.validate_export(payload)

@pytest.mark.parametrize("key,value", [("lat", [False, 30]), ("lon", [True, 20]),
    ("values", [[True, 2], [3, 4]]), ("values", np.array([[False, 2], [3, 4]], dtype=object)),
    ("lat", np.array([False, True]))])
def test_export_rejects_booleans_before_numeric_conversion(payload, key, value):
    payload.update(variable="precipitation", units="mm day-1")
    payload[key] = value
    with pytest.raises(ValueError): lab.validate_export(payload)
