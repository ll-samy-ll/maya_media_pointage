from datetime import datetime, date, time
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class Admin(UserMixin, db.Model):
    """Accès administrateur : juste un mot de passe, pas de profil."""

    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # Paramètre de l'entreprise : heure d'arrivée attendue, utilisée pour
    # calculer automatiquement les retards des employés.
    heure_arrivee_prevue = db.Column(db.Time, nullable=False, default=time(8, 0))

    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return f"admin-{self.id}"

    def __repr__(self):
        return f"<Admin id={self.id}>"


class Employe(UserMixin, db.Model):
    """Un employé de l'entreprise."""

    __tablename__ = "employes"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)

    poste = db.Column(db.String(100), nullable=True)
    actif = db.Column(db.Boolean, default=True, nullable=False)

    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    # Relations : un employé a plusieurs pointages et plusieurs absences
    pointages = db.relationship(
        "Pointage", backref="employe", lazy=True, cascade="all, delete-orphan"
    )
    absences = db.relationship(
        "Absence", backref="employe", lazy=True, cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def has_password(self):
        return self.password_hash is not None

    def get_id(self):
        # Préfixe pour différencier l'ID employé de l'ID admin dans Flask-Login
        return f"employe-{self.id}"

    def __repr__(self):
        return f"<Employe {self.nom}>"


class Pointage(db.Model):
    """Un pointage journalier (arrivée + départ) pour un employé.
    Un seul pointage par employé et par jour (contrainte d'unicité)."""

    __tablename__ = "pointages"
    __table_args__ = (
        db.UniqueConstraint("employe_id", "date_pointage", name="uq_employe_date"),
    )

    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey("employes.id"), nullable=False)

    date_pointage = db.Column(db.Date, nullable=False, default=date.today)

    heure_arrivee = db.Column(db.Time, nullable=True)
    heure_depart = db.Column(db.Time, nullable=True)

    # Calculé automatiquement à l'enregistrement du pointage d'arrivée,
    # en comparant avec Admin.heure_arrivee_prevue
    en_retard = db.Column(db.Boolean, default=False, nullable=False)

    def calculer_heures_travaillees(self):
        """Retourne les heures travaillées sous forme de timedelta, ou None
        si l'employé n'a pas encore pointé son départ."""
        if self.heure_arrivee and self.heure_depart:
            arrivee = datetime.combine(self.date_pointage, self.heure_arrivee)
            depart = datetime.combine(self.date_pointage, self.heure_depart)
            return depart - arrivee
        return None

    def __repr__(self):
        return f"<Pointage {self.employe_id} - {self.date_pointage}>"


class Absence(db.Model):
    """Une déclaration d'absence pour un employé."""

    __tablename__ = "absences"

    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey("employes.id"), nullable=False)

    date_absence = db.Column(db.Date, nullable=False, default=date.today)
    motif = db.Column(db.String(255), nullable=True)

    date_declaration = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Absence {self.employe_id} - {self.date_absence}>"