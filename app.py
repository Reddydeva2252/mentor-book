from dotenv import load_dotenv
load_dotenv()

from flask import Flask, redirect
from config import Config
from models import db

app = Flask(__name__)
app.secret_key = "5bja7@5gaqa"
app.config.from_object(Config)

db.init_app(app)

# Register blueprints
from mentor import mentor

app.register_blueprint(mentor, url_prefix="/mentor")


@app.route("/")
def index():
    return redirect("/mentor/login")


if __name__ == "__main__":
    app.run(debug=True)
