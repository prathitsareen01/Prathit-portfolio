# Hosted portfolio demo

`render.yaml` defines a free Python web service. It builds the app and regenerates the synthetic XLSX, then starts one Uvicorn worker on the host's assigned port. Python is pinned to 3.14.8, the current Render default at preparation time.

## Deployment settings
- Runtime: Python.
- Build: `pip install -r requirements-runtime.txt && python demo/generate_demo.py`.
- Start: `python -m uvicorn financeos.main:app --host 0.0.0.0 --port $PORT --workers 1`.
- Health check: `/api/health` (only returns an availability flag; no data/config).
- `FINANCEOS_MODE=hosted`.
- `FINANCEOS_AUTH_USERNAME=demo`.
- `FINANCEOS_AUTH_PASSWORD`: generate a random secret of at least 20 characters. The blueprint uses Render's `generateValue: true`; a direct service creation must set an equivalent secret.
- `FINANCEOS_EPHEMERAL=true`.
- `FINANCEOS_DB=/tmp/financeos/financeos.db`.
- Render supplies `RENDER_EXTERNAL_HOSTNAME`; the app accepts that exact hostname. For another host/custom domain, set `FINANCEOS_ALLOWED_HOSTS` to a comma-separated exact hostname list, without protocols, paths, ports or wildcards.
- Leave OpenAI credentials unset for the complete offline investigation workflow.

Do not store the demo password or API keys in GitHub, build commands, Dockerfiles or URLs. Read the generated password from Render's environment settings when sharing access. Anyone with the password shares all demo uploads and analysis. Use synthetic data only.

If the project is stored inside a repository subfolder, set the service's root directory to that folder. The deployment branch's root-level Blueprint includes this setting.

## Persistence
The free service's filesystem is temporary: uploads and saved runs reset on a restart/redeploy or host spin-down. The original synthetic data reloads automatically when storage is empty. The app prominently discloses this. For durable storage, provision a paid persistent disk, set `FINANCEOS_DB` inside its mount path, and set `FINANCEOS_EPHEMERAL=false`. Do not enable a paid plan without the owner's approval.

## Auth behavior
Hosted startup fails if the password is absent/short or a public domain is not configured. Visitors sign in on the app's /login page. It issues a signed eight-hour session cookie with Secure, HttpOnly and SameSite=Lax protections. App pages, static files, API documentation, source rows and report downloads remain protected. The login page and minimal health endpoint are public. Wrong passwords are rate-limited. Rotating the configured password invalidates existing sessions. Basic headers remain supported for API clients without triggering browser password popups. This is shared demonstration access, not business-user identity management.

## After the host reports a successful build
1. Confirm the public URL returns a login challenge.
2. Authenticate and check that the synthetic dashboard loads.
3. Run the EBITDA investigation and downside scenario.
4. Validate the dirty CSV and a valid synthetic Excel upload.
5. Download the management report and evidence workbook.
6. Share the final URL and demo credentials with the intended reviewer.

Prepared configuration does not establish that a service exists or is live. Use the hosting provider's returned service/deployment URL and status as the authority.

References: https://render.com/docs/blueprint-spec, https://render.com/docs/free, https://render.com/docs/python-version.
