import os
import io
import zipfile
import streamlit as st
from pypdf import PdfWriter, PdfReader

# --- PENGATURAN HALAMAN ---
st.set_page_config(
    page_title="CHRONIC TOOLS 3.0",
    page_icon="🟣",
    layout="centered"
)

# --- FUNGSI GOOGLE ANALYTICS (LANGSUNG KE HALAMAN UTAMA) ---
def add_google_analytics():
    ga_id = "G-PPE7GHXJCR"
    
    # Mengambil parameter user dari URL jika ada (contoh: ?user=nama_admin)
    query_params = st.query_params
    user_email = query_params.get("user", query_params.get("email", "Anonymous User"))

    ga_script = f"""
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={ga_id}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      
      gtag('config', '{ga_id}', {{
        'user_id': '{user_email}'
      }});
    </script>
    """
    # Menyuntikkan langsung ke DOM utama Streamlit
    st.markdown(ga_script, unsafe_allow_html=True)

# Jalankan fungsi Google Analytics
add_google_analytics()

st.title("🟣 CHRONIC TOOLS 3.0")
st.markdown("### Otomatisasi Penggabungan Resep & eBilling (Web Edition)")
st.write("Aplikasi web fleksibel untuk admin (bisa diakses via HP, Tablet, atau Laptop).")
st.markdown("---")

# --- INISIALISASI SESSION STATE ---
if "merged_results" not in st.session_state:
    st.session_state["merged_results"] = None
if "log_gagal" not in st.session_state:
    st.session_state["log_gagal"] = None
if "session_name" not in st.session_state:
    st.session_state["session_name"] = "20 OKTOBER 2026"
if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 0

# --- FUNGSI RESET / HAPUS SEMUA DATA & UPLOADER ---
def reset_session_data():
    st.session_state["merged_results"] = None
    st.session_state["log_gagal"] = None
    st.session_state["uploader_key"] += 1

# --- MENU NAVIGASI (SIDEBAR) ---
menu = st.sidebar.selectbox("📂 Pilih Menu Utama", ["1. Buat Folder & Sesi Baru", "2. Merge Resep & eBilling"])

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Hapus / Reset Semua File", type="secondary"):
    reset_session_data()
    st.sidebar.success("Semua data dan file berhasil dibersihkan!")
    st.rerun()

# ==========================================
# MENU 1: BUAT SESI / STRUKTUR FOLDER VIRTUAL
# ==========================================
if menu == "1. Buat Folder & Sesi Baru":
    st.subheader("🧩 Sesi Pengerjaan Baru")
    st.info("Di versi web, pembuatan folder fisik digantikan dengan pembuatan sesi kerja virtual untuk mengelompokkan data tanggal tersebut.")
    
    tanggal_input = st.text_input("Masukkan Nama / Tanggal Sesi (Contoh: 20 OKTOBER 2026)", value=st.session_state["session_name"])
    
    if st.button("Mulai Sesi Baru", type="primary"):
        if tanggal_input.strip():
            st.session_state["session_name"] = tanggal_input.strip()
            reset_session_data()
            st.success(f"Sesi untuk folder **'{tanggal_input}'** berhasil diaktifkan!")
            st.markdown("""
            **Struktur Virtual yang disiapkan:**
- 📁 `SCAN_RESEP` (Tempat upload file scan resep)
- 📁 `eBILLING` (Tempat upload file e-billing)
- 📁 `Hasil_Merge` (Tempat hasil gabungan PDF)
            """)
            st.warning("👉 Silakan pindah ke menu **'2. Merge Resep & eBilling'** di sebelah kiri untuk mulai mengunggah file.")
        else:
            st.warning("Nama sesi/tanggal tidak boleh kosong!")

