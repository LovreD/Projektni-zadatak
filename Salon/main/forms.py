from flask_wtf import FlaskForm
from wtforms import RadioField , SelectMultipleField , SelectField , DateField , SubmitField
from wtforms.validators import DataRequired
from datetime import date


BARBERS = [("Marija","Marija"), ("Lovre","Lovre"), ("Gabrijel","Gabrijel"), ("Ivan","Ivan")]


SERVICES = [
    ("classic", "Klasično šišanje (20 min, 12 €)"),
    ("fade", "Fade šišanje (20 min, 15 €)"),
    ("buzz", "Buzz cut (15 min, 10 €)"),
    ("wash", "Pranje kose (+2 €)"),
    ("long", "Šišanje duge kose (30 min, 20 €)")
]

def half_hour_slots(start=9, end=17):
    opts = []
    for h in range(start, end):
        opts.append((f"{h:02d}:00", f"{h:02d}:00"))
        opts.append((f"{h:02d}:30", f"{h:02d}:30"))
    return opts

class ReservationForm(FlaskForm):
    barber = RadioField("Frizer", choices=BARBERS, validators=[DataRequired()])
    services = SelectMultipleField("Usluge", choices=SERVICES, validators=[DataRequired()])
    day = DateField("Datum", default=date.today, validators=[DataRequired()])
    time = SelectField("Termin", choices=half_hour_slots(), validators=[DataRequired()])
    submit = SubmitField("Rezerviraj")
