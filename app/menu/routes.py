from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from . import menu_bp
from ..extensions import db
from ..models import MenuItem, Category


# ── Helper decorator ──────────────────────────────────────────────────────────

def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        if get_jwt().get("role") != "admin":
            return jsonify({"error": "Admin access required."}), 403
        return fn(*args, **kwargs)
    return wrapper


# ── Menu endpoints ────────────────────────────────────────────────────────────

@menu_bp.route("/menu", methods=["GET"])
def get_menu():
    """Public: available items grouped by category."""
    result = []
    for cat in Category.query.all():
        items = MenuItem.query.filter_by(category_id=cat.id, available=True).all()
        if items:
            result.append(
                {"category": cat.name, "category_id": cat.id, "items": [i.to_dict() for i in items]}
            )
    return jsonify(result), 200


@menu_bp.route("/menu/all", methods=["GET"])
@admin_required
def get_all_menu():
    """Admin: all items including unavailable, grouped by category."""
    result = []
    for cat in Category.query.all():
        items = MenuItem.query.filter_by(category_id=cat.id).all()
        result.append(
            {"category": cat.name, "category_id": cat.id, "items": [i.to_dict() for i in items]}
        )
    return jsonify(result), 200


import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

def save_image(file_obj) -> str:
    """Save an uploaded image and return its relative URL path."""
    if not file_obj or file_obj.filename == '':
        return None
    # Ensure upload directory exists
    upload_dir = os.path.join(current_app.static_folder, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    ext = os.path.splitext(file_obj.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(upload_dir, unique_filename)
    file_obj.save(file_path)
    return f"/static/uploads/{unique_filename}"


@menu_bp.route("/menu", methods=["POST"])
@admin_required
def create_item():
    name = request.form.get("name", "").strip()
    price_raw = request.form.get("price")
    category_id = request.form.get("category_id")

    if not name or price_raw is None or not category_id:
        return jsonify({"error": "name, price, and category_id are required."}), 400

    try:
        price = float(price_raw)
        assert price >= 0
    except (ValueError, AssertionError):
        return jsonify({"error": "price must be a non-negative number."}), 400

    if not Category.query.get(category_id):
        return jsonify({"error": "Category not found."}), 404

    image_file = request.files.get("image")
    image_url = save_image(image_file) if image_file else None

    item = MenuItem(
        name=name,
        price=price,
        description=request.form.get("description", ""),
        category_id=category_id,
        available=request.form.get("available", "true").lower() == "true",
        image_url=image_url
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


@menu_bp.route("/menu/<int:item_id>", methods=["PUT"])
@admin_required
def update_item(item_id):
    item = db.get_or_404(MenuItem, item_id)

    if "name" in request.form:
        item.name = request.form.get("name").strip()
    if "price" in request.form:
        try:
            price = float(request.form.get("price"))
            assert price >= 0
            item.price = price
        except (ValueError, AssertionError):
            return jsonify({"error": "price must be a non-negative number."}), 400
    if "description" in request.form:
        item.description = request.form.get("description")
    if "category_id" in request.form:
        if not Category.query.get(request.form.get("category_id")):
            return jsonify({"error": "Category not found."}), 404
        item.category_id = request.form.get("category_id")
    if "available" in request.form:
        item.available = request.form.get("available").lower() == "true"

    image_file = request.files.get("image")
    if image_file and image_file.filename != '':
        new_image_url = save_image(image_file)
        if new_image_url:
            # Optionally, you could delete the old image file here
            item.image_url = new_image_url

    db.session.commit()
    return jsonify(item.to_dict()), 200


@menu_bp.route("/menu/<int:item_id>", methods=["DELETE"])
@admin_required
def delete_item(item_id):
    item = db.get_or_404(MenuItem, item_id)
    name = item.name
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": f'"{name}" removed from menu.'}), 200


@menu_bp.route("/menu/<int:item_id>/toggle", methods=["PATCH"])
@admin_required
def toggle_item(item_id):
    item = db.get_or_404(MenuItem, item_id)
    item.available = not item.available
    db.session.commit()
    return jsonify(item.to_dict()), 200


# ── Category endpoints ────────────────────────────────────────────────────────

@menu_bp.route("/categories", methods=["GET"])
def get_categories():
    return jsonify([c.to_dict() for c in Category.query.all()]), 200


@menu_bp.route("/categories", methods=["POST"])
@admin_required
def create_category():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "name is required."}), 400
    if Category.query.filter_by(name=name).first():
        return jsonify({"error": "Category already exists."}), 409
    cat = Category(name=name)
    db.session.add(cat)
    db.session.commit()
    return jsonify(cat.to_dict()), 201
