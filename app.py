import os
from datetime import datetime
from bson import ObjectId
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from db import get_db

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev-secret-change")

ADMIN_USER = "admin"
ADMIN_PASS_HASH = generate_password_hash("admin123")

UPLOAD_ROOT = os.path.join(app.root_path, "static", "uploads")
os.makedirs(UPLOAD_ROOT, exist_ok=True)


def _ensure_admin_hash():
    global ADMIN_PASS_HASH
    if not ADMIN_PASS_HASH:
        # default password: change-me
        ADMIN_PASS_HASH = generate_password_hash("change-me")


def _is_admin():
    token = request.cookies.get("vertex_admin")
    return token == "1"


def _require_admin():
    if not _is_admin():
        return redirect(url_for("admin_login", next=request.path))
    return None


def _seed_reports(db):
    if db.reports.count_documents({}) > 0:
        return
    seed = [
        {
            "title": "The Investment Readiness Gap: Why Africa’s Best Businesses Struggle to Raise Capital",
            "excerpt": "A flagship report exploring structural bottlenecks in capital formation and the readiness gap facing high-potential African companies.",
            "category": "Flagship Report",
            "quarter": "Q1 2026",
            "featured": True,
            "status": "coming_soon",
            "pdf_url": "",
            "cover_image": ""
        },
        {
            "title": "State of Early-Stage Fundraising Across Africa",
            "excerpt": "A data-led overview of early-stage fundraising dynamics, founder readiness, and investor sentiment across key markets.",
            "category": "Vertex View",
            "quarter": "Q2 2026",
            "featured": False,
            "status": "coming_soon",
            "pdf_url": "",
            "cover_image": ""
        },
        {
            "title": "Fintech Beyond the Hype: Where Real Value Is Being Built",
            "excerpt": "A sector spotlight on sustainable fintech models and the infrastructure layers powering real value creation.",
            "category": "Sector Spotlight",
            "quarter": "Q2 2026",
            "featured": False,
            "status": "coming_soon",
            "pdf_url": "",
            "cover_image": ""
        },
        {
            "title": "What Investors Actually Look for in African Growth Companies",
            "excerpt": "A candid view of investor expectations, diligence lenses, and the signals that separate growth from hype.",
            "category": "Vertex View",
            "quarter": "Q3 2026",
            "featured": False,
            "status": "coming_soon",
            "pdf_url": "",
            "cover_image": ""
        },
        {
            "title": "West Africa Capital Markets: Quarterly Review",
            "excerpt": "Market Pulse tracking capital market activity, liquidity trends, and issuance dynamics across West Africa.",
            "category": "Market Pulse",
            "quarter": "Q3 2026",
            "featured": False,
            "status": "coming_soon",
            "pdf_url": "",
            "cover_image": ""
        },
        {
            "title": "The Diaspora Dividend: How Africa’s Global Community Is Fuelling Development Back Home",
            "excerpt": "A Vertex View on the capital, networks, and knowledge flows reshaping Africa’s private sector from abroad.",
            "category": "Vertex View",
            "quarter": "Q3 2026",
            "featured": False,
            "status": "coming_soon",
            "pdf_url": "",
            "cover_image": ""
        },
        {
            "title": "The Founder’s Guide to Due Diligence Readiness",
            "excerpt": "A practical playbook for founders preparing for investor scrutiny across finance, governance, and operations.",
            "category": "Playbook",
            "quarter": "Q4 2026",
            "featured": False,
            "status": "coming_soon",
            "pdf_url": "",
            "cover_image": ""
        },
        {
            "title": "The Trust Deficit: Why African Collaboration Is the Continent’s Greatest Untapped Asset",
            "excerpt": "An opinion piece on cooperation gaps, market fragmentation, and the opportunity for collective advantage.",
            "category": "Opinion",
            "quarter": "Q4 2026",
            "featured": False,
            "status": "coming_soon",
            "pdf_url": "",
            "cover_image": ""
        }
    ]
    db.reports.insert_many(seed)


@app.route("/")
def index():
    db = get_db()
    _seed_reports(db)
    featured = db.reports.find_one({"featured": True})
    base_query = {"_id": {"$ne": featured.get("_id") if featured else None}}
    reports = list(db.reports.find(base_query).limit(3))
    return render_template("index.html", featured=featured, reports=reports)


