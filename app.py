import os
import difflib  # ✅ Added for fuzzy matching
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Certificate, VerificationLog
from werkzeug.utils import secure_filename
from ocr_utils import extract_text, find_cert_id

# ======================
# CONFIG
# ======================
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 🔹 Change these for your MySQL
DB_URL = "mysql+pymysql://root:tiger@localhost/auth_validator"

app = Flask(__name__)
app.secret_key = "super_secret_key"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# MySQL Connection
engine = create_engine(DB_URL, echo=True)  # echo=True prints SQL in console
SessionLocal = sessionmaker(bind=engine)

# ======================
# AUTH MIDDLEWARE
# ======================
def login_required(role=None):
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "username" not in session:
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("Unauthorized access")
                return redirect(url_for("login"))
            return f(*args, **kwargs)
        return wrapper
    return decorator

# ======================
# ROUTES
# ======================
@app.route("/")
def home():
    if "username" in session:
        if session["role"] == "admin":
            return redirect(url_for("dashboard"))
        return redirect(url_for("upload_page"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        db = SessionLocal()
        user = db.query(User).filter_by(username=username).first()
        db.close()

        if user and user.password_hash == password:  # ✅ plain password check
            session["username"] = user.username
            session["role"] = user.role
            return redirect(url_for("home"))
        else:
            flash("Invalid credentials")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/upload", methods=["GET", "POST"])
@login_required(role="user")
def upload_page():
    if request.method == "POST":
        f = request.files["file"]
        filename = secure_filename(f.filename)
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        f.save(path)

        # 🔹 OCR extraction
        text = extract_text(path)
        cert_id_ocr = find_cert_id(text)

        # 🔹 Manual fallback
        manual_id = request.form.get("manual_cert_id")
        if manual_id:
            cert_id_ocr = manual_id.strip().upper()

        db = SessionLocal()
        result = "not_detected"
        matched_cert = None

        if cert_id_ocr:
            # Fetch all cert IDs from DB to compare with fuzzy matching
            all_certs = db.query(Certificate).all()
            for cert in all_certs:
                similarity = difflib.SequenceMatcher(None,
                                                    cert_id_ocr.strip().upper(),
                                                    cert.cert_id.strip().upper()).ratio()
                if similarity > 0.7:  # ✅ Accept 90%+ match
                    matched_cert = cert
                    break

            result = "valid" if matched_cert else "fake"

        # 🔹 Logging
        log = VerificationLog(
            cert_id=cert_id_ocr or "N/A",
            extracted_text=text[:200],
            detected_cert_id=matched_cert.cert_id if matched_cert else "N/A",
            result=result,
            uploaded_filename=filename,
            verifier=session["username"]
        )
        db.add(log)
        db.commit()
        db.close()

        return render_template("upload.html",
                               uploaded=True,
                               result=result,
                               cert_id=cert_id_ocr,
                               filename=filename)

    return render_template("upload.html", uploaded=False)

@app.route("/admin")
@login_required(role="admin")
def dashboard():
    db = SessionLocal()
    logs = db.query(VerificationLog).all()
    db.close()
    return render_template("dashboard.html", logs=logs)

@app.route("/uploads/<filename>")
def serve_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# ======================
# MAIN
# ======================
if __name__ == "__main__":
    app.run(debug=True, port=5000)
