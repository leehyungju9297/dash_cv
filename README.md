# dash_cv

Modern personal site built with Dash.

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
- `/publications` Publications
- `/contact` Contact

## Deploy (Render)

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
gunicorn app:server --workers 2 --timeout 120
```

Python version is pinned through:
- `runtime.txt`
- `render.yaml` (`PYTHON_VERSION=3.11.9`)

## Content update checklist (monthly)

1. Update headline and summary in `pages/home.py` to match current target roles.
2. Keep impact metrics factual and specific (number + context + source project).
3. Refresh newest outcomes first in Experience (recent role gets strongest bullets).
4. Keep Contact page role list broad (not company-specific).
5. Validate on mobile width and check for overflow/layout breaks.
