from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user


def employee_required(f):
    """Autorise l'accès uniquement aux employés connectés."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.get_id().startswith("employe-"):
            flash("Veuillez vous connecter en tant qu'employé.", "warning")
            return redirect(url_for("auth.login_employee"))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Autorise l'accès uniquement à l'administrateur connecté."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.get_id().startswith("admin-"):
            flash("Veuillez vous connecter en tant qu'administrateur.", "warning")
            return redirect(url_for("auth.login_admin"))
        return f(*args, **kwargs)
    return decorated_function