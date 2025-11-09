from flask import Flask
from flask_bootstrap import Bootstrap5

def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config["SECRET_KEY"] = "tajni_kljuc"

    Bootstrap5(app)

    from .main import bp as main_bp
    app.register_blueprint(main_bp)

    return app