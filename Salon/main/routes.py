from flask import render_template
from . import bp
from flask import render_template, request, redirect, url_for, flash, current_app
from datetime import datetime
from .forms import ReservationForm


@bp.route("/")
def index():
    return render_template("index.html")

@bp.route("/usluge", methods=["GET", "POST"])
def usluge():
    form = ReservationForm()

    if form.validate_on_submit():
        price_map = {"classic":12, "fade":15, "buzz":10, "wash":2, "long":20}
        duration_map = {"classic":20, "fade":20, "buzz":15, "wash":0, "long":30}

        total_price = sum(price_map[s] for s in form.services.data)
        total_minutes = sum(duration_map[s] for s in form.services.data)

        doc = {
            "barber": form.barber.data,
            "services": form.services.data,  
            "date": form.day.data.strftime("%Y-%m-%d"),
            "time": form.time.data,
            "total_price": total_price,
            "total_minutes": total_minutes,
            "created_at": datetime.now()
        }
        current_app.config["RESERVATIONS"].insert_one(doc)
        flash("Rezervacija spremljena!", "success")
        return redirect(url_for("main.moja_sisanja"))

    return render_template("usluge.html", form=form)

@bp.route("/moja_sisanja")
def moja_sisanja():
    reservations = current_app.config.get("RESERVATIONS")
    if reservations is None:
        flash("Baza nije inicijalizirana (RESERVATIONS). Provjeri create_app().", "warning")
        items = []
    else:
        items = list(reservations.find().sort("created_at", -1))

    return render_template("moja_sisanja.html", items=items)


