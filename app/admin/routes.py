from functools import wraps
from datetime import datetime, timedelta, timezone
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy import func
from . import admin_bp
from ..extensions import db, bcrypt
from ..models import User, Order, OrderItem


# ── Guard ─────────────────────────────────────────────────────────────────────

def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        if get_jwt().get("role") != "admin":
            return jsonify({"error": "Admin access required."}), 403
        return fn(*args, **kwargs)
    return wrapper


# ── Analytics ─────────────────────────────────────────────────────────────────

@admin_bp.route("/analytics", methods=["GET"])
@admin_required
def analytics():
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    completed = ["delivered", "ready"]

    total_revenue = (
        db.session.query(func.sum(Order.total))
        .filter(Order.status.in_(completed))
        .scalar() or 0
    )
    today_revenue = (
        db.session.query(func.sum(Order.total))
        .filter(Order.placed_at >= today, Order.status.in_(completed))
        .scalar() or 0
    )
    total_orders = Order.query.count()
    today_orders = Order.query.filter(Order.placed_at >= today).count()

    status_counts = dict(
        db.session.query(Order.status, func.count(Order.id))
        .group_by(Order.status)
        .all()
    )

    top_items = (
        db.session.query(OrderItem.item_name, func.sum(OrderItem.quantity).label("qty"))
        .group_by(OrderItem.item_name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(6)
        .all()
    )

    # Orders per hour for today
    hourly = []
    for h in range(24):
        start = today + timedelta(hours=h)
        end = start + timedelta(hours=1)
        count = Order.query.filter(Order.placed_at >= start, Order.placed_at < end).count()
        hourly.append({"hour": h, "count": count})

    # Last 7 days daily revenue
    weekly = []
    for d in range(6, -1, -1):
        day_start = today - timedelta(days=d)
        day_end = day_start + timedelta(days=1)
        rev = (
            db.session.query(func.sum(Order.total))
            .filter(Order.placed_at >= day_start, Order.placed_at < day_end, Order.status.in_(completed))
            .scalar() or 0
        )
        weekly.append({"date": day_start.strftime("%a"), "revenue": round(float(rev), 2)})

    return jsonify(
        {
            "total_revenue": round(float(total_revenue), 2),
            "today_revenue": round(float(today_revenue), 2),
            "total_orders": total_orders,
            "today_orders": today_orders,
            "status_breakdown": status_counts,
            "top_items": [{"name": n, "quantity": int(q)} for n, q in top_items],
            "hourly_orders": hourly,
            "weekly_revenue": weekly,
        }
    ), 200


# ── Staff management ──────────────────────────────────────────────────────────

@admin_bp.route("/staff", methods=["GET"])
@admin_required
def list_staff():
    staff = User.query.filter(User.role != "admin").all()
    return jsonify([u.to_dict() for u in staff]), 200


@admin_bp.route("/staff", methods=["POST"])
@admin_required
def create_staff():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    role = data.get("role", "")

    if not username or not password or not role:
        return jsonify({"error": "username, password, and role are required."}), 400
    if role not in ("kitchen", "waiter"):
        return jsonify({"error": "role must be 'kitchen' or 'waiter'."}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists."}), 409

    user = User(
        username=username,
        password_hash=bcrypt.generate_password_hash(password).decode(),
        role=role,
    )
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201


@admin_bp.route("/staff/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_staff(user_id):
    user = db.get_or_404(User, user_id)
    if user.role == "admin":
        return jsonify({"error": "Cannot delete admin account."}), 403
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Staff account removed."}), 200


@admin_bp.route("/staff/<int:user_id>/toggle", methods=["PATCH"])
@admin_required
def toggle_staff(user_id):
    user = db.get_or_404(User, user_id)
    if user.role == "admin":
        return jsonify({"error": "Cannot deactivate admin."}), 403
    user.is_active = not user.is_active
    db.session.commit()
    return jsonify(user.to_dict()), 200
