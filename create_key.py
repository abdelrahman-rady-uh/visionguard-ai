from cryptography.fernet import Fernet

# Generate a new Fernet key
key = Fernet.generate_key()
print(f'Generated key size: {len(key)} bytes')

# Write it to the file
with open('backend/aes.key', 'wb') as f:
    f.write(key)

# Verify it was written correctly
with open('backend/aes.key', 'rb') as f:
    read_key = f.read()
    print(f'Read key size: {len(read_key)} bytes')
    print(f'Keys match: {key == read_key}')
    print('✓ Fresh encryption key created successfully')
