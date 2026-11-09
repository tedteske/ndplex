"""Compare notebooks/ndplex_examples.ipynb with the original's saved outputs.

Runs on demand, not under pytest (it needs nbclient, matplotlib, seaborn and
pandas, and executes the whole notebook).

    python tests/notebook_check.py                 # execute, then compare
    python tests/notebook_check.py --executed RUN.ipynb   # compare a notebook
                                                   # already run, e.g. in Colab

Each carried-over cell of the examples notebook records its position in
ndplex_array.ipynb in metadata["ndplex"]["original_cell"]. For every such code
cell, the check compares:
  - text outputs (stdout and execute results), exactly;
  - the number of figures.
It also lists every cell that raised, and every cell that wrote to stderr
(warnings), and checks the fixes in the plotting-helper cell directly
(check_helpers). Cells marked metadata["ndplex"]["network"] (the oeis lookups) are
reported separately: their output depends on oeis.org on the day, so they are
not counted as failures; links are compared with http:// read as https://.

EXPECTED lists the cells whose output is meant to differ from the original,
with the reason. Exit status is 1 if anything else differs or any cell raises.
"""
import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "ndplex_array.ipynb"
EXAMPLES = ROOT / "notebooks" / "ndplex_examples.ipynb"

# Original cell -> why its printed output is meant to differ.
EXPECTED = {
    233: "primes computed with primesfrom2to instead of downloaded; prints a check line",
    276: "N8: nearest prime searched below 2 * max; node (9, 9) is 14, was 16",
}

# Cells whose stderr output is expected, with the reason.
EXPECTED_STDERR = {
    136: "int64 overflow on purpose (the divisor-5 puzzle): one RuntimeWarning",
}


def _text(outputs):
    """Text the cell printed or returned, figures counted separately."""
    parts, figures = [], 0
    for o in outputs:
        t = o.get("output_type")
        if t == "stream" and o.get("name") == "stdout":
            parts.append("".join(o["text"]))
        elif t in ("execute_result", "display_data"):
            data = o.get("data", {})
            if "image/png" in data:
                figures += 1
            elif "text/plain" in data:
                parts.append("".join(data["text/plain"]) + "\n")
    return "".join(parts), figures


def _stderr(outputs):
    return "".join("".join(o["text"]) for o in outputs
                   if o.get("output_type") == "stream" and o.get("name") == "stderr")


def _errors(outputs):
    return [f'{o["ename"]}: {o["evalue"]}' for o in outputs
            if o.get("output_type") == "error"]


def _normalise_links(text):
    return re.sub(r"http://oeis\.org/", "https://oeis.org/", text)


def check_helpers(notebook):
    """Check the fixes in the notebook's plotting-helper cell directly.

    Runs the cell's code with matplotlib's Agg backend and returns a list of
    problems (empty if every check passes):
      - diag_as_hist(normed=True) runs (legend_handles, F7) and colours the
        first legend handle black;
      - more than six data sets work, with the colours cycling;
      - the normal curve equals the normal pdf (checked against the formula
        and that it integrates like a pdf, using math.erf);
      - plot_ndplex leaves the global font alone (F1), uses a serif font in
        its own figure, and draws negative values (N5) but not zeros.
    """
    import math

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from ndplex import ndplex

    cell = next(c for c in notebook["cells"]
                if c["cell_type"] == "code" and "def plot_ndplex" in "".join(c["source"]))
    ns = {}
    exec("".join(cell["source"]), ns)
    problems = []
    figures = []
    show = plt.show
    plt.show = lambda *a, **k: figures.append(plt.gcf())
    try:
        # diag_as_hist, normed, eight data sets (colours cycle past six).
        ys = [ndplex(n, dtype=float).diag(loc=(n - 1, 0), move=(-1, 1))
              for n in range(5, 13)]
        try:
            ns["diag_as_hist"](ys, labels=[str(n) for n in range(5, 13)], normed=True)
        except Exception as e:  # noqa: BLE001
            problems.append(f"diag_as_hist(normed=True), 8 data sets: {e!r}")
        else:
            ax = figures[-1].axes[0]
            leg = ax.get_legend()
            if tuple(leg.legend_handles[0].get_facecolor()[:3]) != (0.0, 0.0, 0.0):
                problems.append("diag_as_hist: first legend handle is not black")
            patches = [p for p in ax.patches]
            colours = {matplotlib.colors.to_hex(p.get_facecolor()) for p in patches}
            if len(colours) != 6:
                problems.append(f"diag_as_hist: {len(colours)} bar colours, expected 6 cycling")
            # Normal curve of data set 0 against the closed form.
            y0 = np.asarray(ys[0])
            x0 = np.arange(len(y0))
            mu = np.average(x0, weights=y0)
            sd = np.average((x0 - mu) ** 2, weights=y0) ** 0.5
            line = ax.get_lines()[0]
            xs, fs = line.get_xdata(), line.get_ydata()
            want = [math.exp(-((x - mu) / sd) ** 2 / 2) / (sd * math.sqrt(2 * math.pi))
                    for x in xs]
            if not np.allclose(fs, want, rtol=1e-12, atol=0):
                problems.append("diag_as_hist: normal curve differs from the normal pdf")
            if not math.isclose(float(np.trapezoid(fs, xs)) if hasattr(np, "trapezoid")
                                else float(np.trapz(fs, xs)),
                                math.erf((xs[-1] - mu) / (sd * math.sqrt(2))) / 2
                                - math.erf((xs[0] - mu) / (sd * math.sqrt(2))) / 2,
                                rel_tol=1e-3):
                problems.append("diag_as_hist: normal curve does not integrate like a pdf")
        plt.close("all")

        # plot_ndplex: global font untouched, serif inside, negatives drawn.
        font_before = list(plt.rcParams["font.family"])
        c = np.arange(6)
        a = ndplex(6, edges=(c, -c))
        ns["plot_ndplex"](a, move=(0, 1), loc=1)
        fig = figures[-1]
        if list(plt.rcParams["font.family"]) != font_before:
            problems.append("plot_ndplex changed the global font.family")
        texts = [t for t in fig.axes[0].texts]
        drawn = sorted(int(t.get_text()) for t in texts)
        want = sorted(int(v) for v in np.asarray(a).ravel() if v != 0)
        if drawn != want:
            problems.append(f"plot_ndplex drew {len(drawn)} nodes, expected the "
                            f"{len(want)} non-zero ones (negative values included)")
        if texts and "serif" not in texts[0].get_fontfamily()[0]:
            problems.append("plot_ndplex: node labels are not serif")
        ns["plot_ndplex"](ndplex(5), as_tri="center")
        if len(figures[-1].axes[0].texts) != 15:
            problems.append("plot_ndplex(as_tri='center') did not draw the 15 triangle nodes")
    finally:
        plt.show = show
        plt.close("all")
    return problems


