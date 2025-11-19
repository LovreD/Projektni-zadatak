README.md — Frizerski salon Malura (Flask + MongoDB)

🎉 Frizerski salon Malura – Web Aplikacija

Ovo je projekt izrađen za kolegij Programiranje za web.
Aplikacija omogućuje korisnicima pregled frizera, odabir usluge, rezervaciju termina, upravljanje korisničkim računom i pregled vlastitih rezervacija.
Posebna admin stranica omogućuje administratoru pregled i brisanje korisnika i rezervacija.

Aplikacija je izrađena koristeći Flask, MongoDB, GridFS, Mailtrap, Flask-Login, Flask-Limiter, Bleach sanitizaciju, Markdown napomene i Render deployment.

🚀 Funkcionalnosti

👤 Korisnici

Registracija

Email verifikacija (Mailtrap)

Prijava/odjava (Flask-Login)

Uređivanje korisničkog računa

Postavljanje profilne slike (GridFS)

Pregled i otkazivanje rezervacija

💈 Rezervacije

Odabir frizera (4 frizera)

Odabir usluge (4 glavne usluge + dodatno pranje kose)

Odabir datuma i vremena

Provjera zauzetosti termina

Spremanje rezervacija u MongoDB

Napomena (Markdown + Bleach sanitizacija)

🛡️ Sigurnost

CSRF zaštita (Flask)

Bleach sanitizacija korisničkog HTML sadržaja

Rate limiting (Flask-Limiter)

Session sigurnosne postavke (cookies)

🔐 Admin panel

Pregled korisnika

Pregled rezervacija

Brisanje korisnika

Brisanje rezervacija

📤 Slanje e-mailova

Email verifikacija (Mailtrap SMTP)

Ponovno slanje verifikacijskog emaila

🖼️ Statički sadržaj

Prikaz 4 slike radova na početnoj stranici

Slike frizera na stranici usluga

☁️ Deployment

Aplikacija je pripremljena za Render hosting:

render.yaml

requirements.txt

runtime.txt

.env spreman za okruženje

🛠️ Tehnologije

Tehnologija	Namjena
Flask	Backend web framework
MongoDB Atlas	Baza podataka
GridFS	Spremanje slika korisnika
Bootstrap 5	Frontend dizajn
Jinja2	Template engine
Flask-Login	Autorizacija
Flask-Limiter	Rate limiting
Bleach	Sanitizacija HTML sadržaja
Markdown2	Markdown konverzija
Mailtrap SMTP	Slanje emaila


📁 Struktura projekta

projektni_zadatak/
│
├── app.py
├── requirements.txt
├── render.yaml
├── runtime.txt
├── .env
├── README.md
│
├── Salon/
│   ├── __init__.py
│   ├── utils.py
│   ├── main/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── forms.py  
│   │   └── templates/
│   │       ├── base.html
│   │       ├── index.html
│   │       ├── usluge.html
│   │       ├── moja_sisanja.html
│   │       ├── auth/
│   │       │   ├── login.html
│   │       │   ├── register.html
│   │       │   ├── resend_verification.html
│   │       │   ├── account.html
│   │       ├── errors/
│   │           ├── 403.html
│   │           ├── 404.html
│   │           ├── 429.html
│   │           └── 500.html
│
└── static/
    ├── img/
        ├── barbers/
        └── radovi/


⚙️ Instalacija
1. Kloniraj projekt:
git clone <url>
cd projektni_zadatak

2. Kreiraj virtual environment:
python -m venv .venv
source .venv/bin/activate       # Linux/Mac
.venv\Scripts\activate          # Windows

3. Instaliraj pakete:
pip install -r requirements.txt

4. Postavi .env datoteku:
MONGO_URI=mongodb+srv://...
SECRET_KEY=...
MAIL_SERVER=sandbox.smtp.mailtrap.io
MAIL_PORT=587
MAIL_USERNAME=...
MAIL_PASSWORD=...

▶️ Pokretanje aplikacije
python app.py


Aplikacija će se otvoriti na:

http://127.0.0.1:5000
