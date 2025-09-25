You can download NULL-FTP with the git clone command

Alternatively, you can consider doing these steps:
1. Install the Flask module with pip install flask
2. Download zip file of this repo
3. Exctract the downloaded zip file
4. Move the folder named NULL-FTP into your home directory
5. Enjoy



In order for login system to work, you need to generate secret key (see line 10 in ftp.py).

You can generate the key with this command:
python3 -c "import secrets; print(secrets.token_hex(32))"
