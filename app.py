import streamlit as st
import sqlite3
import os

# Konfigurasi dasar
DB_NAME = "patients.db"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Inisialisasi session state
if "page" not in st.session_state:
    st.session_state.page = "Upload"
if "selected_patient" not in st.session_state:
    st.session_state.selected_patient = None

# Koneksi database
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        filenames TEXT NOT NULL,
        labels TEXT NOT NULL
    )
''')
conn.commit()

# Fungsi simpan pasien
def save_patient(name, description, filenames, labels):
    filenames_str = ",".join(filenames)
    labels_str = ",".join(labels)
    c.execute("INSERT INTO patients (name, description, filenames, labels) VALUES (?, ?, ?, ?)",
              (name, description, filenames_str, labels_str))
    conn.commit()

# Fungsi ambil semua pasien
def get_all_patients():
    c.execute("SELECT id, name, description FROM patients")
    return c.fetchall()

# Fungsi ambil detail pasien
def get_patient_by_id(pid):
    c.execute("SELECT name, description, filenames, labels FROM patients WHERE id = ?", (pid,))
    return c.fetchone()

# Halaman Upload
def upload_page():
    st.header("Upload Foto Pasien")
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
        file = st.file_uploader(f"{label}", type=["jpg", "jpeg", "png"], key=key)
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
            st.error("Mohon isi semua data dan upload minimal satu foto.")

# Halaman Daftar Pasien
def patients_page():
    st.header("Daftar Pasien")
    patients = get_all_patients()

    if not patients:
        st.info("Belum ada data pasien.")
        return

    for pid, name, desc in patients:
        col1, col2 = st.columns([6, 1])
        with col1:
            st.markdown(f"**{name}** - {desc}")
        with col2:
            if st.button("Lihat Detail", key=f"view_{pid}"):
                st.session_state.clicked_button_id = pid


# Halaman Detail Pasien
def detail_page():
    if st.session_state.selected_patient is None:
        st.warning("Silakan pilih pasien dari daftar.")
        return

    pid = st.session_state.selected_patient
    data = get_patient_by_id(pid)
    if not data:
        st.error("Data pasien tidak ditemukan.")
        return

    name, desc, filenames_str, labels_str = data
    filenames = filenames_str.split(",")
    labels = labels_str.split(",")

    st.markdown(f"<h1 style='text-align:center; color:#4CAF50;'>Foto Pasien: {name}</h1>", unsafe_allow_html=True)
    st.caption(desc)

    num_cols = 3
    for i in range(0, len(filenames), num_cols):
        cols = st.columns(num_cols)
        for j in range(num_cols):
            idx = i + j
            if idx < len(filenames):
                with cols[j]:
                    st.image(os.path.join(UPLOAD_FOLDER, filenames[idx]),
                        caption=labels[idx],
                        use_container_width=True)

    st.markdown("<div style='text-align:center; margin-top:30px;'>", unsafe_allow_html=True)
    if st.button("⬅️ Kembali ke Daftar Pasien"):
        st.session_state.page = "Daftar Pasien"
        st.rerun()
 
# Sidebar Navigasi
menu = st.sidebar.radio("Pilih Halaman", ["Upload", "Daftar Pasien"])
if menu == "Upload":
    st.session_state.page = "Upload"
elif menu == "Daftar Pasien":
    st.session_state.page = "Daftar Pasien"

# Tangani klik tombol detail pasien
if "clicked_button_id" in st.session_state:
    st.session_state.selected_patient = st.session_state.clicked_button_id
    st.session_state.page = "Detail Pasien"
    del st.session_state.clicked_button_id  # reset setelah navigasi

# Routing utama
if st.session_state.page == "Upload":
    upload_page()
elif st.session_state.page == "Daftar Pasien":
    patients_page()
elif st.session_state.page == "Detail Pasien":
    detail_page()

