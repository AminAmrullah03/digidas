from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from os.path import join, dirname
from bson import ObjectId
from werkzeug.security import check_password_hash
import jwt
import hashlib
from datetime import datetime, timedelta

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME = os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
pelanggarans = db['pelanggarans']
datasantri = db['datasantri']

app = Flask(__name__)
app.secret_key = 'hello_print'

TOKEN_KEY = 'mytoken'
SECRET_KEY = 'SPARTA'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method in ['GET', 'POST']:
        if request.method == 'GET':
            return render_template('login.html')
        elif request.method == 'POST':
            nis = request.form.get('nis')
            password = request.form.get('password')
            pw_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
            # print(nis,password)
            user = datasantri.find_one({"nis": nis})
            # print(pw_hash)
            if user and (user["password"] == pw_hash):
                print(user['password'], pw_hash)
                session["user_id"] = str(user["_id"])
                return jsonify({
                    'result': 'success',
                    'user_id': session['user_id'],
                    'nama': user['nama']
                    })
            
            else:
                flash("NIS atau password tidak valid.", "danger")
                return redirect(url_for("home"))
            
        return jsonify({'result': 'success'})

    # # Cek apakah user ditemukan dan password valid
    #     # Login berhasil, set session dan redirect ke dashboard
    
@app.route("/dashboard")
def dashboard():
    user_id = session.get("user_id")
    if not user_id:
        flash("Anda harus login terlebih dahulu!", "danger")
        return redirect(url_for("home"))
    user = datasantri.find_one({"_id": user_id})

    # Render template dashboard dengan data user
    return render_template("dashboard.html", user=user)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/pelanggaran")
def pelanggaran():
    return render_template("pelanggaran.html")

@app.route('/tambah_santri', methods=['GET', 'POST'])
def tambah_santri():
    if request.method == 'POST':
        nama = request.form['nama']
        nis = request.form['nis']
        jenis_kelamin = request.form['jenis_kelamin']
        no_hp = request.form['no_hp']
        alamat = request.form['alamat']
        raw_password = request.form['password']  # Ambil password mentah dari form

        # Hash password menggunakan SHA-256
        hashed_password = hashlib.sha256(raw_password.encode()).hexdigest()

        data = {
            'nama': nama,
            'nis': nis,
            'jenis_kelamin': jenis_kelamin,
            'no_hp': no_hp,
            'alamat': alamat,
            'password': hashed_password,  # Simpan password yang sudah di-hash
            'status': 'santri',
        }
        datasantri.insert_one(data)
        flash('Data berhasil ditambahkan!', 'success')
        return redirect(url_for('tambah_santri', success=1))

    return render_template('tambah_santri.html')
@app.route('/tambah_data', methods=['POST'])
def tambah_data():
    if request.method == 'POST':
        data = {
            'nama': request.form['nama'],
            'nis': request.form['nis'],
            'jenis_pelanggaran': request.form['jenis_pelanggaran'],
            'kategori_pelanggaran': request.form['kategori_pelanggaran'],
            'tanggal': request.form['tanggal'],
        }
        pelanggarans.insert_one(data)
        flash('Data berhasil ditambahkan!', 'success')
        return redirect(url_for('pelanggaran', success=1))

@app.route('/data_pelanggaran')
def data_pelanggaran():
    data = pelanggarans.find()  # Ambil semua data dari pelanggarans
    return render_template('data_pelanggaran.html', data=data)

@app.route('/hapus_data/<id>')
def hapus_data(id):
    pelanggarans.delete_one({'_id': ObjectId(id)})
    return redirect(url_for('data_pelanggaran'))

@app.route('/jurnal')
def jurnal():
    return render_template('jurnal.html')


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
