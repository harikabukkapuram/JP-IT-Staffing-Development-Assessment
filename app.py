from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from pathlib import Path
import csv, io, os, re, uuid, smtplib, ssl
from email.message import EmailMessage
from datetime import datetime
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import requests

BASE = Path(__file__).resolve().parent
UPLOADS = BASE / "uploads"
EXPORTS = BASE / "exports"
UPLOADS.mkdir(exist_ok=True)
EXPORTS.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
contacts = []
campaigns = []
leads = []

BUSINESS_WORDS = {
    "company","corp","corporation","llc","ltd","inc","business","support",
    "sales","admin","info","contact","office","school","academy","institute",
    "university","marketing","team","service","hello"
}

def classify_email(email):
    local = email.split("@")[0].lower()
    if any(word in local for word in BUSINESS_WORDS):
        return "BUSINESS"
    return "INDIVIDUAL"

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/emailpro")
def emailpro():
    return render_template("emailpro.html")

@app.route("/export-desk")
def export_desk():
    return render_template("export_desk.html")

@app.post("/api/email/upload")
def email_upload():
    file = request.files.get("file")
    if not file:
        return jsonify(error="Please choose a CSV file."), 400
    if not file.filename.lower().endswith(".csv"):
        return jsonify(error="Only CSV files are supported."), 400

    raw = file.read().decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(raw))
    rows = []
    for row in reader:
        email = (row.get("email") or row.get("Email") or row.get("EMAIL") or "").strip()
        if email and re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            rows.append({"email": email, "name": row.get("name") or row.get("Name") or ""})

    # remove duplicates while preserving order
    seen, clean = set(), []
    for row in rows:
        if row["email"].lower() not in seen:
            seen.add(row["email"].lower())
            clean.append(row)

    global contacts
    contacts = clean
    return jsonify(
        message=f"{len(clean)} valid contacts uploaded.",
        total=len(clean),
        business=sum(classify_email(x["email"]) == "BUSINESS" for x in clean),
        individual=sum(classify_email(x["email"]) == "INDIVIDUAL" for x in clean)
    )

@app.post("/api/email/classify")
def classify():
    result = []
    for c in contacts:
        result.append({**c, "category": classify_email(c["email"])})
    return jsonify(
        contacts=result,
        business=sum(x["category"] == "BUSINESS" for x in result),
        individual=sum(x["category"] == "INDIVIDUAL" for x in result)
    )

@app.post("/api/email/campaign")
def campaign():
    data = request.get_json(silent=True) or {}
    subject = (data.get("subject") or "").strip()
    audience = data.get("audience", "all")
    content = (data.get("content") or "").strip()
    if not subject or not content:
        return jsonify(error="Subject and email content are required."), 400

    classified = [{**c, "category": classify_email(c["email"])} for c in contacts]
    targets = classified if audience == "all" else [
        c for c in classified if c["category"] == audience.upper()
    ]
    campaign = {
        "id": str(uuid.uuid4())[:8],
        "subject": subject,
        "audience": audience,
        "total": len(targets),
        "sent": 0,
        "failed": 0,
        "created": datetime.now().strftime("%d %b %Y, %H:%M")
    }
    # Demo mode: record the campaign without sending real emails.
    campaign["sent"] = len(targets)
    campaigns.append(campaign)
    return jsonify(message="Campaign completed in demo mode.", campaign=campaign)

@app.get("/api/email/reports")
def reports():
    return jsonify(campaigns=campaigns)

def extract_pdf_text(path):
    try:
        reader = PdfReader(str(path))
        return "\n".join((p.extract_text() or "") for p in reader.pages)[:8000]
    except Exception:
        return ""

@app.post("/api/leads/search")
def search_leads():
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    country = (data.get("country") or "USA").strip()
    limit = max(1, min(int(data.get("limit", 5)), 20))
    if not query:
        return jsonify(error="Enter a search query."), 400

    api_key = os.getenv("SERPER_API_KEY")
    results = []

    if api_key:
        try:
            r = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                json={"q": f"{query} {country}", "num": limit},
                timeout=15
            )
            r.raise_for_status()
            for item in r.json().get("organic", [])[:limit]:
                results.append({
                    "name": item.get("title", "Unknown"),
                    "email": "",
                    "phone": "",
                    "country": country,
                    "source": item.get("link", "")
                })
        except Exception:
            results = []

    if not results:
        # Safe demo fallback so the assignment runs without a paid key.
        samples = [
            ("Acme Wellness", "contact@acmewellness.example", "+1 555 0101"),
            ("Singing Bowls Wholesale", "sales@singingbowls.example", "+1 555 0102"),
            ("Mindful Living Studio", "hello@mindfulliving.example", "+1 555 0103"),
            ("Sound Healing Center", "info@soundhealing.example", "+1 555 0104"),
            ("Zen Home Decor", "business@zenhome.example", "+1 555 0105"),
        ]
        for name, email, phone in samples[:limit]:
            results.append({
                "name": name, "email": email, "phone": phone,
                "country": country, "source": "Demo data"
            })

    global leads
    leads = results
    return jsonify(count=len(results), leads=results)

@app.post("/api/leads/pdf")
def upload_pdf():
    file = request.files.get("pdf")
    if not file:
        return jsonify(error="Choose a PDF file."), 400
    name = secure_filename(file.filename)
    path = UPLOADS / name
    file.save(path)
    text = extract_pdf_text(path)
    return jsonify(
        filename=name,
        text=text,
        preview=(text[:1000] + ("..." if len(text) > 1000 else ""))
    )

@app.post("/api/leads/export")
def export_pdf():
    filename = EXPORTS / f"lead_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    c = canvas.Canvas(str(filename), pagesize=A4)
    width, height = A4
    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(45, y, "Singing Bowl Export Desk - Lead Report")
    y -= 28
    c.setFont("Helvetica", 9)
    for lead in leads:
        text = f'{lead.get("name","")} | {lead.get("email","")} | {lead.get("phone","")} | {lead.get("country","")}'
        for line in [text[i:i+100] for i in range(0, len(text), 100)]:
            if y < 45:
                c.showPage(); y = height - 50
            c.drawString(45, y, line)
            y -= 14
        y -= 5
    c.save()
    return send_file(filename, as_attachment=True, download_name=filename.name)

@app.post("/api/leads/email")
def send_lead_email():
    data = request.get_json(silent=True) or {}
    recipient = (data.get("to") or "").strip()
    subject = (data.get("subject") or "Lead follow-up").strip()
    body = (data.get("body") or "").strip()
    if not recipient or not body:
        return jsonify(error="Recipient and message are required."), 400

    host = os.getenv("SMTP_HOST")
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    if not (host and user and password):
        return jsonify(
            mode="demo",
            message="Demo email recorded. Add SMTP_HOST, SMTP_USER and SMTP_PASSWORD to send real mail."
        )

    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = user, recipient, subject
    msg.set_content(body)
    with smtplib.SMTP_SSL(host, 465, context=ssl.create_default_context()) as server:
        server.login(user, password)
        server.send_message(msg)
    return jsonify(mode="smtp", message="Email sent successfully.")

if __name__ == "__main__":
    app.run(debug=True)
