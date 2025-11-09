from flask import render_template
from . import bp

@bp.route("/")
def index():
    return render_template("index.html")

@bp.route("/usluge")
def usluge():
    return render_template("usluge.html")
