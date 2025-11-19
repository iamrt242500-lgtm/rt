import os
from lib.auth_store import register_user, authenticate_user
from lib import pqc_envelope

username = "pqc_test_user"
password = "pqc_Test#123"

try:
    created = register_user(username, password)
except Exception as e:
    print("register_error:", type(e).__name__, str(e))
    created = False

ok = authenticate_user(username, password)

data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
enc_path = os.path.abspath(os.path.join(data_dir, 'users.enc'))
json_path = os.path.abspath(os.path.join(data_dir, 'users.json'))
pub_path = os.path.abspath(os.path.join(data_dir, 'kem_pub.bin'))
priv_path = os.path.abspath(os.path.join(data_dir, 'kem_priv.bin'))

print("created:", created)
print("auth_ok:", ok)
print("users.enc_exists:", os.path.exists(enc_path), enc_path)
print("users.json_exists:", os.path.exists(json_path), json_path)
print("pqc_available:", pqc_envelope.has_pqc())
print("kem_pub_exists:", os.path.exists(pub_path), pub_path)
print("kem_priv_exists:", os.path.exists(priv_path), priv_path)
