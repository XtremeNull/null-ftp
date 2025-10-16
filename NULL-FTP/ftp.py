from flask import Flask, render_template, request, redirect, url_for, send_from_directory, send_file, session
from io import BytesIO
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import json
import os
import urllib.parse
from ftplib import FTP
app = Flask(__name__)
app.secret_key = ""
USER_FILE = os.path.join(os.path.dirname(__file__), "users.json")
FTP_DIR = '/home/null/NULL-FTP/FTP/files/'
TEST_DIR = '/home/null/NULL-FTP/test/'
app.config['FTP_FOLDER'] = FTP_DIR
app.config['TEST_FOLDER'] = TEST_DIR
def is_safe_path(base_dir, filename):
    """
    Validate that the requested file path is safe and within the base directory.
    Prevents path traversal attacks.
    """
    if not filename:
        return False
    # Decode URL encoding attempts (do this multiple times to handle double encoding)
    original_filename = filename
    for _ in range(3):  # Handle up to triple encoding
        decoded = urllib.parse.unquote(filename)
        if decoded == filename:
            break
        filename = decoded
    # Block paths with null bytes or other suspicious characters
    if '\x00' in filename or '\x00' in original_filename:
        return False
    # Normalize path separators and handle various path traversal attempts
    # Replace Windows-style separators and normalize
    normalized_filename = filename.replace('\\', '/')
    normalized_filename = os.path.normpath(normalized_filename)
    # Block absolute paths and paths that try to go up directories
    if os.path.isabs(normalized_filename) or normalized_filename.startswith('..') or '/..' in normalized_filename:
        return False
    # Construct the full path and verify it's within the base directory
    full_path = os.path.join(base_dir, normalized_filename)
    full_path = os.path.abspath(full_path)
    base_dir = os.path.abspath(base_dir)
    # Check if the resolved path is within the base directory
    return full_path.startswith(base_dir + os.sep) or full_path == base_dir
def get_safe_file_path(base_dir, filename):
    """
    Get a safe file path within the base directory, or None if invalid.
    """
    if not is_safe_path(base_dir, filename):
        return None
    # Decode URL encoding attempts (do this multiple times to handle double encoding)
    for _ in range(3):  # Handle up to triple encoding
        decoded = urllib.parse.unquote(filename)
        if decoded == filename:
            break
        filename = decoded
    # Normalize path separators and handle various path traversal attempts
    normalized_filename = filename.replace('\\', '/')
    normalized_filename = os.path.normpath(normalized_filename)
    return os.path.join(base_dir, normalized_filename)
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
                    # Only include files that pass safety checks
                    if is_safe_path(FTP_DIR, rel_path):
                        results.append(rel_path)
    return render_template("search.html", query=query, results=results)
@app.route('/home', defaults={'subpath': ''})
@app.route('/home/<path:subpath>')
def index(subpath):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    base_dir = app.config['FTP_FOLDER']
    # Handle the root directory safely
    if not subpath:
        safe_path = base_dir
    else:
        safe_path = get_safe_file_path(base_dir, subpath)
        if not safe_path:
            return "Invalid path.", 400
    # Now confirm this is a directory
    if not os.path.exists(safe_path):
        return "Directory not found.", 404
    if not os.path.isdir(safe_path):
        return "Not a directory.", 400
    # List contents
    items = os.listdir(safe_path)
    folders = []
    files = []
    for item in sorted(items):
        full_path = os.path.join(safe_path, item)
        rel_path = os.path.relpath(full_path, base_dir)
        if os.path.isdir(full_path):
            folders.append(rel_path)
        else:
            files.append(rel_path)
    parent_path = os.path.dirname(subpath) if subpath else None
    return render_template(
        'index.html',
        username=session.get("username"),
        current_path=subpath,
        parent_path=parent_path,
        folders=folders,
        files=files
    )
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))
@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect("/")
    file = request.files['file']
    if file and file.filename:
        # Secure the filename to prevent path traversal
        safe_filename = secure_filename(file.filename)
        if not safe_filename:
            return 'Invalid filename.', 400
        file_path = os.path.join(app.config['FTP_FOLDER'], safe_filename)
        file.save(file_path)
        return 'File uploaded successfully to FTP server.'
@app.route('/download/<path:filename>')
def download_file(filename):
    # Validate and get safe file path
    file_path = get_safe_file_path(app.config['FTP_FOLDER'], filename)
    if not file_path:
        return 'Invalid file path.', 400
    # Check if file exists
    if not os.path.exists(file_path):
        return 'File not found.', 404
    # Send the file for download
    return send_file(file_path, as_attachment=True)
@app.route('/view/<path:filename>')
def view_file(filename):
    # Validate and get safe file path
    file_path = get_safe_file_path(app.config['FTP_FOLDER'], filename)
    if not file_path:
        return 'Invalid file path.', 400
    # Check if file exists
    if not os.path.exists(file_path):
        return 'File not found.', 404
    # Send the file for view
    return send_file(file_path, as_attachment=False)
@app.route('/test/<filename>')
def test_file(filename):
    # Validate and get safe file path
    file_path = get_safe_file_path(app.config['TEST_FOLDER'], filename)
    if not file_path:
        return 'Invalid file path.', 400
    # Check if file exists
    if not os.path.exists(file_path):
        return 'File not found.', 404
    return send_file(file_path)
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)