# from flask import Flask, request, jsonify
# from flask_cors import CORS
# from sqlalchemy.orm import Session
# from werkzeug.security import check_password_hash
# from database import SessionLocal, engine
# from models.user import User
# from werkzeug.security import generate_password_hash

# app = Flask(__name__)
# CORS(app)

# # ----------- LOGIN ENDPOINT -----------
# @app.route("/login", methods=["POST"])
# def login():
#     db: Session = SessionLocal()
#     data = request.get_json()
#     email = data.get("email")
#     password = data.get("password")

#     user = db.query(User).filter(User.email == email).first()

#     if not user or not check_password_hash(user.password_hash, password):
#         return jsonify({"message": "Email atau password salah"}), 401

#     return jsonify({
#         "message": "Login berhasil",
#         "user_id": user.user_id,
#         "nama": user.nama,
#         "email": user.email
#     }), 200




# @app.route("/register", methods=["POST"])
# def register():
#     db: Session = SessionLocal()
#     data = request.get_json()
#     nama = data.get("nama")
#     email = data.get("email")
#     password = data.get("password")

#     # Cek jika email sudah ada
#     if db.query(User).filter(User.email == email).first():
#         return jsonify({"message": "Email sudah terdaftar"}), 409

#     hashed_pw = generate_password_hash(password)
#     user = User(nama=nama, email=email, password_hash=hashed_pw)

#     db.add(user)
#     db.commit()

#     return jsonify({"message": "Registrasi berhasil"}), 201


# # ----------- RUN APP -----------
# if __name__ == "__main__":
#     app.run(debug=True)


from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash
from database import SessionLocal, engine
from models.user import User

app = Flask(__name__)

# Konfigurasi CORS yang lebih spesifik
CORS(app, origins=["http://localhost:5174"], 
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"])

# Alternatively, you can use more permissive CORS for development:
# CORS(app, origins="*")

# ----------- LOGIN ENDPOINT -----------
@app.route("/login", methods=["POST"])
def login():
    try:
        db: Session = SessionLocal()
        data = request.get_json()
        
        if not data:
            return jsonify({"message": "No data provided"}), 400
            
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"message": "Email dan password harus diisi"}), 400

        user = db.query(User).filter(User.email == email).first()

        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({"message": "Email atau password salah"}), 401

        return jsonify({
            "message": "Login berhasil",
            "user_id": user.user_id,
            "nama": user.nama,
            "email": user.email
        }), 200
        
    except Exception as e:
        return jsonify({"message": f"Server error: {str(e)}"}), 500
    finally:
        db.close()

# ----------- REGISTER ENDPOINT -----------
@app.route("/register", methods=["POST"])
def register():
    try:
        db: Session = SessionLocal()
        data = request.get_json()
        
        if not data:
            return jsonify({"message": "No data provided"}), 400
            
        # Perhatikan: frontend mengirim 'name', bukan 'nama'
        nama = data.get("name")  # Ubah dari "nama" ke "name"
        email = data.get("email")
        password = data.get("password")

        if not nama or not email or not password:
            return jsonify({"message": "Semua field harus diisi"}), 400

        # Cek jika email sudah ada
        if db.query(User).filter(User.email == email).first():
            return jsonify({"message": "Email sudah terdaftar"}), 409

        hashed_pw = generate_password_hash(password)
        user = User(nama=nama, email=email, password_hash=hashed_pw)

        db.add(user)
        db.commit()

        return jsonify({"message": "Registrasi berhasil"}), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({"message": f"Server error: {str(e)}"}), 500
    finally:
        db.close()

# ----------- HEALTH CHECK -----------
@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"message": "API is running"}), 200

# ----------- RUN APP -----------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)