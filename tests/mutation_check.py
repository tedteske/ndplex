"""
Mutation check for the regression suite.

Makes one small change at a time to the package's source (src/ndplex/_core.py
and src/ndplex/_oeis.py by default), runs the suite against a copy of the
package containing the change, and records whether any test failed
("killed") or all passed ("survived"). A survivor is either an equivalent
change (same behaviour) or a gap in the tests.

    python tests/mutation_check.py                       # the whole package
    python tests/mutation_check.py --src src/ndplex/_oeis.py
    python tests/mutation_check.py --scope ndplex        # just the class
    python tests/mutation_check.py --jobs 4 --json out.json
    python tests/mutation_check.py --expect tests/mutation_equivalent.txt

With --expect, the run fails (exit 1) unless the mutants that survive are
exactly those listed in the file: the ones argued equivalent in the phase
notes. Each is identified by file, the original source line and the change,
not by line number, so the list survives edits elsewhere in the file. The
manually triggered `checks` workflow runs it this way.

Run it with the Python that has the package's test dependencies installed.
Each mutant is a full copy of src/ndplex in a temporary directory, passed to
the suite through NDPLEX_IMPL_PATH (see tests/_impl.py).

Operators: arithmetic (+ - * / % | &), comparisons (< <= > >= == != is
is-not in not-in), integer constants (n -> n+1, n -> n-1), unary minus
removed, and/or swapped, if/while conditions negated, string constants
changed, True/False flipped, and each statement in a function body replaced
by `pass`.

Phase 1 ran this on tests/ndplex_original.py (the notebook's code); that
mode ended when the suite moved to the package in Phase 2.

Not part of the pytest run (the file name does not start with test_).
"""
import argparse
import ast
import concurrent.futures as cf
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
PACKAGE = HERE.parent / "src" / "ndplex"
DEFAULT_SRC = [PACKAGE / "_core.py", PACKAGE / "_oeis.py"]

BINOP_SWAPS = {ast.Add: [ast.Sub], ast.Sub: [ast.Add], ast.Mult: [ast.Div],
               ast.Div: [ast.Mult], ast.Mod: [ast.FloorDiv],
               ast.FloorDiv: [ast.Div], ast.BitOr: [ast.BitAnd],
               ast.BitAnd: [ast.BitOr], ast.Pow: [ast.Mult]}
CMP_SWAPS = {ast.Lt: [ast.LtE], ast.LtE: [ast.Lt], ast.Gt: [ast.GtE],
             ast.GtE: [ast.Gt], ast.Eq: [ast.NotEq], ast.NotEq: [ast.Eq],
             ast.Is: [ast.IsNot], ast.IsNot: [ast.Is], ast.In: [ast.NotIn],
             ast.NotIn: [ast.In]}


def _is_docstring(stmt):
    return (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)
            and isinstance(stmt.value.value, str))


def _scope_nodes(tree, scope):
    """Top-level classes and functions named in scope (all if scope is None)."""
    return [n for n in tree.body
            if isinstance(n, (ast.ClassDef, ast.FunctionDef))
            and (scope is None or n.name in scope)]


