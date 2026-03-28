from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
import os

# ==============================
# KONFIGURASI APLIKASI
# ==============================
app = Flask(__name__)
app.secret_key = "petbutlersecretkey"

# Konfigurasi Upload Folder
UPLOAD_FOLDER = 'static/images/pets'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Membuat folder upload otomatis jika belum ada
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ==============================
# KONFIGURASI DATABASE MYSQL
# ==============================
# Format: mysql+pymysql://username:password@host/nama_database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/petbutler_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==============================
# MODEL DATABASE (TABEL MYSQL)
# ==============================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False) # Sebaiknya di-hash nanti
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    
    # Relasi ke tabel lain
    pets = db.relationship('Pet', backref='owner', lazy=True)
    orders = db.relationship('Order', backref='customer', lazy=True)

class Pet(db.Model):
    id = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    species = db.Column(db.String(50))
    photo = db.Column(db.String(255), nullable=True)
    breed = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    records = db.relationship('MedicalRecord', backref='pet_info', lazy=True)

class Order(db.Model):
    id_pesanan = db.Column(db.String(10), primary_key=True)
    pet = db.Column(db.String(100))
    service = db.Column(db.String(100))
    pickup = db.Column(db.Text)
    destination = db.Column(db.Text)
    total = db.Column(db.Float)
    method = db.Column(db.String(50))
    status = db.Column(db.String(50))
    date = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class MedicalRecord(db.Model):
    record_id = db.Column(db.String(10), primary_key=True)
    clinic_name = db.Column(db.String(100))
    visit_date = db.Column(db.String(50))
    diagnosis = db.Column(db.Text)
    treatment = db.Column(db.Text)
    notes = db.Column(db.Text)
    pet_id = db.Column(db.String(10), db.ForeignKey('pet.id'), nullable=False)

# Membuat tabel di MySQL jika belum ada
with app.app_context():
    db.create_all()


# # ==============================
# # DATA SEMENTARA (DATABASE MOCKUP)
# # ==============================
# # Pindahkan semua dictionary ke atas agar bisa diakses semua route
# pets_data = {}
# orders_data = {}
# user_profiles = {}

# # ==============================
# # LOGIKA BISNIS (CLASSES)
# # ==============================
# class AuthSystem:
#     def __init__(self):
#         self.accounts = {}

#     def register(self, username, email, password):
#         if username in self.accounts:
#             return "Username sudah terdaftar!"
#         self.accounts[username] = {
#             "email": email,
#             "password": password
#         }
#         return "Registrasi berhasil!"

#     def login(self, email, password):
#         for username, data in self.accounts.items():
#             if data["email"] == email and data["password"] == password:
#                 return username
#         return None

class PetServices:
    def __init__(self, id_services, nama_services, harga_dasar):
        self.id_services = id_services
        self.nama_services = nama_services
        self.harga_dasar = harga_dasar
        self.tarif_per_km = 8000 if nama_services == "Mobil AC" else 4000

    def hitungharga(self, jarak_km):
        return self.harga_dasar + (self.tarif_per_km * jarak_km)

class CompanyProfile:
    def __init__(self):
        self.name = "Pet Butler"
        self.description = "Pet Butler adalah solusi transportasi hewan premium yang dirancang untuk memberikan kenyamanan maksimal bagi hewan kesayangan Anda. Kami menyediakan layanan antar-jemput profesional dengan armada yang dilengkapi AC, driver pecinta hewan yang terlatih, serta sistem pelacakan real-time untuk memastikan setiap perjalanan aman, tenang, dan tepat waktu sampai ke tujuan."
        self.faq = [
            "Bagaimana cara memesan? -> Login lalu pilih Buat Order.",
            "Apakah tersedia 24 jam? -> Ya, kami melayani 24/7.",
            "Bagaimana metode pembayaran? -> Non-tunai via sistem."
        ]
        self.support_email = "support@petbutler.com"

    def get_profile(self):
        return {
            "name": self.name,
            "description": self.description,
            "faq": self.faq,
            "support": self.support_email
        }

#auth_system = AuthSystem()
company_profile = CompanyProfile()

