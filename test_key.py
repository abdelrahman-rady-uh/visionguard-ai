from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(f"Generated key: {key}")
print(f"Key type: {type(key)}")
print(f"Key length: {len(key)}")
