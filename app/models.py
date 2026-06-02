from datetime import datetime, timezone
from .extensions import db


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="waiter")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    items = db.relationship("MenuItem", backref="category", lazy=True)

    def to_dict(self):
        return {"id": self.id, "name": self.name}


class MenuItem(db.Model):
    __tablename__ = "menu_items"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(256), default="")
    image_url = db.Column(db.String(256), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "description": self.description,
            "image_url": self.image_url,
            "category": self.category.name if self.category else None,
            "category_id": self.category_id,
            "available": self.available,
        }


class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    order_ref = db.Column(db.String(12), unique=True, nullable=False)
    customer_name = db.Column(db.String(80), nullable=False)
    table_number = db.Column(db.String(10), default="")
    status = db.Column(db.String(20), nullable=False, default="placed")
    total = db.Column(db.Float, nullable=False)
    notes = db.Column(db.String(256), default="")
    qr_code_path = db.Column(db.String(256), default="")
    placed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    accepted_at = db.Column(db.DateTime, nullable=True)
    preparing_at = db.Column(db.DateTime, nullable=True)
    ready_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    items = db.relationship(
        "OrderItem", backref="order", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "order_ref": self.order_ref,
            "customer_name": self.customer_name,
            "table_number": self.table_number,
            "status": self.status,
            "total": self.total,
            "notes": self.notes,
            "qr_code_path": self.qr_code_path,
            "placed_at": self.placed_at.isoformat() if self.placed_at else None,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "preparing_at": self.preparing_at.isoformat() if self.preparing_at else None,
            "ready_at": self.ready_at.isoformat() if self.ready_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "items": [item.to_dict() for item in self.items],
        }


class OrderItem(db.Model):
    __tablename__ = "order_items"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"), nullable=True)
    item_name = db.Column(db.String(120), nullable=False)  # snapshot at order time
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "item_name": self.item_name,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "subtotal": round(self.quantity * self.unit_price, 2),
        }