def _sites(tree, scope):
    """Yield (node, kind, variant, description) in a deterministic order."""
    docstrings = set()
    for top in _scope_nodes(tree, scope):
        for n in ast.walk(top):
            for field in ("body", "orelse"):
                body = getattr(n, field, None)
                for s in body if isinstance(body, list) else []:
                    if _is_docstring(s):
                        docstrings.add(id(s.value))
    for top in _scope_nodes(tree, scope):
        for n in ast.walk(top):
            line = getattr(n, "lineno", None)
            if isinstance(n, ast.BinOp) and type(n.op) in BINOP_SWAPS:
                for new in BINOP_SWAPS[type(n.op)]:
                    yield n, "binop", new, f"L{line}: {type(n.op).__name__} -> {new.__name__}"
            elif isinstance(n, ast.AugAssign) and type(n.op) in BINOP_SWAPS:
                for new in BINOP_SWAPS[type(n.op)]:
                    yield n, "binop", new, f"L{line}: {type(n.op).__name__}= -> {new.__name__}="
            elif isinstance(n, ast.Compare):
                for k, op in enumerate(n.ops):
                    for new in CMP_SWAPS.get(type(op), []):
                        yield n, "cmp", (k, new), f"L{line}: {type(op).__name__} -> {new.__name__}"
            elif isinstance(n, ast.Constant) and id(n) not in docstrings:
                v = n.value
                if isinstance(v, bool):
                    yield n, "const", (not v), f"L{line}: {v} -> {not v}"
                elif isinstance(v, int):
                    yield n, "const", v + 1, f"L{line}: {v} -> {v + 1}"
                    yield n, "const", v - 1, f"L{line}: {v} -> {v - 1}"
                elif isinstance(v, (str, bytes)):
                    new = v + (b"X" if isinstance(v, bytes) else "X")
                    yield n, "const", new, f"L{line}: {v!r} -> {new!r}"
            elif isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
                yield n, "unary", None, f"L{line}: remove unary minus"
            elif isinstance(n, ast.BoolOp):
                new = ast.Or if isinstance(n.op, ast.And) else ast.And
                yield n, "boolop", new, f"L{line}: {type(n.op).__name__} -> {new.__name__}"
            if isinstance(n, (ast.If, ast.While)):
                yield n, "negate", None, f"L{line}: negate {type(n).__name__.lower()} condition"
            if isinstance(n, (ast.FunctionDef, ast.For, ast.While, ast.If, ast.With, ast.Try)):
                for field in ("body", "orelse"):
                    body = getattr(n, field, None) or []
                    for k, s in enumerate(body):
                        if _is_docstring(s) or isinstance(s, (ast.FunctionDef, ast.Pass)):
                            continue
                        yield n, "delete", (field, k), f"L{s.lineno}: delete statement `{ast.unparse(s).splitlines()[0][:60]}`"


def _apply(node, kind, variant):
    if kind == "binop":
        node.op = variant()
    elif kind == "cmp":
        k, new = variant
        node.ops[k] = new()
    elif kind == "const":
        node.value = variant
    elif kind == "unary":
        node.op = ast.UAdd()
    elif kind == "boolop":
        node.op = variant()
    elif kind == "negate":
        node.test = ast.UnaryOp(op=ast.Not(), operand=node.test)
    elif kind == "delete":
        field, k = variant
        getattr(node, field)[k] = ast.Pass()


def _stable_id(filename, lines, desc):
    """file | original source line | change, without the line number."""
    head, _, change = desc.partition(": ")
    line = lines[int(head[1:]) - 1].strip()
    return f"{filename} | {line} | {change}"


def _read_expected(path):
    """Stable ids, one per line; blank lines and # comments are ignored."""
    ids = []
    for raw in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        if raw.strip() and not raw.lstrip().startswith("#"):
            ids.append(raw.strip())
    return ids


def _compare_with_expected(results, path):
    """0 if the survivors are exactly the expected ones, else 1 (reported)."""
    expected = sorted(_read_expected(path))
    survived = sorted(r["stable_id"] for r in results if r["status"] == "survived")
    other = [r for r in results if r["status"] not in ("killed", "survived")]
    unexpected = list(survived)
    missing = []
    for e in expected:
        if e in unexpected:
            unexpected.remove(e)
        else:
            missing.append(e)
    for e in unexpected:
        print("UNEXPECTED SURVIVOR (a gap in the tests, or a new equivalent "
              "mutant to argue and list):", e)
    for e in missing:
        print("LISTED BUT NOT SURVIVING (killed now, or the code changed; "
              "update the list):", e)
    for r in other:
        print(f"{r['status'].upper()}:", r["stable_id"], r["detail"])
    ok = not (unexpected or missing or other)
    print(f"expected survivors: {len(expected)}; survived: {len(survived)}; "
          + ("matches the list" if ok else "DOES NOT match the list"))
    return 0 if ok else 1


