


from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import uuid
import pandas as pd
from werkzeug.utils import secure_filename
from sqlalchemy.orm import Session
from fastapi import Depends  # Kita pinjam konsep Depends untuk get_db
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import numpy as np
import pickle 
from flask import Response
app = Flask(__name__)
# Impor model dan koneksi DB Anda
# Sesuaikan path impor ini dengan struktur proyek Anda
from database import get_db, engine 
from models.dataset import Dataset
from models.produk import Produk
from kneed import KneeLocator 
from database import get_db
from models.dataset import Dataset
from models.produk import Produk
# ... (semua impor Anda, pastikan ada impor untuk kneed, silhouette_score, dll)
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score # DBI tetap kita hitung
from datetime import datetime


# CORS configuration - very permissive for testing
CORS(app, 
     origins=["http://localhost:5173", "http://127.0.0.1:5173"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "Accept"],
     supports_credentials=True)
# Di dalam file backend/app.py

# === 2. TAMBAHKAN KONFIGURASI DATABASE DI SINI ===
# app.config['MYSQL_HOST'] = 'localhost'       # Atau alamat IP server DB Anda
# app.config['MYSQL_USER'] = 'root'            # Username DB Anda
# app.config['MYSQL_PASSWORD'] = 'riyani_100205' # Password DB Anda
# app.config['MYSQL_DB'] = 'db_segmentasi_produk' # Nama database Anda
# app.config['MYSQL_CURSORCLASS'] = 'DictCursor' # Ini akan membuat hasil 

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify({'message': 'OK'})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

@app.route("/", methods=["GET"])
def health_check():
    print("✅ Health check endpoint hit")
    return jsonify({
        "message": "API is running", 
        "status": "OK",
        "port": 8000
    }), 200

@app.route("/login", methods=["POST", "OPTIONS"])
def login():
    if request.method == "OPTIONS":
        return jsonify({'message': 'OK'}), 200
    
    try:
        print("🔍 Login endpoint hit")
        print(f"Request method: {request.method}")
        print(f"Request headers: {dict(request.headers)}")
        
        # Get JSON data
        data = request.get_json()
        print(f"📝 Received data: {data}")
        
        if not data:
            print("❌ No data provided")
            return jsonify({"message": "No data provided"}), 400
        
        email = data.get("email")
        password = data.get("password")
        
        print(f"Email: {email}, Password: {'*' * len(password) if password else None}")
        
        if not email or not password:
            return jsonify({"message": "Email dan password harus diisi"}), 400
        
        # Simple test - accept any email/password for now
        if email and password:
            print("✅ Login successful (test mode)")
            return jsonify({
                "message": "Login berhasil (test mode)",
                "user_id": 1,
                "nama": "Test User",
                "email": email
            }), 200
        else:
            return jsonify({"message": "Email atau password salah"}), 401
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"message": f"Server error: {str(e)}"}), 500

@app.route("/register", methods=["POST", "OPTIONS"])
def register():
    if request.method == "OPTIONS":
        return jsonify({'message': 'OK'}), 200
        
    try:
        print("🔍 Register endpoint hit")
        data = request.get_json()
        print(f"📝 Received data: {data}")
        
        if not data:
            return jsonify({"message": "No data provided"}), 400
        
        nama = data.get("name")
        email = data.get("email")
        password = data.get("password")
        
        if not nama or not email or not password:
            return jsonify({"message": "Semua field harus diisi"}), 400
        
        # Simple test - accept any registration for now
        print("✅ Registration successful (test mode)")
        return jsonify({"message": "Registrasi berhasil (test mode)"}), 201
        
    except Exception as e:
        print(f"❌ Register error: {e}")
        return jsonify({"message": f"Server error: {str(e)}"}), 500
    
# --- ENDPOINT BARU UNTUK DASHBOARD ---
@app.route("/dashboard/summary", methods=["GET"])
def dashboard_summary():
    """
    Endpoint untuk menyediakan data ringkasan untuk halaman dashboard.
    Untuk saat ini, kita akan menggunakan data dummy.
    """
    try:
        # Dalam implementasi nyata, Anda akan mengambil user_id dari sesi atau token
        # user_id = get_current_user_id() 
        # Dan kemudian menjalankan query SQL berdasarkan user_id tersebut.
        
        # Data dummy yang sesuai dengan tampilan Anda
        summary_data = {
            "total_produk": 1247,
            "total_transaksi": 3891,
            "upload_terakhir": "2 hari yang lalu", # Ini bisa dihitung dari tanggal
            "k_means_terakhir": 3,
            "clustering_summary": {
                "labels": ["Cluster 1", "Cluster 2", "Cluster 3"],
                "data": [412, 387, 448]
            },
            "aktivitas_terbaru": [
                {
                    "id": 1,
                    "deskripsi": "Data penjualan berhasil diupload",
                    "waktu": "2 jam lalu"
                },
                {
                    "id": 2,
                    "deskripsi": "Proses K-Means selesai",
                    "waktu": "3 jam lalu"
                },
                {
                    "id": 3,
                    "deskripsi": "Hasil clustering didownload",
                    "waktu": "5 jam lalu"
                }
            ]
        }
        
        return jsonify(summary_data), 200

    except Exception as e:
        print(f"❌ Dashboard summary error: {e}")
        return jsonify({"message": f"Server error: {str(e)}"}), 500
    

UPLOAD_FOLDER = 'temp_uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

## === MODIFIKASI 1: Tambahkan 'bulan' dan 'tahun' ke ALIAS_MAPPING ===
ALIAS_MAPPING = {
    "nama_produk": ["nama_produk", "produk", "item", "product_name", "nama barang"],
    "jumlah_terjual": ["jumlah_terjual", "kuantitas", "qty", "jumlah", "kuantitas_terjual", "terjual"],
    "harga": ["harga", "harga_satuan", "unit_price", "price"],
    "tanggal_transaksi": ["tanggal", "tanggal_transaksi", "tgl", "transaction_date", "date"],
    "kategori_produk": ["kategori", "sub_kategori", "kategori_produk", "category"],
    # Tambahan PENTING agar sistem mencari kolom-kolom ini
    "bulan": ["bulan", "month"],
    "tahun": ["tahun", "year"]
}
KOLOM_INTI = ["nama_produk", "jumlah_terjual", "harga", "tanggal_transaksi"]


# # ======================================================================
# # ENDPOINT 1: UPLOAD & PREVIEW DATA
# # ======================================================================


# ======================================================================
# ENDPOINT UPLOAD & PREVIEW DATA
# ======================================================================

