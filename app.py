import streamlit as st
import sqlite3
import os
from PIL import Image

# Config
DB_NAME = "patients.db"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ACCESS_CODE = "okeoke"

# Authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Akses Terkunci")
    input_code = st.text_input("Masukkan kode akses untuk membuka halaman:", type="password")
    if st.button("Masuk"):
        if input_code == ACCESS_CODE:
            st.session_state.authenticated = True
            st.rerun()  # <-- ini benar ada di dalam button
        else:
            st.error("Kode salah.")
    st.stop()


# Session defaults
if "page" not in st.session_state:
    st.session_state.page = "Daftar Pasien"
if "selected_patient" not in st.session_state:
    st.session_state.selected_patient = None

# URL params handler
params = st.query_params

def load_query_params():
    params = st.query_params

    if "pid" in params and st.session_state.selected_patient is None:
        try:
            pid = int(params["pid"][0])
            st.session_state.selected_patient = pid
            st.session_state.page = "Detail Pasien"
        except:
            st.error("Parameter 'pid' tidak valid.")

load_query_params()


# DB connection
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

def save_patient(name, description, filenames, labels):
    filenames_str = ",".join(filenames)
    labels_str = ",".join(labels)
    c.execute("INSERT INTO patients (name, description, filenames, labels) VALUES (?, ?, ?, ?)",
              (name, description, filenames_str, labels_str))
    conn.commit()

def get_all_patients():
    c.execute("SELECT id, name, description FROM patients")
    return c.fetchall()

def get_patient_by_id(pid):
    c.execute("SELECT name, description, filenames, labels FROM patients WHERE id = ?", (pid,))
    return c.fetchone()

def generate_share_link(pid):
    return f"https://dentalyaska.streamlit.app/?pid={pid}"

def load_and_process_image(path, target_height=400):
    img = Image.open(path)
    w, h = img.size
    new_w = int(w * target_height / h)
    img = img.resize((new_w, target_height))
    # Crop center if landscape
    if new_w > target_height:
        left = (new_w - target_height) // 2
        right = left + target_height
        img = img.crop((left, 0, right, target_height))
    return img

def upload_page():
    st.header("Upload Foto Pasien")
    name = st.text_input("Nama Pasien")
    description = st.text_input("Deskripsi Kasus")

    # Before & After pairs to upload
    photo_inputs = {
        "panoramic_opg_before": "Panoramic/OPG Before",
        "panoramic_opg_after": "Panoramic/OPG After",
        "foto_frontal_before": "Foto Frontal Before",
        "foto_frontal_after": "Foto Frontal After",
        "foto_senyum_before": "Foto Senyum Before",
        "foto_senyum_after": "Foto Senyum After",
        "foto_lateral_before": "Foto Lateral Before",
        "foto_lateral_after": "Foto Lateral After",
        "intra_oral_kanan_before": "Intra Oral Kanan Before",
        "intra_oral_kanan_after": "Intra Oral Kanan After",
        "intra_oral_depan_before": "Intra Oral Depan Before",
        "intra_oral_depan_after": "Intra Oral Depan After",
        "intra_oral_kiri_before": "Intra Oral Kiri Before",
        "intra_oral_kiri_after": "Intra Oral Kiri After",
        "oklusal_rahang_atas_before": "Oklusal Rahang Atas Before",
        "oklusal_rahang_atas_after": "Oklusal Rahang Atas After",
        "oklusal_rahang_bawah_before": "Oklusal Rahang Bawah Before",
        "oklusal_rahang_bawah_after": "Oklusal Rahang Bawah After",
        "foto_tambahan_lateral_kanan_before": "Foto Tambahan Lateral Kanan Before",
        "foto_tambahan_lateral_kanan_after": "Foto Tambahan Lateral Kanan After",
        "foto_tambahan_lateral_kanan_senyum_before": "Foto Tambahan Lateral Kanan Senyum Before",
        "foto_tambahan_lateral_kanan_senyum_after": "Foto Tambahan Lateral Kanan Senyum After",
        "foto_tambahan_depan_bracket_behel_before": "Foto Tambahan Depan Bracket Behel Before",
        "foto_tambahan_depan_bracket_behel_after": "Foto Tambahan Depan Bracket Behel After",
    }

    uploaded_filenames = []
    uploaded_labels = []

    for key, label in photo_inputs.items():
        file = st.file_uploader(label, type=["jpg", "jpeg", "png"], key=key)
        if file:
            safe_name = f"{key}_{file.name}"
            filepath = os.path.join(UPLOAD_FOLDER, safe_name)
            with open(filepath, "wb") as f:
                f.write(file.read())
            uploaded_filenames.append(safe_name)
            uploaded_labels.append(label)

    if st.button("Simpan Data Pasien"):
        if name.strip() and description.strip() and uploaded_filenames:
            save_patient(name.strip(), description.strip(), uploaded_filenames, uploaded_labels)
            st.success("Data pasien berhasil disimpan.")
            st.rerun()
        else:
            st.error("Mohon isi semua data dan upload minimal satu foto.")

