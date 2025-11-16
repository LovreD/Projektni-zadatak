from datetime import datetime, date
from flask import render_template, request, redirect, url_for, flash, current_app
from . import bp
from flask import session, send_file, abort
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from .. import limiter


@bp.route("/")
def index():
    return render_template("index.html")


FRIZERI = [ "Marija", "Lovre", "Gabrijel", "Ivan" ]

USLUGE = [
    ("classic", "Klasično šišanje", 20, 12),
    ("fade", "Fade šišanje", 20, 15),
    ("buzz", "Buzz cut", 15, 10),
    ("long", "Šišanje duge kose", 30, 20),
]

WASH_PRICE = 2 



def current_user():
    uid = session.get("user_id")
    if not uid:
        return None

    users = current_app.config.get("USERS")
    if users is None:
        return None

    return users.find_one({"_id": ObjectId(uid)})

   

def login_required():
    return current_user() is not None

def generate_timeslots():
    slots = []
    for h in range(9, 17):            
        slots.append(f"{h:02d}:00")
        slots.append(f"{h:02d}:30")
    return slots


@bp.route("/usluge", methods=["GET", "POST"])
def usluge():
    reservations = current_app.config.get("RESERVATIONS")
    if reservations is None:
        flash("Baza nije inicijalizirana (RESERVATIONS).", "danger")
        return redirect(url_for("main.index"))

    if request.method == "POST":
        barber = (request.form.get("frizer") or "").strip()
        selected_service = request.form.get("service") 
        wash = request.form.get("wash") == "on"         
        day = request.form.get("datum") or ""
        slot = request.form.get("termin") or ""

        if not barber or not selected_service or not day or not slot:
            flash("Molimo odaberite frizera, uslugu, datum i termin.", "warning")
            return redirect(url_for("main.usluge"))

        already = reservations.find_one({
            "barber": barber,
            "date": day,
            "time": slot
        })
        if already:
            flash("Taj termin je već zauzet za odabranog frizera. Odaberite drugi termin.", "warning")
            return redirect(url_for("main.usluge"))

        price_map = {key: price for (key, _label, _dur, price) in USLUGE}
        label_map = {key: label for (key, label, _dur, _price) in USLUGE}

        if selected_service not in price_map:
            flash("Odabrana usluga nije ispravna.", "danger")
            return redirect(url_for("main.usluge"))

        total_price = price_map[selected_service]
        services_list = [label_map[selected_service]]

        if wash:
            total_price += WASH_PRICE
            services_list.append("Pranje kose")

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
            "services": services_list,   
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
        wash_price=WASH_PRICE,
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
@limiter.limit("3 per minute")
def register():
    users = current_app.config.get("USERS")
    if users is None:
        flash("Baza nije inicijalizirana (USERS).", "danger")
        return redirect(url_for("main.index"))

    if request.method == "POST":
        full_name = (request.form.get("full_name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        phone = (request.form.get("phone") or "").strip()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm") or ""

        has_error = False

        if len(full_name) < 3:
            flash("Ime i prezime mora imati barem 3 znaka.", "warning")
            has_error = True

        if not phone.isdigit() or len(phone) < 10:
            flash("Broj mobitela mora sadržavati samo znamenke i imati najmanje 10 znamenki.", "warning")
            has_error = True

        if len(password) < 8:
            flash("Lozinka mora imati najmanje 8 znakova.", "warning")
            has_error = True

        if password != confirm:
            flash("Lozinke se ne podudaraju.", "warning")
            has_error = True

        if users.find_one({"email": email}):
            flash("Taj email je već registriran.", "warning")
            has_error = True

        if has_error:
            return redirect(url_for("main.register"))

        users.insert_one({
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "password": password, 
            "photo_id": None,
            "created_at": datetime.now(),
        })

        flash("Registracija uspješna! Sad se možete prijaviti.", "success")
        return redirect(url_for("main.login"))

    return render_template("register.html")

@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
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


@bp.post("/rezervacije/<id>/cancel")
def cancel_reservation(id):
    reservations = current_app.config.get("RESERVATIONS")
    if reservations is None:
        flash("Baza nije inicijalizirana (RESERVATIONS).", "danger")
        return redirect(url_for("main.moja_sisanja"))

    u = current_user()
    if not u:
        flash("Prijavite se za otkazivanje rezervacije.", "info")
        return redirect(url_for("main.login"))

    try:
        oid = ObjectId(id)
    except Exception:
        abort(404)

    res = reservations.find_one({"_id": oid})
    if not res:
        abort(404)

    if res.get("user_id") != str(u["_id"]):
        abort(403)

    reservations.delete_one({"_id": oid})
    flash("Rezervacija uspješno otkazana.", "success")
    return redirect(url_for("main.moja_sisanja"))
