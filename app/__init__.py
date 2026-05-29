from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import Usuario
        return Usuario.query.get(int(user_id))

    from app.routes.emprestimos import bp as emp_bp
    from app.routes.equipamentos import bp as equip_bp
    from app.routes.relatorios import bp as rel_bp
    from app.routes.inventario import bp as inv_bp
    from app.routes.manutencoes import bp as man_bp
    from app.routes.chamados import bp as cham_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.usuarios import bp as usr_bp

    app.register_blueprint(emp_bp)
    app.register_blueprint(equip_bp)
    app.register_blueprint(rel_bp)
    app.register_blueprint(inv_bp)
    app.register_blueprint(man_bp)
    app.register_blueprint(cham_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(usr_bp)

    from app.scheduler import iniciar_scheduler
    iniciar_scheduler(app)

    # Cria tabelas automaticamente se não existirem
    with app.app_context():
        db.create_all()

    return app