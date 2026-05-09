from cryptography.fernet import Fernet
import os

if os.path.exists('backend/aes.key'):
    os.remove('backend/aes.key')

key = Fernet.generate_key()
with open('backend/aes.key', 'wb') as f:
    f.write(key)

key_size = len(open('backend/aes.key', 'rb').read())
print(f'✓ Key generated: {key_size} bytes')
