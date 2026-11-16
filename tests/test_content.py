import json
from pathlib import Path
from urllib.parse import urlsplit
import re
import nbformat
ROOT = Path(__file__).resolve().parents[1]

def test_notebook_contract_and_links():
    notebooks = sorted((ROOT / "content").glob("*.ipynb"))
    assert len(notebooks) >= 32
    manifest = json.loads((ROOT / "content/lessons.json").read_text())
    assert {p.stem for p in notebooks} == {item["slug"] for item in manifest}
    for path in notebooks:
        nb = nbformat.read(path, as_version=4); nbformat.validate(nb)
        assert "assets/splash.png" in nb.cells[0].source
        source = "\n".join(c.source for c in nb.cells)
        for required in ["## Objectives", "## Exercise", "## Interpretation", "## References", "assert ", "synthetic"]:
            assert required in source, (path, required)
        assert len([c for c in nb.cells if c.cell_type == "code"]) >= 2
        for url in re.findall(r"\]\(([^)]+)\)", source):
            if not urlsplit(url).scheme:
                assert (path.parent / urlsplit(url).path).exists(), (path, url)

def test_splash_is_same_original():
    assert (ROOT/"assets/splash.png").read_bytes() == (ROOT/"content/assets/splash.png").read_bytes()

def test_coverage_in_book_configuration():
    config = (ROOT / "myst.yml").read_text(encoding="utf-8")
    for path in (ROOT / "content").glob("*.ipynb"):
        assert f"content/{path.name}" in config

def test_gallery_routes_and_local_assets():
    for view in ("map","terrain","globe","dashboard","flow","compare"):
        page = ROOT / "web/gallery" / view / "index.html"
        html = page.read_text(encoding="utf-8")
        for control in ('id="variable"','id="time"','id="render"','id="summary"'):
            assert control in html
        assert "ORIGINAL SYNTHETIC DATA" in html

def test_landing_preserves_jupyterlite_parent_config():
    # Lab fetches its parent's HTML and reads this block before jupyter-lite.json.
    html = (ROOT / "web/index.html").read_text(encoding="utf-8")
    match = re.search(r'<script id="jupyter-config-data" type="application/json">(.*?)</script>', html, re.S)
    assert match is not None
    assert isinstance(json.loads(match.group(1)), dict)
