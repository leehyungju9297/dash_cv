# dash_cv

Personal CV site built with Dash.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:8050`.

## Current public pages

- `/` Home
- `/publications` Publications
- `/contact` Contact

Navigation is intentionally limited to these pages in `app.py`.

## Update points

- Main profile content: `pages/home.py`
- Publications: `pages/publications.py`
- Contact information: `pages/contact.py`