@app.route("/upload/preview", methods=["POST"])
def upload_preview():
    try:
        # Validasi file
        if 'file' not in request.files:
            return jsonify({"message": "Tidak ada file yang diunggah"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"message": "Tidak ada file yang dipilih"}), 400
        
        if not file or not allowed_file(file.filename):
            return jsonify({"message": "Tipe file tidak valid. Gunakan CSV atau Excel."}), 400

        print("\n--- [DEBUG] Memulai Proses Upload ---")
        
        # Generate unique session ID
        upload_session_id = str(uuid.uuid4())
        print(f"[DEBUG] Generated upload_session_id: {upload_session_id}")
        
        # Load data
        if 'csv' in file.filename.lower():
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        
        print(f"[DEBUG] Nama kolom ASLI dari file: {df.columns.tolist()}")
        
        # Simpan kolom asli untuk referensi
        original_columns = df.columns.tolist()
        
        # Standarisasi kolom
        df.columns = df.columns.str.lower().str.strip()
        print(f"[DEBUG] Nama kolom SETELAH standarisasi: {df.columns.tolist()}")

        if df.empty:
            return jsonify({"message": "File yang diunggah kosong."}), 400

        mapped_info = {}
        processed_df = pd.DataFrame()

        # Mapping kolom berdasarkan ALIAS_MAPPING
        for standard_name, aliases in ALIAS_MAPPING.items():
            original_df_columns_lower = [col.lower().strip() for col in original_columns]
            for alias in aliases:
                if alias in df.columns:
                    processed_df[standard_name] = df[alias]
                    # Cari nama kolom asli untuk pesan
                    original_col_name = original_columns[original_df_columns_lower.index(alias)]
                    mapped_info[standard_name] = f"Ditemukan dari kolom '{original_col_name}'"
                    print(f"[DEBUG] Mapped '{standard_name}' dari kolom '{original_col_name}'")
                    break
        
        print(f"[DEBUG] Kolom yang berhasil dipetakan: {processed_df.columns.tolist()}")

        # Handle tanggal_transaksi - buat dari bulan/tahun jika tidak ada
        if 'tanggal_transaksi' not in processed_df.columns:
            print("[DEBUG] 'tanggal_transaksi' tidak ditemukan, mencoba membuat dari 'bulan' dan 'tahun'.")
            if 'bulan' in processed_df.columns and 'tahun' in processed_df.columns:
                print("[DEBUG] Kolom 'bulan' DAN 'tahun' ditemukan! Mencoba menggabungkan...")
                
                # Mapping nama bulan Indonesia ke angka
                BULAN_MAPPING = {
                    'januari': 1, 'jan': 1, 'january': 1,
                    'februari': 2, 'feb': 2, 'february': 2,
                    'maret': 3, 'mar': 3, 'march': 3,
                    'april': 4, 'apr': 4,
                    'mei': 5, 'may': 5,
                    'juni': 6, 'jun': 6, 'june': 6,
                    'juli': 7, 'jul': 7, 'july': 7,
                    'agustus': 8, 'agu': 8, 'ags': 8, 'august': 8,
                    'september': 9, 'sep': 9, 'sept': 9,
                    'oktober': 10, 'okt': 10, 'oct': 10, 'october': 10,
                    'november': 11, 'nov': 11,
                    'desember': 12, 'des': 12, 'dec': 12, 'december': 12
                }
                
                # Konversi bulan dari nama ke angka
                bulan_series = processed_df['bulan'].astype(str).str.lower().str.strip()
                bulan_numeric = bulan_series.map(BULAN_MAPPING)
                
                # Jika tidak bisa dimap, coba konversi langsung ke numeric
                bulan_numeric = bulan_numeric.fillna(pd.to_numeric(bulan_series, errors='coerce'))
                
                # Konversi tahun ke numeric
                tahun_numeric = pd.to_numeric(processed_df['tahun'], errors='coerce')
                
                # Buat mask untuk data yang valid
                valid_mask = bulan_numeric.notna() & tahun_numeric.notna() & \
                            (bulan_numeric >= 1) & (bulan_numeric <= 12) & \
                            (tahun_numeric >= 1900) & (tahun_numeric <= 2100)
                
                print(f"[DEBUG] Jumlah baris dengan bulan/tahun valid: {valid_mask.sum()}")
                
                if valid_mask.sum() > 0:
                    # Buat string tanggal
                    date_strings = tahun_numeric.astype('Int64').astype(str) + '-' + \
                                  bulan_numeric.astype('Int64').astype(str).str.zfill(2) + '-01'
                    
                    # Konversi ke datetime
                    date_series = pd.to_datetime(date_strings, format='%Y-%m-%d', errors='coerce')
                    
                    if date_series.notna().sum() > 0:
                        processed_df['tanggal_transaksi'] = date_series
                        mapped_info['tanggal_transaksi'] = "Dibuat dari gabungan kolom 'bulan' dan 'tahun'"
                        print("[DEBUG] Berhasil membuat kolom 'tanggal_transaksi'!")
                        
                        # Hapus kolom bulan dan tahun setelah berhasil
                        processed_df.drop(columns=['bulan', 'tahun'], inplace=True, errors='ignore')
                    else:
                        return jsonify({
                            "message": "Tidak dapat membuat tanggal dari kolom 'bulan' dan 'tahun'."
                        }), 400
                else:
                    return jsonify({
                        "message": "Tidak ada data bulan/tahun yang valid."
                    }), 400
            else:
                return jsonify({
                    "message": "Kolom tanggal tidak ditemukan. Diperlukan kolom 'tanggal_transaksi' atau kombinasi 'bulan' dan 'tahun'."
                }), 400

        # Validasi kolom inti
        missing_columns = []
        for col in KOLOM_INTI:
            if col not in processed_df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            return jsonify({
                "message": f"Kolom wajib tidak ditemukan: {', '.join(missing_columns)}"
            }), 400
        
        # Konversi tipe data
        for col in ["harga", "jumlah_terjual"]:
            processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce')

        # Konversi tanggal jika belum dalam format datetime
        if processed_df['tanggal_transaksi'].dtype != 'datetime64[ns]':
            processed_df['tanggal_transaksi'] = pd.to_datetime(processed_df['tanggal_transaksi'], errors='coerce')
        
        # Bersihkan data yang tidak valid
        initial_rows = len(processed_df)
        processed_df.dropna(subset=KOLOM_INTI, inplace=True)
        final_rows = len(processed_df)
        
        print(f"[DEBUG] Baris data: awal={initial_rows}, setelah pembersihan={final_rows}")

        if processed_df.empty:
            return jsonify({"message": "Data tidak valid setelah pembersihan."}), 400

        # Simpan file processed ke temporary
        temp_filename = f"{upload_session_id}_processed.csv"
        temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
        processed_df.to_csv(temp_filepath, index=False)
        
        print(f"[DEBUG] File temporary disimpan: {temp_filepath}")

        # Hitung total penjualan
        processed_df['total_penjualan'] = processed_df['harga'] * processed_df['jumlah_terjual']
        
        # Buat preview data (5 baris pertama)
        preview_data = processed_df.head(5).to_dict('records')
        
        # Format tanggal untuk preview
        for row in preview_data:
            if 'tanggal_transaksi' in row and pd.notna(row['tanggal_transaksi']):
                row['tanggal_transaksi'] = pd.to_datetime(row['tanggal_transaksi']).strftime('%Y-%m-%d')

        # Statistik dasar
        stats = {
            'total_rows': len(processed_df),
            'total_products': processed_df['nama_produk'].nunique(),
            'date_range': {
                'start': processed_df['tanggal_transaksi'].min().strftime('%Y-%m-%d'),
                'end': processed_df['tanggal_transaksi'].max().strftime('%Y-%m-%d')
            },
            'total_revenue': float(processed_df['total_penjualan'].sum()),
            'avg_price': float(processed_df['harga'].mean()),
        }

        return jsonify({
            "success": True,
            "message": "File berhasil diproses!",
            "upload_session_id": upload_session_id,
            "mapped_columns": mapped_info,
            "stats": stats,
            "preview": preview_data,
            "columns": list(processed_df.columns)
        }), 200

    except Exception as e:
        print(f"[ERROR] Upload error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"message": f"Terjadi error saat memproses file: {str(e)}"}), 500
# ======================================================================
# ENDPOINT 1: UPLOAD, SAVE TO DATABASE & PREVIEW DATA
# ======================================================================

# @app.route("/upload/preview", methods=["POST"])
# def upload_preview():
#     if 'file' not in request.files:
#         return jsonify({"message": "Tidak ada file yang diunggah"}), 400
#     file = request.files['file']
#     if file.filename == '':
#         return jsonify({"message": "Tidak ada file yang dipilih"}), 400
#     if not file or not allowed_file(file.filename):
#         return jsonify({"message": "Tipe file tidak valid. Gunakan CSV atau Excel."}), 400

#     try:
#         print("\n--- [DEBUG] Memulai Proses Upload ---")
        
#         # Load data
#         if 'csv' in file.filename:
#             df = pd.read_csv(file)
#         else:
#             df = pd.read_excel(file)
        
#         print(f"[DEBUG] Nama kolom ASLI dari file: {df.columns.tolist()}")
        
#         # Simpan kolom asli untuk referensi
#         original_columns = df.columns.tolist()
        
#         # Standarisasi kolom
#         df.columns = df.columns.str.lower().str.strip()
#         print(f"[DEBUG] Nama kolom SETELAH standarisasi: {df.columns.tolist()}")

#         if df.empty:
#              return jsonify({"message": "File yang diunggah kosong."}), 400

#         mapped_info = {}
#         processed_df = pd.DataFrame()

#         # Mapping kolom berdasarkan ALIAS_MAPPING
#         for standard_name, aliases in ALIAS_MAPPING.items():
#             original_df_columns_lower = [col.lower().strip() for col in original_columns]
#             for alias in aliases:
#                 if alias in df.columns:
#                     processed_df[standard_name] = df[alias]
#                     # Cari nama kolom asli untuk pesan
#                     original_col_name = original_columns[original_df_columns_lower.index(alias)]
#                     mapped_info[standard_name] = f"Ditemukan dari kolom '{original_col_name}'"
#                     print(f"[DEBUG] Mapped '{standard_name}' dari kolom '{original_col_name}'")
#                     break
        
#         print(f"[DEBUG] Kolom yang berhasil dipetakan: {processed_df.columns.tolist()}")

#         # PERBAIKAN: Cek dan buat tanggal_transaksi SEBELUM validasi kolom inti
#         if 'tanggal_transaksi' not in processed_df.columns:
#             print("[DEBUG] 'tanggal_transaksi' tidak ditemukan, mencoba membuat dari 'bulan' dan 'tahun'.")
#             if 'bulan' in processed_df.columns and 'tahun' in processed_df.columns:
#                 print("[DEBUG] Kolom 'bulan' DAN 'tahun' ditemukan! Mencoba menggabungkan...")
                
#                 # Mapping nama bulan Indonesia ke angka
#                 BULAN_MAPPING = {
#                     'januari': 1, 'jan': 1,
#                     'februari': 2, 'feb': 2,
#                     'maret': 3, 'mar': 3,
#                     'april': 4, 'apr': 4,
#                     'mei': 5,
#                     'juni': 6, 'jun': 6,
#                     'juli': 7, 'jul': 7,
#                     'agustus': 8, 'agu': 8, 'ags': 8,
#                     'september': 9, 'sep': 9, 'sept': 9,
#                     'oktober': 10, 'okt': 10, 'oct': 10,
#                     'november': 11, 'nov': 11,
#                     'desember': 12, 'des': 12, 'dec': 12,
#                     # Tambahan untuk bahasa Inggris
#                     'january': 1, 'february': 2, 'march': 3,
#                     'may': 5, 'june': 6, 'july': 7,
#                     'august': 8, 'october': 10, 'december': 12
#                 }
                
#                 print(f"[DEBUG] Sample bulan original: {processed_df['bulan'].head()}")
#                 print(f"[DEBUG] Sample tahun original: {processed_df['tahun'].head()}")
                
#                 # Konversi bulan dari nama ke angka
#                 bulan_series = processed_df['bulan'].astype(str).str.lower().str.strip()
#                 bulan_numeric = bulan_series.map(BULAN_MAPPING)
                
#                 # Jika tidak bisa dimap, coba konversi langsung ke numeric (untuk kasus data sudah angka)
#                 bulan_numeric = bulan_numeric.fillna(pd.to_numeric(bulan_series, errors='coerce'))
                
#                 # Konversi tahun ke numeric
#                 tahun_numeric = pd.to_numeric(processed_df['tahun'], errors='coerce')
                
#                 print(f"[DEBUG] Sample bulan setelah konversi: {bulan_numeric.head()}")
#                 print(f"[DEBUG] Sample tahun setelah konversi: {tahun_numeric.head()}")
                
#                 # Buat mask untuk data yang valid
#                 valid_mask = bulan_numeric.notna() & tahun_numeric.notna() & \
#                             (bulan_numeric >= 1) & (bulan_numeric <= 12) & \
#                             (tahun_numeric >= 1900) & (tahun_numeric <= 2100)
                
#                 print(f"[DEBUG] Jumlah baris dengan bulan/tahun valid: {valid_mask.sum()}")
#                 print(f"[DEBUG] Total baris: {len(processed_df)}")
                
#                 if valid_mask.sum() > 0:
#                     # Buat string tanggal dengan format yang konsisten
#                     date_strings = tahun_numeric.astype('Int64').astype(str) + '-' + \
#                                   bulan_numeric.astype('Int64').astype(str).str.zfill(2) + '-01'
                    
#                     print(f"[DEBUG] Sample date strings: {date_strings.head()}")
                    
#                     # Konversi ke datetime dengan format yang eksplisit
#                     try:
#                         date_series = pd.to_datetime(date_strings, format='%Y-%m-%d', errors='coerce')
#                         print(f"[DEBUG] Sample parsed dates: {date_series.head()}")
                        
#                         # Cek apakah ada tanggal yang berhasil diparsing
#                         valid_dates = date_series.notna().sum()
#                         print(f"[DEBUG] Jumlah tanggal valid yang berhasil dibuat: {valid_dates}")
                        
#                         if valid_dates > 0:
#                             processed_df['tanggal_transaksi'] = date_series
#                             mapped_info['tanggal_transaksi'] = "Dibuat dari gabungan kolom 'bulan' dan 'tahun'"
#                             print("[DEBUG] Berhasil membuat kolom 'tanggal_transaksi'!")
                            
#                             # Hapus kolom bulan dan tahun setelah berhasil membuat tanggal
#                             processed_df.drop(columns=['bulan', 'tahun'], inplace=True, errors='ignore')
#                         else:
#                             print("[DEBUG] Gagal membuat tanggal yang valid dari kolom 'bulan' dan 'tahun'.")
#                             return jsonify({
#                                 "message": "Tidak dapat membuat tanggal dari kolom 'bulan' dan 'tahun'. Pastikan nama bulan valid (Januari, Februari, dll) dan tahun (1900-2100) valid."
#                             }), 400
                            
#                     except Exception as date_error:
#                         print(f"[DEBUG] Error saat parsing tanggal: {str(date_error)}")
#                         return jsonify({
#                             "message": f"Error saat membuat tanggal dari kolom bulan/tahun: {str(date_error)}"
#                         }), 400
#                 else:
#                     print("[DEBUG] Tidak ada baris dengan bulan/tahun yang valid.")
#                     print(f"[DEBUG] Contoh bulan yang tidak dikenali: {bulan_series[bulan_numeric.isna()].unique()[:5]}")
#                     return jsonify({
#                         "message": "Tidak ada data bulan/tahun yang valid. Pastikan nama bulan dalam format Indonesia (Januari, Februari, dll) atau Inggris (January, February, dll) dan tahun 1900-2100."
#                     }), 400
#             else:
#                 missing_cols = []
#                 if 'bulan' not in processed_df.columns:
#                     missing_cols.append('bulan')
#                 if 'tahun' not in processed_df.columns:
#                     missing_cols.append('tahun')
#                 print(f"[DEBUG] Kolom yang hilang: {missing_cols}")
#                 return jsonify({
#                     "message": f"Kolom tanggal tidak ditemukan. Diperlukan kolom 'tanggal_transaksi' atau kombinasi 'bulan' dan 'tahun'. Kolom yang hilang: {', '.join(missing_cols)}"
#                 }), 400

#         print("[DEBUG] Memulai validasi kolom inti...")
#         missing_columns = []
#         for col in KOLOM_INTI:
#             if col not in processed_df.columns:
#                 missing_columns.append(col)
#                 print(f"[DEBUG] GAGAL VALIDASI! Kolom wajib '{col}' tidak ditemukan.")
        
#         if missing_columns:
#             return jsonify({
#                 "message": f"Kolom wajib tidak ditemukan: {', '.join(missing_columns)}. Pastikan file Anda memiliki kolom yang sesuai."
#             }), 400
        
#         print("[DEBUG] Semua kolom inti ditemukan. Validasi sukses.")
        
#         # Konversi tipe data
#         for col in ["harga", "jumlah_terjual"]:
#             processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce')

#         # Konversi tanggal jika belum dalam format datetime
#         if processed_df['tanggal_transaksi'].dtype != 'datetime64[ns]':
#             processed_df['tanggal_transaksi'] = pd.to_datetime(processed_df['tanggal_transaksi'], errors='coerce')
        
#         # Bersihkan data yang tidak valid
#         initial_rows = len(processed_df)
#         processed_df.dropna(subset=KOLOM_INTI, inplace=True)
#         final_rows = len(processed_df)
        
#         print(f"[DEBUG] Baris data: awal={initial_rows}, setelah pembersihan={final_rows}")

#         if processed_df.empty:
#              return jsonify({"message": "Data tidak valid setelah pembersihan. Pastikan semua kolom wajib memiliki nilai yang valid."}), 400

#         # ======================================================================
#         # SAVE TO DATABASE
#         # ======================================================================
#         print("[DEBUG] Mulai menyimpan data ke database...")
        
#         try:
#             # Generate upload session ID
#             upload_session_id = str(uuid.uuid4())
#             upload_timestamp = datetime.now()
            
#             # Prepare data untuk database
#             db_data = []
#             for _, row in processed_df.iterrows():
#                 db_record = {
#                     'upload_session_id': upload_session_id,
#                     'nama_produk': row['nama_produk'],
#                     'jumlah_terjual': int(row['jumlah_terjual']) if pd.notna(row['jumlah_terjual']) else 0,
#                     'harga': float(row['harga']) if pd.notna(row['harga']) else 0.0,
#                     'tanggal_transaksi': row['tanggal_transaksi'],
#                     'kategori_produk': row.get('kategori_produk', 'Tidak Dikategorikan'),
#                     'total_revenue': float(row['jumlah_terjual'] * row['harga']) if pd.notna(row['jumlah_terjual']) and pd.notna(row['harga']) else 0.0,
#                     'upload_timestamp': upload_timestamp
#                 }
#                 db_data.append(db_record)
            
#             # Insert ke database (batch insert untuk performance)
#             cursor = mysql.connection.cursor()
            
#             # Create table jika belum ada
#             create_table_query = """
#             CREATE TABLE IF NOT EXISTS sales_data (
#                 id INT AUTO_INCREMENT PRIMARY KEY,
#                 upload_session_id VARCHAR(255) NOT NULL,
#                 nama_produk VARCHAR(255) NOT NULL,
#                 jumlah_terjual INT DEFAULT 0,
#                 harga DECIMAL(15,2) DEFAULT 0.00,
#                 tanggal_transaksi DATE NOT NULL,
#                 kategori_produk VARCHAR(255) DEFAULT 'Tidak Dikategorikan',
#                 total_revenue DECIMAL(15,2) DEFAULT 0.00,
#                 upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                 INDEX idx_upload_session (upload_session_id),
#                 INDEX idx_nama_produk (nama_produk),
#                 INDEX idx_tanggal (tanggal_transaksi)
#             ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
#             """
#             cursor.execute(create_table_query)
            
#             # Batch insert data
#             insert_query = """
#             INSERT INTO sales_data 
#             (upload_session_id, nama_produk, jumlah_terjual, harga, tanggal_transaksi, 
#              kategori_produk, total_revenue, upload_timestamp)
#             VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
#             """
            
#             insert_values = [
#                 (record['upload_session_id'], record['nama_produk'], record['jumlah_terjual'],
#                  record['harga'], record['tanggal_transaksi'], record['kategori_produk'],
#                  record['total_revenue'], record['upload_timestamp'])
#                 for record in db_data
#             ]
            
#             cursor.executemany(insert_query, insert_values)
#             mysql.connection.commit()
#             cursor.close()
            
#             print(f"[DEBUG] Berhasil menyimpan {len(db_data)} baris ke database")
            
#         except Exception as db_error:
#             print(f"[DEBUG] Error saat menyimpan ke database: {str(db_error)}")
#             return jsonify({
#                 "message": f"Data berhasil divalidasi, tetapi gagal disimpan ke database: {str(db_error)}"
#             }), 500


        # ======================================================================
        # PREPARE PREVIEW DATA
        # ======================================================================
        # Buat preview data dengan format tanggal yang lebih bersih
        preview_df = processed_df.head(10).copy()
        
        # Format tanggal sesuai dengan data asli (hanya tahun-bulan)
        if 'tanggal_transaksi' in preview_df.columns:
            preview_df['tanggal_transaksi'] = preview_df['tanggal_transaksi'].dt.strftime('%Y-%m')
        
        # Tambahkan kolom total_revenue untuk preview
        if 'total_revenue' not in preview_df.columns:
            preview_df['total_revenue'] = preview_df['jumlah_terjual'] * preview_df['harga']
        
        preview_data = preview_df.to_json(orient='records')

        print("[DEBUG] Upload, database save, dan preview berhasil!")
        return jsonify({
            "message": "File berhasil divalidasi dan disimpan ke database.",
            "upload_session_id": upload_session_id,
            "temp_file_id": temp_filename,  # Untuk clustering jika diperlukan
            "column_mapping_info": mapped_info,
            "preview_data": json.loads(preview_data),
            "database_info": {
                "total_rows_saved": len(db_data),
                "upload_timestamp": upload_timestamp.isoformat(),
                "session_id": upload_session_id
            },
            "data_info": {
                "total_rows": final_rows,
                "columns_found": list(processed_df.columns)
            }
        }), 200

    except Exception as e:
        print(f"[DEBUG] Terjadi EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"message": f"Terjadi error saat memproses file: {str(e)}"}), 500

# ======================================================================
# ENDPOINT UNTUK MENGAMBIL DATA DARI DATABASE
# ======================================================================

@app.route("/data/sessions", methods=["GET"])
def get_upload_sessions():
    """Get list of upload sessions"""
    try:
        cursor = mysql.connection.cursor()
        query = """
        SELECT 
            upload_session_id,
            COUNT(*) as total_records,
            MIN(upload_timestamp) as upload_time,
            COUNT(DISTINCT nama_produk) as unique_products,
            SUM(total_revenue) as total_revenue
        FROM sales_data 
        GROUP BY upload_session_id, DATE(upload_timestamp)
        ORDER BY upload_time DESC
        LIMIT 20
        """
        cursor.execute(query)
        sessions = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            "sessions": sessions
        }), 200
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

