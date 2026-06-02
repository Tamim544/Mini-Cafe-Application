import io
from datetime import datetime, timezone
from flask import request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt
from . import orders_bp
from ..extensions import db, socketio
from ..models import Order, OrderItem, MenuItem
from ..utils import generate_qr_code, generate_order_ref, generate_pdf_receipt

# ── Role-based allowed status transitions ─────────────────────────────────────
STATUS_FLOW = {
    "admin": {
        "placed":    ["accepted", "cancelled"],
        "accepted":  ["preparing", "cancelled"],
        "preparing": ["ready",    "cancelled"],
        "ready":     ["delivered","cancelled"],
        "delivered": [],
        "cancelled": [],
    },
    "kitchen": {
        "placed":    ["accepted"],
        "accepted":  ["preparing"],
        "preparing": ["ready"],
    },
    "waiter": {
        "ready": ["delivered"],
    },
}


# ── Place order (public) ──────────────────────────────────────────────────────

@orders_bp.route("/orders", methods=["POST"])
def place_order():
    data = request.get_json(silent=True) or {}
    customer_name = data.get("customer_name", "").strip()
    if not customer_name:
        return jsonify({"error": "customer_name is required."}), 400

    items_data = data.get("items", [])
    if not items_data:
        return jsonify({"error": "Order must contain at least one item."}), 400

    total = 0.0
    order_items = []
    for entry in items_data:
        menu_item = MenuItem.query.get(entry.get("id"))
        if not menu_item or not menu_item.available:
            return jsonify({"error": f"Item id={entry.get('id')} not available."}), 400
        try:
            qty = int(entry.get("quantity", 1))
            assert qty >= 1
        except (ValueError, AssertionError):
            return jsonify({"error": "Quantity must be a positive integer."}), 400

        total += menu_item.price * qty
        order_items.append(
            OrderItem(
                menu_item_id=menu_item.id,
                item_name=menu_item.name,
                quantity=qty,
                unit_price=menu_item.price,
            )
        )

    order_ref = generate_order_ref()
    order = Order(
        order_ref=order_ref,
        customer_name=customer_name,
        table_number=data.get("table_number", ""),
        status="placed",
        total=round(total, 2),
        notes=data.get("notes", ""),
        placed_at=datetime.now(timezone.utc),
    )
    db.session.add(order)
    db.session.flush()

    for oi in order_items:
        oi.order_id = order.id
        db.session.add(oi)

    qr_path = generate_qr_code(order_ref)
    order.qr_code_path = qr_path
    db.session.commit()

    order_dict = order.to_dict()
    # Notify staff in real-time
    socketio.emit("new_order", order_dict, room="admin_room")
    socketio.emit("new_order", order_dict, room="kitchen_room")

    return jsonify(order_dict), 201


# ── Get single order (public — for QR tracking) ──────────────────────────────

@orders_bp.route("/orders/<order_ref>", methods=["GET"])
def get_order(order_ref):
    order = Order.query.filter_by(order_ref=order_ref.upper()).first_or_404()
    return jsonify(order.to_dict()), 200


# ── List orders (staff only) ──────────────────────────────────────────────────

@orders_bp.route("/orders", methods=["GET"])
@jwt_required()
def get_orders():
    role = get_jwt().get("role")
    status_filter = request.args.get("status")
    query = Order.query

    if role == "kitchen":
        if status_filter:
            query = query.filter(Order.status == status_filter)
        else:
            query = query.filter(Order.status.in_(["placed", "accepted", "preparing"]))
    elif role == "waiter":
        if status_filter:
            query = query.filter(Order.status == status_filter)
        else:
            query = query.filter(Order.status == "ready")
    elif role == "admin":
        if status_filter:
            query = query.filter(Order.status == status_filter)
    else:
        return jsonify({"error": "Unauthorized."}), 403

    orders = query.order_by(Order.placed_at.desc()).all()
    return jsonify([o.to_dict() for o in orders]), 200


# ── Update order status (staff only, role-gated transitions) ─────────────────

@orders_bp.route("/orders/<order_ref>/status", methods=["PATCH"])
@jwt_required()
def update_status(order_ref):
    role = get_jwt().get("role")
    order = Order.query.filter_by(order_ref=order_ref.upper()).first_or_404()
    data = request.get_json(silent=True) or {}
    new_status = data.get("status", "").lower()

    allowed = STATUS_FLOW.get(role, {}).get(order.status, [])
    if new_status not in allowed:
        return jsonify(
            {"error": f"Role '{role}' cannot move order from '{order.status}' to '{new_status}'."}
        ), 403

    now = datetime.now(timezone.utc)
    order.status = new_status
    if new_status == "accepted":
        order.accepted_at = now
    elif new_status == "preparing":
        order.preparing_at = now
    elif new_status == "ready":
        order.ready_at = now
    elif new_status == "delivered":
        order.delivered_at = now

    db.session.commit()
    order_dict = order.to_dict()

    # Broadcast to all staff rooms and the specific order-tracking room
    for room in ("admin_room", "kitchen_room", "waiter_room", f"order_{order.order_ref}"):
        socketio.emit("order_status_update", order_dict, room=room)

    return jsonify(order_dict), 200


# ── PDF receipt download ──────────────────────────────────────────────────────

@orders_bp.route("/orders/<order_ref>/receipt", methods=["GET"])
def get_receipt(order_ref):
    order = Order.query.filter_by(order_ref=order_ref.upper()).first_or_404()
    pdf_bytes = generate_pdf_receipt(order)
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"receipt_{order.order_ref}.pdf",
    )