# ==========================================
# MENU 2: MERGE RESEP & eBILLING
# ==========================================
elif menu == "2. Merge Resep & eBilling":
    st.subheader("⚙️ Proses Merge PDF Resep & eBilling (Strict Matching)")
    
    active_session = st.session_state.get("session_name", "Sesi Default")
    st.markdown(f"📌 **Sesi Aktif:** `{active_session}`")
    
    col1, col2 = st.columns(2)
    
    current_key = st.session_state["uploader_key"]
    
    with col1:
        st.markdown("#### 📥 SCAN RESEP")
        scan_files = st.file_uploader(
            "Upload file PDF Scan Resep", 
            type=["pdf"], 
            accept_multiple_files=True,
            key=f"scan_upload_{current_key}"
        )
        
    with col2:
        st.markdown("#### 📥 eBILLING")
        ebill_files = st.file_uploader(
            "Upload file PDF e-Billing", 
            type=["pdf"], 
            accept_multiple_files=True,
            key=f"ebill_upload_{current_key}"
        )
    
    if scan_files or ebill_files:
        st.markdown("")
        if st.button("🗑️ Kosongkan Semua File yang Di-upload (Reset Uploader)"):
            reset_session_data()
            st.success("Semua file di kotak uploader berhasil dikosongkan!")
            st.rerun()
        
    st.markdown("---")
    
    if scan_files and ebill_files:
        scan_dict = {f.name: f for f in scan_files}
        ebill_dict = {f.name: f for f in ebill_files}
        
        scan_names = set(scan_dict.keys())
        ebill_names = set(ebill_dict.keys())
        
        nama_sama = sorted(list(scan_names.intersection(ebill_names)))
        hanya_di_scan = sorted(list(scan_names - ebill_names))
        hanya_di_ebill = sorted(list(ebill_names - scan_names))
        
        st.markdown("### 🔍 Analisis Pencocokan Nama File (Strict):")
        m1, m2, m3 = st.columns(3)
        m1.metric("Nama Sama & Valid", len(nama_sama))
        m2.metric("Hanya di Scan Resep", len(hanya_di_scan))
        m3.metric("Hanya di eBilling", len(hanya_di_ebill))
        
        preview_data = []
        for name in sorted(scan_names.union(ebill_names)):
            if name in nama_sama:
                status = "✅ Sesuai (Akan Digabung)"
            else:
                status = "❌ Tidak Ada Pasangan (Dilewati)"
            
            preview_data.append({
                "Nama File": name,
                "Ada di SCAN_RESEP": "✔️" if name in scan_names else "❌",
                "Ada di eBILLING": "✔️" if name in ebill_names else "❌",
                "Status Pencocokan": status
            })
        st.table(preview_data)
        
        if len(hanya_di_scan) > 0 or len(hanya_di_ebill) > 0:
            st.warning("⚠️ Ada file yang tidak memiliki nama kembaran/pasangan di folder seberang. File tersebut **tidak akan digabung** dan otomatis masuk ke log error.")

        btn_merge = st.button("🚀 Mulai Proses Merge Hanya Nama yang Sama", type="primary")

        if btn_merge:
            if not nama_sama:
                st.error("❌ Tidak ada satupun nama file yang sama persis! Proses dibatalkan.")
            else:
                log_gagal = []
                merged_results = {}
                
                for f_scan in hanya_di_scan:
                    log_gagal.append((f_scan, "-", "File Scan Resep tidak memiliki pasangan nama eBilling yang sama persis."))
                for f_ebill in hanya_di_ebill:
                    log_gagal.append(("-", f_ebill, "File eBilling tidak memiliki pasangan nama Scan Resep yang sama persis."))
                
                with st.spinner("Sedang memproses penggabungan file yang namanya sama..."):
                    for filename in nama_sama:
                        scan_f = scan_dict[filename]
                        ebill_f = ebill_dict[filename]
                        try:
                            scan_bytes = scan_f.getvalue()
                            ebill_bytes = ebill_f.getvalue()
                            
                            if scan_bytes.startswith(b'<') or ebill_bytes.startswith(b'<'):
                                raise ValueError("File terdeteksi berisi kode HTML/Error, bukan PDF biner murni.")
                            
                            merger = PdfWriter()
                            reader_scan = PdfReader(io.BytesIO(scan_bytes), strict=False)
                            reader_ebill = PdfReader(io.BytesIO(ebill_bytes), strict=False)
                            
                            merger.append(reader_scan)
                            merger.append(reader_ebill)
                            
                            output_buffer = io.BytesIO()
                            merger.write(output_buffer)
                            merger.close()
                            
                            merged_results[filename] = output_buffer.getvalue()
                        except Exception as e:
                            log_gagal.append((filename, filename, str(e)))
                
                st.session_state["merged_results"] = merged_results
                st.session_state["log_gagal"] = log_gagal
                st.success(f"🎉 Berhasil menggabungkan {len(merged_results)} pasang file yang namanya sama!")
                st.rerun()

    else:
        st.info("💡 Silakan unggah file PDF pada kedua kolom **SCAN RESEP** dan **eBILLING** di atas untuk mulai mencocokkan nama file.")

    # --- BAGIAN DOWNLOAD & PENGHAPUSAN HASIL ---
    if st.session_state["merged_results"]:
        st.markdown("---")
        st.markdown("### 📥 Download Hasil Akhir:")
        
        merged_results = st.session_state["merged_results"]
        log_gagal = st.session_state["log_gagal"]
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for filename, file_bytes in merged_results.items():
                zip_file.writestr(filename, file_bytes)
            
            if log_gagal:
                log_text = "=== LOG KEGAGALAN / FILE TIDAK BERPASANGAN (STRICT MODE) ===\n\n"
                for s, b, err in log_gagal:
                    log_text += f"Scan Resep: {s} | eBilling: {b} | Keterangan: {err}\n"
                zip_file.writestr("log_gagal.txt", log_text.encode("utf-8"))
        
        st.download_button(
            label="📦 Download Semua Hasil (Format .ZIP + Log)",
            data=zip_buffer.getvalue(),
            file_name=f"Hasil_Merge_{active_session.replace(' ', '_')}.zip",
            mime="application/zip",
            type="primary"
        )
        
        if st.button("🗑️ Selesai & Bersihkan Semua File (Reset Total)"):
            reset_session_data()
            st.success("Semua file upload dan hasil kerja berhasil dibersihkan dari memori.")
            st.rerun()
        
        with st.expander("Lihat & Download File Satuan"):
            for fname, fbytes in merged_results.items():
                st.download_button(
                    label=f"📥 Download {fname}",
                    data=fbytes,
                    file_name=fname,
                    mime="application/pdf",
                    key=f"dl_satuan_{fname}"
                )
                
        if log_gagal:
            st.error("⚠️ Catatan file yang dilewati karena nama tidak sama:")
            for s, b, err in log_gagal:
                st.write(f"- Scan: **{s}** | eBilling: **{b}** -> `{err}`")

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>CHRONIC TOOLS 3.0 (Web Edition) • Created by Moa Wahid</p>", unsafe_allow_html=True)