@app.route("/data/session/<session_id>", methods=["GET"])
def get_session_data(session_id):
    """Get data from specific upload session"""
    try:
        cursor = mysql.connection.cursor()
        query = """
        SELECT * FROM sales_data 
        WHERE upload_session_id = %s 
        ORDER BY tanggal_transaksi, nama_produk
        """
        cursor.execute(query, (session_id,))
        data = cursor.fetchall()
        cursor.close()

        # Format tanggal_transaksi
        for row in data:
            if 'tanggal_transaksi' in row:
                row['tanggal_transaksi'] = row['tanggal_transaksi'].strftime('%Y-%m')

        return jsonify({
            "data": data,
            "total_records": len(data)
        }), 200
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

# @app.route("/upload/preview", methods=["POST"])
# def upload_preview():
#     if 'file' not in request.files:
#         return jsonify({"message": "Tidak ada file yang diunggah"}), 400
#     file = request.files['file']
#     if file.filename == '':
#         return jsonify({"message": "Tidak ada file yang dipilih"}), 400
#     if not file or not allowed_file(file.filename):
#         return jsonify({"message": "Tipe file tidak valid. Gunakan CSV atau Excel."}), 400

#     try:
#         print("\n--- [DEBUG] Memulai Proses Upload ---")
        
#         # Load data
#         if 'csv' in file.filename:
#             df = pd.read_csv(file)
#         else:
#             df = pd.read_excel(file)
        
