"""
Mutation check for the regression suite.

Makes one small change at a time to the implementation (tests/ndplex_original.py
by default), runs the suite against the changed copy, and records whether
any test failed ("killed") or all passed ("survived"). A survivor is either
an equivalent change (same behaviour) or a gap in the tests.

    python tests/mutation_check.py                   # ndplex class + oeis
    python tests/mutation_check.py --scope ndplex    # just the class
    python tests/mutation_check.py --jobs 4 --json out.json

Operators: arithmetic (+ - * / % |), comparisons (< <= > >= == != is is-not),
integer constants (n -> n+1, n -> n-1), unary minus removed, and/or swapped,
if-conditions negated, string constants changed, True/False flipped, and
each statement in a function body replaced by `pass`.

Not part of the pytest run (the file name does not start with test_).
"""
import argparse
import ast
import concurrent.futures as cf
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_SRC = HERE / "ndplex_original.py"

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
    return [n for n in tree.body
            if isinstance(n, (ast.ClassDef, ast.FunctionDef)) and n.name in scope]


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


def mutants(source, scope):
    n = sum(1 for _ in _sites(ast.parse(source), scope))
    for i in range(n):
        tree = ast.parse(source)
        node, kind, variant, desc = list(_sites(tree, scope))[i]
        _apply(node, kind, variant)
        ast.fix_missing_locations(tree)
        yield i, desc, ast.unparse(tree)


def run_suite(path, timeout):
    env = dict(os.environ, NDPLEX_IMPL_PATH=str(path), PYTHONDONTWRITEBYTECODE="1")
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
    i, desc, src, tmpdir, timeout = args
    path = pathlib.Path(tmpdir) / f"mutant_{i}.py"
    path.write_text(src)
    t0 = time.time()
    status, detail = run_suite(path, timeout)
    return dict(id=i, mutation=desc, status=status, detail=detail,
                seconds=round(time.time() - t0, 1))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--src", default=str(DEFAULT_SRC))
    ap.add_argument("--scope", nargs="+", default=["ndplex", "oeis"])
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 1)
    ap.add_argument("--timeout", type=float, default=120)
    ap.add_argument("--json")
    ap.add_argument("--only", type=int, nargs="*", help="mutant ids to run")
    args = ap.parse_args()

    source = pathlib.Path(args.src).read_text()
    with tempfile.TemporaryDirectory() as tmp:
        # The unmutated (re-unparsed) source must pass, or nothing means anything.
        base = pathlib.Path(tmp) / "baseline.py"
        base.write_text(ast.unparse(ast.parse(source)))
        status, detail = run_suite(base, args.timeout)
        if status != "survived":
            sys.exit(f"baseline does not pass: {status} {detail}")
        work = [(i, d, s, tmp, args.timeout) for i, d, s in mutants(source, args.scope)
                if not args.only or i in args.only]
        print(f"{len(work)} mutants, scope {args.scope}, {args.jobs} jobs", flush=True)
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


if __name__ == "__main__":
    main()
