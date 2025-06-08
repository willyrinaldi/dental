from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# Konfigurasi database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///patients.db'
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
db = SQLAlchemy(app)

# Model untuk menyimpan data pasien dan foto
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    filenames = db.Column(db.String(1000), nullable=False)  # Menyimpan nama file foto sebagai string
    labels = db.Column(db.String(1000), nullable=False)  # Menyimpan label foto sebagai string

    def __repr__(self):
        return f'<Patient {self.name}>'

# Fungsi untuk memeriksa ekstensi file yang diizinkan
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Menambahkan route untuk melayani file dari folder 'uploads'
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Halaman utama (Frontend)
@app.route('/')
def index():
    return render_template('index.html')

# Halaman daftar pasien
@app.route('/patients')
def patients():
    patients = Patient.query.all()
    patients_list = [{"id": p.id, "name": p.name, "category": p.description} for p in patients]
    return jsonify(patients=patients_list)

# Halaman detail pasien dan foto
@app.route('/patient/<int:patient_id>/photos')
def view_photos(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    filenames = patient.filenames.split(',')  # Pisahkan nama file berdasarkan koma
    labels = patient.labels.split(',')  # Pisahkan label berdasarkan koma

    # Combine filenames and labels
    photos = [{'filename': filename, 'label': label} for filename, label in zip(filenames, labels)]

    return render_template('view_photos.html', patient=patient, photos=photos)


# Form upload foto pasien
@app.route('/upload', methods=['POST'])
def upload_files():
    st.title("Upload Foto Pasien")
    name = st.text_input("Nama Pasien")
    description = st.text_input("Deskripsi Kasus")

    photo_inputs = {
        "panoramic_opg": "Panoramic/OPG",
        "foto_frontal": "Foto Frontal",
        "foto_senyum": "Foto Senyum",
        "foto_lateral": "Foto Lateral",
        "intra_oral_kanan": "Intra Oral Kanan",
        "intra_oral_depan": "Intra Oral Depan",
        "intra_oral_kiri": "Intra Oral Kiri",
        "oklusal_rahang_atas": "Oklusal Rahang Atas",
        "oklusal_rahang_bawah": "Oklusal Rahang Bawah",
        "foto_tambahan_lateral_kanan": "Foto Tambahan Lateral Kanan",
        "foto_tambahan_lateral_kanan_senyum": "Foto Tambahan Lateral Kanan Senyum",
        "foto_tambahan_depan_bracket_behel": "Foto Tambahan Depan Bracket Behel"
    }

    uploaded_filenames = []
    uploaded_labels = []

    for key, label in photo_inputs.items():
        file = st.file_uploader(f"Upload {label}", type=["png", "jpg", "jpeg"], key=key)
        if file:
            filepath = os.path.join(UPLOAD_FOLDER, file.name)
            with open(filepath, "wb") as f:
                f.write(file.read())
            uploaded_filenames.append(file.name)
            uploaded_labels.append(label)

    if st.button("Simpan Data Pasien"):
        if name and description and uploaded_filenames:
            save_patient(name, description, uploaded_filenames, uploaded_labels)
            st.success("Data pasien berhasil disimpan.")
        else:
            st.error("Mohon isi nama, deskripsi, dan upload minimal satu foto.")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Membuat database jika belum ada
    app.run(debug=True, host='0.0.0.0', port=8181)
