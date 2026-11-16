"""Execute each canonical notebook in a fresh kernel and retain its book outputs."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
import time
import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]

def select_notebooks(notebooks, requested):
    if requested is None:
        return notebooks
    unknown = set(requested) - {path.stem for path in notebooks}
    if unknown:
        raise ValueError("Unknown notebook stems: " + ", ".join(sorted(unknown)))
    return [path for path in notebooks if path.stem in requested]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="+", help="Notebook stems to execute (default: all)")
    parser.add_argument("--output-dir", type=Path, help="Optional output directory instead of canonical files")
    parser.add_argument("--timeout", type=int, default=30, help="Per-cell native execution deadline in seconds")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("timeout must be positive")
    notebooks = sorted((ROOT / "content").glob("*.ipynb"))
    try:
        notebooks = select_notebooks(notebooks, args.only)
    except ValueError as exc:
        parser.error(str(exc))
    if not notebooks: raise SystemExit("No notebooks selected")
    if sys.platform == "win32":
        # ZeroMQ needs add_reader; the Windows Proactor loop otherwise relies on
        # a selector helper thread that can stall across repeated kernel runs.
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    os.environ.setdefault("MPLBACKEND", "module://matplotlib_inline.backend_inline")
    report = []
    for path in notebooks:
        started = time.monotonic()
        print(f"RUN {path.name}", flush=True)
        notebook = nbformat.read(path, as_version=4)
        client = NotebookClient(notebook, timeout=args.timeout, raise_on_iopub_timeout=True, kernel_name="python3", resources={"metadata": {"path": str(ROOT / "content")}})
        client.execute()
        if not any("image/png" in output.get("data", {}) for cell in notebook.cells if cell.cell_type == "code" for output in cell.get("outputs", [])):
            raise AssertionError(f"No rendered PNG figure in {path.name}")
        destination = args.output_dir / path.name if args.output_dir else path
        destination.parent.mkdir(parents=True, exist_ok=True)
        nbformat.write(notebook, destination)
        result = {"notebook": path.name, "seconds": round(time.monotonic()-started, 2), "status": "passed"}
        report.append(result)
        print(f"PASS {path.name} ({result['seconds']}s)", flush=True)
    output = ROOT / "_executed"
    output.mkdir(exist_ok=True)
    report_name = "execution-selected-report.json" if args.only else "execution-report.json"
    (output / report_name).write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(f"Executed {len(report)} notebooks with independent kernels")

if __name__ == "__main__": main()
