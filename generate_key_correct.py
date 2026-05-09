from cryptography.fernet import Fernet

# Generate and save the key properly
key = Fernet.generate_key()
print(f"Key to save: {key}")

# Write to file (the key is already in the correct format as bytes)
with open('backend/aes.key', 'wb') as f:
    f.write(key)

# Read it back and verify
with open('backend/aes.key', 'rb') as f:
    saved_key = f.read()
    
print(f"Saved key: {saved_key}")
print(f"Saved key length: {len(saved_key)}")

# Test it can be used by Fernet
try:
    cipher = Fernet(saved_key)
    print("✓ Key is valid and can be used by Fernet!")
except Exception as e:
    print(f"✗ Error: {e}")
