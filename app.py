


from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import uuid
import pandas as pd
from werkzeug.utils import secure_filename
from sqlalchemy.orm import Session
from fastapi import Depends  # Kita pinjam konsep Depends untuk get_db
app = Flask(__name__)
# Impor model dan koneksi DB Anda
# Sesuaikan path impor ini dengan struktur proyek Anda
from database import get_db, engine 
from models.dataset import Dataset
from models.produk import Produk


# CORS configuration - very permissive for testing
CORS(app, 
     origins=["http://localhost:5173", "http://127.0.0.1:5173"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "Accept"],
     supports_credentials=True)

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


# ======================================================================
# ENDPOINT 1: UPLOAD & PREVIEW DATA
# ======================================================================

@app.route("/upload/preview", methods=["POST"])
def upload_preview():
    if 'file' not in request.files:
        return jsonify({"message": "Tidak ada file yang diunggah"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "Tidak ada file yang dipilih"}), 400
    if not file or not allowed_file(file.filename):
        return jsonify({"message": "Tipe file tidak valid. Gunakan CSV atau Excel."}), 400

    try:
        print("\n--- [DEBUG] Memulai Proses Upload ---")
        
        # Load data
        if 'csv' in file.filename:
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

        # PERBAIKAN: Cek dan buat tanggal_transaksi SEBELUM validasi kolom inti
        if 'tanggal_transaksi' not in processed_df.columns:
            print("[DEBUG] 'tanggal_transaksi' tidak ditemukan, mencoba membuat dari 'bulan' dan 'tahun'.")
            if 'bulan' in processed_df.columns and 'tahun' in processed_df.columns:
                print("[DEBUG] Kolom 'bulan' DAN 'tahun' ditemukan! Mencoba menggabungkan...")
                
                # Mapping nama bulan Indonesia ke angka
                BULAN_MAPPING = {
                    'januari': 1, 'jan': 1,
                    'februari': 2, 'feb': 2,
                    'maret': 3, 'mar': 3,
                    'april': 4, 'apr': 4,
                    'mei': 5,
                    'juni': 6, 'jun': 6,
                    'juli': 7, 'jul': 7,
                    'agustus': 8, 'agu': 8, 'ags': 8,
                    'september': 9, 'sep': 9, 'sept': 9,
                    'oktober': 10, 'okt': 10, 'oct': 10,
                    'november': 11, 'nov': 11,
                    'desember': 12, 'des': 12, 'dec': 12,
                    # Tambahan untuk bahasa Inggris
                    'january': 1, 'february': 2, 'march': 3,
                    'may': 5, 'june': 6, 'july': 7,
                    'august': 8, 'october': 10, 'december': 12
                }
                
                print(f"[DEBUG] Sample bulan original: {processed_df['bulan'].head()}")
                print(f"[DEBUG] Sample tahun original: {processed_df['tahun'].head()}")
                
                # Konversi bulan dari nama ke angka
                bulan_series = processed_df['bulan'].astype(str).str.lower().str.strip()
                bulan_numeric = bulan_series.map(BULAN_MAPPING)
                
                # Jika tidak bisa dimap, coba konversi langsung ke numeric (untuk kasus data sudah angka)
                bulan_numeric = bulan_numeric.fillna(pd.to_numeric(bulan_series, errors='coerce'))
                
                # Konversi tahun ke numeric
                tahun_numeric = pd.to_numeric(processed_df['tahun'], errors='coerce')
                
                print(f"[DEBUG] Sample bulan setelah konversi: {bulan_numeric.head()}")
                print(f"[DEBUG] Sample tahun setelah konversi: {tahun_numeric.head()}")
                
                # Buat mask untuk data yang valid
                valid_mask = bulan_numeric.notna() & tahun_numeric.notna() & \
                            (bulan_numeric >= 1) & (bulan_numeric <= 12) & \
                            (tahun_numeric >= 1900) & (tahun_numeric <= 2100)
                
                print(f"[DEBUG] Jumlah baris dengan bulan/tahun valid: {valid_mask.sum()}")
                print(f"[DEBUG] Total baris: {len(processed_df)}")
                
                if valid_mask.sum() > 0:
                    # Buat string tanggal dengan format yang konsisten
                    date_strings = tahun_numeric.astype('Int64').astype(str) + '-' + \
                                  bulan_numeric.astype('Int64').astype(str).str.zfill(2) + '-01'
                    
                    print(f"[DEBUG] Sample date strings: {date_strings.head()}")
                    
                    # Konversi ke datetime dengan format yang eksplisit
                    try:
                        date_series = pd.to_datetime(date_strings, format='%Y-%m-%d', errors='coerce')
                        print(f"[DEBUG] Sample parsed dates: {date_series.head()}")
                        
                        # Cek apakah ada tanggal yang berhasil diparsing
                        valid_dates = date_series.notna().sum()
                        print(f"[DEBUG] Jumlah tanggal valid yang berhasil dibuat: {valid_dates}")
                        
                        if valid_dates > 0:
                            processed_df['tanggal_transaksi'] = date_series
                            mapped_info['tanggal_transaksi'] = "Dibuat dari gabungan kolom 'bulan' dan 'tahun'"
                            print("[DEBUG] Berhasil membuat kolom 'tanggal_transaksi'!")
                            
                            # Hapus kolom bulan dan tahun setelah berhasil membuat tanggal
                            processed_df.drop(columns=['bulan', 'tahun'], inplace=True, errors='ignore')
                        else:
                            print("[DEBUG] Gagal membuat tanggal yang valid dari kolom 'bulan' dan 'tahun'.")
                            return jsonify({
                                "message": "Tidak dapat membuat tanggal dari kolom 'bulan' dan 'tahun'. Pastikan nama bulan valid (Januari, Februari, dll) dan tahun (1900-2100) valid."
                            }), 400
                            
                    except Exception as date_error:
                        print(f"[DEBUG] Error saat parsing tanggal: {str(date_error)}")
                        return jsonify({
                            "message": f"Error saat membuat tanggal dari kolom bulan/tahun: {str(date_error)}"
                        }), 400
                else:
                    print("[DEBUG] Tidak ada baris dengan bulan/tahun yang valid.")
                    print(f"[DEBUG] Contoh bulan yang tidak dikenali: {bulan_series[bulan_numeric.isna()].unique()[:5]}")
                    return jsonify({
                        "message": "Tidak ada data bulan/tahun yang valid. Pastikan nama bulan dalam format Indonesia (Januari, Februari, dll) atau Inggris (January, February, dll) dan tahun 1900-2100."
                    }), 400
            else:
                missing_cols = []
                if 'bulan' not in processed_df.columns:
                    missing_cols.append('bulan')
                if 'tahun' not in processed_df.columns:
                    missing_cols.append('tahun')
                print(f"[DEBUG] Kolom yang hilang: {missing_cols}")
                return jsonify({
                    "message": f"Kolom tanggal tidak ditemukan. Diperlukan kolom 'tanggal_transaksi' atau kombinasi 'bulan' dan 'tahun'. Kolom yang hilang: {', '.join(missing_cols)}"
                }), 400

        print("[DEBUG] Memulai validasi kolom inti...")
        missing_columns = []
        for col in KOLOM_INTI:
            if col not in processed_df.columns:
                missing_columns.append(col)
                print(f"[DEBUG] GAGAL VALIDASI! Kolom wajib '{col}' tidak ditemukan.")
        
        if missing_columns:
            return jsonify({
                "message": f"Kolom wajib tidak ditemukan: {', '.join(missing_columns)}. Pastikan file Anda memiliki kolom yang sesuai."
            }), 400
        
        print("[DEBUG] Semua kolom inti ditemukan. Validasi sukses.")
        
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
             return jsonify({"message": "Data tidak valid setelah pembersihan. Pastikan semua kolom wajib memiliki nilai yang valid."}), 400

        # Simpan file sementara dengan fallback format
        try:
            # Coba parquet dulu (format terbaik)
            temp_filename = f"temp_{uuid.uuid4()}.parquet"
            temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
            processed_df.to_parquet(temp_filepath)
            print("[DEBUG] File disimpan dalam format parquet")
        except ImportError:
            # Jika parquet tidak tersedia, gunakan pickle
            temp_filename = f"temp_{uuid.uuid4()}.pkl"
            temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
            processed_df.to_pickle(temp_filepath)
            print("[DEBUG] File disimpan dalam format pickle")
        except Exception as e:
            # Fallback ke CSV
            temp_filename = f"temp_{uuid.uuid4()}.csv"
            temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
            processed_df.to_csv(temp_filepath, index=False)
            print("[DEBUG] File disimpan dalam format CSV")

        # Buat preview data dengan format tanggal yang lebih bersih
        preview_df = processed_df.head(10).copy()
        
        # Format tanggal sesuai dengan data asli (hanya tahun-bulan)
        if 'tanggal_transaksi' in preview_df.columns:
            preview_df['tanggal_transaksi'] = preview_df['tanggal_transaksi'].dt.strftime('%Y-%m')
        
        preview_data = preview_df.to_json(orient='records')

        print("[DEBUG] Upload dan preview berhasil!")
        return jsonify({
            "message": "File berhasil divalidasi.",
            "temp_file_id": temp_filename,
            "column_mapping_info": mapped_info,
            "preview_data": json.loads(preview_data),
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
#

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