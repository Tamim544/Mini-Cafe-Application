import logging
from flask_socketio import join_room, leave_room
from flask_jwt_extended import decode_token
from .extensions import socketio

logger = logging.getLogger(__name__)


@socketio.on("connect")
def handle_connect(auth):
    """Client connects; join their role-based room if they have a JWT."""
    token = (auth or {}).get("token")
    if token:
        try:
            decoded = decode_token(token)
            claims = decoded.get("additional_claims") or decoded
            role = claims.get("role", "customer")
            join_room(f"{role}_room")
            logger.info("Client joined %s_room", role)
        except Exception as exc:
            logger.warning("Invalid token on connect: %s", exc)
    return True


@socketio.on("join_order")
def handle_join_order(data):
    """Customer joins a specific order room to receive live status updates."""
    order_ref = (data or {}).get("order_ref")
    if order_ref:
        join_room(f"order_{order_ref}")
        logger.info("Client tracking order %s", order_ref)


@socketio.on("leave_order")
def handle_leave_order(data):
    order_ref = (data or {}).get("order_ref")
    if order_ref:
        leave_room(f"order_{order_ref}")


@socketio.on("disconnect")
def handle_disconnect():
    logger.info("Client disconnected")
