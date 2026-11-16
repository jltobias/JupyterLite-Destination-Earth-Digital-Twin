"""Validate required routes, packaged notebooks and static HTML references."""
import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]

class Links(HTMLParser):
    def __init__(self): super().__init__(); self.urls = []
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in {"href", "src"} and value: self.urls.append(value)

def local_target(site, page, raw, base):
    if raw.startswith("/"):
        if base:
            if raw != base and not raw.startswith(base + "/"):
                raise ValueError("root-relative URL omits the repository prefix")
            raw = raw[len(base):]
        return site / raw.lstrip("/")
    return page.parent / raw

def check(base=""):
    site = ROOT / "_site"
    required = ["index.html", "book/index.html", "lab/index.html", "lab/assets/splash.png", "files/earthlab.py", "files/assets/splash.png", "build-manifest.json"]
    required += [f"gallery/{mode}/index.html" for mode in ("map", "terrain", "globe", "dashboard", "flow", "compare")]
    required += [f"files/{p.name}" for p in (ROOT / "content").glob("*.ipynb")]
    failures = [f"Missing route: {p}" for p in required if not (site / p).is_file()]
    alias = site / "lab/assets/splash.png"
    if alias.exists() and alias.read_bytes() != (ROOT / "content/assets/splash.png").read_bytes():
        failures.append("Lab splash alias differs from the original notebook artwork")
    landing = (site / "index.html").read_text(encoding="utf-8") if (site / "index.html").exists() else ""
    config_match = re.search(r'<script id="jupyter-config-data" type="application/json">(.*?)</script>', landing, re.S)
    if config_match is None:
        failures.append("Landing page is missing JupyterLite's parent configuration block")
    else:
        try:
            if not isinstance(json.loads(config_match.group(1)), dict):
                failures.append("Landing JupyterLite configuration must be a JSON object")
        except ValueError:
            failures.append("Landing JupyterLite configuration is invalid JSON")
    html_files = [site / "index.html", *sorted((site / "gallery").rglob("*.html")), *sorted((site / "book").rglob("*.html"))]
    count = 0
    for page in html_files:
        if not page.exists(): continue
        parser = Links(); parser.feed(page.read_text(encoding="utf-8"))
        for url in parser.urls:
            parts = urlsplit(url)
            if parts.scheme or parts.netloc or not parts.path: continue
            raw = unquote(parts.path)
            try:
                target = local_target(site, page, raw, base)
            except ValueError as exc:
                failures.append(f"{page.relative_to(site)}: {exc}: {url}")
                continue
            candidates = [target, target / "index.html", target.with_suffix(".html")]
            if not any(p.exists() for p in candidates): failures.append(f"{page.relative_to(site)}: missing {url}")
            count += 1
    configured_prefix = "/JupyterLite-Destination-Earth-Digital-Twin"
    for url in re.findall(r"\]\((https://jltobias\.github\.io/[^)]+)\)", (ROOT / "README.md").read_text(encoding="utf-8")):
        parts = urlsplit(url)
        route = unquote(parts.path)
        if not route.startswith(configured_prefix + "/"):
            failures.append(f"Unexpected README deployment path: {url}")
            continue
        target = site / route[len(configured_prefix):].lstrip("/")
        if not (target.is_file() or (target / "index.html").is_file()):
            failures.append(f"README route missing from artifact: {url}")
        for notebook in parse_qs(parts.query).get("path", []):
            if not (site / "files" / notebook).is_file():
                failures.append(f"README notebook missing from artifact: {notebook}")
        count += 1
    if failures: raise AssertionError("\n".join(failures[:60]))
    print(f"PASS {len(required)} required routes and {count} local HTML references")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--base-url", default="")
    check(parser.parse_args().base_url.rstrip("/"))
