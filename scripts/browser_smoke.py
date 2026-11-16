"""Browser-only checks against a built static site; never a substitute for native tests.

Run after build.py. Chromium comes from Playwright by default; --browser-executable
can select an existing installation. App inspection is enabled only in intercepted
test responses, never in the published configuration.
"""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import math
from pathlib import Path
import threading

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
VIEWS = ("map", "terrain", "globe", "dashboard", "flow", "compare")
UNITS = {"temperature": "°C", "precipitation": "mm day⁻¹", "wind": "m s⁻¹"}


class PrefixHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, prefix, **kwargs):
        self.prefix = prefix
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.prefix:
            if not self.path.startswith(self.prefix + "/"):
                self.send_error(404, "Outside the configured repository prefix")
                return
        super().do_GET()

    def translate_path(self, path):
        # Preserve the public request path so directory redirects retain the
        # repository prefix; strip it only when resolving the filesystem path.
        if self.prefix and path.startswith(self.prefix + "/"):
            path = path[len(self.prefix):]
        return super().translate_path(path)

    def log_message(self, *args):
        pass


def synthetic_value(lat, lon, day, variable):
    """Independent scalar expectation for the documented gallery equations."""
    phi, lam, phase = math.radians(lat), math.radians(lon), 2 * math.pi * day / 30
    u = 10 * math.cos(2 * phi) + 2 * math.sin(lam + phase)
    v = 3 * math.sin(phi) * math.cos(lam - phase)
    return {"temperature": 288 - 35 * math.sin(phi)**2 + 4 * math.cos(lam - phase) + .025 * day - 273.15,
            "precipitation": max(0, 5 * math.cos(phi)**4 * (1 + .6 * math.sin(lam + phase))),
            "wind": math.hypot(u, v), "u": u, "v": v}[variable]


def expected_stats(day, variable):
    values, weighted, weights = [], 0., 0.
    for i in range(24):
        lat = -84 + 168 * (i + .5) / 24
        for j in range(48):
            lon = -180 + 360 * (j + .5) / 48
            value, weight = synthetic_value(lat, lon, day, variable), math.cos(math.radians(lat))
            values.append(value); weighted += value * weight; weights += weight
    return {"mean": weighted / weights, "min": min(values), "max": max(values)}


def canvas_pixels(page):
    return page.locator("#visualization").evaluate("canvas => canvas.toDataURL()")


def set_day(page, day):
    page.locator("#time").fill(str(day))
    page.locator("#time").dispatch_event("input")


def check_summary(page, day, variable):
    expected = expected_stats(day, variable)
    for key, value in expected.items():
        text = page.locator("#" + key).inner_text()
        assert UNITS[variable] in text, (key, text)
        assert math.isclose(float(text.split()[0]), value, abs_tol=.0051), (key, text, value)
    assert f"day {day}" in page.locator("#summary").inner_text()
    assert UNITS[variable] in page.locator("#summary").inner_text()
    for row, lat in zip(page.locator("#sample-values tr").all(), (-60, 0, 60)):
        actual = float(row.locator("td").nth(2).inner_text().split()[0])
        assert math.isclose(actual, synthetic_value(lat, 0, day, variable), abs_tol=.00051)