#         print(f"[DEBUG] Nama kolom ASLI dari file: {df.columns.tolist()}")
        
#         # Simpan kolom asli untuk referensi
#         original_columns = df.columns.tolist()
        
#         # Standarisasi kolom
#         df.columns = df.columns.str.lower().str.strip()
#         print(f"[DEBUG] Nama kolom SETELAH standarisasi: {df.columns.tolist()}")

#         if df.empty:
#              return jsonify({"message": "File yang diunggah kosong."}), 400

#         mapped_info = {}
#         processed_df = pd.DataFrame()

#         # Mapping kolom berdasarkan ALIAS_MAPPING
#         for standard_name, aliases in ALIAS_MAPPING.items():
#             original_df_columns_lower = [col.lower().strip() for col in original_columns]
#             for alias in aliases:
#                 if alias in df.columns:
#                     processed_df[standard_name] = df[alias]
#                     # Cari nama kolom asli untuk pesan
#                     original_col_name = original_columns[original_df_columns_lower.index(alias)]
#                     mapped_info[standard_name] = f"Ditemukan dari kolom '{original_col_name}'"
#                     print(f"[DEBUG] Mapped '{standard_name}' dari kolom '{original_col_name}'")
#                     break
        
#         print(f"[DEBUG] Kolom yang berhasil dipetakan: {processed_df.columns.tolist()}")

