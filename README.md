# ☕ Mini Cafe — Full-Stack Cafe Management System

> A premium, real-time cafe ordering and management platform built with Flask, WebSockets, JWT authentication, and a sleek dark glassmorphism UI.

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=for-the-badge&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Socket.IO](https://img.shields.io/badge/Socket.IO-010101?style=for-the-badge&logo=socket.io&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

---

## 📌 Project Overview

Mini Cafe is a full-stack web application that simulates a real-world cafe ordering and management system. Customers can browse the menu, place orders, download receipts, and track their order status in real-time — all without needing an account. Staff members (Admin, Kitchen, Waiter) log in through a secure portal to manage the entire order lifecycle from placement to delivery.

---

## ✨ Advanced & Unique Features

### 🔴 Real-Time Order Tracking with WebSockets (Socket.IO)

This is the most technically advanced feature in the application. Every order update is broadcast **instantly** across all relevant parties using **Flask-SocketIO** with room-based architecture:

- **Role-based rooms**: On login, each staff member automatically joins their role room (`admin_room`, `kitchen_room`, `waiter_room`) by authenticating their JWT token over the WebSocket connection.
- **Order-specific rooms**: Customers join a dedicated room (`order_<REF>`) to receive live status updates for their specific order — no polling, no page refresh.
- **Bidirectional events**: When a kitchen staff member marks an order as "Preparing", the update is simultaneously broadcast to `admin_room`, `kitchen_room`, `waiter_room`, and the customer's `order_<REF>` room.

```python
# From app/sockets.py
@socketio.on("connect")
def handle_connect(auth):
    token = (auth or {}).get("token")
    decoded = decode_token(token)
    role = claims.get("role", "customer")
    join_room(f"{role}_room")  # Staff join role-based rooms
```

---

### 🔐 JWT Authentication with Automatic Token Refresh

Authentication uses **Flask-JWT-Extended** with a dual-token system:

- **Access tokens** expire in 8 hours; **refresh tokens** last 30 days.
- The frontend `api()` wrapper in `app.js` **transparently intercepts 401 responses**, automatically calls `/auth/refresh`, and retries the original request — the user never sees a login prompt during normal use.
- Role claims are embedded directly in the JWT payload, enabling **stateless role-based access control** on every API endpoint without a database lookup.

```javascript
// From static/js/app.js
if (res.status === 401 && Auth.refresh) {
    const rRes = await fetch('/auth/refresh', { ... });
    if (rRes.ok) {
        // Retry original request with new token transparently
        return fetch(path, { ...opts, headers });
    }
}
```

---

### 🔑 Role-Based Access Control (RBAC) Across 4 Roles

The system enforces a strict permission model with 4 distinct roles:

| Role     | Capabilities                                                                 |
|----------|------------------------------------------------------------------------------|
| Customer | Browse menu, place orders, track order, download receipt (no login needed)   |
| Kitchen  | View & accept/prepare/complete active orders (real-time)                     |
| Waiter   | View ready orders, mark as delivered                                         |
| Admin    | Full access: manage menu, staff, orders, view analytics dashboard            |

Order status transitions are **explicitly gated** per role on the backend — a waiter cannot accept or prepare an order, only deliver it:

```python
# From app/orders/routes.py
STATUS_FLOW = {
    "admin":   { "placed": ["accepted", "cancelled"], "accepted": ["preparing", "cancelled"], ... },
    "kitchen": { "placed": ["accepted"], "accepted": ["preparing"], "preparing": ["ready"] },
    "waiter":  { "ready": ["delivered"] },
}
```

---

### 📊 Live Admin Analytics Dashboard

The admin dashboard features **real-time charts** built with **Chart.js** showing:
- **Top selling items** — ranked by total units sold
- **Weekly revenue trend** — aggregated daily revenue for the past 7 days
- **Live order KPIs** — active order counts, revenue totals, today's order count

All data is pulled directly from the database with no hardcoded or synthetic values.

---

### 📄 Auto-Generated PDF Receipts

When a customer places an order, they can download a **professionally formatted PDF receipt** generated server-side using **fpdf2**:

- Includes order reference, customer name, table number, itemised line items, unit prices, subtotals, and grand total
- A custom `_sanitize_pdf_text()` function handles Unicode-to-Latin-1 conversion so names with special characters never crash the PDF renderer
- Served via Flask's `send_file()` as an inline `application/pdf` download

---

### 📱 QR Code Order Tracking

Every order automatically generates a **unique QR code** using the `qrcode[pil]` library:

- The QR code encodes the direct tracking URL `/track/<ORDER_REF>`
- Displayed in the success modal immediately after ordering
- Customers can scan with any phone camera to jump straight to their live order status page
- QR images are stored in `static/qrcodes/` and served statically

---

### 🛒 Item Detail Modal with Quantity Picker

Instead of simple inline `+` buttons (which had cross-browser event delegation issues), clicking any menu item opens a **full-screen item detail modal** featuring:

- Large item image or emoji
- Full description
- A quantity selector with `−` / `+` controls
- A dynamic "Add to Cart — $X.XX" button that updates the total as quantity changes

This pattern eliminates all event bubbling conflicts and provides a much richer mobile-friendly UX.

---

### 🔄 Persistent Order Tracking Across Sessions

After placing an order, the order reference is saved to **`localStorage`**. When the customer returns to the menu page later, the tracking input is **automatically pre-filled** with their last order reference — so they can instantly check status without memorising or writing down the code.

---

### 🖼️ Admin Image Upload for Menu Items

Admin users can upload custom images for any menu item directly from the admin menu management page:

- Images are uploaded via `multipart/form-data`, renamed with a UUID to avoid collisions, and saved to `static/uploads/`
- The `image_url` is stored in the database and rendered in both the customer menu and admin views
- Falls back to contextual emoji (e.g. ☕ for coffee, 🍕 for pizza) when no image is provided

---

### 🏗️ Flask Application Factory Pattern with Blueprints

The app uses the **application factory pattern** (`create_app()`) for clean separation of concerns and easy testability:

```
app/
├── auth/        → JWT login, token refresh
├── menu/        → Menu API + image uploads
├── orders/      → Order lifecycle API
├── admin/       → Admin-only management APIs
├── views/       → Page rendering (Jinja2 templates)
├── models.py    → SQLAlchemy ORM models
├── sockets.py   → WebSocket event handlers
└── extensions.py → Shared extensions (db, jwt, bcrypt, socketio)
```

Each module is a self-contained **Flask Blueprint** registered at startup — zero circular imports.

---

### 🗃️ Price Snapshot Pattern in Order Items

`OrderItem` stores `item_name` and `unit_price` as a **snapshot at order time**, not as foreign key references to the current menu price. This means:

- Historical receipts always show the price the customer actually paid
- Admin can freely change menu prices without corrupting past order records
- This mirrors how production-grade e-commerce systems work

---

### 🐳 Docker & Docker Compose Support

The application is fully containerised:

- **`Dockerfile`** — Python 3.12-slim base with OS-level Pillow dependencies (libjpeg, zlib) for QR image generation
- **`docker-compose.yml`** — Named volumes persist the SQLite database and QR codes across container restarts
- Environment variables for `SECRET_KEY` and `JWT_SECRET_KEY` keep secrets out of source code

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- pip

### Local Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd "Mini cafe application"

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment (optional — defaults work for dev)
cp .env.example .env

# 5. Run the server
python run.py
```

The app will start at **http://localhost:5001**

### Docker Setup

```bash
docker-compose up --build
```

App available at **http://localhost:5000**

---

## 🔑 Default Credentials

| Role  | Username | Password   |
|-------|----------|------------|
| Admin | `admin`  | `admin123` |

> ⚠️ **Change these credentials immediately in any production deployment.**

Additional staff accounts (kitchen, waiter) are created through the Admin → Staff Management panel.

---

## 📐 Tech Stack

| Layer        | Technology                                         |
|--------------|----------------------------------------------------|
| Backend      | Flask 3.0, Flask-SocketIO, Flask-JWT-Extended      |
| Database     | SQLite + SQLAlchemy ORM + Flask-Migrate            |
| Auth         | JWT (access + refresh tokens), Flask-Bcrypt        |
| Real-time    | Socket.IO 4.x (WebSockets with threading mode)     |
| PDF          | fpdf2                                              |
| QR Codes     | qrcode[pil] + Pillow                               |
| Frontend     | Vanilla JS (ES6+), CSS custom properties           |
| UI Style     | Dark glassmorphism, CSS animations, Chart.js       |
| Deployment   | Docker, Docker Compose                             |

---

## 📁 Project Structure

```
Mini cafe application/
├── app/
│   ├── __init__.py          # App factory + DB seeding
│   ├── models.py            # SQLAlchemy models (User, MenuItem, Order, OrderItem)
│   ├── sockets.py           # WebSocket event handlers
│   ├── extensions.py        # Shared extension instances
│   ├── utils.py             # QR code + PDF receipt generation
│   ├── auth/                # JWT auth endpoints
│   ├── menu/                # Menu API + image uploads
│   ├── orders/              # Order CRUD + status transitions
│   ├── admin/               # Admin management APIs
│   └── views/               # Jinja2 page routes
├── static/
│   ├── css/main.css         # Design system + glassmorphism theme
│   ├── js/
│   │   ├── app.js           # Auth, navbar, JWT refresh, toasts
│   │   ├── menu_v6.js       # Menu, cart, item modal, order flow
│   │   ├── kitchen.js       # Kitchen dashboard + real-time updates
│   │   ├── waiter.js        # Waiter dashboard
│   │   └── socket.js        # Socket.IO client initialisation
│   └── qrcodes/             # Auto-generated QR code images
├── templates/
│   ├── base.html            # Shared layout + navbar
│   ├── menu.html            # Customer menu + cart
│   ├── order_status.html    # Real-time order tracking
│   ├── login.html           # Staff login portal
│   ├── kitchen.html         # Kitchen view
│   ├── waiter.html          # Waiter view
│   └── admin/               # Admin dashboard, orders, menu, staff
├── config.py                # Dev/Prod config classes
├── run.py                   # Entry point
├── Dockerfile
└── docker-compose.yml
```

---

## 🔗 API Endpoints

| Method | Endpoint                          | Auth Required | Description                    |
|--------|-----------------------------------|---------------|--------------------------------|
| POST   | `/auth/login`                     | No            | Login, receive JWT tokens      |
| POST   | `/auth/refresh`                   | Refresh token | Get new access token           |
| GET    | `/api/menu`                       | No            | Get full menu by category      |
| POST   | `/api/orders`                     | No            | Place a new order              |
| GET    | `/api/orders/<ref>`               | No            | Get order status (for tracking)|
| GET    | `/api/orders`                     | Staff JWT     | List orders (role-filtered)    |
| PATCH  | `/api/orders/<ref>/status`        | Staff JWT     | Update order status            |
| GET    | `/api/orders/<ref>/receipt`       | No            | Download PDF receipt           |
| POST   | `/api/menu/items`                 | Admin JWT     | Add menu item                  |
| PUT    | `/api/menu/items/<id>`            | Admin JWT     | Edit menu item + image upload  |
| DELETE | `/api/menu/items/<id>`            | Admin JWT     | Delete menu item               |

---

## 📸 Pages at a Glance

| Page              | Route              | Access    |
|-------------------|--------------------|-----------|
| Customer Menu     | `/`                | Public    |
| Order Tracking    | `/track/<ref>`     | Public    |
| Staff Login       | `/login`           | Public    |
| Kitchen Display   | `/kitchen`         | Kitchen+  |
| Waiter Display    | `/waiter`          | Waiter+   |
| Admin Dashboard   | `/admin`           | Admin     |
| Admin Orders      | `/admin/orders`    | Admin     |
| Admin Menu Mgmt   | `/admin/menu`      | Admin     |
| Admin Staff Mgmt  | `/admin/staff`     | Admin     |

---

## 📝 License

This project is for educational and portfolio purposes.

---

> Built with ☕ and a lot of attention to real-world engineering patterns.
