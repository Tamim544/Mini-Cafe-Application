import os
import random
import string

import qrcode


def generate_order_ref() -> str:
    """Human-friendly order ref: CAF-XXXX"""
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"CAF-{suffix}"


def generate_qr_code(order_ref: str) -> str:
    """
    Generate a QR code PNG pointing to /track/<order_ref>.
    Returns the public URL path string.
    """
    qr_dir = os.path.join(
        os.path.dirname(__file__), "..", "static", "qrcodes"
    )
    os.makedirs(qr_dir, exist_ok=True)

    track_url = f"/track/{order_ref}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(track_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    file_path = os.path.join(qr_dir, f"{order_ref}.png")
    img.save(file_path)

    return f"/static/qrcodes/{order_ref}.png"


def _sanitize_pdf_text(text: str) -> str:
    """Replace Unicode chars that Helvetica can't render."""
    if not text:
        return ""
    replacements = {
        '\u2014': '-',   # em dash
        '\u2013': '-',   # en dash
        '\u2018': "'",   # left single quote
        '\u2019': "'",   # right single quote
        '\u201c': '"',   # left double quote
        '\u201d': '"',   # right double quote
        '\u2026': '...', # ellipsis
        '\u2022': '*',   # bullet
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    # Strip any remaining non-latin1 chars
    return text.encode('latin-1', errors='replace').decode('latin-1')


def generate_pdf_receipt(order) -> bytes:
    """Generate a formatted PDF receipt for an order."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ── Header ─────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 12, "Mini Cafe", new_x="LMARGIN", new_y="NEXT", align="C")

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, "123 Cafe Street, Foodville", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(0, 6, "contact@minicafe.com", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)

    # Divider
    pdf.set_draw_color(200, 200, 200)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # ── Order Info ─────────────────────────────────────
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, f"Receipt - Order {order.order_ref}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 6, f"Customer: {_sanitize_pdf_text(order.customer_name)}", new_x="LMARGIN", new_y="NEXT")
    if order.table_number:
        pdf.cell(0, 6, f"Table: {order.table_number}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(
        0, 6,
        f"Date: {order.placed_at.strftime('%Y-%m-%d %H:%M')} UTC",
        new_x="LMARGIN", new_y="NEXT"
    )
    pdf.cell(0, 6, f"Status: {order.status.upper()}", new_x="LMARGIN", new_y="NEXT")
    if order.notes:
        pdf.cell(0, 6, f"Notes: {_sanitize_pdf_text(order.notes)}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # ── Items Table ────────────────────────────────────
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_fill_color(245, 245, 245)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(80, 9, "Item", border=1, fill=True)
    pdf.cell(30, 9, "Qty", border=1, fill=True, align="C")
    pdf.cell(40, 9, "Unit Price", border=1, fill=True, align="R")
    pdf.cell(40, 9, "Subtotal", border=1, fill=True, align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(50, 50, 50)
    for item in order.items:
        pdf.cell(80, 8, _sanitize_pdf_text(item.item_name), border=1)
        pdf.cell(30, 8, str(item.quantity), border=1, align="C")
        pdf.cell(40, 8, f"${item.unit_price:.2f}", border=1, align="R")
        pdf.cell(
            40, 8, f"${item.quantity * item.unit_price:.2f}",
            border=1, align="R", new_x="LMARGIN", new_y="NEXT"
        )

    pdf.ln(4)

    # ── Total ──────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(150, 10, "TOTAL", align="R")
    pdf.cell(40, 10, f"${order.total:.2f}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    # ── Footer ─────────────────────────────────────────
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(130, 130, 130)
    pdf.cell(0, 6, "Thank you for visiting Mini Cafe!", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(
        0, 6,
        f"Track your order at: /track/{order.order_ref}",
        new_x="LMARGIN", new_y="NEXT", align="C"
    )

    return bytes(pdf.output())
