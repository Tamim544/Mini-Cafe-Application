import os
from flask import Flask
from config import config
from .extensions import db, jwt, bcrypt, socketio, migrate


def create_app(config_name: str = "default") -> Flask:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "templates"),
        static_folder=os.path.join(base_dir, "static"),
    )
    app.config.from_object(config[config_name])

    # ── Extensions ────────────────────────────────────────
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*", async_mode="threading")
    migrate.init_app(app, db)

    # ── Blueprints ────────────────────────────────────────
    from .auth import auth_bp
    from .menu import menu_bp
    from .orders import orders_bp
    from .admin import admin_bp
    from .views import views_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(views_bp)

    # ── Socket handlers (import to register) ──────────────
    from . import sockets  # noqa: F401

    # ── DB + Seed ─────────────────────────────────────────
    with app.app_context():
        db.create_all()
        _seed_database()

    return app


def _seed_database() -> None:
    """Create the bootstrap admin account and demo items on first run.

    Staff accounts should be created through the admin UI.
    """
    from .models import User, Category, MenuItem
    from .extensions import bcrypt as _bcrypt

    # Bootstrap admin — needed to access the system and create everything else
    if not User.query.filter_by(username="admin").first():
        db.session.add(
            User(
                username="admin",
                password_hash=_bcrypt.generate_password_hash("admin123").decode(),
                role="admin",
            )
        )
        db.session.commit()

    # Categories
    cat_names = ["Hot Drinks", "Cold Drinks", "Food", "Desserts"]
    cat_map: dict[str, Category] = {}
    for name in cat_names:
        cat = Category.query.filter_by(name=name).first()
        if not cat:
            cat = Category(name=name)
            db.session.add(cat)
            db.session.flush()
        cat_map[name] = cat

    # Menu items (migrated from original data.json)
    seed_items = [
        ("Coffee", 2.50, "Rich, bold espresso blend served hot.", "Hot Drinks"),
        ("Tea", 2.00, "Freshly brewed loose-leaf tea.", "Hot Drinks"),
        ("Iced Latte", 3.50, "Espresso over ice with silky oat milk.", "Cold Drinks"),
        ("Lemonade", 2.50, "Fresh-squeezed with a hint of mint.", "Cold Drinks"),
        ("Sandwich", 5.00, "Toasted club sandwich with fillings of the day.", "Food"),
        ("Pizza", 10.00, "Stone-baked personal pizza, your choice of toppings.", "Food"),
        ("Cake", 3.50, "Homemade slice — ask staff for today's flavour.", "Desserts"),
        ("Brownie", 2.75, "Warm chocolate fudge brownie.", "Desserts"),
    ]
    for name, price, desc, cat_name in seed_items:
        if not MenuItem.query.filter_by(name=name).first():
            db.session.add(
                MenuItem(
                    name=name,
                    price=price,
                    description=desc,
                    category_id=cat_map[cat_name].id,
                )
            )

    db.session.commit()
