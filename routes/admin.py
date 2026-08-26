from datetime import date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash

from extensions import db
from models import Employe, Pointage, Absence
from decorators import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

MOIS_FR = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
]


# ------------------------------------------------------------------
# DASHBOARD
# ------------------------------------------------------------------
@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    today = date.today()

    total_employes = Employe.query.count()
    actifs = Employe.query.filter_by(actif=True).all()
    actifs_ids = [e.id for e in actifs]

    pointages_today = Pointage.query.filter(
        Pointage.date_pointage == today, Pointage.employe_id.in_(actifs_ids)
    ).all() if actifs_ids else []

    presents_today = len([p for p in pointages_today if p.heure_arrivee])
    absents_today = len(actifs) - presents_today
    retards_today = len([p for p in pointages_today if p.en_retard])

    total_minutes = 0
    for p in pointages_today:
        delta = p.calculer_heures_travaillees()
        if delta:
            total_minutes += int(delta.total_seconds() // 60)
    total_heures_today = f"{total_minutes // 60}h{total_minutes % 60:02d}"

    lignes = build_presence_rows(actifs, pointages_today)

    # Liste détaillée des absences déclarées aujourd'hui (nom + motif)
    absences_declarees = Absence.query.filter(
        Absence.date_absence == today, Absence.employe_id.in_(actifs_ids)
    ).all() if actifs_ids else []

    absences_details = [
        {"nom": a.employe.nom, "motif": a.motif or "Non précisé"}
        for a in absences_declarees
    ]

    return render_template(
        "admin/dashboard.html",
        total_employes=total_employes,
        presents_today=presents_today,
        absents_today=absents_today,
        retards_today=retards_today,
        pointages_count=len(pointages_today),
        total_heures_today=total_heures_today,
        lignes=lignes,
        absences_details=absences_details,
    )

def build_presence_rows(employes, pointages_du_jour):
    """Construit les lignes du tableau de présence à partir d'une liste
    d'employés et de leurs pointages du jour."""
    pointage_par_employe = {p.employe_id: p for p in pointages_du_jour}
    lignes = []

    for e in employes:
        p = pointage_par_employe.get(e.id)
        if p and p.heure_depart:
            statut, temps = "Présent", None
            delta = p.calculer_heures_travaillees()
            if delta:
                m = int(delta.total_seconds() // 60)
                temps = f"{m // 60}h{m % 60:02d}"
        elif p and p.heure_arrivee:
            statut, temps = "En cours", None
        else:
            statut, temps = "Absent", None

        lignes.append({
            "nom": e.nom,
            "arrivee": p.heure_arrivee.strftime("%Hh%M") if p and p.heure_arrivee else "--",
            "depart": p.heure_depart.strftime("%Hh%M") if p and p.heure_depart else "--",
            "statut": statut,
            "retard": "Oui" if p and p.en_retard else "Non",
            "temps": temps or "--",
        })
    return lignes


# ------------------------------------------------------------------
# LISTE DES EMPLOYÉS
# ------------------------------------------------------------------
@admin_bp.route("/employees")
@admin_required
def employees_list():
    search = request.args.get("q", "").strip()
    query = Employe.query

    if search:
        query = query.filter(
            db.or_(Employe.nom.ilike(f"%{search}%"), Employe.email.ilike(f"%{search}%"))
        )

    employes = query.order_by(Employe.date_creation.desc()).all()
    return render_template("admin/employees.html", employes=employes, search=search)


@admin_bp.route("/employees/add", methods=["POST"])
@admin_required
def add_employee():
    nom = request.form.get("nom", "").strip()
    email = request.form.get("email", "").strip().lower()
    poste = request.form.get("poste", "").strip()

    if not nom or not email:
        flash("Le nom et l'e-mail sont obligatoires.", "danger")
        return redirect(url_for("admin.employees_list"))

    if Employe.query.filter_by(email=email).first():
        flash("Un employé avec cet e-mail existe déjà.", "danger")
        return redirect(url_for("admin.employees_list"))

    employe = Employe(nom=nom, email=email, poste=poste or None)
    db.session.add(employe)
    db.session.commit()

    flash(f"Employé {nom} ajouté. Il pourra créer son mot de passe via l'onglet Inscription.", "success")
    return redirect(url_for("admin.employees_list"))


@admin_bp.route("/employees/<int:employee_id>/edit", methods=["POST"])
@admin_required
def edit_employee(employee_id):
    employe = Employe.query.get_or_404(employee_id)

    nom = request.form.get("nom", "").strip()
    email = request.form.get("email", "").strip().lower()
    poste = request.form.get("poste", "").strip()

    if not nom or not email:
        flash("Le nom et l'e-mail sont obligatoires.", "danger")
        return redirect(url_for("admin.employees_list"))

    existing = Employe.query.filter(Employe.email == email, Employe.id != employee_id).first()
    if existing:
        flash("Un autre employé utilise déjà cet e-mail.", "danger")
        return redirect(url_for("admin.employees_list"))

    employe.nom = nom
    employe.email = email
    employe.poste = poste or None
    db.session.commit()

    flash(f"Employé {nom} modifié avec succès.", "success")
    return redirect(url_for("admin.employees_list"))


@admin_bp.route("/employees/<int:employee_id>/toggle-active", methods=["POST"])
@admin_required
def toggle_active(employee_id):
    employe = Employe.query.get_or_404(employee_id)
    employe.actif = not employe.actif
    db.session.commit()

    statut = "réactivé" if employe.actif else "désactivé"
    flash(f"Employé {employe.nom} {statut}.", "success")
    return redirect(url_for("admin.employees_list"))

@admin_bp.route("/employees/<int:employee_id>/reset-password", methods=["POST"])
@admin_required
def reset_password(employee_id):
    employe = Employe.query.get_or_404(employee_id)
    employe.password_hash = None
    db.session.commit()

    flash(f"Mot de passe de {employe.nom} réinitialisé. Il pourra en recréer un via l'onglet Inscription.", "success")
    return redirect(url_for("admin.employees_list"))


# ------------------------------------------------------------------
# SUIVI DES POINDAGES (temps réel, aujourd'hui)
# ------------------------------------------------------------------
@admin_bp.route("/presences/suivi")
@admin_required
def suivi_pointages():
    today = date.today()
    search = request.args.get("q", "").strip()

    query = Employe.query.filter_by(actif=True)
    if search:
        query = query.filter(Employe.nom.ilike(f"%{search}%"))
    actifs = query.order_by(Employe.nom.asc()).all()
    actifs_ids = [e.id for e in actifs]

    pointages_today = Pointage.query.filter(
        Pointage.date_pointage == today, Pointage.employe_id.in_(actifs_ids)
    ).all() if actifs_ids else []

    lignes = build_presence_rows(actifs, pointages_today)

    return render_template(
        "admin/suivi_pointages.html",
        lignes=lignes,
        search=search,
        today=today,
    )


# ------------------------------------------------------------------
# RÉCAPITULATIF (synthèse par employé, semaine ou mois)
# ------------------------------------------------------------------
def get_period_bounds(period_type, ref_date):
    """Retourne (debut, fin, label) pour la période demandée."""
    if period_type == "semaine":
        debut = ref_date - timedelta(days=ref_date.weekday())  # Lundi
        fin = debut + timedelta(days=6)  # Dimanche
        label = f"Semaine du {debut.strftime('%d/%m')} au {fin.strftime('%d/%m/%Y')}"
    else:  # mois
        debut = ref_date.replace(day=1)
        if debut.month == 12:
            fin = debut.replace(year=debut.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            fin = debut.replace(month=debut.month + 1, day=1) - timedelta(days=1)
        label = f"{MOIS_FR[debut.month - 1]} {debut.year}"
    return debut, fin, label


@admin_bp.route("/presences/recapitulatif")
@admin_required
def recapitulatif():
    period_type = request.args.get("period", "mois")
    if period_type not in ("semaine", "mois"):
        period_type = "mois"

    ref_str = request.args.get("ref")
    ref_date = date.fromisoformat(ref_str) if ref_str else date.today()

    debut, fin, label = get_period_bounds(period_type, ref_date)

    # Navigation précédent/suivant
    delta = timedelta(days=7) if period_type == "semaine" else timedelta(days=32)
    if period_type == "mois":
        prev_ref = (debut - timedelta(days=1)).replace(day=1)
        next_ref = (fin + timedelta(days=1))
    else:
        prev_ref = debut - timedelta(days=7)
        next_ref = debut + timedelta(days=7)

    employes = Employe.query.order_by(Employe.nom.asc()).all()

    lignes = []
    for e in employes:
        pointages = Pointage.query.filter(
            Pointage.employe_id == e.id,
            Pointage.date_pointage >= debut,
            Pointage.date_pointage <= fin,
        ).all()
        absences = Absence.query.filter(
            Absence.employe_id == e.id,
            Absence.date_absence >= debut,
            Absence.date_absence <= fin,
        ).count()

        jours_presents = len([p for p in pointages if p.heure_arrivee])
        retards = len([p for p in pointages if p.en_retard])

        total_minutes = 0
        for p in pointages:
            d = p.calculer_heures_travaillees()
            if d:
                total_minutes += int(d.total_seconds() // 60)
        total_heures = f"{total_minutes // 60}h{total_minutes % 60:02d}"

        lignes.append({
            "nom": e.nom,
            "actif": e.actif,
            "jours_presents": jours_presents,
            "jours_absents": absences,
            "retards": retards,
            "total_heures": total_heures,
        })

    return render_template(
        "admin/recapitulatif.html",
        lignes=lignes,
        period_type=period_type,
        label=label,
        prev_ref=prev_ref.isoformat(),
        next_ref=next_ref.isoformat(),
    )

# ------------------------------------------------------------------
# HISTORIQUE (tous les pointages + absences, filtrable)
# ------------------------------------------------------------------
@admin_bp.route("/presences/historique")
@admin_required
def historique():
    employe_id = request.args.get("employe_id", type=int)
    date_debut_str = request.args.get("date_debut", "")
    date_fin_str = request.args.get("date_fin", "")

    date_debut = date.fromisoformat(date_debut_str) if date_debut_str else None
    date_fin = date.fromisoformat(date_fin_str) if date_fin_str else None

    pointage_query = Pointage.query
    absence_query = Absence.query

    if employe_id:
        pointage_query = pointage_query.filter(Pointage.employe_id == employe_id)
        absence_query = absence_query.filter(Absence.employe_id == employe_id)

    if date_debut:
        pointage_query = pointage_query.filter(Pointage.date_pointage >= date_debut)
        absence_query = absence_query.filter(Absence.date_absence >= date_debut)

    if date_fin:
        pointage_query = pointage_query.filter(Pointage.date_pointage <= date_fin)
        absence_query = absence_query.filter(Absence.date_absence <= date_fin)

    pointages = pointage_query.all()
    absences = absence_query.all()

    # Fusionne pointages et absences par (employe, date)
    lignes = {}
    for p in pointages:
        key = (p.employe_id, p.date_pointage)
        lignes[key] = {
            "date": p.date_pointage,
            "nom": p.employe.nom,
            "arrivee": p.heure_arrivee.strftime("%Hh%M") if p.heure_arrivee else "--",
            "depart": p.heure_depart.strftime("%Hh%M") if p.heure_depart else "--",
            "absence": False,
            "motif": "--",
        }

    for a in absences:
        key = (a.employe_id, a.date_absence)
        if key in lignes:
            lignes[key]["absence"] = True
            lignes[key]["motif"] = a.motif or "--"
        else:
            lignes[key] = {
                "date": a.date_absence,
                "nom": a.employe.nom,
                "arrivee": "--",
                "depart": "--",
                "absence": True,
                "motif": a.motif or "--",
            }

    lignes_triees = sorted(lignes.values(), key=lambda x: x["date"], reverse=True)
    employes = Employe.query.order_by(Employe.nom.asc()).all()

    return render_template(
        "admin/historique.html",
        lignes=lignes_triees,
        employes=employes,
        employe_id=employe_id,
        date_debut=date_debut_str,
        date_fin=date_fin_str,
    )

# ------------------------------------------------------------------
# PARAMÈTRES (heure de retard + mot de passe admin)
# ------------------------------------------------------------------
from flask_login import current_user
from datetime import time as time_type


@admin_bp.route("/parametres", methods=["GET", "POST"])
@admin_required
def parametres():
    admin = current_user

    if request.method == "POST":
        form_type = request.form.get("form_type")

        # --- Formulaire 1 : heure de retard ---
        if form_type == "heure_retard":
            heure_str = request.form.get("heure_arrivee_prevue", "").strip()
            try:
                h, m = map(int, heure_str.split(":"))
                admin.heure_arrivee_prevue = time_type(h, m)
                db.session.commit()
                flash("Heure de retard mise à jour avec succès.", "success")
            except (ValueError, AttributeError):
                flash("Format d'heure invalide.", "danger")

        # --- Formulaire 2 : changement de mot de passe ---
        elif form_type == "changer_password":
            ancien = request.form.get("ancien_password", "")
            nouveau = request.form.get("nouveau_password", "")
            confirmation = request.form.get("confirmation_password", "")

            if not admin.check_password(ancien):
                flash("Ancien mot de passe incorrect.", "danger")
            elif len(nouveau) < 6:
                flash("Le nouveau mot de passe doit contenir au moins 6 caractères.", "danger")
            elif nouveau != confirmation:
                flash("Les mots de passe ne correspondent pas.", "danger")
            else:
                admin.set_password(nouveau)
                db.session.commit()
                flash("Mot de passe modifié avec succès.", "success")

        return redirect(url_for("admin.parametres"))

    return render_template("admin/parametres.html", admin=admin)

    # ------------------------------------------------------------------
# BILAN EMPLOYÉ (résumé individuel, semaine/mois/personnalisé)
# ------------------------------------------------------------------
@admin_bp.route("/bilan")
@admin_required
def bilan_employe():
    employe_id = request.args.get("employe_id", type=int)
    period_type = request.args.get("period", "mois")
    date_debut_str = request.args.get("date_debut", "")
    date_fin_str = request.args.get("date_fin", "")

    employes = Employe.query.order_by(Employe.nom.asc()).all()

    employe = None
    stats = None
    label = None

    if employe_id:
        employe = Employe.query.get_or_404(employe_id)

        if period_type == "personnalise" and date_debut_str and date_fin_str:
            debut = date.fromisoformat(date_debut_str)
            fin = date.fromisoformat(date_fin_str)
            label = f"Du {debut.strftime('%d/%m/%Y')} au {fin.strftime('%d/%m/%Y')}"
        else:
            if period_type not in ("semaine", "mois"):
                period_type = "mois"
            debut, fin, label = get_period_bounds(period_type, date.today())

        pointages = Pointage.query.filter(
            Pointage.employe_id == employe.id,
            Pointage.date_pointage >= debut,
            Pointage.date_pointage <= fin,
        ).all()
        nb_absences = Absence.query.filter(
            Absence.employe_id == employe.id,
            Absence.date_absence >= debut,
            Absence.date_absence <= fin,
        ).count()

        jours_presents = len([p for p in pointages if p.heure_arrivee])
        retards = len([p for p in pointages if p.en_retard])

        total_minutes = 0
        for p in pointages:
            d = p.calculer_heures_travaillees()
            if d:
                total_minutes += int(d.total_seconds() // 60)
        total_heures = f"{total_minutes // 60}h{total_minutes % 60:02d}"

        moyenne_minutes = total_minutes // jours_presents if jours_presents else 0
        moyenne_heures = f"{moyenne_minutes // 60}h{moyenne_minutes % 60:02d}"

        stats = {
            "jours_presents": jours_presents,
            "jours_absents": nb_absences,
            "retards": retards,
            "total_heures": total_heures,
            "moyenne_heures_jour": moyenne_heures,
        }

    return render_template(
        "admin/bilan_employe.html",
        employes=employes,
        employe=employe,
        stats=stats,
        period_type=period_type,
        date_debut=date_debut_str,
        date_fin=date_fin_str,
        label=label,
    )