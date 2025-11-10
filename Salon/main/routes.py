from datetime import datetime, date
from flask import render_template, request, redirect, url_for, flash, current_app
from . import bp

# --- Početna ---
@bp.route("/")
def index():
    return render_template("index.html")


# --- Podaci za usluge ---
FRIZERI = ["Marija", "Lovre", "Gabrijel", "Ivan"]
USLUGE = [
    ("Klasično šišanje", 20, 12),
    ("Fade šišanje", 20, 15),
    ("Buzz cut", 15, 10),
    ("Pranje kose", 0, 2),            # dodatno
    ("Šišanje duge kose", 30, 20),
]

def generate_timeslots():
    """Termini svakih 30 min od 09:00 do 16:30"""
    slots = []
    for h in range(9, 17):            # 09..16
        slots.append(f"{h:02d}:00")
        slots.append(f"{h:02d}:30")
    return slots


# --- Usluge (GET/POST) ---
@bp.route("/usluge", methods=["GET", "POST"])
def usluge():
    if request.method == "POST":
        # Čitanje iz forme
        barber = (request.form.get("frizer") or "").strip()
        selected_services = request.form.getlist("usluge")   # više checkboxa
        day = request.form.get("datum") or ""
        slot = request.form.get("termin") or ""

        # Jednostavna validacija
        if not barber or not selected_services or not day or not slot:
            flash("Molimo odaberite frizera, barem jednu uslugu, datum i termin.", "warning")
            return redirect(url_for("main.usluge"))

        # Cijena (zbroj)
        price_map = {name: price for (name, _dur, price) in USLUGE}
        total_price = sum(price_map.get(s, 0) for s in selected_services)

        # Spremi u Mongo (ako postoji config)
        reservations = current_app.config.get("RESERVATIONS")
        if reservations is None:
            flash("Baza nije inicijalizirana (RESERVATIONS). Provjeri create_app().", "danger")
            return redirect(url_for("main.usluge"))

        doc = {
            "user": "demo",                 # kasnije zamijeniti stvarnim korisnikom
            "barber": barber,
            "services": selected_services,
            "date": day,                    # 'YYYY-MM-DD'
            "time": slot,                   # 'HH:MM'
            "total_price": total_price,
            "created_at": datetime.now(),
        }
        reservations.insert_one(doc)
        flash("Rezervacija je spremljena!", "success")
        return redirect(url_for("main.moja_sisanja"))

    # GET – pošalji podatke templateu
    return render_template(
        "usluge.html",
        frizeri=FRIZERI,
        usluge=USLUGE,
        timeslots=generate_timeslots(),
        today=date.today().isoformat(),
    )


# --- Moja šišanja (lista iz baze) ---
@bp.route("/moja_sisanja")
def moja_sisanja():
    reservations = current_app.config.get("RESERVATIONS")
    items = []
    if reservations is None:
        flash("Baza nije inicijalizirana (RESERVATIONS).", "warning")
    else:
        items = list(reservations.find().sort("created_at", -1))
    return render_template("moja_sisanja.html", items=items)
