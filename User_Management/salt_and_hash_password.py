#!/Users/porta031/eman2-sphire-sparx/bin/python

import os
import hashlib

def generate_salt(length=16):
    """Generate a random salt of specified length"""
    return os.urandom(length)

def hash_password(password, salt):
    """Hash password using the salt"""
    salted_password = password.encode('utf-8') + salt
    hashed_password = hashlib.sha256(salted_password).hexdigest()
    return hashed_password

salt = generate_salt()
password = "ENTER PASSWORD"
hashed_password = hash_password(password, salt)

print("Salt:", salt.hex())
print("Hashed password:", hashed_password)
