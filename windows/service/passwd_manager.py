from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from dotenv import dotenv_values
import cryptography.exceptions
import sys
import base64
import os

SALT_DIM = 16


def key_from_password(password: str, salt: bytes) -> bytes:
    """Return bits usable to encode/decode from a password"""
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32,
                     salt=salt, iterations=480000)
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def encrypt_env(password: str):
    """Encode .env file"""
    salt = os.urandom(SALT_DIM)
    with open(".env", "rb") as f:
        data = f.read()
    encrypted = Fernet(key_from_password(password, salt)).encrypt(data)
    with open(".env.enc", "wb") as f:
        f.write(salt+encrypted)


def load_encrypted_env(password: str):  # -> bytes
    """Load variables from encoded .env"""
    with open(".env.enc", "rb") as f:
        content = f.read()

    salt = content[:16]
    encrypted = content[16:]

    key = key_from_password(password, salt)
    try:
        decrypted = Fernet(key).decrypt(encrypted)
    except cryptography.exceptions.InvalidSignature as e:
        return e
    except InvalidToken as e:
        return e
    except Exception as e:
        return e
    import io
    # .replace('\r\n', '\n')
    return dotenv_values(stream=io.StringIO(decrypted.decode().strip()))


if __name__ == '__main__':
    match len(sys.argv):
        case 1:
            pass  # only name
        case 2:
            try:
                load_encrypted_env(str(sys.argv[1]))
            except FileNotFoundError:
                print(
                    "The file you are trying to read doesn't exist. You should create it")
        case 3:
            match sys.argv[1]:
                case 'read':
                    try:
                        dict_data = load_encrypted_env(str(sys.argv[2]))
                        print(dict_data)
                    except FileNotFoundError:
                        print(
                            "The file you are trying to read doesn't exist. You should create it")
                    except Exception as e:
                        print("Exception:", e)
                case 'write':
                    try:
                        encrypt_env(str(sys.argv[2]))
                    except Exception as e:
                        print(e)
                case _:
                    print("Expected \"mode\" and \"password\" as argument")
        case _:
            print(
                "Wrong number of arguments, expected \"mode\" and \"password\" as argument")
