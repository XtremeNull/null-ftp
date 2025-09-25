from flask import Flask, render_template, request, redirect, url_for, send_from_directory, send_file, session
from io import BytesIO
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from ftplib import FTP

app = Flask(__name__)

app.secret_key = ""

USER_FILE = os.path.join(os.path.dirname(__file__), "users.json")

FTP_DIR = '/home/null/NULL-FTP/FTP/files'
TEST_DIR = '/home/null/NULL-FTP/test'
app.config['FTP_FOLDER'] = FTP_DIR
app.config['TEST_FOLDER'] = TEST_DIR

def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f)

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    username = request.form.get("username")
    password = request.form.get("password")
    if request.method == 'POST':
        attempted_username = request.form['username'].strip()
        attempted_password = request.form['password']

        users = load_users()

        if username in users and check_password_hash(users[username], password):
            session["logged_in"] = True
            session["username"] = username
            return redirect(url_for('index'))
        else:
            error = "Incorrect username or password!"
    return render_template('login.html', error=error)

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        users = load_users()
        if username in users:
            error = "This username already exists!"
        else:
            users[username] = generate_password_hash(password)
            save_users(users)
            return redirect(url_for("login"))
    return render_template("register.html", error=error)

@app.route("/unregister", methods=["GET", "POST"])
def unregister():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    users = load_users()

    if request.method == "POST":
        password = request.form.get("password")
        stored_hash = users.get(username)

        if stored_hash and check_password_hash(stored_hash, password):
            del users[username]
            save_users(users)
            session.clear()
            return redirect(url_for("login"))
        else:
            error = "Incorrect password. Account not deleted."
            return render_template("unregister.html", error=error)

    return render_template("unregister.html")

@app.route('/search')
def search():
    query = request.args.get('q', '').lower()
    results = []

    if query:
        for root, dirs, files in os.walk(FTP_DIR):
            for file in files:
                if query in file.lower():
                    rel_path = os.path.relpath(os.path.join(root, file), FTP_DIR)
                    results.append(rel_path)

    return render_template("search.html", query=query, results=results)

@app.route('/home')
def index():
    files = os.listdir(app.config['FTP_FOLDER'])
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template('index.html', username=session.get("username"), files=files)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect("/")
    file = request.files['file']
    if file:
        file_path = os.path.join(app.config['FTP_FOLDER'], file.filename)
        file.save(file_path)

        return 'File uploaded successfully to FTP server.'

@app.route('/download/<filename>')
def download_file(filename):
    # Get the full path of the requested file
    file_path = os.path.join(app.config['FTP_FOLDER'], filename)
    # Send the file for download
    return send_file(file_path, as_attachment=True)

@app.route('/view/<filename>')
def view_file(filename):
    # Get the full path of the requested file
    file_path = os.path.join(app.config['FTP_FOLDER'], filename)
    # Send the file for view
    return send_file(file_path, as_attachment=False)

@app.route('/test/<filename>')
def test_file(filename):
    file_path = os.path.join(app.config['TEST_FOLDER'], filename)
    return send_file(file_path)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)