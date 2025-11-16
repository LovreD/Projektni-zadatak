from flask import Flask, render_template
from flask_bootstrap import Bootstrap5
from pymongo import MongoClient
import gridfs
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"] 
)


def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config["SECRET_KEY"] = "tajni_kljuc"


    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax" 
    app.config["SESSION_COOKIE_SECURE"] = False


    Bootstrap5(app)

    client = MongoClient("mongodb://localhost:27017/")
    db = client["frizerski_salon"]
    app.config["DB"] = db
    app.config["RESERVATIONS"] = db["reservations"]

    app.config["USERS"] = db["users"]
    app.config["FS"] = gridfs.GridFS(db)

    limiter.init_app(app)

    from .main import bp as main_bp
    app.register_blueprint(main_bp)



    @app.errorhandler(429)
    def too_many_requests(e):
        return render_template("429.html"), 429
    
    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "no-referrer-when-downgrade"
        return response


    return app
