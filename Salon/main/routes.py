from datetime import datetime, date
from flask import render_template, request, redirect, url_for, flash, current_app
from . import bp
from flask import session, send_file, abort
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

@bp.route("/")
def index():
    return render_template("index.html")


FRIZERI = ["Marija", "Lovre", "Gabrijel", "Ivan"]
USLUGE = [
    ("Klasično šišanje", 20, 12),
    ("Fade šišanje", 20, 15),
    ("Buzz cut", 15, 10),
    ("Pranje kose", 0, 2),            
    ("Šišanje duge kose", 30, 20),
]

def current_user():
    """Vrati dokument korisnika iz baze ako je prijavljen, inače None."""
    uid = session.get("user_id")
    if not uid:
        return None

    users = current_app.config.get("USERS")
    if users is None:
        return None

    return users.find_one({"_id": ObjectId(uid)})

   

def login_required():
    """Jednostavna provjera (koristi je u rutama)"""
    return current_user() is not None

def generate_timeslots():
    """Termini svakih 30 min od 09:00 do 16:30"""
    slots = []
    for h in range(9, 17):            
        slots.append(f"{h:02d}:00")
        slots.append(f"{h:02d}:30")
    return slots


@bp.route("/usluge", methods=["GET", "POST"])
def usluge():
    if request.method == "POST":
        barber = (request.form.get("frizer") or "").strip()
        selected_services = request.form.getlist("usluge")
        day = request.form.get("datum") or ""
        slot = request.form.get("termin") or ""

        if not barber or not selected_services or not day or not slot:
            flash("Molimo odaberite frizera, barem jednu uslugu, datum i termin.", "warning")
            return redirect(url_for("main.usluge"))

        reservations = current_app.config.get("RESERVATIONS")
        if reservations is None:
            flash("Baza nije inicijalizirana (RESERVATIONS).", "danger")
            return redirect(url_for("main.usluge"))

        already = reservations.find_one({"barber": barber, "date": day, "time": slot})
        if already:
            flash("Taj termin je već zauzet za odabranog frizera. Odaberite drugi termin.", "warning")
            return redirect(url_for("main.usluge"))

        price_map = {name: price for (name, _dur, price) in USLUGE}
        total_price = sum(price_map.get(s, 0) for s in selected_services)

        u = current_user()
        username = "demo"
        user_id = None
        if u:
            username = u.get("full_name") or u.get("name") or u.get("email") or "demo"
            user_id = str(u["_id"])


        doc = {
            "user_id": user_id,
            "user_name": username,
            "barber": barber,
            "services": selected_services,
            "date": day,
            "time": slot,
            "total_price": total_price,
            "created_at": datetime.now(),
        }

        reservations.insert_one(doc)
        flash("Rezervacija je spremljena!", "success")
        return redirect(url_for("main.moja_sisanja"))

    return render_template(
        "usluge.html",
        frizeri=FRIZERI,
        usluge=USLUGE,
        timeslots=generate_timeslots(),
        today=date.today().isoformat(),
    )


@bp.route("/moja_sisanja")
def moja_sisanja():
    reservations = current_app.config.get("RESERVATIONS")
    if reservations is None:
        flash("Baza nije inicijalizirana (RESERVATIONS).", "danger")
        return render_template("moja_sisanja.html", items=[])

    u = current_user()
    items = []
    if u:
        items = list(
            reservations.find({"user_id": str(u["_id"])}).sort("created_at", -1)
        )
    else:
        flash("Prijavite se za pregled svojih rezervacija.", "info")

    return render_template("moja_sisanja.html", items=items)


@bp.route("/register", methods=["GET", "POST"])
def register():
    users = current_app.config.get("USERS")
    if users is None:
        flash("Baza nije inicijalizirana (USERS).", "danger")
        return redirect(url_for("main.index"))

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        password = request.form.get("password")

        if users.find_one({"email": email}):
            flash("Taj email je već registriran.", "warning")
            return redirect(url_for("main.register"))

        users.insert_one({
            "name": name,
            "email": email,
            "phone": phone,
            "password": password,
            "photo_id": None
        })

        flash("Registracija uspješna! Sad se možete prijaviti.", "success")
        return redirect(url_for("main.login"))

    return render_template("register.html")

@bp.route("/login", methods=["GET", "POST"])
def login():
    users = current_app.config.get("USERS")
    if users is None:
        flash("Baza nije inicijalizirana (USERS).", "danger")
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = users.find_one({"email": email, "password": password})
        if not user:
            flash("Neispravni podaci za prijavu.", "danger")
            return redirect(url_for("main.login"))

        session["user_id"] = str(user["_id"])
        flash("Uspješno ste prijavljeni.", "success")
        return redirect(url_for("main.account"))

    return render_template("login.html")


@bp.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Odjavljeni ste.", "info")
    return redirect(url_for("main.index"))


@bp.route("/account", methods=["GET", "POST"])
def account():
    user = current_user()
    if not user:
        flash("Morate biti prijavljeni.", "warning")
        return redirect(url_for("main.login"))

    users = current_app.config.get("USERS")
    fs = current_app.config.get("FS")
    if users is None or fs is None:
        flash("Baza nije inicijalizirana (USERS/FS).", "danger")
        return redirect(url_for("main.index"))

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")

        photo = request.files.get("photo")
        photo_id = user.get("photo_id")

        if photo and photo.filename:
            if photo_id:
                fs.delete(ObjectId(photo_id))
            new_photo_id = fs.put(photo, filename=photo.filename)
            photo_id = new_photo_id

        users.update_one(
            {"_id": user["_id"]},
            {"$set": {"name": name, "email": email, "phone": phone, "photo_id": photo_id}}
        )

        flash("Podaci uspješno ažurirani.", "success")
        return redirect(url_for("main.account"))

    return render_template("account.html", user=user)


@bp.route("/photo/<id>")
def photo(id):
    fs = current_app.config.get("FS")
    if fs is None:
        abort(404)

    try:
        photo = fs.get(ObjectId(id))
    except:
        abort(404)

    return send_file(photo, mimetype="image/jpeg")


