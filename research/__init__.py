"""Research-only reference code for interpretation, ranking and comparison (Member 5).

This package is deliberately outside ``backend/flameguard``. Runtime ranking and
comparison belong to Member 1 and must not import this package.

Integrity rules this package enforces (master spec section 2):

- It ranks *research relevance* to a stated question. It never scores fire danger and
  never outputs a probability.
- Numerical comparison is refused unless the evidence is scientifically comparable.
- Missing values stay missing (``None``) and are listed explicitly.
- Simulation output is rejected as an input. This package must not import simulation code.
"""

from research.common import NOT_A_RISK_SCORE

__all__ = ["NOT_A_RISK_SCORE"]
