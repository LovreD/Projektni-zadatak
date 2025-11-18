from datetime import date
from flask_wtf import FlaskForm
from wtforms import RadioField, SelectField, DateField, SubmitField, BooleanField
from wtforms.validators import DataRequired


# Moraju odgovarati FRIZERI i USLUGE iz routes.py
BARBERS = [
    ("Marija", "Marija"),
    ("Lovre", "Lovre"),
    ("Gabrijel", "Gabrijel"),
    ("Ivan", "Ivan"),
]

# key mora biti isti kao u USLUGE u routes.py
SERVICES = [
    ("classic", "Klasično šišanje (20 min, 12 €)"),
    ("fade",   "Fade šišanje (20 min, 15 €)"),
    ("buzz",   "Buzz cut (15 min, 10 €)"),
    ("long",   "Šišanje duge kose (30 min, 20 €)"),
]

def half_hour_slots(start=9, end=17):
    """Generira termine svakih 30 min od 09:00 do 16:30."""
    opts = []
    for h in range(start, end):
        opts.append((f"{h:02d}:00", f"{h:02d}:00"))
        opts.append((f"{h:02d}:30", f"{h:02d}:30"))
    return opts

class ReservationForm(FlaskForm):
    barber = RadioField(
        "Frizer",
        choices=BARBERS,
        validators=[DataRequired()]
    )

    # jedna glavna usluga
    service = SelectField(
        "Usluga",
        choices=SERVICES,
        validators=[DataRequired()]
    )

    # dodatna usluga – pranje kose
    wash = BooleanField("Pranje kose (+2 €)")

    date = DateField(
        "Datum",
        default=date.today,
        validators=[DataRequired()]
    )

    time = SelectField(
        "Termin",
        choices=half_hour_slots(),
        validators=[DataRequired()]
    )

    submit = SubmitField("Rezerviraj")


class CSRFForm(FlaskForm):
    """Prazan formular – služi samo za CSRF zaštitu."""
    pass
