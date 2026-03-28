from flask import Flask, render_template, request, redirect, url_for, session
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
# DATA SEMENTARA (DATABASE MOCKUP)
# ==============================
# Pindahkan semua dictionary ke atas agar bisa diakses semua route
pets_data = {}
orders_data = {}
user_profiles = {}

# ==============================
# LOGIKA BISNIS (CLASSES)
# ==============================
class AuthSystem:
    def __init__(self):
        self.accounts = {}

    def register(self, username, email, password):
        if username in self.accounts:
            return "Username sudah terdaftar!"
        self.accounts[username] = {
            "email": email,
            "password": password
        }
        return "Registrasi berhasil!"

    def login(self, email, password):
        for username, data in self.accounts.items():
            if data["email"] == email and data["password"] == password:
                return username
        return None

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

auth_system = AuthSystem()
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
        result = auth_system.register(username, email, password)
        if result == "Registrasi berhasil!":
            return redirect(url_for("login", s="success"))
        else:
            message = result
    return render_template("register.html", message=message)

@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        username = auth_system.login(email, password)
        if username:
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            message = "Login gagal!"
    return render_template("login.html", message=message)

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    username_login = session["user"]
    
    # Ambil Data Profil
    profile_data = user_profiles.get(username_login, {})
    display_name = profile_data.get("name", username_login)

    # Ambil Daftar Hewan (PENTING untuk Medical Record)
    user_pets = pets_data.get(username_login, [])

    # Ambil Order Terakhir
    user_orders = orders_data.get(username_login, [])
    latest_order = user_orders[-1] if user_orders else None

    return render_template("dashboard.html", 
                           username=display_name, 
                           pets=user_pets,  # Kirim list hewan ke HTML
                           latest_order=latest_order)

@app.route("/add_pet", methods=["GET", "POST"])
def add_pet():
    if "user" not in session:
        return redirect(url_for("login"))
    
    username = session["user"]
    
    if request.method == "POST":
        # Ambil data dari form (Pastikan atribut 'name' di HTML-mu sesuai)
        pet_name = request.form.get("pet_name") or request.form.get("name")
        species = request.form.get("species")
        breed = request.form.get("breed")
        
        # Buat ID unik
        new_pet = {
            "id": str(uuid.uuid4())[:8],
            "name": pet_name if pet_name else "Tanpa Nama", # Mencegah muncul 'None'
            "species": species,
            "breed": breed,
            "photo": None # Set ke None dulu untuk pengecekan di HTML
        }

        if username not in pets_data:
            pets_data[username] = []
        
        pets_data[username].append(new_pet)

        # SELESAI DAFTAR, LANGSUNG KE HALAMAN KLINIK
        return redirect(url_for("klinik"))

    return render_template("add_pet.html", username=username)

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user" not in session:
        return redirect(url_for("login"))
    username = session["user"]
    if request.method == "POST":
        user_profiles[username] = {
            "name": request.form.get("name"),
            "phone": request.form.get("phone"),
            "address": request.form.get("address")
        }
        return render_template("profile.html", profile=user_profiles[username], message="Profil berhasil diperbarui!")
    profile_data = user_profiles.get(username, {"name": username, "phone": "", "address": ""})
    return render_template("profile.html", profile=profile_data)

@app.route("/create_order", methods=["GET"])
def create_order():
    if "user" not in session:
        return redirect(url_for("login"))
    user = session["user"]
    user_pets = pets_data.get(user, [])
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
    user = session["user"]
    method = request.form.get("payment_method")
    new_order = {
        "id_pesanan": str(uuid.uuid4())[:8].upper(),
        "pet": request.form.get("pet"),
        "service": request.form.get("service"),
        "pickup": request.form.get("pickup"),
        "destination": request.form.get("destination"),
        "total": float(request.form.get("total", 0)),
        "method": method,
        "status": "Paid" if method == "Bank Transfer" else "Pending (Cash)",
        "date": datetime.now().strftime("%d %b %Y, %H:%M")
    }
    if user not in orders_data:
        orders_data[user] = []
    orders_data[user].append(new_order)
    return redirect(url_for("orders"))

@app.route("/orders")
def orders():
    if "user" not in session:
        return redirect(url_for("login"))
    user = session["user"]
    user_orders = orders_data.get(user, [])
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
        # Sesuai atribut di CRC Card: clinicName, visitDate, diagnosis, treatment
        new_record = {
            "record_id": str(uuid.uuid4())[:8].upper(),
            "clinic_name": request.form.get("clinic_name"),
            "visit_date": request.form.get("visit_date"),
            "diagnosis": request.form.get("diagnosis"),
            "treatment": request.form.get("treatment"),
            "notes": request.form.get("notes")
        }

        if pet_id not in medical_records:
            medical_records[pet_id] = []
        
        medical_records[pet_id].append(new_record)
        return redirect(url_for("medical_history", pet_id=pet_id))

    return render_template("add_medical_record.html", pet_id=pet_id)

@app.route("/klinik")
def klinik():
    if "user" not in session:
        return redirect(url_for("login"))
    
    username = session["user"]
    # Ambil data hewan milik user dari database/dictionary
    user_pets = pets_data.get(username, []) 
    
    return render_template("klinik.html", username=username, pets=user_pets)


@app.route("/medical_history/<pet_id>")
def medical_history(pet_id):
    if "user" not in session:
        return redirect(url_for("login"))
    
    username = session["user"]
    records = medical_records.get(pet_id, [])
    
    # 1. Inisialisasi pet_name dengan nilai default agar tidak Error
    pet_name = "Hewan" 
    
    # 2. Cari nama hewan yang sesuai dengan pet_id
    user_pets = pets_data.get(username, [])
    for pet in user_pets:
        if pet['id'] == pet_id:
            pet_name = pet['name']
            break # Hentikan loop jika sudah ketemu
            
    return render_template("medical_history.html", 
                           records=records, 
                           pet_name=pet_name, 
                           pet_id=pet_id)

if __name__ == "__main__":
    app.run(debug=True)