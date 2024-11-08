from flask import Flask, render_template, request, redirect, url_for, send_from_directory, send_file
from io import BytesIO

import os

from ftplib import FTP

app = Flask(__name__)

FTP_DIR = './FTP/files'
FTP_DIR = './test'
app.config['FTP_FOLDER'] = FTP_DIR
app.config['TEST_FOLDER'] = TEST_DIR

@app.route('/')
def index():
    files = os.listdir(app.config['FTP_FOLDER'])
    return render_template('index.html', files=files)

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
    dir = '/data/data/com.termux/files/home/NULL-FTP/test'
    file_path = os.path.join(app.config['TEST_FOLDER'], filename)
    return send_file(file_path)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)
