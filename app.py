from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def home():
    """Renders the single-page portfolio. Jinja assembles it from the
    section partials in templates/partials/ — see index.html."""
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