# Fungsi bantuan untuk file
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==============================
# ROUTES
# ==============================

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    message = ""
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        
        # Cek apakah username sudah ada
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            message = "Username sudah terdaftar!"
        else:
            # Simpan ke database
            new_user = User(username=username, email=email, password=password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for("login", s="success"))
            
    return render_template("register.html", message=message)

@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        # Cari user di database
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session["user"] = user.username # Atau simpan user.id agar lebih aman
            return redirect(url_for("dashboard"))
        else:
            message = "Login gagal! Email atau password salah."
            
    return render_template("login.html", message=message)

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    username_login = session["user"]
    # Cari user di database berdasarkan username dari session
    user = User.query.filter_by(username=username_login).first()
    
    if not user:
        return redirect(url_for("logout")) # Jika user terhapus tapi session masih ada

    # Ambil Data Profil (gunakan nama asli jika ada, jika tidak gunakan username)
    display_name = user.name if user.name else user.username

    # Ambil Daftar Hewan milik user ini
    user_pets = Pet.query.filter_by(user_id=user.id).all()

    # Ambil Order Terakhir (diurutkan berdasarkan ID dari yang terbaru)
    latest_order = Order.query.filter_by(user_id=user.id).order_by(Order.id_pesanan.desc()).first()

    return render_template("dashboard.html", 
                           username=display_name, 
                           pets=user_pets, 
                           latest_order=latest_order)

@app.route("/add_pet", methods=["GET", "POST"])
def add_pet():
    if "user" not in session:
        return redirect(url_for("login"))
    
    username = session["user"]
    user = User.query.filter_by(username=username).first()
    
    if request.method == "POST":
        pet_name = request.form.get("pet_name") or request.form.get("name")
        species = request.form.get("species")
        breed = request.form.get("breed")
        
        # --- LOGIKA UPLOAD FOTO ---
        filename = None
        # UBAH 'photo' MENJADI 'pet_photo' DI DUA BARIS BAWAH INI:
        if 'pet_photo' in request.files:
            file = request.files['pet_photo']
            if file and file.filename != '' and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f"{uuid.uuid4().hex}.{ext}"
                
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
        # ---------------------------

        # Buat data hewan baru
        new_pet = Pet(
            id=str(uuid.uuid4())[:8],
            name=pet_name if pet_name else "Tanpa Nama",
            species=species,
            breed=breed,
            photo=filename, # Simpan nama file ke MySQL
            user_id=user.id 
        )
        
        # Simpan ke DB
        db.session.add(new_pet)
        db.session.commit()

        return redirect(url_for("klinik"))

    return render_template("add_pet.html", username=username)

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user" not in session:
        return redirect(url_for("login"))
    
    username = session["user"]
    user = User.query.filter_by(username=username).first()

    if request.method == "POST":
        # Update data user yang ada di database
        user.name = request.form.get("name")
        user.phone = request.form.get("phone")
        user.address = request.form.get("address")
        
        # Simpan perubahan
        db.session.commit()
        return render_template("profile.html", profile=user, message="Profil berhasil diperbarui!")
    
    return render_template("profile.html", profile=user)

@app.route("/create_order", methods=["GET"])
def create_order():
    if "user" not in session:
        return redirect(url_for("login"))
    
    user = User.query.filter_by(username=session["user"]).first()
    user_pets = Pet.query.filter_by(user_id=user.id).all()
    
    return render_template("create_order.html", pets=user_pets)
    

@app.route("/checkout", methods=["POST"])
def checkout():
    if "user" not in session:
        return redirect(url_for("login"))
    try:
        jarak = float(request.form.get("distance", "0"))
    except ValueError:
        jarak = 0
    bill_data = {
        "pet": request.form.get("pet"),
        "service": request.form.get("service_type"),
        "pickup": request.form.get("pickup"),
        "destination": request.form.get("destination"),
        "distance": jarak
    }
    harga_awal = 50000 if bill_data["service"] == "Mobil AC" else 20000
    service_obj = PetServices("SRV-01", bill_data["service"], harga_awal)
    bill_data["total"] = service_obj.hitungharga(jarak)
    return render_template("checkout.html", bill=bill_data)


