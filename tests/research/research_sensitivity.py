"""Weight-sensitivity assessment for the research-relevance ranking (Member 1, D-01 condition 3).

Pure functions over a criterion-score matrix, so the method is independent of how each
criterion is computed. Used by ``test_research_sensitivity.py`` and by
``docs/research/member5/WEIGHT_SENSITIVITY.md``.

Method:

1. For each criterion ``c`` and each shift ``d`` in (+0.05, -0.05), set
   ``w_c' = w_c + d`` and leave the others unchanged.
2. Renormalize so the weights sum to 1: ``w_i'' = w_i' / (1 + d)``. Every other weight
   is scaled by the same factor, so their ratios are preserved.
3. Recompute every score as ``sum(w_i'' * s_i)`` and re-rank (descending score, ties
   broken by investigation id, the same rule as ``rank_investigations``).
4. The ranking is **weight-sensitive** if the ordered top 3 differs from the baseline in
   any of the 8 scenarios. Also reported: the largest rank change of any investigation,
   and near-ties (score gap below 1e-9).

Print the tables with ``python tests/research/research_sensitivity.py``.
"""

import json
import sys
from pathlib import Path

DELTA = 0.05
CRITERIA = ("purpose_relevance", "condition_match", "source_traceability", "data_completeness")
TIE_EPS = 1e-9
FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "research"
    / "synthetic_criterion_scores.json"
)


def perturbed_weights(weights: dict[str, float], criterion: str, delta: float) -> dict[str, float]:
    raw = {c: w + (delta if c == criterion else 0.0) for c, w in weights.items()}
    if raw[criterion] < 0:
        raise ValueError(f"{criterion} weight would become negative")
    total = sum(raw.values())
    return {c: w / total for c, w in raw.items()}


def scores(matrix: dict[str, dict[str, float]], weights: dict[str, float]) -> dict[str, float]:
    return {inv: sum(weights[c] * s[c] for c in CRITERIA) for inv, s in matrix.items()}


def ranking(score_map: dict[str, float]) -> list[str]:
    return [inv for inv, _ in sorted(score_map.items(), key=lambda kv: (-kv[1], kv[0]))]


def near_ties(score_map: dict[str, float]) -> list[tuple[str, str]]:
    order = ranking(score_map)
    return [
        (a, b)
        for a, b in zip(order, order[1:], strict=False)
        if abs(score_map[a] - score_map[b]) < TIE_EPS
    ]


def assess(matrix: dict[str, dict[str, float]], weights: dict[str, float]) -> dict:
    base_scores = scores(matrix, weights)
    base = ranking(base_scores)
    base_pos = {inv: i for i, inv in enumerate(base, 1)}
    scenarios = []
    for c in CRITERIA:
        for d in (DELTA, -DELTA):
            w = perturbed_weights(weights, c, d)
            s = scores(matrix, w)
            order = ranking(s)
            shift = max(
                abs({inv: i for i, inv in enumerate(order, 1)}[inv] - base_pos[inv])
                for inv in order
            )
            scenarios.append(
                {
                    "criterion": c,
                    "delta": d,
                    "weights": w,
                    "scores": s,
                    "order": order,
                    "top3_changed": order[:3] != base[:3],
                    "max_rank_shift": shift,
                    "near_ties": near_ties(s),
                }
            )
    return {
        "baseline_scores": base_scores,
        "baseline_order": base,
        "contributions": {
            inv: {c: weights[c] * matrix[inv][c] for c in CRITERIA} for inv in matrix
        },
        "scenarios": scenarios,
        "weight_sensitive": any(s["top3_changed"] for s in scenarios),
        "baseline_near_ties": near_ties(base_scores),
    }


def load_fixture(path: Path = FIXTURE) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _f(x: float) -> str:
    return f"{x:.4f}"


def markdown(name: str, matrix: dict, weights: dict) -> str:
    r = assess(matrix, weights)
    lines = [f"#### Scenario `{name}` (synthetic)", ""]
    lines += ["Baseline criterion scores (synthetic inputs) and weighted contributions:", ""]
    lines += [
        "| Investigation | "
        + " | ".join(f"{c} (score → contribution)" for c in CRITERIA)
        + " | Total |",
        "|---|" + "---|" * len(CRITERIA) + "---|",
    ]
    for inv in r["baseline_order"]:
        cells = [f"{_f(matrix[inv][c])} → {_f(r['contributions'][inv][c])}" for c in CRITERIA]
        lines.append(f"| `{inv}` | " + " | ".join(cells) + f" | {_f(r['baseline_scores'][inv])} |")
    lines += ["", f"Baseline order: {', '.join(f'`{i}`' for i in r['baseline_order'])}", ""]
    lines += [
        "| Shift | Effective weights (P / C / T / D) | Order | Top 3 changed | Max rank shift |",
        "|---|---|---|---|---|",
    ]
    for s in r["scenarios"]:
        w = " / ".join(_f(s["weights"][c]) for c in CRITERIA)
        lines.append(
            f"| {s['criterion']} {s['delta']:+.2f} | {w} | {', '.join(s['order'])} | "
            f"{'**yes**' if s['top3_changed'] else 'no'} | {s['max_rank_shift']} |"
        )
    verdict = "**weight-sensitive**" if r["weight_sensitive"] else "**stable**"
    lines += ["", f"Verdict: {verdict} under ±{DELTA} shifts."]
    return "\n".join(lines)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # the tables contain non-ASCII characters
    fx = load_fixture()
    for name, scenario in fx["scenarios"].items():
        print(markdown(name, scenario["criterion_scores"], fx["weights"]))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
