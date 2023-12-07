from flask import Flask,redirect,url_for,render_template,request

app=Flask(__name__)
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register.html')
def register():
    return render_template('register.html')


if __name__ == '__main__':
    app.run('0.0.0.0',port=5000,debug=True)