def delete_patient(pid):
    # Hapus data dari DB
    c.execute("SELECT filenames FROM patients WHERE id = ?", (pid,))
    row = c.fetchone()
    if row:
        filenames_str = row[0]
        filenames = filenames_str.split(",")
        # Hapus file foto dari folder
        for fn in filenames:
            try:
                os.remove(os.path.join(UPLOAD_FOLDER, fn))
            except FileNotFoundError:
                pass
    c.execute("DELETE FROM patients WHERE id = ?", (pid,))
    conn.commit()

def patients_page():
    st.header("Daftar Pasien")
    patients = get_all_patients()

    if not patients:
        st.info("Belum ada data pasien.")
        return

    for pid, name, desc in patients:
        col1, col2, col3, col4 = st.columns([4, 2, 2, 5])
        with col1:
            st.markdown(f"**{name}** - {desc}")
        with col2:
            link = generate_share_link(pid)
            st.markdown(
                f'<a href="{link}" target="_blank"><button>Lihat Detail</button></a>',
                unsafe_allow_html=True
            )
        with col3:
            # Checkbox untuk konfirmasi hapus
            confirm_key = f"confirm_delete_{pid}"
            if st.checkbox("Hapus", key=confirm_key):
                if st.button("🗑️ Hapus", key=f"delete_{pid}"):
                    delete_patient(pid)
                    st.success("Data pasien berhasil dihapus.")
                    st.rerun()

        with col4:
            link = generate_share_link(pid)
            st.markdown(
                f"""
                <div style='display: flex; align-items: center; gap: 10px;'>
                    <strong>Link Share:</strong>
                    <input type="text" value="{link}" readonly 
                        style="flex: 1; padding: 6px; border: 1px solid #ccc; border-radius: 5px;">
                </div>
                """,
                unsafe_allow_html=True
            )


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

    # Group photos by base label and before/after
    # "foto_frontal_before" -> base = "foto_frontal", state = "before"
    grouped_photos = {}
    for f, l in zip(filenames, labels):
        # coba pisah label: expect label punya "_Before" atau "_After" (case insensitive)
        # Contoh label: "Foto Frontal Before"
        parts = l.lower().split()
        if parts[-1] in ("before", "after"):
            state = parts[-1]
            base_label = " ".join(parts[:-1]).title()
        else:
            # fallback
            state = "before"
            base_label = l.title()

        if base_label not in grouped_photos:
            grouped_photos[base_label] = {}
        grouped_photos[base_label][state] = grouped_photos[base_label].get(state, []) + [f]

    # Tampilkan foto before after berdampingan dengan portrait resize
    for base_label, images in grouped_photos.items():
        st.markdown(f"### {base_label}")

        cols = st.columns(2)

        with cols[0]:
            if "before" in images:
                st.markdown("**Before**")
                img_before = load_and_process_image(os.path.join(UPLOAD_FOLDER, images["before"][0]))
                st.image(img_before, use_container_width=True)

        with cols[1]:
            if "after" in images:
                st.markdown("**After**")
                img_after = load_and_process_image(os.path.join(UPLOAD_FOLDER, images["after"][0]))
                st.image(img_after, use_container_width=True)

        st.markdown("---")




    if st.button("⬅️ Kembali ke Daftar Pasien"):
        st.session_state.page = "Daftar Pasien"
        st.session_state.selected_patient = None
        st.set_query_params(**{})  # Clear all query params, including pid
        st.experimental_rerun()



# Sidebar navigation (hide if using ?pid=)
if "pid" not in params:
    default_index = 1 if st.session_state.page == "Daftar Pasien" else 0
    menu = st.sidebar.radio("Pilih Halaman", ["Upload", "Daftar Pasien"], key="menu_radio", index=default_index)
    st.session_state.page = menu

# Routing
if st.session_state.page == "Upload":
    upload_page()
elif st.session_state.page == "Daftar Pasien":
    patients_page()
elif st.session_state.page == "Detail Pasien":
    detail_page()
