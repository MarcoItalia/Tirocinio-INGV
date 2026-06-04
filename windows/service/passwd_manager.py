from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from dotenv import dotenv_values
import cryptography.exceptions
import sys
import base64
import os
import io
from types import SimpleNamespace
from dict_to_namespace import dict_to_namespace

__SALT_DIM = 16


def __key_from_password(password: str, salt: bytes) -> bytes:
    """Return bits usable to encode/decode from a password"""
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32,
                     salt=salt, iterations=480000)
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def encrypt_env(password: str):
    """Encode .env file"""
    salt = os.urandom(__SALT_DIM)
    with open(".env", "rb") as f:
        data = f.read()
    encrypted = Fernet(__key_from_password(password, salt)).encrypt(data)
    with open(".env.enc", "wb") as f:
        f.write(salt+encrypted)


def load_encrypted_env(password: str) -> dict:
    """Load variables from encoded .env. Return them as a Dictionary or None if an error occured"""
    with open(".env.enc", "rb") as f:
        content = f.read()

    salt = content[:__SALT_DIM]
    encrypted = content[__SALT_DIM:]

    key = __key_from_password(password, salt)
    try:
        decrypted = Fernet(key).decrypt(encrypted)
    except cryptography.exceptions.InvalidSignature as e:
        print("load_encrypted_env raised", repr(e))
        return None
    except InvalidToken as e:
        print("load_encrypted_env raised", repr(e))
        return None
    except Exception as e:
        print("load_encrypted_env raised", repr(e))
        return None
    return dotenv_values(stream=io.StringIO(decrypted.decode().strip()))


def load_encrypted_env_snmspace(password: str) -> SimpleNamespace:
    """Load variables from encoded .env. Return them as a SimpleNamespace or None if an error occured"""
    return dict_to_namespace(load_encrypted_env(password))


if __name__ == '__main__':
    match len(sys.argv):
        case 2:
            try:
                dict_data = load_encrypted_env(str(sys.argv[1]))
                if dict_data is not None:
                    print(dict_data)
            except FileNotFoundError:
                print(
                    "The file you are trying to read doesn't exist. You should create it")
            except Exception as e:
                print("Exception:", repr(e))
        case 3:
            match sys.argv[1]:
                case 'read':
                    try:
                        dict_data = load_encrypted_env(str(sys.argv[2]))
                        if dict_data is not None:
                            print(dict_data)
                    except FileNotFoundError:
                        print(
                            "The file you are trying to read doesn't exist. You should create it")
                    except Exception as e:
                        print("Exception:", repr(e))
                case 'write':
                    try:
                        encrypt_env(str(sys.argv[2]))
                    except Exception as e:
                        print("Exception: ", e)
                case _:
                    print("Expected \"mode\" and \"password\" as argument")
        case _:
            print(
                "Wrong number of arguments, expected \"mode\" and \"password\" as argument")
