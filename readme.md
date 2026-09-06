# Ayushman Singh — Portfolio

Personal developer portfolio built with plain HTML, CSS and JavaScript — no framework, no build step.

## Live sections

- Hero — intro, photo, quick stats
- About — background and current focus
- Skills — frontend, backend, database, AI & data, tools, UI/UX
- Projects — WattWise, Private Photo Vault, GenAI Project, Personal Portfolio
- Certificates & recognition
- Contact

## Folder structure

```
ayushman-portfolio/
├── index.html
├── css/
│   ├── style.css
│   └── responsive.css
├── js/
│   └── script.js
├── assets/
│   └── images/
│       └── profile.jpg
└── README.md
```

## Run it locally

Just open `index.html` in a browser. For live-reload while editing, use the
"Live Server" extension in VS Code and click "Go Live".

## Deploy it for free

**GitHub Pages**
1. Push this folder to a GitHub repo.
2. Repo → Settings → Pages → set source to the `main` branch, root folder.
3. Your site goes live at `https://<username>.github.io/<repo-name>/`.

**Netlify / Vercel**
1. Drag and drop this folder into Netlify's dashboard, or import the repo.
2. It deploys automatically — no build command needed.

## Editing

- Text/content → `index.html`
- Colors/layout → `css/style.css` (colors are CSS variables at the top — edit `:root` to re-theme)
- Mobile layout → `css/responsive.css`
- Interactivity (nav toggle, count-up numbers) → `js/script.js`
- Photo → replace `assets/images/profile.jpg` with a new image of the same name