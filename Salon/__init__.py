from flask import Flask, render_template
from flask_bootstrap import Bootstrap5
from pymongo import MongoClient
import gridfs
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager, UserMixin, current_user
from bson import ObjectId
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import os
from flask_login import UserMixin
from flask import current_app
from dotenv import load_dotenv




limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"] 
)

mail = Mail()

def create_app():
    load_dotenv()   # <-- ovo učita .env
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

    login_manager.init_app(app)

    limiter.init_app(app)

    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS") == "True"
    app.config["MAIL_USE_SSL"] = os.getenv("MAIL_USE_SSL") == "True"
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")

    mail.init_app(app)

    from .main import bp as main_bp
    app.register_blueprint(main_bp)


    @app.errorhandler(403)
    def err403(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def err404(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def err500(e):
        return render_template("errors/500.html"), 500
    
    @app.errorhandler(429)
    def too_many_requests(e):
        return render_template("errors/429.html"), 429
    
    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "no-referrer-when-downgrade"
        return response


    return app

login_manager = LoginManager()
login_manager.login_view = "main.login"  # ako ti je login ruta main.login




class User(UserMixin):
    def __init__(self, data):
        self.data = data
        # Flask-Login koristi ovo svojstvo za identifikaciju usera
        self.id = str(data["_id"])

    @property
    def full_name(self):
        return self.data.get("full_name") or self.data.get("name") or ""

    @property
    def email(self):
        return self.data.get("email") or ""

    @property
    def email_verified(self):
        return self.data.get("email_verified", False)

    @property
    def role(self):
        return self.data.get("role", "user")



@login_manager.user_loader
def load_user(user_id):
    """Funkcija koju Flask-Login koristi da iz sessiona učita korisnika iz baze."""
    users = current_app.config.get("USERS")
    if users is None:
        return None
    try:
        doc = users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None
    if not doc:
        return None
    return User(doc)
