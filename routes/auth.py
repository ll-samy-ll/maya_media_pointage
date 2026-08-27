from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from extensions import db
from models import Admin, Employe

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/", methods=["GET"])
def index():
    return redirect(url_for("auth.login_employee"))


# ------------------------------------------------------------------
# CONNEXION EMPLOYÉ (onglet "Se connecter")
# ------------------------------------------------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login_employee():
    if current_user.is_authenticated:
        if current_user.get_id().startswith("employe-"):
            return redirect(url_for("employee.dashboard"))
        elif current_user.get_id().startswith("admin-"):
            return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        nom = request.form.get("nom", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        employe = Employe.query.filter_by(email=email).first()

        if not employe or employe.nom.strip().lower() != nom.lower():
            flash("Nom ou e-mail incorrect.", "danger")
            return render_template("auth/login_employee.html", active_tab="login")

        if not employe.actif:
            flash("Compte désactivé, contactez votre administrateur.", "danger")
            return render_template("auth/login_employee.html", active_tab="login")

        if not employe.has_password():
            flash("Vous n'avez pas encore de compte. Utilisez l'onglet Inscription.", "warning")
            return render_template("auth/login_employee.html", active_tab="signup")

        if not employe.check_password(password):
            flash("Mot de passe incorrect.", "danger")
            return render_template("auth/login_employee.html", active_tab="login")

        login_user(employe)
        flash(f"Bienvenue, {employe.nom} !", "success")
        return redirect(url_for("employee.dashboard"))

    return render_template("auth/login_employee.html", active_tab="login")


# ------------------------------------------------------------------
# INSCRIPTION EMPLOYÉ (onglet "S'inscrire")
# L'admin doit avoir pré-créé l'employé (nom + email) au préalable.
# ------------------------------------------------------------------
@auth_bp.route("/signup", methods=["POST"])
def signup_employee():
    nom = request.form.get("nom", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")

    employe = Employe.query.filter_by(email=email).first()

    if not employe or employe.nom.strip().lower() != nom.lower():
        flash("Aucun compte ne correspond à ce nom et cet e-mail. Contactez votre administrateur.", "danger")
        return render_template("auth/login_employee.html", active_tab="signup")

    if not employe.actif:
        flash("Compte désactivé, contactez votre administrateur.", "danger")
        return render_template("auth/login_employee.html", active_tab="signup")

    if employe.has_password():
        flash("Ce compte existe déjà. Utilisez l'onglet Connexion.", "warning")
        return render_template("auth/login_employee.html", active_tab="login")

    if len(password) < 6:
        flash("Le mot de passe doit contenir au moins 6 caractères.", "danger")
        return render_template("auth/login_employee.html", active_tab="signup")

    if password != confirm:
        flash("Les mots de passe ne correspondent pas.", "danger")
        return render_template("auth/login_employee.html", active_tab="signup")

    employe.set_password(password)
    db.session.commit()

    login_user(employe)
    flash("Compte créé avec succès. Bienvenue !", "success")
    return redirect(url_for("employee.dashboard"))


# ------------------------------------------------------------------
# CONNEXION ADMIN
# ------------------------------------------------------------------
@auth_bp.route("/admin/login", methods=["GET", "POST"])
def login_admin():
    if current_user.is_authenticated:
        if current_user.get_id().startswith("admin-"):
            return redirect(url_for("admin.dashboard"))
        elif current_user.get_id().startswith("employe-"):
            return redirect(url_for("employee.dashboard"))

    if request.method == "POST":
        password = request.form.get("password", "")
        admin = Admin.query.first()

        if not admin or not admin.check_password(password):
            flash("Mot de passe administrateur incorrect.", "danger")
            return render_template("auth/login_admin.html")

        login_user(admin)
        flash("Connexion réussie.", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("auth/login_admin.html")


# ------------------------------------------------------------------
# DÉCONNEXION
# ------------------------------------------------------------------
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Vous avez été déconnecté.", "info")
    return redirect(url_for("auth.login_employee"))

# ------------------------------------------------------------------
# API - Suggestions de noms d'employés (autocomplétion)
# ------------------------------------------------------------------
@auth_bp.route("/api/employe-noms")
def api_employe_noms():
    from flask import jsonify
    noms = [e.nom for e in Employe.query.filter_by(actif=True).order_by(Employe.nom.asc()).all()]
    return jsonify(noms)