def gallery_checks(browser, base, report):
    context = browser.new_context(viewport={"width": 1440, "height": 1000})
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(base + "/", wait_until="networkidle")
    assert page.locator(".hero img").evaluate("e => e.complete && e.naturalWidth > 0")
    for mode in VIEWS:
        page.goto(f"{base}/gallery/{mode}/", wait_until="networkidle")
        page.locator("details > summary").click()
        before = canvas_pixels(page)
        check_summary(page, 0, "temperature")
        set_day(page, 17)
        assert canvas_pixels(page) != before, mode + " time control did not redraw"
        check_summary(page, 17, "temperature")
        for variable in ("precipitation", "wind"):
            before = canvas_pixels(page)
            page.select_option("#variable", variable)
            assert canvas_pixels(page) != before, mode + " field control did not redraw"
            check_summary(page, 17, variable)
        before = canvas_pixels(page)
        page.select_option("#render", "points")
        assert canvas_pixels(page) != before, mode + " rendering control did not redraw"
        if mode in ("globe", "terrain"):
            before = canvas_pixels(page)
            page.locator("#rotation").fill("70")
            page.locator("#rotation").dispatch_event("input")
            assert canvas_pixels(page) != before, mode + " rotation did not redraw"
        page.locator("#play").click()
        page.wait_for_function("document.querySelector('#time').value !== '17'")
        page.locator("#play").click()
        assert page.locator("#play").get_attribute("aria-pressed") == "false"
        set_day(page, 17)
        if mode == "dashboard":
            assert page.locator("#view-values tr").count() == 60
            row = page.locator("#view-values tr").nth(17).locator("td")
            assert math.isclose(float(row.nth(1).inner_text().split()[0]), expected_stats(17, "wind")["mean"], abs_tol=.00051)
        elif mode == "compare":
            for row, lat in zip(page.locator("#view-values tr").all(), (-60, 0, 60)):
                values = row.locator("td")
                baseline = synthetic_value(lat, 0, 0, "wind")
                selected = synthetic_value(lat, 0, 17, "wind")
                for column, expected in ((2, baseline), (3, selected), (4, selected-baseline)):
                    assert math.isclose(float(values.nth(column).inner_text().split()[0]), expected, abs_tol=.00051)
        elif mode == "flow":
            for row, lat in zip(page.locator("#view-values tr").all(), (-60, 0, 60)):
                for column, component in ((2, "u"), (3, "v"), (4, "wind")):
                    actual = float(row.locator("td").nth(column).inner_text().split()[0])
                    assert math.isclose(actual, synthetic_value(lat, 0, 17, component), abs_tol=.00051)
        report.append({"check": "gallery " + mode, "status": "passed"})
        print(f"PASS gallery {mode}: numerical summaries, fields, time and rendering controls", flush=True)
    page.set_viewport_size({"width": 390, "height": 844})
    for route in ("/", *(f"/gallery/{mode}/" for mode in VIEWS)):
        page.goto(base + route, wait_until="networkidle")
        if route != "/":
            page.locator("details").evaluate("element => element.open = true")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), route
    report.append({"check": "mobile layouts including accessible tables", "status": "passed"})
    page.set_viewport_size({"width": 1440, "height": 1000})
    page.goto(base + "/book/", wait_until="networkidle")
    page.get_by_role("link", name="the system lesson", exact=True).click()
    page.get_by_role("heading", name="A digital twin is a connected system", exact=True).wait_for(state="visible")
    assert not errors, errors
    report.append({"check": "book navigation and page JavaScript", "status": "passed"})
    context.close()


