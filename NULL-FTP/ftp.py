from flask import Flask, render_template, request, redirect, url_for, send_from_directory, send_file
from io import BytesIO

import os

from ftplib import FTP

app = Flask(__name__)

FTP_DIR = '/data/data/com.termux/files/home/NULL-FTP/FTP/files'

app.config['UPLOAD_FOLDER'] = FTP_DIR

@app.route('/')
def index():
    directory = '/data/data/com.termux/files/home/NULL-FTP/FTP/files'
    files = os.listdir(directory)
    return render_template('index.html', files=files)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect("/")

    file = request.files['file']

    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        return 'File uploaded successfully to FTP server.'

@app.route('/download/<filename>')
def download_file(filename):
    # Set the path to your files directory
    dir = '/data/data/com.termux/files/home/NULL-FTP/FTP/files'
    # Get the full path of the requested file
    file_path = os.path.join(dir, filename)
    # Send the file for download
    return send_file(file_path, as_attachment=True)

@app.route('/view/<filename>')
def view_file(filename):
    # Set the path to your files directory
    dir = '/data/data/com.termux/files/home/NULL-FTP/FTP/files'
    # Get the full path of the requested file
    file_path = os.path.join(dir, filename)
    # Send the file for view
    return send_file(file_path)

@app.route('/test/<filename>')
def test_file(filename):
    dir = '/data/data/com.termux/files/home/NULL-FTP/test'
    file_path = os.path.join(dir, filename)
    return send_file(file_path)

@app.route('/nullftp/<filename>')
def download_nullftp(filename):
    dir = '/data/data/com.termux/files/home/NULL-FTP/download_nullftp'
    file_path = os.path.join(dir, filename)
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)
