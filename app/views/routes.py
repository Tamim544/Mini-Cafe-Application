from flask import render_template
from . import views_bp


@views_bp.route("/")
def index():
    return render_template("menu.html")


@views_bp.route("/login")
def login():
    return render_template("login.html")


@views_bp.route("/track/<order_ref>")
def track_order(order_ref):
    return render_template("order_status.html", order_ref=order_ref.upper())


@views_bp.route("/kitchen")
def kitchen():
    return render_template("kitchen.html")


@views_bp.route("/waiter")
def waiter():
    return render_template("waiter.html")


@views_bp.route("/admin")
def admin_dashboard():
    return render_template("admin/dashboard.html")


@views_bp.route("/admin/orders")
def admin_orders():
    return render_template("admin/orders.html")


@views_bp.route("/admin/menu")
def admin_menu():
    return render_template("admin/menu.html")


@views_bp.route("/admin/staff")
def admin_staff():
    return render_template("admin/staff.html")
