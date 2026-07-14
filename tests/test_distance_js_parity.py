from __future__ import annotations

import json
import shutil
import subprocess
from itertools import product
from pathlib import Path

import pytest

from app.modules.maps.distance import segment_distance

RULER_JS = (
    Path(__file__).resolve().parent.parent
    / "app"
    / "core"
    / "static"
    / "maps"
    / "layers"
    / "ruler.js"
)

RULES = ("chebyshev", "five_ten_five", "euclidean", "manhattan")

# 0, equal magnitudes, unequal magnitudes, and negative deltas.
DELTAS = (-8, -5, -3, -1, 0, 1, 2, 3, 5, 8)

# Node ESM-import shim: pull the real segmentFeet straight out of ruler.js (no
# reimplementation here) and dump results for a (dx, dy, feet, rule) matrix as JSON.
NODE_SHIM = """
import { pathToFileURL } from "node:url";
import { readFileSync } from "node:fs";

const [, , rulerPath, matrixPath] = process.argv;
const { segmentFeet } = await import(pathToFileURL(rulerPath).href);
const matrix = JSON.parse(readFileSync(matrixPath, "utf8"));
const results = matrix.map(([dx, dy, feet, rule]) => segmentFeet(dx, dy, feet, rule));
process.stdout.write(JSON.stringify(results));
"""


def _build_matrix() -> list[tuple[int, int, int, str]]:
    matrix: list[tuple[int, int, int, str]] = []
    for feet in (5, 10):
        for rule in RULES:
            for dx, dy in product(DELTAS, DELTAS):
                matrix.append((dx, dy, feet, rule))
    return matrix


@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
def test_ruler_js_segment_feet_matches_python_across_matrix(tmp_path):
    """Runs the ACTUAL ruler.js segmentFeet() (via node) against the same input
    matrix as the canonical Python segment_distance() and asserts every value
    agrees. This is the only thing standing between ruler.js drift and a DM
    reading a wrong distance off the live ruler label."""
    matrix = _build_matrix()

    matrix_path = tmp_path / "matrix.json"
    matrix_path.write_text(json.dumps(matrix), encoding="utf-8")

    shim_path = tmp_path / "run_segment_feet.mjs"
    shim_path.write_text(NODE_SHIM, encoding="utf-8")

    proc = subprocess.run(
        ["node", str(shim_path), str(RULER_JS), str(matrix_path)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, f"node failed: {proc.stderr}"
    js_results = json.loads(proc.stdout)

    assert len(js_results) == len(matrix)

    mismatches = []
    for (dx, dy, feet, rule), js_value in zip(matrix, js_results, strict=True):
        py_value = segment_distance(dx, dy, feet, rule)
        if py_value != js_value:
            mismatches.append((dx, dy, feet, rule, py_value, js_value))

    assert not mismatches, (
        f"ruler.js segmentFeet() disagrees with the canonical Python "
        f"segment_distance() for {len(mismatches)} input(s) "
        f"(dx, dy, feet, rule, python, js): {mismatches[:10]}"
    )
