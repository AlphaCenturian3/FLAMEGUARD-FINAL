# Owner checklist: FlameGuard-SI public staging on Render

This is a staging **development preview**. It is not production and not scientifically validated. It
serves only the evidence the B1 loader accepts from `data/manifest.json`, which is none today.
Compare, rankings, the assistant and simulations answer HTTP 501.

## Before you start

- [ ] PR #40's checks are green on the commit you will deploy, including **Docker preview**.
      That check builds the image, starts it on `PORT=10000`, checks the endpoints, the image
      contents and the health check, and runs the real-browser site check against it.
- [ ] Note the commit SHA you deploy. Every deploy is checked against one commit.
- [ ] A repository owner (admin on `AlphaCenturian3/FLAMEGUARD-FINAL`) does the steps below.
      Render needs GitHub access to the repository.

## Create the service (once)

1. Sign in at https://dashboard.render.com with GitHub. Give the Render GitHub app access to
   **only** `AlphaCenturian3/FLAMEGUARD-FINAL`.
2. **New > Blueprint**, then select the repository and the branch **`integration/website-preview`**.
   Render reads `render.yaml`.
3. Confirm that the settings Render shows match these:

   | Setting | Value |
   |---|---|
   | Service name | `flameguard-si-preview` (gives `https://flameguard-si-preview.onrender.com` if free) |
   | Type / runtime | Web service / Docker, `./Dockerfile`, context = repository root |
   | Branch | `integration/website-preview` |
   | Plan | Free (0.1 CPU, 512 MB; sleeps when idle) |
   | Region | Oregon (cannot be changed later) |
   | Health check path | `/api/investigations` |
   | Auto-deploy | **Off** (`autoDeployTrigger: "off"`) |
   | Environment variables | `FLAMEGUARD_AI_API_KEY` empty. **Add no other variable and no secret.** `PORT` is set by Render |

4. **Apply** the Blueprint. Render builds the image and deploys it.

## Validate the deploy (every deploy)

Replace `$URL` with the address Render shows.

- [ ] `$URL/api/health` → 200 `{"status":"ok","service":"flameguard-si","contract_version":"0.2.2"}`
- [ ] `$URL/api/investigations` → 200 `{"contract_version":"0.2.2","items":[],"total":0}`
- [ ] `$URL/api/findings` → 200, `"total":0`
- [ ] `$URL/api/compare?quantity=burn_time` and `$URL/api/rankings` → 501 `not_implemented`
- [ ] `$URL/` shows **Development preview.** at the top and "No investigations available" or equivalent
      honest empty text, with **no** fixture banner
- [ ] `$URL/?fixtures=1` shows **FIXTURE DATA. NOT NASA DATA.** on every page
- [ ] `$URL/tests/index.html` and `$URL/tools/site_check.py` → 404
- [ ] Real-browser check (any computer with Chrome and Python 3.11+):

      python frontend/tools/site_check.py https://<service>.onrender.com/ --out-dir site-shots

  Expect 0 failed. With no registered evidence, 1 check is skipped (the excluded-number check).
- [ ] In Render **Events**, the deployed commit equals the SHA you noted.

Free instances sleep after inactivity. The first request after a sleep can take about a minute, so
open `/api/health` once before running the browser check.

## Deploy a newer commit

Auto-deploy is off. After the new commit's checks are green, use **Manual Deploy > Deploy latest
commit** and repeat the validation above.

## Roll back

1. Render dashboard, then the service, then **Deploys** (Events). Find the last deploy that passed validation.
2. **Rollback**, then confirm. Render redeploys that deploy's **existing build artifact**, with no rebuild.
3. Repeat the validation above against the rolled-back deploy.
4. A dashboard rollback **turns auto-deploy off** (it is already off here). Leave it off.

Render keeps a limited number of build artifacts (it depends on the plan). If the good deploy's
artifact is gone, use **Manual Deploy > Deploy a specific commit** with that SHA instead.

## Take the site down

Service **Settings > Suspend** stops serving at once. **Delete** removes the service and its URL.

## Never do this on staging

- Do not add an AI key or any secret.
- Do not register NASA evidence, or point the service at a branch that does, without the
  registration approvals.
- Do not remove the Development preview notice or the fixture banner.
- Do not call this deployment production, or a source of fire-safety guidance.
- Do not turn auto-deploy on for a branch that is not reviewed.
