import binascii
import os


def generate_token() -> str:
    return binascii.hexlify(os.urandom(40)).decode()
