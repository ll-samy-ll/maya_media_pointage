from datetime import date, timedelta, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash

from extensions import db
from models import Employe, Pointage, Absence
from decorators import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

MOIS_FR = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
]

# --- Correctif temporaire de fuseau horaire ---
# Railway héberge le serveur en UTC, alors que l'entreprise est sur le
# fuseau UTC+1. En attendant une