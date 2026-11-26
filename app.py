
from flask import Flask, render_template, jsonify
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import csv
import io
import requests


# =========================================================
# GOOGLE SHEETS CONFIGURATION
# =========================================================

# IPO DOCUMENTS - GOOGLE APPS SCRIPT JSON API
GOOGLE_SHEET_API_URL = "https://script.google.com/macros/s/AKfycbz0yGOIyMZ1-4IC4Oply0x9UcPWZQ44Ude4b_S8nOB7fnok9xlI9efs7BWoRQpqpEecrg/exec"


# IPO CALENDAR - ORIGINAL PUBLISHED GOOGLE SHEET CSV
# Keep this separate from the Documents Apps Script URL.
GOOGLE_CALENDAR_CSV_URL = "https://script.google.com/macros/s/AKfycbyAD1KbdfUG3_ocHuNTqZsYU8z0hDYMXTHkPyyrPmqJlf6m1pLq0--c-yol_h9cfid6/exec"


app = Flask(__name__)


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


# =========================================================
# ALLOTMENT
# =========================================================

@app.route("/allotment")
def allotment():
    return render_template("allotment.html")


# =========================================================
# CONTACT
# =========================================================

@app.route("/contact")
def contact():
    return render_template("contact.html")


# =========================================================
# IPO DOCUMENTS
# =========================================================

@app.route("/ipo-documents")
def ipo_documents():
    return render_template("ipo-documents.html")


# =========================================================
# BLOG
# =========================================================

@app.route("/blog")
def blog():
    return render_template("blog.html")


# =========================================================
# TERMS
# =========================================================

@app.route("/terms")
def terms():
    return render_template("terms.html")


# =========================================================
# IPO CALENDAR PAGE
# =========================================================

@app.route("/ipo-calendar")
def ipo_calendar():

    now = datetime.now(
        ZoneInfo("Asia/Kolkata")
    )

    current_date = now.strftime("%Y-%m-%d")

    calendar_folder = os.path.join(
        app.static_folder,
        "calendar"
    )

    latest_image = None

    for ext in [
        ".jpg",
        ".jpeg",
        ".png",
        ".webp"
    ]:

        filename = current_date + ext

        image_path = os.path.join(
            calendar_folder,
            filename
        )

        if os.path.exists(image_path):

            latest_image = filename
            break

    show_calendar = now.hour >= 6

    return render_template(
        "ipo-calendar.html",
        latest_image=latest_image,
        show_calendar=show_calendar,
        current_time=now.strftime(
            "%d %b %Y %I:%M %p"
        )
    )


# =========================================================
# IPO DOCUMENTS GOOGLE SHEET JSON API
# =========================================================

@app.route("/api/documents")
@app.route("/api/ipo-documents")
def api_ipo_documents():

    try:

        response = requests.get(
            GOOGLE_SHEET_API_URL,
            timeout=30,
            allow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, list):

            raise ValueError(
                "Invalid Google Apps Script JSON response"
            )

        documents = []

        for row in data:

            company = str(
                row.get("Company", "")
            ).strip()

            doc_type = str(
                row.get("Type", "")
            ).strip().upper().replace(".", "")

            document_url = str(
                row.get("Document URL", "")
            ).strip()

            document_name = str(
                row.get("Document Name", doc_type)
            ).strip()

            document_type = str(
                row.get("Document Type", doc_type)
            ).strip()

            if not (
                company
                and doc_type
                and document_url
            ):
                continue

            documents.append({

                # Uppercase keys for existing frontend
                "Company": company,
                "Type": doc_type,
                "Document Name": document_name,
                "Document Type": document_type,
                "Document URL": document_url,

                # Lowercase keys for compatibility
                "company": company,
                "type": doc_type,
                "name": document_name,
                "document_type": document_type,
                "url": document_url

            })

        app.logger.info(
            "IPO DOCUMENTS LOADED: %s",
            len(documents)
        )

        return jsonify(documents)

    except requests.exceptions.RequestException:

        app.logger.exception(
            "IPO DOCUMENT GOOGLE SHEETS CONNECTION ERROR"
        )

        return jsonify({
            "error": True,
            "message": "Unable to connect to Google Sheets"
        }), 502

    except Exception:

        app.logger.exception(
            "IPO DOCUMENT ERROR"
        )

        return jsonify({
            "error": True,
            "message": "Unable to load IPO documents"
        }), 500


# =========================================================
# IPO CALENDAR GOOGLE SHEET CSV API
# =========================================================

@app.route("/api/ipo-calendar")
def ipo_calendar_data():

    try:

        response = requests.get(
            GOOGLE_CALENDAR_CSV_URL,
            timeout=20,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        response.raise_for_status()

        csv_text = response.text.lstrip("\ufeff")

        reader = csv.DictReader(
            io.StringIO(csv_text)
        )

        calendar_data = []

        for row in reader:

            company = row.get(
                "Company",
                ""
            ).strip()

            ipo_type = row.get(
                "Type",
                ""
            ).strip()

            open_date = row.get(
                "Open Date",
                ""
            ).strip()

            close_date = row.get(
                "Close Date",
                ""
            ).strip()

            allotment_date = row.get(
                "Allotment Date",
                ""
            ).strip()

            listing_date = row.get(
                "Listing Date",
                ""
            ).strip()

            if not company:
                continue

            calendar_data.append({

                "company": company,

                "type": ipo_type or "Mainboard",

                "open_date": open_date,

                "close_date": close_date,

                "allotment_date": allotment_date,

                "listing_date": listing_date

            })

        app.logger.info(
            "IPO CALENDAR LOADED: %s",
            len(calendar_data)
        )

        return jsonify(calendar_data)

    except Exception:

        app.logger.exception(
            "IPO CALENDAR ERROR"
        )

        return jsonify({
            "error": True,
            "message": "Unable to load IPO calendar"
        }), 500


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=False
    )
