import os
from dotenv import load_dotenv
from app import create_app
from app.extensions import socketio

load_dotenv()

config_name = os.environ.get("FLASK_ENV", "development")
app = create_app(config_name)

if __name__ == "__main__":
    print("🍵  Mini Cafe starting on http://localhost:5001")
    print("    Admin panel → /admin  (bootstrap: admin / admin123)")
    print("    Create staff & menu items from the admin dashboard.")
    socketio.run(
        app,
        debug=app.config.get("DEBUG", True),
        host="0.0.0.0",
        port=5001,
        allow_unsafe_werkzeug=True,
    )
