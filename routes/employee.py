from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user

from extensions import db
from models import Pointage, Absence, Admin
from decorators import employee_required

employee_bp = Blueprint("employee", __name__, url_prefix="/employee")

COOLDOWN_MINUTES = 10

JOURS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
MOIS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre"
]


def format_date_fr(d):
    return f"{JOURS_FR[d.weekday()]} {d.day} {MOIS_FR[d.month - 1].capitalize()} {d.year}"


def get_today_pointage():
    return Pointage.query.filter_by(
        employe_id=current_user.id, date_pointage=date.today()
    ).first()


def get_today_absence():
    return Absence.query.filter_by(
        employe_id=current_user.id, date_absence=date.today()
    ).first()


@employee_bp.route("/dashboard")
@employee_required
def dashboard():
    pointage = get_today_pointage()
    absence = get_today_absence()

    # Détermination de l'état de la journée
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
        now_label=format_date_fr(date.today()),
    )


@employee_bp.route("/pointer-arrivee", methods=["POST"])
@employee_required
def pointer_arrivee():
    if get_today_absence():
        flash("Vous avez déclaré une absence aujourd'hui, impossible de pointer.", "danger")
        return redirect(url_for("employee.dashboard"))

    pointage = get_today_pointage()
    if pointage and pointage.heure_arrivee:
        flash("Vous avez déjà pointé votre arrivée aujourd'hui.", "warning")
        return redirect(url_for("employee.dashboard"))

    now = datetime.now()
    admin = Admin.query.first()

    if not pointage:
        pointage = Pointage(employe_id=current_user.id, date_pointage=date.today())
        db.session.add(pointage)

    pointage.heure_arrivee = now.time().replace(microsecond=0) + timedelta(hours=1)
    pointage.en_retard = bool(admin and admin.heure_arrivee_prevue and now.time() > admin.heure_arrivee_prevue)

    db.session.commit()
    flash("Arrivée pointée avec succès.", "success")
    return redirect(url_for("employee.dashboard"))


@employee_bp.route("/annuler-arrivee", methods=["POST"])
@employee_required
def annuler_arrivee():
    pointage = get_today_pointage()
    if pointage and pointage.heure_arrivee and not pointage.heure_depart:
        pointage.heure_arrivee = None
        pointage.en_retard = False
        db.session.commit()
        flash("Pointage d'arrivée annulé.", "info")
    return redirect(url_for("employee.dashboard"))


@employee_bp.route("/pointer-depart", methods=["POST"])
@employee_required
def pointer_depart():
    pointage = get_today_pointage()

    if not pointage or not pointage.heure_arrivee:
        flash("Vous devez d'abord pointer votre arrivée.", "danger")
        return redirect(url_for("employee.dashboard"))

    if pointage.heure_depart:
        flash("Vous avez déjà pointé votre départ aujourd'hui.", "warning")
        return redirect(url_for("employee.dashboard"))

    now = datetime.now()
    arrivee_dt = datetime.combine(pointage.date_pointage, pointage.heure_arrivee)

    if now < arrivee_dt + timedelta(minutes=COOLDOWN_MINUTES):
        flash(f"Vous devez attendre au moins {COOLDOWN_MINUTES} minutes après votre arrivée.", "danger")
        return redirect(url_for("employee.dashboard"))
    
    pointage.heure_depart = now.time().replace(microsecond=0) + timedelta(hours=1)
    db.session.commit()
    flash("Merci pour votre pointage.", "success")
    return redirect(url_for("employee.dashboard"))


@employee_bp.route("/annuler-depart", methods=["POST"])
@employee_required
def annuler_depart():
    pointage = get_today_pointage()
    if pointage and pointage.heure_depart:
        pointage.heure_depart = None
        db.session.commit()
        flash("Pointage de départ annulé.", "info")
    return redirect(url_for("employee.dashboard"))


@employee_bp.route("/absence", methods=["POST"])
@employee_required
def declarer_absence():
    pointage = get_today_pointage()
    if pointage and pointage.heure_arrivee:
        flash("Vous avez déjà commencé votre pointage aujourd'hui, impossible de déclarer une absence.", "danger")
        return redirect(url_for("employee.dashboard"))

    if get_today_absence():
        flash("Vous avez déjà déclaré une absence aujourd'hui.", "warning")
        return redirect(url_for("employee.dashboard"))

    motif = request.form.get("motif", "").strip()
    absence = Absence(employe_id=current_user.id, date_absence=date.today(), motif=motif)
    db.session.add(absence)
    db.session.commit()
    flash("Absence déclarée avec succès.", "success")
    return redirect(url_for("employee.dashboard"))


@employee_bp.route("/historiques")
@employee_required
def historiques():
    pointages = Pointage.query.filter_by(employe_id=current_user.id).order_by(
        Pointage.date_pointage.desc()
    ).all()
    return render_template("employee/historiques.html", pointages=pointages)


@employee_bp.route("/retards")
@employee_required
def retards():
    pointages_retard = Pointage.query.filter_by(
        employe_id=current_user.id, en_retard=True
    ).order_by(Pointage.date_pointage.desc()).all()
    return render_template("employee/retards.html", pointages_retard=pointages_retard)

@employee_bp.route("/annuler-absence", methods=["POST"])
@employee_required
def annuler_absence():
    absence = get_today_absence()
    if absence:
        db.session.delete(absence)
        db.session.commit()
        flash("Déclaration d'absence annulée.", "info")
    return redirect(url_for("employee.dashboard"))