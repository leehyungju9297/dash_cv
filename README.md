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
- `/projects` Projects
- `/publications` Publications
- `/contact` Contact

## Deploy (Render)

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
gunicorn app:server --workers 1 --timeout 120
```

Python version is pinned through:
- `runtime.txt`
- `render.yaml` (`PYTHON_VERSION=3.11.9`)

## Notes

- Resume download is at `/assets/Hyungju_Lee_Resume.pdf`.
- Legacy Dash experiment files were moved to `sandbox_pages/` so they are not auto-imported in production.
