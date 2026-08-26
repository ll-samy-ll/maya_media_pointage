from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user

from extensions import db
from models import Pointage, Absence, Admin
from decorators import employee_required

employee_bp = Blueprint("employee", __name__, url_prefix="/employee")

COOLDOWN_MINUTES = 10

# --- Correctif temporaire de fuseau horaire ---
# Railway héberge le serveur en UTC, alors que l'entreprise est sur le
# fuseau UTC+1. En attendant une meilleure solution (stocker en UTC et
# convertir à l'affichage avec zoneinfo selon le fuseau du client), on
# décale artificiellement l'heure serveur.
TIMEZONE_OFFSET_HOURS = 1


def now_local():
    """Retourne l'heure actuelle corrigée du décalage serveur/entreprise."""
    return datetime.now() + timedelta(hours=TIMEZONE_OFFSET_HOURS)


JOURS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
MOIS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre"
]


def format_date_fr(d):
    return f"{JOURS_FR[d.weekday()]} {d.day} {MOIS_FR[d.month - 1].capitalize()} {d.year}"


def get_today_pointage():
    return Pointage.query.filter_by(
        employe_id=current_user.id, date_pointage=now_local().date()
    ).first()


def get_today_absence():
    return Absence.query.filter_by(
        employe_id=current_user.id, date_absence=now_local().date()
    ).first()


@employee_bp.route("/dashboard")
@employee_required
def dashboard():
    pointage = get_today_pointage()
    absence = get_today_absence()

    if absence:
        etat = "absent"
    elif not pointage or not pointage.heure_arrivee:
        etat = "avant_arrivee"
    elif not pointage.heure_depart:
        etat = "attente_depart"
    else:
        etat = "termine"

    heures_travaillees = None
    if etat == "termine":
        delta = pointage.calculer_heures_travaillees()
        if delta:
            total_minutes = int(delta.total_seconds() // 60)
            heures_travaillees = f"{total_minutes // 60}h{total_minutes % 60:02d}"

    depart_disponible_a = None
    if etat == "attente_depart":
        arrivee_dt = datetime.combine(pointage.date_pointage, pointage.heure_arrivee)
        depart_disponible_a = (arrivee_dt + timedelta(minutes=COOLDOWN_MINUTES)).isoformat()

    return render_template(
        "employee/dashboard.html",
        pointage=pointage,
        absence=absence,
        etat=etat,
        heures_travaillees=heures_travaillees,
        depart_disponible_a=depart_disponible_a,
        now_label=format_date_fr(now_local().date()),
    )


@employee_bp.route("/pointer-arrivee", methods=["POST"])
@employee_required
def pointer_arrivee():
    if get_today_absence():
        flash("Vous avez déclaré une absence aujourd'hui, impossible de pointer.", "danger")
        return