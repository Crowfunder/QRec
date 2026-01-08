# https://flask.palletsprojects.com/en/3.0.x/config/#SECRET_KEY
SECRET_KEY = 'your-very-secret-key-here'  # does not matter - for lab only
                    # remember to change it if backend is working in the production environment!!!

JSON_SORT_KEYS = False
BABEL_DEFAULT_LOCALE = 'en'
TEMPLATES_AUTO_RELOAD = True

SECURITY_PASSWORD_SALT = ''
QR_SECRET_KEY = b'bMpM5ECy4iwHXYyaQvflStzVrkjXn0D5SGM_cJG_zgY=' # Fernet.generate_key()