from flask import Flask, render_template
import xp_engine
import github_sync

app = Flask(__name__)

xp_engine.init_db()
xp_engine.seed_initial_xp()


@app.context_processor
def inject_dev_progress():
    """Makes {{ dev_progress }} available in every template automatically —
    real Level/XP/Title computed server-side, never client-editable.
    Syncs GitHub activity first (this is a no-op most of the time —
    see SYNC_INTERVAL_SECONDS in github_sync.py)."""
    github_sync.sync_github_xp()
    return {'dev_progress': xp_engine.get_progress()}

# label shown in the sections menu / page title for each route
SECTIONS = [
    {'slug': 'about', 'label': 'About'},
    {'slug': 'skills', 'label': 'Skills'},
    {'slug': 'projects', 'label': 'Projects'},
    {'slug': 'certificates', 'label': 'Certificates'},
    {'slug': 'github', 'label': 'GitHub Activity'},
    {'slug': 'contact', 'label': 'Contact'},
]

@app.route('/')
def home():
    """Landing page — hero only. Other sections live on their own pages,
    reachable from the sections icon in the top bar."""
    return render_template('index.html', sections=SECTIONS)


@app.route('/about')
def about():
    return render_template('section.html', section='about', section_label='About', sections=SECTIONS)


@app.route('/skills')
def skills():
    return render_template('section.html', section='skills', section_label='Skills', sections=SECTIONS)


@app.route('/projects')
def projects():
    return render_template('section.html', section='projects', section_label='Projects', sections=SECTIONS)


@app.route('/certificates')
def certificates():
    return render_template('section.html', section='certificates', section_label='Certificates', sections=SECTIONS)

@app.route('/github')
def github():
    return render_template('section.html', section='github', section_label='GitHub Activity', sections=SECTIONS)
@app.route('/contact')
def contact():
    return render_template('section.html', section='contact', section_label='Contact', sections=SECTIONS)


if __name__ == '__main__':
    app.run(debug=True, port=5001)
