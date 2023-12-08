from flask import Flask,redirect,url_for,render_template,request
from pymongo import MongoClient
import jwt
from dotenv import load_dotenv
import os
from os.path import join, dirname


dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URI)

db = client[DB_NAME]


app=Flask(__name__)
@app.route('/')
def home():
    return render_template('index.html')

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/pelanggaran")
def pelanggaran():
    return render_template("pelanggaran.html")

if __name__ == '__main__':
    app.run('0.0.0.0',port=5000,debug=True)