#         # PERBAIKAN: Cek dan buat tanggal_transaksi SEBELUM validasi kolom inti
#         if 'tanggal_transaksi' not in processed_df.columns:
#             print("[DEBUG] 'tanggal_transaksi' tidak ditemukan, mencoba membuat dari 'bulan' dan 'tahun'.")
#             if 'bulan' in processed_df.columns and 'tahun' in processed_df.columns:
#                 print("[DEBUG] Kolom 'bulan' DAN 'tahun' ditemukan! Mencoba menggabungkan...")
                
#                 # Mapping nama bulan Indonesia ke angka
#                 BULAN_MAPPING = {
#                     'januari': 1, 'jan': 1,
#                     'februari': 2, 'feb': 2,
#                     'maret': 3, 'mar': 3,
#                     'april': 4, 'apr': 4,
#                     'mei': 5,
#                     'juni': 6, 'jun': 6,
#                     'juli': 7, 'jul': 7,
#                     'agustus': 8, 'agu': 8, 'ags': 8,
#                     'september': 9, 'sep': 9, 'sept': 9,
#                     'oktober': 10, 'okt': 10, 'oct': 10,
#                     'november': 11, 'nov': 11,
#                     'desember': 12, 'des': 12, 'dec': 12,
#                     # Tambahan untuk bahasa Inggris
#                     'january': 1, 'february': 2, 'march': 3,
#                     'may': 5, 'june': 6, 'july': 7,
#                     'august': 8, 'october': 10, 'december': 12
#                 }
                
#                 print(f"[DEBUG] Sample bulan original: {processed_df['bulan'].head()}")
#                 print(f"[DEBUG] Sample tahun original: {processed_df['tahun'].head()}")
                
#                 # Konversi bulan dari nama ke angka
#                 bulan_series = processed_df['bulan'].astype(str).str.lower().str.strip()
#                 bulan_numeric = bulan_series.map(BULAN_MAPPING)
                
#                 # Jika tidak bisa dimap, coba konversi langsung ke numeric (untuk kasus data sudah angka)
#                 bulan_numeric = bulan_numeric.fillna(pd.to_numeric(bulan_series, errors='coerce'))
                
#                 # Konversi tahun ke numeric
#                 tahun_numeric = pd.to_numeric(processed_df['tahun'], errors='coerce')
                
#                 print(f"[DEBUG] Sample bulan setelah konversi: {bulan_numeric.head()}")
#                 print(f"[DEBUG] Sample tahun setelah konversi: {tahun_numeric.head()}")
                
#                 # Buat mask untuk data yang valid
#                 valid_mask = bulan_numeric.notna() & tahun_numeric.notna() & \
#                             (bulan_numeric >= 1) & (bulan_numeric <= 12) & \
#                             (tahun_numeric >= 1900) & (tahun_numeric <= 2100)
                
#                 print(f"[DEBUG] Jumlah baris dengan bulan/tahun valid: {valid_mask.sum()}")
#                 print(f"[DEBUG] Total baris: {len(processed_df)}")
                
#                 if valid_mask.sum() > 0:
#                     # Buat string tanggal dengan format yang konsisten
#                     date_strings = tahun_numeric.astype('Int64').astype(str) + '-' + \
#                                   bulan_numeric.astype('Int64').astype(str).str.zfill(2) + '-01'
                    
#                     print(f"[DEBUG] Sample date strings: {date_strings.head()}")
                    
#                     # Konversi ke datetime dengan format yang eksplisit
#                     try:
#                         date_series = pd.to_datetime(date_strings, format='%Y-%m-%d', errors='coerce')
#                         print(f"[DEBUG] Sample parsed dates: {date_series.head()}")
                        
#                         # Cek apakah ada tanggal yang berhasil diparsing
#                         valid_dates = date_series.notna().sum()
#                         print(f"[DEBUG] Jumlah tanggal valid yang berhasil dibuat: {valid_dates}")
                        
#                         if valid_dates > 0:
#                             processed_df['tanggal_transaksi'] = date_series
#                             mapped_info['tanggal_transaksi'] = "Dibuat dari gabungan kolom 'bulan' dan 'tahun'"
#                             print("[DEBUG] Berhasil membuat kolom 'tanggal_transaksi'!")
                            
#                             # Hapus kolom bulan dan tahun setelah berhasil membuat tanggal
#                             processed_df.drop(columns=['bulan', 'tahun'], inplace=True, errors='ignore')
#                         else:
#                             print("[DEBUG] Gagal membuat tanggal yang valid dari kolom 'bulan' dan 'tahun'.")
#                             return jsonify({
#                                 "message": "Tidak dapat membuat tanggal dari kolom 'bulan' dan 'tahun'. Pastikan nama bulan valid (Januari, Februari, dll) dan tahun (1900-2100) valid."
#                             }), 400
                            
