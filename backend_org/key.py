import secrets

SECRET_KEY = secrets.token_hex(32)  # Generates a 64-character key
print(SECRET_KEY)
