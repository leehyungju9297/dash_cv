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
gunicorn app:server --workers 2 --timeout 120
```

Python version is pinned through:
- `runtime.txt`
- `render.yaml` (`PYTHON_VERSION=3.11.9`)

## Content update checklist

### Monthly
1. Update summary and headline in `pages/home.py` to reflect target roles.
2. Keep impact metrics factual (`number + context + source`).
3. Keep skills honest with level separation: `Strong (Production)` vs `Working Knowledge`.
4. Check mobile layout and interaction (no overflow, no clipped cards).

### Quarterly
1. Refresh `pages/projects.py` with the newest 1-2 real outcomes.
2. Reorder projects so the strongest/recent one appears first.
3. Replace weaker impact cards with newer evidence when available.
