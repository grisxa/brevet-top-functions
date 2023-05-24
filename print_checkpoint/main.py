import logging
import os
import re
from datetime import datetime, timedelta
from io import BytesIO

import firebase_admin
import google.cloud.firestore
import google.cloud.logging
import qrcode
from flask import Request, json, send_file
from flask_cors import cross_origin
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

log_client = google.cloud.logging.Client()
log_client.get_default_handler()
log_client.setup_logging(log_level=logging.DEBUG)
# logging.basicConfig(level=logging.DEBUG)

firebase_admin.initialize_app()
db_client = google.cloud.firestore.Client()


@cross_origin(methods="GET")
def print_checkpoint(request: Request):
    found = re.match(r".*/brevet/([^/]+)/checkpoint/([^/]+)", request.path)
    if found:
        brevet_uid, checkpoint_uid = found.group(1, 2)
    else:
        message = "UID search failed"
        logging.error(message)
        return json.dumps({"message": message}), 404

    checkpoint_dict = (
        db_client.document(f"brevets/{brevet_uid}/checkpoints/{checkpoint_uid}")
        .get()
        .to_dict()
    )
    file_name = f"checkpoint-{checkpoint_uid}.pdf"

    script_directory = os.path.dirname(os.path.abspath(__file__))

    # Apply the font
    pdfmetrics.registerFont(
        TTFont("Lucida", os.path.join(script_directory, "lucida.ttf"))
    )

    # Create the PDF file
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    # Load the logo using ImageReader
    logo = ImageReader(os.path.join(script_directory, "logo.png"))

    # Get the dimensions of the vector image
    logo_width, logo_height = logo.getSize()

    # Calculate the aspect ratio to maintain proportions
    aspect_ratio = logo_height / logo_width

    # Specify the desired width of the image in the PDF
    desired_width = 200

    # Calculate the corresponding height based on the aspect ratio
    desired_height = aspect_ratio * desired_width

    # Draw the logo
    c.drawImage(logo, x=50, y=640, width=desired_width, height=desired_height)

    # Add content
    c.setFont("Lucida", 45)
    c.drawString(263, 720, "Балтийская")
    c.drawString(265, 680, "звезда")

    c.setFontSize(20)
    c.drawString(265, 650, "веломарафонский клуб")

    c.setFontSize(30)
    brevet_name = checkpoint_dict.get("brevet", {}).get("name", "")
    brevet_length = checkpoint_dict.get("brevet", {}).get("length", "")
    c.drawString(50, 590, f"Бревет {brevet_name}, {brevet_length} км")

    c.setFontSize(20)
    start_date: datetime = checkpoint_dict.get("brevet", {}).get("startDate")
    if start_date:
        c.drawString(80, 560, start_date.strftime("%d.%m.%y"))

    c.setFontSize(30)
    checkpoint_name = checkpoint_dict.get("displayName", "")
    checkpoint_distance = checkpoint_dict.get("distance", 0)
    c.drawString(50, 510, f"{checkpoint_name}, {checkpoint_distance} км")

    c.setFontSize(20)
    c.drawString(50, 110, "Внимание! Проводится велопробег!")
    c.drawString(50, 80, "Просим не снимать плакат")
    end_date: datetime = checkpoint_dict.get("brevet", {}).get("endDate")
    if end_date:
        c.drawString(325, 80, "до")
        c.drawString(360, 80, (end_date + timedelta(days=1)).strftime("%d.%m.%y"))

    # Draw a QR code
    url = f"https://brevet.top/c/{checkpoint_uid}"
    code = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        border=4,
    )
    code.add_data(url)
    code.make(fit=True)
    image = code.make_image(fill_color="black", back_color="white")
    c.drawInlineImage(image, 30, 150, width=350, height=350)
    c.drawInlineImage(image, 380, 300, width=180, height=180)
    c.drawInlineImage(image, 365, 200, width=100, height=100)
    c.drawInlineImage(image, 465, 150, width=100, height=100)

    # Save and close the PDF
    c.save()

    # Get the PDF content from the buffer
    pdf_content = buffer.getvalue()

    # Close the buffer
    buffer.close()

    return send_file(
        BytesIO(pdf_content),
        mimetype="application/pdf",
        download_name=file_name,
        as_attachment=False,
    )
