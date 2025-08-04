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

# from flask import Flask, request, jsonify
# from flask_cors import CORS
# from sqlalchemy.orm import Session
# from werkzeug.security import check_password_hash, generate_password_hash
# from database import SessionLocal, engine
# from models.user import User

# app = Flask(__name__)

# # Konfigurasi CORS yang benar - sesuaikan port dengan frontend Anda
# CORS(app, 
#      origins=["http://localhost:5173"],  # Ubah dari 5174 ke 5173
#      methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
#      allow_headers=["Content-Type", "Authorization", "Accept"],
#      supports_credentials=True)

# # Atau untuk development, gunakan konfigurasi yang lebih permisif:
# # CORS(app, origins="*", allow_headers="*", methods="*")

# # ----------- LOGIN ENDPOINT -----------
# @app.route("/login", methods=["POST"])
# def login():
#     try:
#         db: Session = SessionLocal()
#         data = request.get_json()
        
#         if not data:
#             return jsonify({"message": "No data provided"}), 400
            
#         email = data.get("email")
#         password = data.get("password")

#         if not email or not password:
#             return jsonify({"message": "Email dan password harus diisi"}), 400

#         user = db.query(User).filter(User.email == email).first()

#         if not user or not check_password_hash(user.password_hash, password):
#             return jsonify({"message": "Email atau password salah"}), 401

#         return jsonify({
#             "message": "Login berhasil",
#             "user_id": user.user_id,
#             "nama": user.nama,
#             "email": user.email
#         }), 200
        
#     except Exception as e:
#         return jsonify({"message": f"Server error: {str(e)}"}), 500
#     finally:
#         db.close()

# # ----------- REGISTER ENDPOINT -----------
# @app.route("/register", methods=["POST"])
# def register():
#     try:
#         db: Session = SessionLocal()
#         data = request.get_json()
        
#         if not data:
#             return jsonify({"message": "No data provided"}), 400
            
#         # Perhatikan: frontend mengirim 'name', bukan 'nama'
#         nama = data.get("name")  # Ubah dari "nama" ke "name"
#         email = data.get("email")
#         password = data.get("password")

#         if not nama or not email or not password:
#             return jsonify({"message": "Semua field harus diisi"}), 400

#         # Cek jika email sudah ada
#         if db.query(User).filter(User.email == email).first():
#             return jsonify({"message": "Email sudah terdaftar"}), 409

#         hashed_pw = generate_password_hash(password)
#         user = User(nama=nama, email=email, password_hash=hashed_pw)

#         db.add(user)
#         db.commit()

#         return jsonify({"message": "Registrasi berhasil"}), 201
        
#     except Exception as e:
#         db.rollback()
#         return jsonify({"message": f"Server error: {str(e)}"}), 500
#     finally:
#         db.close()

# # ----------- HEALTH CHECK -----------
# @app.route("/", methods=["GET"])
# def health_check():
#     return jsonify({"message": "API is running"}), 200

# # ----------- RUN APP -----------
# if __name__ == "__main__":
#     app.run(debug=True, host="0.0.0.0", port=8000)

from flask import Flask, request, jsonify
from flask_cors import CORS
import json

app = Flask(__name__)

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