#                     except Exception as date_error:
#                         print(f"[DEBUG] Error saat parsing tanggal: {str(date_error)}")
#                         return jsonify({
#                             "message": f"Error saat membuat tanggal dari kolom bulan/tahun: {str(date_error)}"
#                         }), 400
#                 else:
#                     print("[DEBUG] Tidak ada baris dengan bulan/tahun yang valid.")
#                     print(f"[DEBUG] Contoh bulan yang tidak dikenali: {bulan_series[bulan_numeric.isna()].unique()[:5]}")
#                     return jsonify({
#                         "message": "Tidak ada data bulan/tahun yang valid. Pastikan nama bulan dalam format Indonesia (Januari, Februari, dll) atau Inggris (January, February, dll) dan tahun 1900-2100."
#                     }), 400
#             else:
#                 missing_cols = []
#                 if 'bulan' not in processed_df.columns:
#                     missing_cols.append('bulan')
#                 if 'tahun' not in processed_df.columns:
#                     missing_cols.append('tahun')
#                 print(f"[DEBUG] Kolom yang hilang: {missing_cols}")
#                 return jsonify({
#                     "message": f"Kolom tanggal tidak ditemukan. Diperlukan kolom 'tanggal_transaksi' atau kombinasi 'bulan' dan 'tahun'. Kolom yang hilang: {', '.join(missing_cols)}"
#                 }), 400

#         print("[DEBUG] Memulai validasi kolom inti...")
#         missing_columns = []
#         for col in KOLOM_INTI:
#             if col not in processed_df.columns:
#                 missing_columns.append(col)
#                 print(f"[DEBUG] GAGAL VALIDASI! Kolom wajib '{col}' tidak ditemukan.")
        
#         if missing_columns:
#             return jsonify({
#                 "message": f"Kolom wajib tidak ditemukan: {', '.join(missing_columns)}. Pastikan file Anda memiliki kolom yang sesuai."
#             }), 400
        
#         print("[DEBUG] Semua kolom inti ditemukan. Validasi sukses.")
        
#         # Konversi tipe data
#         for col in ["harga", "jumlah_terjual"]:
#             processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce')

#         # Konversi tanggal jika belum dalam format datetime
#         if processed_df['tanggal_transaksi'].dtype != 'datetime64[ns]':
#             processed_df['tanggal_transaksi'] = pd.to_datetime(processed_df['tanggal_transaksi'], errors='coerce')
        
#         # Bersihkan data yang tidak valid
#         initial_rows = len(processed_df)
#         processed_df.dropna(subset=KOLOM_INTI, inplace=True)
#         final_rows = len(processed_df)
        
#         print(f"[DEBUG] Baris data: awal={initial_rows}, setelah pembersihan={final_rows}")

#         if processed_df.empty:
#              return jsonify({"message": "Data tidak valid setelah pembersihan. Pastikan semua kolom wajib memiliki nilai yang valid."}), 400

#         # Simpan file sementara dengan fallback format
#         try:
#             # Coba parquet dulu (format terbaik)
#             temp_filename = f"temp_{uuid.uuid4()}.parquet"
#             temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
#             processed_df.to_parquet(temp_filepath)
#             print("[DEBUG] File disimpan dalam format parquet")
#         except ImportError:
#             # Jika parquet tidak tersedia, gunakan pickle
#             temp_filename = f"temp_{uuid.uuid4()}.pkl"
#             temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
#             processed_df.to_pickle(temp_filepath)
#             print("[DEBUG] File disimpan dalam format pickle")
#         except Exception as e:
#             # Fallback ke CSV
#             temp_filename = f"temp_{uuid.uuid4()}.csv"
#             temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
#             processed_df.to_csv(temp_filepath, index=False)
#             print("[DEBUG] File disimpan dalam format CSV")

#         # Buat preview data dengan format tanggal yang lebih bersih
#         preview_df = processed_df.head(10).copy()
        
#         # Format tanggal sesuai dengan data asli (hanya tahun-bulan)
#         if 'tanggal_transaksi' in preview_df.columns:
#             preview_df['tanggal_transaksi'] = preview_df['tanggal_transaksi'].dt.strftime('%Y-%m')
        
#         preview_data = preview_df.to_json(orient='records')

#         print("[DEBUG] Upload dan preview berhasil!")
#         return jsonify({
#             "message": "File berhasil divalidasi.",
#             "temp_file_id": temp_filename,
#             "column_mapping_info": mapped_info,
#             "preview_data": json.loads(preview_data),
#             "data_info": {
#                 "total_rows": final_rows,
#                 "columns_found": list(processed_df.columns)
#             }
#         }), 200

#     except Exception as e:
#         print(f"[DEBUG] Terjadi EXCEPTION: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         return jsonify({"message": f"Terjadi error saat memproses file: {str(e)}"}), 500
# #

# ======================================================================
# ENDPOINT 2: SIMPAN DATA DARI PREVIEW (Tidak ada perubahan di sini)
# ======================================================================
@app.route("/upload/save", methods=["POST"])
def save_processed_data():
    # ... isi fungsi ini tetap sama
    data = request.get_json()
    temp_file_id = data.get('temp_file_id')
    nama_dataset = data.get('nama_dataset')
    user_id = data.get('user_id')

    if not all([temp_file_id, nama_dataset, user_id]):
        return jsonify({"message": "Informasi tidak lengkap. ID file, nama dataset, dan ID user dibutuhkan."}), 400

    temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], temp_file_id)

    if not os.path.exists(temp_filepath):
        return jsonify({"message": "File sesi tidak ditemukan. Mungkin sudah kedaluwarsa."}), 404

    db: Session = next(get_db())
    try:
        new_dataset = Dataset(nama_dataset=nama_dataset, user_id=user_id)
        db.add(new_dataset)
        db.flush()
        
        dataset_id = new_dataset.dataset_id

        df = pd.read_parquet(temp_filepath)
        df['dataset_id'] = dataset_id
        
        df.rename(columns={
            "nama_produk": "nama_produk",
            "kategori_produk": "kategori_produk",
            "jumlah_terjual": "jumlah_terjual",
            "harga": "harga",
            "tanggal_transaksi": "tanggal_transaksi"
        }, inplace=True)
        
        data_to_insert = df.to_dict(orient='records')

        db.bulk_insert_mappings(Produk, data_to_insert)
        db.commit()

        return jsonify({"message": f"Sukses! {len(data_to_insert)} baris data telah disimpan ke dalam dataset '{nama_dataset}'."}), 201

    except Exception as e:
        db.rollback()
        return jsonify({"message": f"Gagal menyimpan ke database: {str(e)}"}), 500
    finally:
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        db.close()


# Fungsi helper untuk load temporary dataframe
def load_temp_dataframe(temp_filename, upload_folder):
    """Load DataFrame dari file temporary berdasarkan ekstensi"""
    temp_filepath = os.path.join(upload_folder, temp_filename)
    # temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
    
    
    if not os.path.exists(temp_filepath):
        raise FileNotFoundError(f"File temporary {temp_filename} tidak ditemukan")
    
    if temp_filename.endswith('.parquet'):
        return pd.read_parquet(temp_filepath)
    elif temp_filename.endswith('.pkl'):
        return pd.read_pickle(temp_filepath)
    elif temp_filename.endswith('.csv'):
        return pd.read_csv(temp_filepath, parse_dates=['tanggal_transaksi'])
    else:
        raise ValueError(f"Format file {temp_filename} tidak didukung")

