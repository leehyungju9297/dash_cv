# dash_cv

Modern portfolio site built with Dash.

## Local run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:8050`.

## Public pages

- `/` Home
- `/projects` Case Studies
- `/publications` Publications
- `/contact` Contact

## GitHub Pages (Free Static Option)

A static copy of the site is in `docs/` for GitHub Pages hosting without backend cold starts.

Setup:
1. Push the current branch to GitHub.
2. Repo `Settings` -> `Pages`.
3. Source: `Deploy from a branch`.
4. Branch: `master` (or `main`) and folder: `/docs`.
5. Save and wait for publish.

Project site URL pattern:
- `https://<username>.github.io/dash_cv/`

## Deployment Scope

GitHub Pages only. No Vercel/Render deployment config is kept in this repository.

## Notes

- Resume download is at `/assets/Hyungju_Lee_Resume.pdf`.
- Canonical resume content lives in `resume/resume.json`; rebuild PDF and DOCX with `python3 resume/build_resume.py`.
- Legacy Dash experiment files were moved to `sandbox_pages/` so they are not auto-imported in production.