def mutants(source, scope):
    n = sum(1 for _ in _sites(ast.parse(source), scope))
    for i in range(n):
        tree = ast.parse(source)
        node, kind, variant, desc = list(_sites(tree, scope))[i]
        _apply(node, kind, variant)
        ast.fix_missing_locations(tree)
        yield i, desc, ast.unparse(tree)


def _package_copy(root, filename, source):
    """A copy of the package under root/ndplex with one file replaced."""
    dest = pathlib.Path(root) / "ndplex"
    shutil.copytree(PACKAGE, dest, ignore=shutil.ignore_patterns("__pycache__"))
    (dest / filename).write_text(source, encoding="utf-8")
    return pathlib.Path(root)


def run_suite(root, timeout):
    env = dict(os.environ, NDPLEX_IMPL_PATH=str(root), PYTHONDONTWRITEBYTECODE="1")
    cmd = [sys.executable, "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider",
           "--no-header", str(HERE)]
    try:
        r = subprocess.run(cmd, env=env, capture_output=True, text=True,
                           timeout=timeout, cwd=HERE.parent)
    except subprocess.TimeoutExpired:
        return "timeout", ""
    if r.returncode == 0:
        return "survived", ""
    failed = [l.split(" ")[1] for l in r.stdout.splitlines() if l.startswith("FAILED ")]
    if r.returncode == 1:
        return "killed", failed[0] if failed else ""
    return "error", (r.stdout + r.stderr).strip().splitlines()[-1:]  # collection error etc.


def _one(args):
    key, filename, desc, src, tmpdir, timeout, stable = args
    root = _package_copy(pathlib.Path(tmpdir) / key, filename, src)
    t0 = time.time()
    status, detail = run_suite(root, timeout)
    shutil.rmtree(root, ignore_errors=True)
    return dict(id=key, mutation=f"{filename} {desc}", stable_id=stable,
                status=status, detail=detail, seconds=round(time.time() - t0, 1))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--src", nargs="+", default=[str(p) for p in DEFAULT_SRC],
                    help="files of src/ndplex to mutate")
    ap.add_argument("--scope", nargs="+", default=None,
                    help="top-level classes/functions to mutate (default: all)")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 1)
    ap.add_argument("--timeout", type=float, default=120)
    ap.add_argument("--json")
    ap.add_argument("--expect", help="file listing the expected (equivalent) "
                                     "survivors by stable id; fail on any difference")
    ap.add_argument("--only", nargs="*", help="mutant ids to run, e.g. _core.py:12")
    args = ap.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        work = []
        for src in args.src:
            path = pathlib.Path(src).resolve()
            if path.parent != PACKAGE.resolve():
                sys.exit(f"{src} is not a file of {PACKAGE}")
            source = path.read_text(encoding="utf-8")
            # The unmutated (re-unparsed) source must pass, or nothing means anything.
            base = _package_copy(pathlib.Path(tmp) / f"baseline_{path.stem}",
                                 path.name, ast.unparse(ast.parse(source)))
            status, detail = run_suite(base, args.timeout)
            if status != "survived":
                sys.exit(f"baseline for {path.name} does not pass: {status} {detail}")
            lines = source.splitlines()
            for i, d, s in mutants(source, args.scope):
                key = f"{path.name}:{i}"
                if not args.only or key in args.only:
                    work.append((key, path.name, d, s, tmp, args.timeout,
                                 _stable_id(path.name, lines, d)))
        print(f"{len(work)} mutants, scope {args.scope or 'all'}, {args.jobs} jobs",
              flush=True)
        results = []
        with cf.ProcessPoolExecutor(args.jobs) as ex:
            for r in ex.map(_one, work):
                results.append(r)
                if r["status"] != "killed":
                    print(f"  [{r['id']}] {r['status'].upper()}: {r['mutation']} {r['detail'] or ''}",
                          flush=True)
    counts = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print("summary:", counts)
    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(results, indent=1))
    if args.expect:
        sys.exit(_compare_with_expected(results, args.expect))


if __name__ == "__main__":
    main()
