from datetime import datetime, date
from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    session,
    send_file,
    abort,
)
from . import bp
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from .. import limiter, User
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from .. import mail
from flask_mail import Message
from flask_login import UserMixin


@bp.route("/")
def index():
    return render_template("index.html")



FRIZERI = ["Marija", "Lovre", "Gabrijel", "Ivan"]

USLUGE = [
    ("classic", "Klasično šišanje", 20, 12),
    ("fade", "Fade šišanje", 20, 15),
    ("buzz", "Buzz cut", 15, 10),
    ("long", "Šišanje duge kose", 30, 20),
]

WASH_PRICE = 2 


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

        already = reservations.find_one(
            {
                "barber": barber,
                "date": day,
                "time": slot,
            }
        )
        if already:
            flash(
                "Taj termin je već zauzet za odabranog frizera. Odaberite drugi termin.",
                "warning",
            )
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

        if not current_user.is_authenticated:
            session["pending_reservation"] = {
                "barber": barber,
                "services": services_list,
                "date": day,
                "time": slot,
                "total_price": total_price,
            }
            flash("Prijavite se kako biste dovršili rezervaciju.", "info")
            return redirect(url_for("main.login", next=url_for("main.moja_sisanja")))

        username = current_user.full_name or current_user.email or "demo"
        user_id = current_user.id

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


@bp.route("/moja-sisanja")
@login_required
def moja_sisanja():
    reservations = current_app.config.get("RESERVATIONS")
    if reservations is None:
        flash("Baza nije inicijalizirana (RESERVATIONS).", "danger")
        return redirect(url_for("main.index"))

    res = list(
        reservations.find({"user_id": current_user.id}).sort("date", 1)
    )

    items = []
    for r in res:
        items.append(
            {
                "id": str(r["_id"]),
                "barber": r["barber"],
                "services": r["services"],
                "date": r["date"],
                "time": r["time"],
                "total_price": r.get("total_price", 0),
            }
        )

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
            flash(
                "Broj mobitela mora sadržavati samo znamenke i imati najmanje 10 znamenki.",
                "warning",
            )
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

        result = users.insert_one({
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "password": password, 
            "photo_id": None,
            "created_at": datetime.now(),
            "email_verified": False,  
            "role": "user",            
        })

        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        token = s.dumps(email, salt="email-confirm")

        confirm_url = url_for("main.confirm_email", token=token, _external=True)

        msg = Message(
            subject="Potvrda registracije - Frizerski salon",
            recipients=[email],
        )
        msg.body = (
            f"Bok {full_name},\n\n"
            f"Hvala na registraciji u naš frizerski salon.\n"
            f"Za potvrdu svog emaila klikni na sljedeći link:\n{confirm_url}\n\n"
            f"Link vrijedi 1 sat.\n\n"
            f"Lijep pozdrav!"
        )

        try:
            mail.send(msg)
            flash("Registracija uspješna! Provjerite email za verifikaciju.", "success")
        except Exception:
            flash("Registracija uspješna, ali slanje verifikacijskog emaila nije uspjelo.", "warning")

        return redirect(url_for("main.login"))

    return render_template("register.html")


@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        users = current_app.config.get("USERS")
        if users is None:
            flash("Baza korisnika nije inicijalizirana.", "danger")
            return redirect(url_for("main.login"))

        doc = users.find_one({"email": email, "password": password})
        if not doc:
            flash("Pogrešan email ili lozinka.", "danger")
            return redirect(url_for("main.login"))
        
        if not doc.get("email_verified"):
            flash("Email nije verificiran. Provjerite email ili zatražite novi verifikacijski link.", "warning")
            return redirect(url_for("main.resend_verification"))


        user_obj = User(doc)
        login_user(user_obj, remember=True)

        flash("Uspješno ste prijavljeni.", "success")


        pending = session.pop("pending_reservation", None)
        if pending:
            reservations = current_app.config.get("RESERVATIONS")
            if reservations is not None:
                already = reservations.find_one(
                    {
                        "barber": pending["barber"],
                        "date": pending["date"],
                        "time": pending["time"],
                    }
                )
                if already:
                    flash(
                        "Termin koji ste ranije odabrali u međuvremenu je zauzet. Odaberite drugi termin.",
                        "warning",
                    )
                else:
                    username = current_user.full_name or current_user.email or "demo"
                    doc = {
                        "user_id": current_user.id,
                        "user_name": username,
                        "barber": pending["barber"],
                        "services": pending["services"],
                        "date": pending["date"],
                        "time": pending["time"],
                        "total_price": pending["total_price"],
                        "created_at": datetime.now(),
                    }
                    reservations.insert_one(doc)
                    flash("Vaša ranije odabrana rezervacija je spremljena.", "success")

        next_page = request.args.get("next") or request.form.get("next")
        if next_page:
            return redirect(next_page)

        return redirect(url_for("main.index"))

    return render_template("login.html")


