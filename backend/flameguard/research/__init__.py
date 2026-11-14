"""Research interpretation, relevance ranking and Moon/Mars insight cards (Member 5).

Status: draft, pending CP1 (contract v0.2.0) and scientific review by Member 1.
Nothing in this package is wired into the API yet; ``app.py`` is unchanged.

Integrity rules this package enforces (master spec section 2):

- It ranks *research relevance* to a stated question. It never scores fire danger and
  never outputs a probability.
- Numerical comparison is refused unless the evidence is scientifically comparable.
- Missing values stay missing (``None``) and are listed explicitly.
- Simulation output is rejected as an input. This package must not import simulation code.
"""

from flameguard.research.common import NOT_A_RISK_SCORE

__all__ = ["NOT_A_RISK_SCORE"]
