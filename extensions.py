from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

# Instances des extensions, initialisées ici pour éviter les imports circulaires.
# Elles seront reliées à l'app via extension.init_app(app) dans app.py

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()