from datetime import datetime

from flask import Flask, render_template

app = Flask(__name__)

FEATURES = [
    ("Zero setup", "Everything fits in a single file plus one HTML template."),
    ("Jinja2 templates", "Insert Python data into HTML using familiar {{ }} blocks."),
    ("Reusable layout", "Keep your HTML organized with sections for header, content, and footer."),
]


@app.route("/")
def homepage():
    """Render a simple HTML page that uses dynamic data."""
    return render_template(
        "index.html",
        features=FEATURES,
        current_time=datetime.utcnow(),
    )


if __name__ == "__main__":
    app.run(debug=True)