@app.route("/research")
def research():
    db = get_db()
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    status = request.args.get("status", "").strip().lower()
    page = request.args.get("page", "1").strip()
    try:
        page = max(1, int(page))
    except ValueError:
        page = 1

    query = {}
    if q:
        query["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"excerpt": {"$regex": q, "$options": "i"}},
        ]
    if category:
        query["category"] = category
    if status in {"published", "coming_soon"}:
        query["status"] = status

    page_size = 10
    total = db.reports.count_documents(query)
    total_pages = max(1, (total + page_size - 1) // page_size)
    if page > total_pages:
        page = total_pages
    reports = list(
        db.reports.find(query).sort("quarter", 1).skip((page - 1) * page_size).limit(page_size)
    )
    categories = sorted(db.reports.distinct("category"))
    return render_template(
        "research.html",
        reports=reports,
        categories=categories,
        q=q,
        category=category,
        status=status,
        page=page,
        total_pages=total_pages,
        total=total,
    )


@app.route("/admin")
def admin():
    return redirect(url_for("admin_reports"))


@app.route("/admin/reports")
def admin_reports():
    gate = _require_admin()
    if gate:
        return gate
    db = get_db()
    reports = list(db.reports.find({}).sort("quarter", 1))
    total_reports = db.reports.count_documents({})
    total_subscribers = db.subscribers.count_documents({})
    total_inquiries = db.inquiries.count_documents({})
    total_downloads = sum([r.get("download_requests", 0) for r in reports])
    published_count = db.reports.count_documents({"status": "published"})
    coming_soon_count = db.reports.count_documents({"status": "coming_soon"})
    top_report = db.reports.find_one(sort=[("download_requests", -1)])
    return render_template(
        "reports.html",
        reports=reports,
        total_reports=total_reports,
        total_subscribers=total_subscribers,
        total_inquiries=total_inquiries,
        total_downloads=total_downloads,
        published_count=published_count,
        coming_soon_count=coming_soon_count,
        top_report=top_report,
    )


@app.route("/admin/dashboard")
def admin_dashboard():
    gate = _require_admin()
    if gate:
        return gate
    db = get_db()
    total_reports = db.reports.count_documents({})
    published_reports = db.reports.count_documents({"status": "published"})
    subscribers_count = db.subscribers.count_documents({})
    inquiries_count = db.inquiries.count_documents({})
    total_downloads = sum([r.get("download_requests", 0) for r in db.reports.find({})])
    top_report = db.reports.find_one(sort=[("download_requests", -1)])

    # Recent lists
    recent_subscribers = list(db.subscribers.find({}).sort("created_at", -1).limit(5))
    recent_inquiries = list(db.inquiries.find({}).sort("created_at", -1).limit(5))
    recent_leads = list(
        db.subscribers.find({"report_tags": {"$exists": True, "$ne": []}})
        .sort("created_at", -1)
        .limit(8)
    )

    # System summary
    last_report = db.reports.find_one({"status": "published"}, sort=[("quarter", -1)])
    latest_subscriber = db.subscribers.find_one(sort=[("created_at", -1)])
    latest_inquiry = db.inquiries.find_one(sort=[("created_at", -1)])
    latest_download_lead = db.subscribers.find_one(
        {"report_tags": {"$exists": True, "$ne": []}}, sort=[("created_at", -1)]
    )

    conversion_rate = 0
    if subscribers_count:
        conversion_rate = round((total_downloads / subscribers_count) * 100)

    # Chart: downloads by report
    report_cursor = list(
        db.reports.find({}).sort("download_requests", -1).limit(8)
    )
    report_labels = [r.get("title", "Untitled") for r in report_cursor]
    report_download_values = [r.get("download_requests", 0) for r in report_cursor]

    # Monthly downloads + subscriber growth (last 6 months)
    def _last_n_months(n=6):
        now = datetime.utcnow()
        months = []
        year, month = now.year, now.month
        for _ in range(n):
            months.append((year, month))
            month -= 1
            if month == 0:
                month = 12
                year -= 1
        return list(reversed(months))

    month_keys = _last_n_months(6)
    month_labels = [f"{y}-{m:02d}" for y, m in month_keys]
    monthly_downloads = {k: 0 for k in month_labels}
    monthly_subscribers = {k: 0 for k in month_labels}

    for lead in db.subscribers.find({"report_tags": {"$exists": True, "$ne": []}}):
        created = lead.get("created_at")
        if created:
            key = created.strftime("%Y-%m")
            if key in monthly_downloads:
                monthly_downloads[key] += 1

    for sub in db.subscribers.find({}):
        created = sub.get("created_at")
        if created:
            key = created.strftime("%Y-%m")
            if key in monthly_subscribers:
                monthly_subscribers[key] += 1

    monthly_download_labels = month_labels
    monthly_download_values = [monthly_downloads[k] for k in month_labels]
    subscriber_growth_labels = month_labels
    subscriber_growth_values = [monthly_subscribers[k] for k in month_labels]

    # Interest by sector (proxy using report categories tied to downloads)
    sector_counts = {}
    for lead in db.subscribers.find({"report_tags": {"$exists": True, "$ne": []}}):
        for title in lead.get("report_tags", []):
            matched = db.reports.find_one({"title": title})
            if matched:
                cat = matched.get("category", "Other")
                sector_counts[cat] = sector_counts.get(cat, 0) + 1
    sector_interest_labels = list(sector_counts.keys())
    sector_interest_values = list(sector_counts.values())

    return render_template(
        "dashboard.html",
        total_reports=total_reports,
        published_reports=published_reports,
        subscribers_count=subscribers_count,
        downloads_count=total_downloads,
        inquiries_count=inquiries_count,
        conversion_rate=conversion_rate,
        report_labels=report_labels,
        report_download_values=report_download_values,
        monthly_download_labels=monthly_download_labels,
        monthly_download_values=monthly_download_values,
        subscriber_growth_labels=subscriber_growth_labels,
        subscriber_growth_values=subscriber_growth_values,
        sector_interest_labels=sector_interest_labels,
        sector_interest_values=sector_interest_values,
        last_report_title=last_report.get("title") if last_report else None,
        top_report_title=top_report.get("title") if top_report else None,
        latest_subscriber_email=latest_subscriber.get("email") if latest_subscriber else None,
        latest_inquiry_name=latest_inquiry.get("name") if latest_inquiry else None,
        latest_download_lead_email=latest_download_lead.get("email") if latest_download_lead else None,
        recent_leads=recent_leads,
        recent_inquiries=recent_inquiries,
    )


@app.route("/admin/users")
def admin_users():
    gate = _require_admin()
    if gate:
        return gate
    db = get_db()
    users = list(db.subscribers.find({}).sort("created_at", -1))
    return render_template("users.html", users=users)


@app.route("/admin/messages")
def admin_messages():
    gate = _require_admin()
    if gate:
        return gate
    db = get_db()
    messages = list(db.inquiries.find({}).sort("created_at", -1))
    return render_template("messages.html", messages=messages)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    _ensure_admin_hash()
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == ADMIN_USER and check_password_hash(ADMIN_PASS_HASH, password):
            resp = make_response(redirect(url_for("admin")))
            resp.set_cookie("vertex_admin", "1", httponly=True, samesite="Lax")
            return resp
        flash("Invalid credentials", "error")
    return render_template("login.html")


@app.route("/admin/logout")
def admin_logout():
    resp = make_response(redirect(url_for("admin_login")))
    resp.set_cookie("vertex_admin", "0", expires=0)
    return resp


@app.route("/admin/report/new", methods=["GET", "POST"])
def report_new():
    gate = _require_admin()
    if gate:
        return gate
    if request.method == "POST":
        db = get_db()
        payload = _report_payload(request)
        result = db.reports.insert_one(payload)
        if payload.get("featured"):
            db.reports.update_many({"_id": {"$ne": result.inserted_id}}, {"$set": {"featured": False}})
        return redirect(url_for("admin"))
    return render_template("edit.html", report=None)


@app.route("/admin/report/<report_id>/edit", methods=["GET", "POST"])
def report_edit(report_id):
    gate = _require_admin()
    if gate:
        return gate
    db = get_db()
    report = db.reports.find_one({"_id": ObjectId(report_id)})
    if not report:
        return redirect(url_for("admin"))
    if request.method == "POST":
        payload = _report_payload(request, current=report)
        db.reports.update_one({"_id": ObjectId(report_id)}, {"$set": payload})
        if payload.get("featured"):
            db.reports.update_many({"_id": {"$ne": ObjectId(report_id)}}, {"$set": {"featured": False}})
        return redirect(url_for("admin"))
    return render_template("edit.html", report=report)


@app.route("/admin/report/<report_id>/delete", methods=["POST"])
def report_delete(report_id):
    gate = _require_admin()
    if gate:
        return gate
    db = get_db()
    db.reports.delete_one({"_id": ObjectId(report_id)})
    return redirect(url_for("admin"))


@app.route("/newsletter/subscribe", methods=["POST"])
def subscribe_newsletter():
    db = get_db()
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    if not email:
        return jsonify({"ok": False, "message": "Email required"}), 400
    db.subscribers.update_one(
        {"email": email},
        {
            "$setOnInsert": {
                "email": email,
                "name": name,
                "source": "newsletter",
                "created_at": datetime.utcnow(),
            }
        },
        upsert=True,
    )
    return jsonify({"ok": True, "message": "Thank you. Please check your inbox to confirm subscription."})


@app.route("/subscribe-report", methods=["POST"])
def subscribe_report():
    db = get_db()
    report_id = request.form.get("report_id")
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    company = request.form.get("company", "").strip()
    report = db.reports.find_one({"_id": ObjectId(report_id)}) if report_id else None
    if not report or not email or not name:
        return jsonify({"ok": False, "message": "Name and email required."}), 400
    db.subscribers.update_one(
        {"email": email},
        {
            "$setOnInsert": {
                "email": email,
                "name": name,
                "company": company,
                "created_at": datetime.utcnow(),
            },
            "$addToSet": {"report_tags": report.get("title")},
        },
        upsert=True,
    )
    db.reports.update_one({"_id": ObjectId(report_id)}, {"$inc": {"download_requests": 1}})
    # Mailchimp automation should be configured to deliver the report.
    if str(report.get("status", "")).lower() == "published" and report.get("pdf_url"):
        return jsonify({"ok": True, "download": report.get("pdf_url")})
    return jsonify({"ok": True, "message": "Thank you. We will email you once the report is available."})


@app.route("/contact/submit", methods=["POST"])
def contact():
    db = get_db()
    payload = {
        "name": request.form.get("name", "").strip(),
        "email": request.form.get("email", "").strip(),
        "company": request.form.get("company", "").strip(),
        "interest": request.form.get("interest", "").strip(),
        "message": request.form.get("message", "").strip(),
        "created_at": datetime.utcnow(),
    }
    honeypot = request.form.get("website", "").strip()
    if not payload["name"] or not payload["email"]:
        return jsonify({"ok": False, "message": "Name and email required."}), 400
    if honeypot:
        return jsonify({"ok": True, "message": "Thank you."})
    db.inquiries.insert_one(payload)
    return jsonify({"ok": True, "message": "Thank you. We will respond shortly."})


def _save_upload(file_obj, folder, allowed_ext):
    if not file_obj or not file_obj.filename:
        return ""
    ext = os.path.splitext(file_obj.filename)[1].lower()
    if ext not in allowed_ext:
        return ""
    filename = secure_filename(file_obj.filename)
    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    target_dir = os.path.join(UPLOAD_ROOT, folder)
    os.makedirs(target_dir, exist_ok=True)
    saved_name = f"{stamp}_{filename}"
    file_obj.save(os.path.join(target_dir, saved_name))
    return f"/static/uploads/{folder}/{saved_name}"


def _report_payload(req, current=None):
    status = req.form.get("status", "coming_soon").strip().lower()
    
    # Keep existing values by default
    pdf_url = current.get("pdf_url", "") if current else ""
    cover_image = current.get("cover_image", "") if current else ""
    audio_url = current.get("audio_url", "") if current else ""
    
    # Override with form values if provided
    if req.form.get("pdf_url_current"):
        pdf_url = req.form.get("pdf_url_current", "").strip()
    if req.form.get("cover_image_current"):
        cover_image = req.form.get("cover_image_current", "").strip()
    if req.form.get("audio_url_current"):
        audio_url = req.form.get("audio_url_current", "").strip()
    
    # Upload new files if provided
    pdf_file = req.files.get("pdf_file")
    cover_file = req.files.get("cover_file")
    audio_file = req.files.get("audio_file")
    
    new_pdf = _save_upload(pdf_file, "pdfs", {".pdf"})
    new_cover = _save_upload(cover_file, "covers", {".png", ".jpg", ".jpeg", ".webp"})
    new_audio = _save_upload(audio_file, "audio", {".mp3", ".wav", ".m4a", ".ogg"})
    
    # Replace only if new file was uploaded
    if new_pdf:
        pdf_url = new_pdf
    if new_cover:
        cover_image = new_cover
    if new_audio:
        audio_url = new_audio
    
    return {
        "title": req.form.get("title", "").strip(),
        "excerpt": req.form.get("excerpt", "").strip(),
        "category": req.form.get("category", "").strip(),
        "quarter": req.form.get("quarter", "").strip(),
        "featured": True if req.form.get("featured") == "on" else False,
        "status": status,
        "pdf_url": pdf_url,
        "cover_image": cover_image,
        "audio_url": audio_url,
    }


if __name__ == "__main__":
    app.run(debug=True)