@app.route("/clustering/parameters", methods=["GET"])
def get_clustering_parameters():
    """Get available clustering parameters and options"""
    try:
        return jsonify({
            "clustering_methods": [
                {"value": "kmeans", "label": "K-Means", "description": "Clustering berdasarkan jarak ke centroid"},
                {"value": "kmeans_plus", "label": "K-Means++", "description": "K-Means dengan inisialisasi yang lebih baik"}
            ],
            "cluster_options": {
                "min_clusters": 2,
                "max_clusters": 10,
                "default_clusters": 3
            },
            "feature_options": [
                {"value": "total_pembelian", "label": "Total Pembelian", "description": "Jumlah total pembelian per produk"},
                {"value": "frekuensi_pembelian", "label": "Frekuensi Pembelian", "description": "Berapa kali produk dibeli"},
                {"value": "rata_rata_harga", "label": "Rata-rata Harga", "description": "Harga rata-rata produk"},
                {"value": "total_revenue", "label": "Total Revenue", "description": "Total pendapatan dari produk"}
            ]
        }), 200
    except Exception as e:
        print(f"[DEBUG] Error get clustering parameters: {str(e)}")
        return jsonify({"message": f"Error: {str(e)}"}), 500

# file: backend/app.py



# Endpoint ini tidak perlu diubah
# @app.route("/clustering/parameters", methods=["GET"])
# def get_clustering_parameters():
#     """Get available clustering parameters and options"""
#     try:
#         # ... (isi fungsi ini tetap sama)
#         pass
#     except Exception as e:
#         # ... (isi exception ini tetap sama)
#         pass

# # Fungsi helper untuk persona cluster, kita letakkan di sini agar rapi
# def get_cluster_persona(cluster_series, global_means):
#     """Membuat nama 'persona' untuk cluster."""
#     persona_parts = []
#     # Anda bisa menambahkan lebih banyak logika di sini
#     if cluster_series['total_pembelian'] > global_means['total_pembelian']:
#         persona_parts.append("Volume Tinggi")
#     else:
#         persona_parts.append("Volume Rendah")

#     if cluster_series['rata_rata_harga'] > global_means['rata_rata_harga']:
#         persona_parts.append("Harga Premium")
#     else:
#         persona_parts.append("Harga Terjangkau")
#     return " / ".join(persona_parts)


# ==============================================================
# === ENDPOINT PROSES CLUSTERING YANG SUDAH DIINTEGRASIKAN ===
# ==============================================================
@app.route("/clustering/process", methods=["POST"])
def process_clustering():
    try:
        data = request.get_json()
        temp_file_id = data.get('temp_file_id')
        selected_features = data.get('selected_features', ['total_pembelian', 'rata_rata_harga'])
        user_selected_k = int(data.get('n_clusters', 3))

        if not temp_file_id:
            # Menggunakan jsonify di sini aman karena tidak ada data NumPy
            return jsonify({"message": "temp_file_id diperlukan"}), 400

        # Langkah 1: Load Data
        temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], temp_file_id)
        if not os.path.exists(temp_filepath):
            return jsonify({"message": f"File temporary {temp_file_id} tidak ditemukan"}), 404
        df = pd.read_parquet(temp_filepath)
        print(f"[DEBUG] Loaded data dengan {len(df)} baris")

        # Langkah 2: Agregasi Data
        print("[DEBUG] Memulai proses agregasi data per produk...")
        features_df = df.groupby('nama_produk').agg(
            total_pembelian=('jumlah_terjual', 'sum'),
            frekuensi_pembelian=('jumlah_terjual', 'count'),
            rata_rata_harga=('harga', 'mean')
        ).reset_index()
        features_df['total_revenue'] = features_df['total_pembelian'] * features_df['rata_rata_harga']
        features_df = features_df.fillna(0)
        print(f"[DEBUG] Agregasi selesai. {len(features_df)} produk unik ditemukan.")
        
        # Langkah 3: Standardisasi Data
        if len(selected_features) < 2:
            return jsonify({"message": "Minimal 2 fitur diperlukan untuk clustering"}), 400
        
        clustering_data = features_df[selected_features]
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(clustering_data)
        
        # Langkah 4: Analisis K Optimal
        print("[DEBUG] Memulai analisis K optimal...")
        k_range = range(2, 11)
        inertias = []
        silhouette_scores = []
        for k in k_range:
            kmeans = KMeans(n_clusters=k, init='k-means++', random_state=42, n_init=10)
            kmeans.fit(scaled_data)
            inertias.append(kmeans.inertia_)
            silhouette_scores.append(silhouette_score(scaled_data, kmeans.labels_))
        
        knee_finder = KneeLocator(k_range, inertias, curve='convex', direction='decreasing')
        optimal_k = knee_finder.elbow if knee_finder.elbow else user_selected_k
        print(f"[DEBUG] Rekomendasi K Optimal: {optimal_k}")

        # Langkah 5: Clustering Final
        final_kmeans = KMeans(n_clusters=user_selected_k, init='k-means++', random_state=42, n_init=10)
        final_labels = final_kmeans.fit_predict(scaled_data)
        features_df['cluster'] = final_labels

        # Langkah 6: Profiling Cluster
        print("[DEBUG] Menghitung profil untuk setiap cluster...")
        global_means = features_df[selected_features].mean()
        cluster_profiles = []
        for i in range(user_selected_k):
            cluster_data = features_df[features_df['cluster'] == i]
            profile = {
                "cluster_id": i,
                "product_count": len(cluster_data),
                "persona": get_cluster_persona(cluster_data, global_means),
                "average_metrics": cluster_data[selected_features].mean().to_dict(),
                "sample_products": cluster_data['nama_produk'].head(5).tolist()
            }
            cluster_profiles.append(profile)

   # Langkah 7: Siapkan Respons
        visualization_df = features_df[['nama_produk', 'cluster'] + selected_features].copy()
        response_data = {
            "optimal_k_recommendation": optimal_k,
            "elbow_data": [{"k": k, "inertia": inertia} for k, inertia in zip(k_range, inertias)],
            "silhouette_data": [{"k": k, "score": score} for k, score in zip(k_range, silhouette_scores)],
            "selected_k_results": {
                "k_value": user_selected_k,
                "silhouette_score": silhouette_score(scaled_data, final_labels),
                "davies_bouldin_score": davies_bouldin_score(scaled_data, final_labels),
                "profiles": cluster_profiles,
                "visualization_data": visualization_df.to_dict(orient='records')
            }
        }
        
        # --- PERBAIKAN DI SINI ---
        # Gunakan argumen 'cls' untuk memberitahu json.dumps agar memakai encoder kustom kita
        json_response = json.dumps(response_data, cls=NumpyJSONEncoder)
        
        return Response(response=json_response, status=200, mimetype='application/json')
    
    except Exception as e:
        # Blok except dengan indentasi yang benar
        print(f"[DEBUG] Terjadi EXCEPTION di /clustering/process: {str(e)}")
        import traceback
        traceback.print_exc()
        
        error_response_data = {"message": f"Error internal server saat memproses clustering: {str(e)}"}
        error_json_response = json.dumps(error_response_data)
        return Response(response=error_json_response, status=500, mimetype='application/json')
# ======================================================================
# === FUNGSI HELPER BARU UNTUK PROFILING CLUSTER ===
# ======================================================================
# Di dalam file backend/app.py

