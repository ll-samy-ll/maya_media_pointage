from flask import Flask, render_template
from config import Config
from extensions import db, login_manager, migrate
from company_config import COMPANY_NAME


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = "auth.login_employee"

    from models import Admin, Employe

    @login_manager.user_loader
    def load_user(user_id):
        if user_id.startswith("admin-"):
            return Admin.query.get(int(user_id.split("-")[1]))
        elif user_id.startswith("employe-"):
            return Employe.query.get(int(user_id.split("-")[1]))
        return None

    from routes.auth import auth_bp
    from routes.employee import employee_bp
    from routes.admin import admin_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(admin_bp)

    @app.context_processor
    def inject_company():
        return dict(company_name=COMPANY_NAME)

    @app.route("/")
    def landing():
        return render_template("landing.html")

    @app.route("/health")
    def health():
        return {"status": "ok", "message": "Le serveur Flask fonctionne."}

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)  