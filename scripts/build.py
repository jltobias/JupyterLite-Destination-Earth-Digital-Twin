"""Build Jupyter Book 2 and JupyterLite into one repository-subpath-safe site."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def run(args, env=None, cwd=ROOT):
    print("+ " + " ".join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), cwd=cwd, env=env, check=True)

def clean_local(name):
    path = (ROOT / name).resolve()
    if path.parent != ROOT.resolve() or name not in {"_site", "_lite"}:
        raise ValueError("Refusing to clean an unrecognized build directory")
    if path.exists(): shutil.rmtree(path)
    path.mkdir()
    return path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="", help="Hosting path, e.g. /JupyterLite-Destination-Earth-Digital-Twin")
    parser.add_argument("--execute", action="store_true", help="Execute all notebooks before building")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    if base and (not base.startswith("/") or ":" in base or ".." in base):
        raise SystemExit("base-url must be a root-relative path without '..'")
    env = os.environ.copy()
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    env["PYTHONUTF8"] = "1"
    if args.execute: run([sys.executable, "scripts/execute_notebooks.py"], env)
    run([sys.executable, "scripts/create_gallery.py"], env)
    site = clean_local("_site")
    stage = clean_local("_lite")
    shutil.copytree(ROOT / "content", stage / "content", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy2(ROOT / "jupyter-lite.json", stage / "jupyter-lite.json")
    run([sys.executable, "-m", "jupyter", "lite", "build", "--lite-dir", stage,
         "--contents", "content", "--output-dir", site, "--no-sourcemaps"], env, cwd=stage)
    bookenv = {**env, "BASE_URL": base + "/book"}
    run([sys.executable, "-m", "jupyter_book", "build", "--html", "--strict"], bookenv)
    html = ROOT / "_build" / "html"
    if not (html / "index.html").is_file(): raise SystemExit("Jupyter Book did not produce _build/html/index.html")
    shutil.copytree(html, site / "book", dirs_exist_ok=True)
    shutil.copytree(ROOT / "web", site, dirs_exist_ok=True)
    shutil.copytree(ROOT / "assets", site / "assets", dirs_exist_ok=True)
    # Lite markdown resolves notebook image URLs relative to its /lab/ app.
    # Keep the portable notebook path and provide the same asset at that URL.
    shutil.copytree(ROOT / "content" / "assets", site / "lab" / "assets", dirs_exist_ok=True)
    for name in ("README.md", "ATTRIBUTIONS.md", "CITATION.cff", "LICENSE"):
        shutil.copy2(ROOT / name, site / name)
    (site / ".nojekyll").touch()
    manifest = {"base_url": base, "book": "book/index.html", "lab": "lab/index.html", "synthetic": True,
                "notebooks": [p.name for p in sorted((ROOT / "content").glob("*.ipynb"))]}
    (site / "build-manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    run([sys.executable, "scripts/check_site.py", "--base-url", base], env)
    print(f"Built {site}; serve over HTTP, not file://")

if __name__ == "__main__": main()
