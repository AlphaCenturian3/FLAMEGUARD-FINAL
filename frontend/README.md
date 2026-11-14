# Frontend

Owner: `feat/frontend-dashboard`. **Not started.**

Planned stack (spec §3): static HTML, CSS, and vanilla JS with no build step. The backend will serve it at `/`.

Until the backend serves real data, develop against `contracts/examples/*.json`. Those files are fixtures. They must never be shown as NASA data.

UI requirements from the spec:

- Show each value's evidence class (measured, interpretation, or illustrative simulation).
- Always display the simulation label on simulation views.
- Show missing values as missing. Never interpolate them.
- Attribute generated text to FlameGuard-SI.
- Handle HTTP 501 (`not_implemented`) from planned endpoints.