@app.route("/about") # Kita gunakan /about agar lebih umum
def about():
    # Mengambil data dari class CompanyProfile yang sudah kamu buat di atas
    data = company_profile.get_profile()
    return render_template("about.html", data=data)


@app.route("/confirm_payment", methods=["POST"])
def confirm_payment():
    if "user" not in session:
        return redirect(url_for("login"))
    
    user = User.query.filter_by(username=session["user"]).first()
    method = request.form.get("payment_method")
    
    # Buat objek order baru
    new_order = Order(
        id_pesanan=str(uuid.uuid4())[:8].upper(),
        pet=request.form.get("pet"),
        service=request.form.get("service"),
        pickup=request.form.get("pickup"),
        destination=request.form.get("destination"),
        total=float(request.form.get("total", 0)),
        method=method,
        status="Paid" if method == "Bank Transfer" else "Pending (Cash)",
        date=datetime.now().strftime("%d %b %Y, %H:%M"),
        user_id=user.id # Hubungkan dengan ID user yang memesan
    )
    
    # Simpan ke database
    db.session.add(new_order)
    db.session.commit()
    
    return redirect(url_for("orders"))

@app.route("/orders")
def orders():
    if "user" not in session:
        return redirect(url_for("login"))
    
    user = User.query.filter_by(username=session["user"]).first()
    # Ambil semua order milik user ini
    user_orders = Order.query.filter_by(user_id=user.id).all()
    
    return render_template("orders.html", orders=user_orders)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/company")
def company():
    data = company_profile.get_profile()
    return render_template("company.html", data=data)

medical_records = {} # Format: { 'pet_id': [record1, record2] }

# # ROUTES MEDICAL RECORD
# @app.route("/medical_history/<pet_id>")
# def medical_history(pet_id):
#     if "user" not in session:
#         return redirect(url_for("login"))
    
#     # Ambil catatan medis berdasarkan ID Hewan
#     records = medical_records.get(pet_id, [])
    
#     # Cari nama hewan untuk ditampilkan di judul
#     pet_name = "Hewan"
#     username = session["user"]
#     for pet in pets_data.get(username, []):
#         if pet['id'] == pet_id:
#             pet_name = pet['name']
#             break

#     return render_template("medical_history.html", records=records, pet_name=pet_name, pet_id=pet_id)

@app.route("/add_medical_record/<pet_id>", methods=["GET", "POST"])
def add_medical_record(pet_id):
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        # Buat rekam medis baru
        new_record = MedicalRecord(
            record_id=str(uuid.uuid4())[:8].upper(),
            clinic_name=request.form.get("clinic_name"),
            visit_date=request.form.get("visit_date"),
            diagnosis=request.form.get("diagnosis"),
            treatment=request.form.get("treatment"),
            notes=request.form.get("notes"),
            pet_id=pet_id # Hubungkan ke ID hewan yang sedang diperiksa
        )

        db.session.add(new_record)
        db.session.commit()
        
        return redirect(url_for("medical_history", pet_id=pet_id))

    return render_template("add_medical_record.html", pet_id=pet_id)

@app.route("/klinik")
def klinik():
    if "user" not in session:
        return redirect(url_for("login"))
    
    user = User.query.filter_by(username=session["user"]).first()
    user_pets = Pet.query.filter_by(user_id=user.id).all()
    
    return render_template("klinik.html", username=user.username, pets=user_pets)


@app.route("/medical_history/<pet_id>")
def medical_history(pet_id):
    if "user" not in session:
        return redirect(url_for("login"))
    
    # Ambil data hewan dari DB untuk mendapatkan namanya
    pet = Pet.query.filter_by(id=pet_id).first()
    pet_name = pet.name if pet else "Hewan"
    
    # Ambil semua rekam medis yang terhubung dengan pet_id ini
    records = MedicalRecord.query.filter_by(pet_id=pet_id).all()
            
    return render_template("medical_history.html", 
                           records=records, 
                           pet_name=pet_name, 
                           pet_id=pet_id)

if __name__ == "__main__":
    app.run(debug=True)