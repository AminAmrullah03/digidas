from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from os.path import join, dirname
from bson import ObjectId, json_util
import jwt
import hashlib
from datetime import datetime, timedelta
import json

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME = os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
pindahan = db['pindahan']
pelanggarans = db['pelanggarans']
datasantri = db['datasantri']
datainv = db['datainv']
datapulang = db['pulang']
dataizin = db['izin']
targets = db['target']

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
            user = datasantri.find_one({"nis": nis})
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
                return redirect(url_for("login"))
            
        return jsonify({'result': 'success'})
    
@app.route("/dashboard")
def dashboard():
    user_id = session.get("user_id")
    if not user_id:
        flash("Anda harus login terlebih dahulu!", "danger")
        return redirect(url_for("home"))
    user = datasantri.find_one({"_id": user_id})
    return render_template("dashboard.html", user=user)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/pendataan")
def pendataan():
    return render_template("pendataan_santri.html")

@app.route("/profile")
def profile():
    user_id = session.get("user_id")

    if not user_id:
        flash("Anda harus login terlebih dahulu!", "danger")
        return redirect(url_for("home"))

    user_data = datasantri.find_one({"_id": ObjectId(user_id)})

    if user_data:
        return render_template("profile.html", user=user_data)
    else:
        flash("Data santri tidak ditemukan.", "danger")
        return redirect(url_for("home"))

@app.route("/inventaris")
def inventaris():
    data = list(datainv.find())
    return render_template('inventaris.html', data=data)

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
        raw_password = request.form['password']
        hashed_password = hashlib.sha256(raw_password.encode()).hexdigest()
        data = {
            'nama': nama,
            'nis': nis,
            'jenis_kelamin': jenis_kelamin,
            'no_hp': no_hp,
            'alamat': alamat,
            'password': hashed_password,
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
        return redirect(url_for('pelanggaran', success=1))

@app.route('/data_pelanggaran')
def data_pelanggaran():
    data = pelanggarans.find()
    return render_template('data_pelanggaran.html', data=data)

@app.route('/hapus_data/<id>')
def hapus_data(id):
    pelanggarans.delete_one({'_id': ObjectId(id)})
    return redirect(url_for('data_pelanggaran'))

@app.route('/jurnal')
def jurnal():
    return render_template('jurnal.html')

@app.route('/tambah_daftar', methods=['GET', 'POST'])
def tambah_daftar():
    if request.method == 'POST':
        data = {
            'nama_barang': request.form['nama_barang'],
            'jumlah': request.form['jumlah'],
            'kondisi_bagus': request.form['kondisi_bagus'],
            'kondisi_rusak': request.form['kondisi_rusak'],
        }
        datainv.insert_one(data)
        return redirect(url_for('inventaris', success=1))
    
@app.route('/hapus_data_inventaris/<id>')
def hapus_data_inventaris(id):
    datainv.delete_one({'_id': ObjectId(id)})
    return jsonify({'result': 'success'})

@app.route('/get_data_inventaris/<id>')
def get_data_inventaris(id):
    data = datainv.find_one({'_id': ObjectId(id)})
    data['_id'] = str(data['_id'])
    return jsonify(json.loads(json_util.dumps(data)))

@app.route('/edit_data_inventaris/<id>', methods=['POST'])
def edit_data_inventaris(id):
    if request.method == 'POST':
        filter_query = {'_id': ObjectId(id)}
        update_data = {
            '$set': {
                'nama_barang': request.form['nama_barang'],
                'jumlah': request.form['jumlah'],
                'kondisi_bagus': request.form['kondisi_bagus'],
                'kondisi_rusak': request.form['kondisi_rusak'],
            }
        }

        datainv.update_one(filter_query, update_data)
        return jsonify({'result': 'success'})

@app.route('/mutasi')
def mutasi():
    data = pindahan.find()
    return render_template('mutasi.html', data=data)

@app.route('/tambah_mutasi', methods=['POST'])
def tambah_mutasi():
    if request.method == 'POST':
        data = {
            'nama': request.form['nama'],
            'jenis_kelamin': request.form['jenis_kelamin'],
            'tanggal': request.form['tanggal'],
            'status': request.form['status'],
        }
        pindahan.insert_one(data)
        return redirect(url_for('mutasi', success=1))
    
@app.route('/santri_pulang')
def santri_pulang():
    return render_template('santri_pulang.html')

@app.route('/data_pulang')
def data_pulang():
    data = datapulang.find()
    return render_template('data_pulang.html', data=data)

@app.route('/tambah_pulang', methods=['POST'])
def tambah_pulang():
    if request.method == 'POST':
        data = {
            'nama': request.form['nama'],
            'nis': request.form['nis'],
            'alasan': request.form['alasan'],
            'durasi': request.form['durasi'],
            'tanggal': request.form['tanggal'],
            'penjemput': request.form['penjemput'],
            'status_penjemput': request.form['status_penjemput'],
            'pemberi_izin': request.form['pemberi_izin'],
        }
        datapulang.insert_one(data)
        return redirect(url_for('santri_pulang', success=1))

@app.route('/pengumuman')
def pengumuman():
    return render_template('/pengumuman.html')

@app.route('/izin_keluar')
def izin_keluar():
    return render_template('izin_keluar.html')

@app.route('/tambah_keluar', methods=['POST'])
def tambah_keluar():
    if request.method == 'POST':
        data = {
            'nama': request.form['nama'],
            'nis': request.form['nis'],
            'alasan': request.form['alasan'],
            'tanggal': request.form['tanggal'],
        }
        dataizin.insert_one(data)
        return redirect(url_for('izin_keluar', success=1))

@app.route('/data_izin')
def data_izin():
    data = dataizin.find()
    return render_template('data_izin.html', data=data)

@app.route('/hapus_izin/<id>')
def hapus_izin(id):
    dataizin.delete_one({'_id': ObjectId(id)})
    return redirect(url_for('data_izin'))

@app.route('/target')
def target():
    data = targets.find()
    return render_template('target.html', data=data)

@app.route('/tambah_target', methods=['GET', 'POST'])
def tambah_target():
    if request.method == 'POST':
        data = {
            'judul': request.form['judul'],
            'isi': request.form['isi'],
        }
        targets.insert_one(data)
        return redirect(url_for('target', success=1))
    
@app.route('/edit_target', methods=['POST'])
def edit_target():
    if request.method == 'POST':
        target_id = request.form['target_id']
        if ObjectId.is_valid(target_id):
            updated_data = {
                'judul': request.form['judul'],
                'isi': request.form['isi'],
            }
            targets.update_one({'_id': ObjectId(target_id)}, {'$set': updated_data})
            return redirect(url_for('target'))
        else:
            flash('Invalid ObjectId', 'error')
            return redirect(url_for('target'))

@app.route('/delete_target/<target_id>', methods=['DELETE'])
def delete_target(target_id):
    try:
        # Convert target_id to ObjectId
        target_id_obj = ObjectId(target_id)

        # Perform deletion
        result = targets.delete_one({'_id': target_id_obj})

        if result.deleted_count > 0:
            # Successful deletion
            return '', 204  # HTTP status code for No Content
        else:
            # No document found with the specified ID
            return 'Target not found', 404

    except Exception as e:
        print('Error during deletion:', str(e))
        return 'Internal Server Error', 500

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
