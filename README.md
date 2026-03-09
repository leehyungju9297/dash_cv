# dash_cv

Modern Dash-based CV site.

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

## Structure

- `app.py`: shell, header, top-level routing
- `assets/custom.css`: full visual system (typography, color, layout, animations)
- `pages/home.py`: hero, experience, skills, education
- `pages/publications.py`: selected papers
- `pages/contact.py`: contact CTA cards

## Deploy (Render recommended)

Service type: **Web Service**  
Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
gunicorn app:server --workers 2 --timeout 120
```

Notes:
- Free instance spins down after idle and can be slow on first hit.
- Use paid instance if you want always-on behavior.