def notebook_check(browser, base, stem, timeout, report):
    # A fresh context has no saved notebooks, outputs, service workers or kernel.
    context = browser.new_context(viewport={"width": 1440, "height": 1000})
    page = context.new_page()

    def inspectable_config(route):
        response = route.fetch()
        config = response.json()
        config.setdefault("jupyter-config-data", {})["exposeAppInBrowser"] = "true"
        route.fulfill(response=response, json=config)

    page.route("**/jupyter-lite.json", inspectable_config)
    page.goto(f"{base}/lab/index.html?path={stem}.ipynb", wait_until="domcontentloaded")
    page.wait_for_function("window.jupyterapp && window.jupyterapp.shell.currentWidget?.content?.model", timeout=timeout)
    page.evaluate("""() => {
      window.__smokeRun = (async () => {
        try {
          const app = window.jupyterapp;
          await app.restored;
          const panel = app.shell.currentWidget;
          await panel.context.ready;
          await panel.sessionContext.ready;
          await app.commands.execute('notebook:clear-all-cell-outputs');
          const cleared = panel.content.model.toJSON().cells.filter(c => c.cell_type === 'code');
          if (cleared.some(c => c.execution_count !== null || c.outputs.length)) throw Error('Saved outputs were not cleared');
          await app.commands.execute('notebook:run-all-cells');
          const cells = panel.content.model.toJSON().cells;
          window.__smokeResult = {
            code_cells: cells.filter(c => c.cell_type === 'code').map(c => ({count:c.execution_count,
              outputs:c.outputs.map(o => ({type:o.output_type, mime:Object.keys(o.data || {}), error:o.evalue || null}))})),
            widget_cell: cells.findIndex(c => c.cell_type === 'code' && c.source.includes('widgets.interactive')),
            kernel: panel.sessionContext.session.kernel.status
          };
        } catch (error) { window.__smokeResult = {error: String(error), stack: error.stack}; }
      })();
    }""")
    print(f"Running {stem} in a fresh Pyodide kernel", flush=True)
    page.wait_for_function("window.__smokeResult", timeout=timeout)
    result = page.evaluate("window.__smokeResult")
    assert "error" not in result, result
    cells = result["code_cells"]
    assert cells and [cell["count"] for cell in cells] == list(range(1, len(cells)+1)), result
    assert not any(output["type"] == "error" for cell in cells for output in cell["outputs"]), result
    assert any("image/png" in output["mime"] for cell in cells for output in cell["outputs"]), result
    assert result["kernel"] == "idle", result
    assert page.evaluate("fetch('assets/splash.png').then(response => response.status)") == 200
    if stem == "05-labelled-arrays":
        # Query real kernel values through the supported execute protocol, not DOM text.
        extra = page.evaluate("""async () => {
          const kernel = window.jupyterapp.shell.currentWidget.sessionContext.session.kernel;
          const messages = [];
          const future = kernel.requestExecute({code: "import json\\nprint(json.dumps({'dims': list(da.dims), 'shape': list(da.shape), 'regional_dims': list(regional.dims), 'regional_size': regional.size, 'matches': bool(np.allclose(regional.values, region.mean(('latitude', 'longitude')).values - 273.15)), 'units': da.attrs['units']}))", store_history:false});
          future.onIOPub = message => { if (message.header.msg_type === 'stream') messages.push(message.content.text); };
          const reply = await future.done;
          return {status:reply.content.status, text:messages.join('')};
        }""")
        assert extra["status"] == "ok", extra
        values = json.loads(extra["text"].strip())
        assert values == {"dims": ["day", "latitude", "longitude"], "shape": [60, 25, 49], "regional_dims": ["day"], "regional_size": 60, "matches": True, "units": "K"}, values
        result["xarray"] = values
    if stem == "14-maps":
        assert any("application/vnd.jupyter.widget-view+json" in output["mime"] for cell in cells for output in cell["outputs"]), result
        page.evaluate("async index => {await window.jupyterapp.shell.currentWidget.content.scrollToItem(index);}", result["widget_cell"])
        dropdown = page.locator(".widget-dropdown select")
        dropdown.wait_for(state="visible", timeout=30000)
        # Pyodide does not implement kernel user_expressions. Inspect the actual
        # visible widget image after bringing this virtualized cell into view.
        plot = page.locator(".widget-interact img").last
        plot.wait_for(state="visible", timeout=30000)
        before = plot.get_attribute("src")
        assert before and plot.evaluate("image => image.complete && image.naturalWidth > 0")
        dropdown.select_option(label="precipitation")
        page.wait_for_function("""previous => {
          const images = document.querySelectorAll('.widget-interact img');
          const image = images[images.length - 1];
          return image && image.complete && image.naturalWidth > 0 && image.getAttribute('src') !== previous;
        }""", arg=before, timeout=30000)
        assert "Traceback" not in page.locator(".widget-interact").inner_text()
        result["widget_plot_changed"] = True
    report.append({"check": "Pyodide " + stem, "status": "passed", "result": result})
    print(f"PASS Pyodide {stem}: {len(cells)} executed cells, figures and no errors", flush=True)
    context.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", type=Path, default=ROOT / "_site")
    parser.add_argument("--base-url", default=None, help="Defaults to build-manifest.json base_url")
    parser.add_argument("--browser-executable", help="Optional Chromium executable; otherwise Playwright's installed Chromium")
    parser.add_argument("--timeout", type=int, default=300000, help="Maximum startup/execution wait per notebook in milliseconds")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--gallery-only", action="store_true", help="Skip the Pyodide portion")
    selection.add_argument("--notebooks-only", action="store_true", help="Skip gallery and book checks")
    parser.add_argument("--notebooks", nargs="+", choices=("01-system", "05-labelled-arrays", "14-maps"),
                        default=("01-system", "05-labelled-arrays", "14-maps"))
    parser.add_argument("--report", type=Path, default=ROOT / "_executed/browser-smoke-report.json")
    args = parser.parse_args()
    manifest = json.loads((args.site / "build-manifest.json").read_text(encoding="utf-8"))
    prefix = (args.base_url if args.base_url is not None else manifest["base_url"]).rstrip("/")
    if prefix and (not prefix.startswith("/") or ".." in prefix or ":" in prefix):
        parser.error("base-url must be a root-relative repository path")
    handler = partial(PrefixHandler, prefix=prefix, directory=str(args.site.resolve()))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}{prefix}"
    report = []
    try:
        with sync_playwright() as playwright:
            options = {"headless": True}
            if args.browser_executable: options["executable_path"] = args.browser_executable
            browser = playwright.chromium.launch(**options)
            if not args.notebooks_only:
                gallery_checks(browser, base, report)
            if not args.gallery_only:
                for stem in args.notebooks:
                    notebook_check(browser, base, stem, args.timeout, report)
            browser.close()
        print(f"PASS {len(report)} browser checks (separate from native notebook execution)")
    except Exception as error:
        report.append({"status": "failed", "error": str(error)})
        raise
    finally:
        server.shutdown(); server.server_close()
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")


if __name__ == "__main__": main()
