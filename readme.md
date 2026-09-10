# Ayushman Singh — Portfolio (Flask)

Personal developer portfolio, served with Flask so each section lives in its
own template file instead of one giant HTML file.

The page is still a **single page** — same smooth-scroll navigation, same
look and behaviour as before. Only the code organisation changed.

## Folder structure

```
flask-portfolio/
├── app.py                     # Flask app — one route, renders index.html
├── requirements.txt
├── templates/
│   ├── index.html             # shell that includes every partial below
│   └── partials/
│       ├── background.html    # site-wide animated background layer
│       ├── cursor.html        # custom cursor
│       ├── cmdk.html          # command palette (Ctrl/Cmd+K)
│       ├── topbar.html        # logo, profile menu, "Say hello"
│       ├── bottomnav.html     # section links (About/Skills/…)
│       ├── hero.html
│       ├── about.html
│       ├── skills.html
│       ├── projects.html
│       ├── certificates.html
│       ├── terminal.html
│       └── contact.html
│       └── footer.html
├── static/
│   ├── css/
│   │   ├── style.css
│   │   └── responsive.css
│   ├── js/
│   │   └── script.js
│   └── images/
│       ├── profile.jpg
│       └── certificates/
│           ├── gold-certificate.png
│           ├── course-completion-certificate.png
│           ├── google-certificate.png
│           └── nexus-participation.jpg
```

Flask's convention: templates (`.html` files Flask renders) live in
`templates/`, and files served as-is (CSS, JS, images) live in `static/`.
That's why the CSS/JS/image links in the partials use
`{{ url_for('static', filename='...') }}` instead of plain relative paths.

## Run it locally

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

## Editing

- Want to change a section's content? Open its file directly —
  `templates/partials/skills.html`, `templates/partials/projects.html`,
  etc. — instead of hunting through one long file.
- Adding a brand-new section: create `templates/partials/your-section.html`,
  then add `{% include 'partials/your-section.html' %}` in
  `templates/index.html` wherever you want it to appear.
- Colors/layout → `static/css/style.css` (all colors are CSS variables at
  the top — including the 3-theme system, unchanged from before).
- Interactivity (cursor, sound, terminal, command palette, themes) →
  `static/js/script.js`.
- Certificate/profile images → replace the files in `static/images/` with
  the same filenames.

## Deploying

Flask apps need a server that can run Python (unlike the old static-file
version, this can't go on GitHub Pages). Free options: **Render**,
**Railway**, or **PythonAnywhere**. All of them detect `requirements.txt`
and `app.py` automatically — just point them at the repo.
