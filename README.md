Steps for downloading NULL-FTP:
1. Download zip file of this repo
2. Exctract the downloaded zip file
3. Move the folder named NULL-FTP into your home directory
4. Enjoy

In order for login system to work, you need to generate secret key (see line 10 in ftp.py).

You can generate the key with this command:
python3 -c "import secrets; print(secrets.token_hex(32))"