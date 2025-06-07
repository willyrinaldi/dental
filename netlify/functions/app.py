from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

# Specify the path for the template folder explicitly
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '../../templates'))

# Konfigurasi database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///patients.db'
app.config['UPLOAD_FOLDER'] = '../../uploads'  # Use /tmp for Netlify functions
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
    return render_template('index.html')  # Flask should now find this template in the '../templates' folder

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
def upload():
    required_files = [
        'panoramic_opg', 'foto_frontal', 'foto_senyum', 'foto_lateral',
        'intra_oral_kanan', 'intra_oral_depan', 'intra_oral_kiri',
        'oklusal_rahang_atas', 'oklusal_rahang_bawah', 'foto_tambahan_lateral_kanan',
        'foto_tambahan_lateral_kanan_senyum', 'foto_tambahan_depan_bracket_behel'
    ]

    for file in required_files:
        if file not in request.files:
            return f'Missing file for {file}', 400

    files = {
        'panoramic_opg': request.files['panoramic_opg'],
        'foto_frontal': request.files['foto_frontal'],
        'foto_senyum': request.files['foto_senyum'],
        'foto_lateral': request.files['foto_lateral'],
        'intra_oral_kanan': request.files['intra_oral_kanan'],
        'intra_oral_depan': request.files['intra_oral_depan'],
        'intra_oral_kiri': request.files['intra_oral_kiri'],
        'oklusal_rahang_atas': request.files['oklusal_rahang_atas'],
        'oklusal_rahang_bawah': request.files['oklusal_rahang_bawah'],
        'foto_tambahan_lateral_kanan': request.files['foto_tambahan_lateral_kanan'],
        'foto_tambahan_lateral_kanan_senyum': request.files['foto_tambahan_lateral_kanan_senyum'],
        'foto_tambahan_depan_bracket_behel': request.files['foto_tambahan_depan_bracket_behel']
    }

    labels = [
        'Panoramic/OPG', 'Foto Frontal', 'Foto Senyum', 'Foto Lateral',
        'Intra Oral Kanan', 'Intra Oral Depan', 'Intra Oral Kiri',
        'Oklusal Rahang Atas', 'Oklusal Rahang Bawah', 'Foto Tambahan Lateral Kanan',
        'Foto Tambahan Lateral Kanan Senyum', 'Foto Tambahan Depan Bracket Behel'
    ]

    filenames = []
    file_labels = []

    for key, label in zip(files.keys(), labels):
        file = files[key]
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            filenames.append(filename)
            file_labels.append(label)

    patient_name = request.form['patient_name']
    description = request.form['description']
    filenames_str = ','.join(filenames)
    labels_str = ','.join(file_labels)

    new_patient = Patient(name=patient_name, description=description, filenames=filenames_str, labels=labels_str)
    db.session.add(new_patient)
    db.session.commit()

    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Membuat database jika belum ada
    app.run(debug=True, host='0.0.0.0', port=8181)
