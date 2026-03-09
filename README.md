# dash_cv

Static portfolio site for Vercel deployment (no Python app boot required).

## Routes

- `/` Home
- `/projects/` Projects
- `/publications/` Publications
- `/contact/` Contact

## Local preview (static)

```bash
python3 -m http.server 4173
```

Open `http://127.0.0.1:4173`.

## Deploy to Vercel

1. Push this repo to GitHub.
2. In Vercel, import the repo.
3. Framework preset: `Other` (no build command needed).
4. Deploy.

`vercel.json` is already configured for:
- trailing slashes (`/projects/`, `/contact/`, etc.)
- long-term caching on `/assets/*`
- revalidation for HTML routes

## Notes

- Resume download is at `/assets/Hyungju_Lee_Resume.pdf`.
- Legacy Dash experiment files were moved to `sandbox_pages/` and are not used by the static site.
