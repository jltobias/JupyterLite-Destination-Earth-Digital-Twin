import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]

def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


@pytest.mark.parametrize("url", ["/book/index.html", "/styles.css", "/repository/book/", "/"])
def test_prefixed_site_rejects_unprefixed_root_urls(url):
    checker = module("check_site")
    with pytest.raises(ValueError, match="repository prefix"):
        checker.local_target(Path("site"), Path("site/book/page.html"), url, "/repo")


def test_prefixed_site_accepts_relative_and_correctly_prefixed_urls():
    checker = module("check_site")
    site, page = Path("site"), Path("site/book/page.html")
    assert checker.local_target(site, page, "/repo/book/index.html", "/repo") == site / "book/index.html"
    assert checker.local_target(site, page, "/repo", "/repo") == site
    assert checker.local_target(site, page, "../styles.css", "/repo") == page.parent / "../styles.css"
    assert checker.local_target(site, page, "/book/index.html", "") == site / "book/index.html"


def test_unknown_selection_rejects_entire_request_before_execution():
    runner = module("execute_notebooks")
    notebooks = [Path("01-system.ipynb"), Path("14-maps.ipynb")]
    with pytest.raises(ValueError, match="unknown-name"):
        runner.select_notebooks(notebooks, ["01-system", "unknown-name"])
    assert runner.select_notebooks(notebooks, ["14-maps"]) == [notebooks[1]]