# ======================================================================
# === GANTI SELURUH FUNGSI INI DENGAN VERSI BARU ===
# ======================================================================
def get_cluster_persona(cluster_series, global_means):
    """Membuat nama 'persona' untuk cluster berdasarkan perbandingannya dengan rata-rata global."""
    persona_parts = []
    
    # --- PERBAIKAN DI SINI: Gunakan .mean() untuk mendapatkan satu nilai rata-rata ---
    total_pembelian_mean = cluster_series['total_pembelian'].mean()
    if total_pembelian_mean > global_means['total_pembelian'] * 1.2:
        persona_parts.append("Volume Tinggi")
    elif total_pembelian_mean < global_means['total_pembelian'] * 0.8:
        persona_parts.append("Volume Rendah")
    else:
        persona_parts.append("Volume Sedang")

    # --- PERBAIKAN DI SINI: Gunakan .mean() juga untuk harga ---
    harga_mean = cluster_series['rata_rata_harga'].mean()
    if harga_mean > global_means['rata_rata_harga'] * 1.2:
        persona_parts.append("Harga Premium")
    elif harga_mean < global_means['rata_rata_harga'] * 0.8:
        persona_parts.append("Harga Terjangkau")
    else:
        persona_parts.append("Harga Menengah")
        
    return " / ".join(persona_parts)


# @app.route("/clustering/process", methods=["POST"])
# def process_clustering():
#     """Process clustering on uploaded data"""
#     try:
#         data = request.get_json()
#         temp_file_id = data.get('temp_file_id')
#         clustering_method = data.get('clustering_method', 'kmeans')
#         n_clusters = int(data.get('n_clusters', 3))
#         selected_features = data.get('selected_features', ['total_pembelian', 'frekuensi_pembelian'])
        
#         print(f"[DEBUG] Processing clustering with {n_clusters} clusters using {clustering_method}")
        
#         if not temp_file_id:
#             return jsonify({"message": "temp_file_id diperlukan"}), 400
        
#         # Load data dari temporary file
#         df = load_temp_dataframe(temp_file_id, app.config['UPLOAD_FOLDER'])
#         print(f"[DEBUG] Loaded data dengan {len(df)} baris")
        
#         # Prepare features untuk clustering
#         features_df = prepare_clustering_features(df)
#         print(f"[DEBUG] Prepared features: {features_df.columns.tolist()}")
        
#         # Filter features berdasarkan pilihan user
#         available_features = []
#         for feature in selected_features:
#             if feature in features_df.columns:
#                 available_features.append(feature)
        
#         if len(available_features) < 2:
#             return jsonify({"message": "Minimal 2 fitur diperlukan untuk clustering"}), 400
        
#         clustering_data = features_df[available_features]
        
#         # Standardize data
#         scaler = StandardScaler()
#         scaled_data = scaler.fit_transform(clustering_data)
        
#         # Perform clustering
#         if clustering_method == 'kmeans_plus':
#             kmeans = KMeans(n_clusters=n_clusters, init='k-means++', random_state=42, n_init=10)
#         else:
#             kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        
#         cluster_labels = kmeans.fit_predict(scaled_data)
        
#         # Add cluster labels to features dataframe
#         features_df['cluster'] = cluster_labels
        
#         # Calculate cluster statistics
#         cluster_stats = calculate_cluster_statistics(features_df, available_features)
        
#         # Prepare visualization data (PCA for 2D visualization)
#         pca = PCA(n_components=2)
#         pca_data = pca.fit_transform(scaled_data)
        
#         visualization_data = []
#         for i in range(len(pca_data)):
#             visualization_data.append({
#                 'x': float(pca_data[i][0]),
#                 'y': float(pca_data[i][1]),
#                 'cluster': int(cluster_labels[i]),
#                 'nama_produk': features_df.iloc[i]['nama_produk'] if 'nama_produk' in features_df.columns else f"Produk {i+1}"
#             })
        
#         # Save clustering results
#         results_filename = f"clustering_results_{uuid.uuid4()}.pkl"
#         results_filepath = os.path.join(app.config['UPLOAD_FOLDER'], results_filename)
        
#         clustering_results = {
#             'features_df': features_df,
#             'cluster_labels': cluster_labels,
#             'scaler': scaler,
#             'kmeans_model': kmeans,
#             'selected_features': available_features
#         }
        
#         with open(results_filepath, 'wb') as f:
#             pickle.dump(clustering_results, f)
        
#         return jsonify({
#             "message": "Clustering berhasil diproses",
#             "results_file_id": results_filename,
#             "cluster_count": n_clusters,
#             "features_used": available_features,
#             "cluster_statistics": cluster_stats,
#             "visualization_data": visualization_data,
#             "pca_explained_variance": [float(var) for var in pca.explained_variance_ratio_]
#         }), 200
    
#     except Exception as e:
#         print(f"[DEBUG] Error processing clustering: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         return jsonify({"message": f"Error saat memproses clustering: {str(e)}"}), 500

# def prepare_clustering_features(df):
#     """Prepare features for clustering from transaction data"""
#     print("[DEBUG] Preparing clustering features...")
    
#     # Aggregate data per produk
#     features = df.groupby('nama_produk').agg({
#         'jumlah_terjual': ['sum', 'count', 'mean'],
#         'harga': ['mean', 'std'],
#         'tanggal_transaksi': ['count']
#     }).reset_index()
    
#     # Flatten column names
#     features.columns = [
#         'nama_produk',
#         'total_pembelian',      # sum of jumlah_terjual
#         'frekuensi_pembelian',  # count of transactions
#         'rata_rata_pembelian',  # mean of jumlah_terjual
#         'rata_rata_harga',      # mean of harga
#         'std_harga',           # std of harga
#         'jumlah_transaksi'     # count of transactions (duplicate)
#     ]
    
#     # Calculate additional features
#     features['total_revenue'] = features['total_pembelian'] * features['rata_rata_harga']
#     features['coefficient_variation_harga'] = features['std_harga'] / features['rata_rata_harga']
    
#     # Fill NaN values
#     features = features.fillna(0)
    
#     print(f"[DEBUG] Features prepared: {features.shape}")
#     return features

# def calculate_cluster_statistics(features_df, selected_features):
#     """Calculate statistics for each cluster"""
#     cluster_stats = {}
    
#     for cluster_id in sorted(features_df['cluster'].unique()):
#         cluster_data = features_df[features_df['cluster'] == cluster_id]
        
#         stats = {
#             'cluster_id': int(cluster_id),
#             'product_count': len(cluster_data),
#             'products': cluster_data['nama_produk'].tolist()[:10],  # Max 10 products for preview
#             'feature_stats': {}
#         }
        
#         for feature in selected_features:
#             if feature in cluster_data.columns:
#                 stats['feature_stats'][feature] = {
#                     'mean': float(cluster_data[feature].mean()),
#                     'median': float(cluster_data[feature].median()),
#                     'std': float(cluster_data[feature].std()),
#                     'min': float(cluster_data[feature].min()),
#                     'max': float(cluster_data[feature].max())
#                 }
        
#         cluster_stats[f'cluster_{cluster_id}'] = stats
    
    # return cluster_stats





if __name__ == "__main__":
    print("🚀 Starting Flask test server...")
    print("📍 Server will be available at:")
    print("   - http://localhost:8000")
    print("   - http://127.0.0.1:8000")
    print("\n🔧 Test endpoints:")
    print("   - GET  /         (health check)")
    print("   - POST /login    (test login)")
    print("   - POST /register (test register)")
    print("\n⚠️  This is a TEST SERVER - accepts any credentials!")
    print("-" * 50)
    
    try:
        app.run(debug=True, host="0.0.0.0", port=8000)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        print("💡 Try a different port:")
        print("   app.run(debug=True, host='0.0.0.0', port=3001)")