def execute(path, timeout=600):
    import nbformat
    from nbclient import NotebookClient

    nb = nbformat.read(path, as_version=4)
    NotebookClient(nb, timeout=timeout, kernel_name="python3",
                   allow_errors=True,
                   resources={"metadata": {"path": str(path.parent)}}).execute()
    return json.loads(nbformat.writes(nb))


def compare(executed, original):
    orig_cells = original["cells"]
    ok, problems, network, stderr_cells, expected_seen = 0, [], [], [], []
    for k, cell in enumerate(executed["cells"]):
        if cell["cell_type"] != "code":
            continue
        meta = cell.get("metadata", {}).get("ndplex", {})
        outputs = cell.get("outputs", [])
        label = (f"cell {k} (original {meta['original_cell']})"
                 if "original_cell" in meta else f"cell {k} (new)")

        for err in _errors(outputs):
            problems.append(f"{label}: raised {err}")
        err_text = _stderr(outputs)
        if err_text.strip():
            lines = err_text.strip().splitlines()
            warning = next((ln for ln in lines if "Warning" in ln), lines[-1])
            stderr_cells.append((label, meta.get("original_cell"), warning[:200]))

        if "original_cell" not in meta:
            continue
        i = meta["original_cell"]
        new_text, new_figs = _text(outputs)
        old_text, old_figs = _text(orig_cells[i].get("outputs", []))

        if meta.get("network"):
            same = _normalise_links(old_text) == _normalise_links(new_text)
            network.append((label, same, new_text))
            continue
        if new_figs != old_figs:
            problems.append(f"{label}: {new_figs} figures, original {old_figs}")
        if new_text != old_text:
            if i in EXPECTED:
                expected_seen.append((label, EXPECTED[i], old_text, new_text))
            else:
                problems.append(f"{label}: text differs\n--- original\n{old_text}"
                                f"--- examples\n{new_text}")
                continue
        elif i in EXPECTED:
            problems.append(f"{label}: expected a difference ({EXPECTED[i]}), "
                            "but the output matches the original")
        if new_figs == old_figs:
            ok += 1

    for label, i, last in stderr_cells:
        if i not in EXPECTED_STDERR:
            problems.append(f"{label}: unexpected stderr: {last}")
    seen = {i for _, i, _ in stderr_cells}
    for i, why in EXPECTED_STDERR.items():
        if i not in seen:
            problems.append(f"original cell {i}: expected stderr ({why}), none")
    return ok, problems, network, stderr_cells, expected_seen


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--executed", type=pathlib.Path,
                    help="compare this already-executed notebook instead of running")
    ap.add_argument("--save", type=pathlib.Path,
                    help="write the executed notebook here")
    args = ap.parse_args(argv)

    original = json.loads(ORIGINAL.read_text(encoding="utf-8"))
    if args.executed:
        executed = json.loads(args.executed.read_text(encoding="utf-8"))
    else:
        executed = execute(EXAMPLES)
        if args.save:
            args.save.write_text(json.dumps(executed, indent=1), encoding="utf-8")

    ok, problems, network, stderr_cells, expected_seen = compare(executed, original)
    helper_problems = check_helpers(executed)
    problems += [f"helpers: {p}" for p in helper_problems]

    print(f"{ok} carried-over code cells match the original's saved output.")
    print(f"Plotting helpers: {'all checks pass' if not helper_problems else 'FAILED'}.")
    print(f"\nExpected differences ({len(expected_seen)}):")
    for label, why, old, new in expected_seen:
        print(f"- {label}: {why}")
    print(f"\nCells writing to stderr ({len(stderr_cells)}):")
    for label, i, last in stderr_cells:
        tag = "expected" if i in EXPECTED_STDERR else "UNEXPECTED"
        print(f"- {label} [{tag}]: {last}")
    print(f"\nNetwork cells ({len(network)}), not counted as failures:")
    for label, same, text in network:
        first = next((ln for ln in text.splitlines() if ln.startswith("row 0")), "")
        print(f"- {label}: {'same as original' if same else 'differs'}; {first[:100]}")
    print(f"\nProblems ({len(problems)}):")
    for p in problems:
        print(f"- {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