@bp.route("/confirm/<token>")
def confirm_email(token):
    users = current_app.config.get("USERS")
    if users is None:
        flash("Baza nije inicijalizirana (USERS).", "danger")
        return redirect(url_for("main.index"))

    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

    try:
        email = s.loads(token, salt="email-confirm", max_age=3600)  # 1 sat
    except Exception:
        flash("Link za verifikaciju je nevažeći ili je istekao.", "danger")
        return redirect(url_for("main.login"))

    # pronađi korisnika
    user = users.find_one({"email": email})
    if not user:
        flash("Korisnik ne postoji.", "danger")
        return redirect(url_for("main.register"))

    if user.get("email_verified"):
        flash("Email je već potvrđen.", "info")
        return redirect(url_for("main.login"))

    # ažuriraj status
    users.update_one({"_id": user["_id"]}, {"$set": {"email_verified": True}})

    flash("Email uspješno potvrđen! Sada se možete prijaviti.", "success")
    return redirect(url_for("main.login"))




@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Odjavljeni ste.", "info")
    return redirect(url_for("main.index"))



@bp.route("/account", methods=["GET", "POST"])
@login_required
def account():
    users = current_app.config.get("USERS")
    fs = current_app.config.get("FS")
    if users is None or fs is None:
        flash("Baza nije inicijalizirana (USERS/FS).", "danger")
        return redirect(url_for("main.index"))

    user_doc = users.find_one({"_id": ObjectId(current_user.id)})
    if not user_doc:
        flash("Korisnik nije pronađen.", "danger")
        return redirect(url_for("main.logout"))

    if request.method == "POST":
        name = request.form.get("name") or ""
        email = request.form.get("email") or ""
        phone = request.form.get("phone") or ""

        photo = request.files.get("photo")
        photo_id = user_doc.get("photo_id")

        if photo and photo.filename:
            if photo_id:
                try:
                    fs.delete(ObjectId(photo_id))
                except Exception:
                    pass
            new_photo_id = fs.put(photo, filename=photo.filename)
            photo_id = new_photo_id

        users.update_one(
            {"_id": user_doc["_id"]},
            {"$set": {"name": name, "email": email, "phone": phone, "photo_id": photo_id}},
        )

        flash("Podaci uspješno ažurirani.", "success")
        return redirect(url_for("main.account"))

    return render_template("account.html", user=user_doc)



@bp.route("/photo/<id>")
def photo(id):
    fs = current_app.config.get("FS")
    if fs is None:
        abort(404)

    try:
        photo = fs.get(ObjectId(id))
    except Exception:
        abort(404)

    return send_file(photo, mimetype="image/jpeg")



@bp.route("/rezervacije/<id>/cancel", methods=["POST"])
@login_required
def cancel_reservation(id):
    reservations = current_app.config.get("RESERVATIONS")
    if reservations is None:
        flash("Baza nije inicijalizirana (RESERVATIONS).", "danger")
        return redirect(url_for("main.moja_sisanja"))

    u = current_user
    if not u.is_authenticated:
        flash("Prijavite se za otkazivanje rezervacije.", "info")
        return redirect(url_for("main.login"))

    try:
        oid = ObjectId(id)
    except Exception:
        abort(404)

    res = reservations.find_one({"_id": oid})
    if not res:
        abort(404)

    if str(res.get("user_id")) != str(u.id):
        abort(403)

    reservations.delete_one({"_id": oid})
    flash("Rezervacija uspješno otkazana.", "success")
    return redirect(url_for("main.moja_sisanja"))

@bp.route("/resend-verification", methods=["GET", "POST"])
def resend_verification():
    users = current_app.config.get("USERS")
    if users is None:
        flash("Baza nije inicijalizirana (USERS).", "danger")
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        user = users.find_one({"email": email})

        if not user:
            flash("Ne postoji korisnik s tim emailom.", "warning")
            return redirect(url_for("main.resend_verification"))

        if user.get("email_verified"):
            flash("Ovaj email je već verificiran. Možete se prijaviti.", "info")
            return redirect(url_for("main.login"))

        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        token = s.dumps(email, salt="email-confirm")
        confirm_url = url_for("main.confirm_email", token=token, _external=True)

        msg = Message(
            subject="Ponovni verifikacijski email - Frizerski salon",
            recipients=[email],
        )
        msg.body = (
            f"Bok {user.get('full_name', '')},\n\n"
            f"Evo novog verifikacijskog linka:\n{confirm_url}\n\n"
            f"Link vrijedi 1 sat.\n\n"
            f"Lijep pozdrav!"
        )

        try:
            mail.send(msg)
            flash("Novi verifikacijski email je poslan.", "success")
        except Exception:
            flash("Slanje verifikacijskog emaila nije uspjelo.", "danger")

        return redirect(url_for("main.login"))

    return render_template("resend_verification.html")


@bp.route("/test-mail")
def test_mail():
    from flask_mail import Message
    from .. import mail

    msg = Message(
        subject="Test Mailtrap",
        recipients=["test@example.com"],
        body="Ovo je test mail iz frizerskog salona. :)"
    )
    try:
        mail.send(msg)
        return "OK — mail poslan! Pogledaj Mailtrap inbox."
    except Exception as e:
        return f"Greška pri slanju: {e}"
