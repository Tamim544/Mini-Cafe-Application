from flask import Blueprint

menu_bp = Blueprint("menu", __name__, url_prefix="/api")

from . import routes  # noqa: E402, F401
