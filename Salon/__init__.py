from flask import Flask
from flask_bootstrap import Bootstrap5
from pymongo import MongoClient

def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config["SECRET_KEY"] = "tajni_kljuc"

    Bootstrap5(app)

    client = MongoClient("mongodb://localhost:27017/")
    db = client["frizerski_salon"]
    app.config["DB"] = db
    app.config["RESERVATIONS"] = db["reservations"]

    from .main import bp as main_bp
    app.register_blueprint(main_bp)

    return app