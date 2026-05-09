"""
Security Service - Encryption, hashing, and secure storage
"""
import hashlib
import logging
import os
from typing import Dict, Any, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logger = logging.getLogger(__name__)


class SecurityService:
    """Handle all security operations"""
    
    def __init__(self, key_path: str = "backend/fernet.key"):
        """
        Initialize security service
        
        Args:
            key_path: Path to encryption key file
        """
        self.key_path = key_path
        self.cipher = self._load_or_create_key()
    
    def _load_or_create_key(self) -> Fernet:
        """Load encryption key or create new one"""
        try:
            if os.path.exists(self.key_path):
                with open(self.key_path, 'rb') as f:
                    key = f.read().strip()
                try:
                    return Fernet(key)
                except Exception:
                    backup_path = self.key_path + ".invalid"
                    os.replace(self.key_path, backup_path)
                    logger.warning(
                        "Invalid Fernet key detected at %s. Backed it up to %s and generated a new key.",
                        self.key_path,
                        backup_path,
                    )
            else:
                os.makedirs(os.path.dirname(self.key_path), exist_ok=True)

            key = Fernet.generate_key()
            with open(self.key_path, 'wb') as f:
                f.write(key)

            return Fernet(key)
        except Exception as e:
            logger.error(f"Error loading/creating encryption key: {e}")
            raise
    
    def hash_file(self, file_path: str, algorithm: str = "sha256") -> Dict[str, Any]:
        """
        Generate hash for file integrity verification
        
        Args:
            file_path: Path to file
            algorithm: Hash algorithm (sha256, sha512, md5)
        
        Returns:
            Hash result with metadata
        """
        try:
            hash_obj = hashlib.new(algorithm)
            
            # Read file in chunks
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    hash_obj.update(chunk)
            
            file_size = os.path.getsize(file_path)
            
            return {
                "status": "success",
                "file_path": file_path,
                "hash": hash_obj.hexdigest(),
                "algorithm": algorithm,
                "file_size": file_size,
                "timestamp": self._get_timestamp()
            }
        except Exception as e:
            logger.error(f"Error hashing file: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def encrypt_file(self, file_path: str, output_path: str = None) -> Dict[str, Any]:
        """
        Encrypt file using Fernet (AES)
        
        Args:
            file_path: Path to file to encrypt
            output_path: Output path for encrypted file
        
        Returns:
            Encryption result
        """
        try:
            if output_path is None:
                output_path = file_path + ".enc"
            
            # Read original file
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # Encrypt
            encrypted_data = self.cipher.encrypt(data)
            
            # Write encrypted file
            with open(output_path, 'wb') as f:
                f.write(encrypted_data)
            
            original_hash = hashlib.sha256(data).hexdigest()
            
            return {
                "status": "success",
                "output_path": output_path,
                "original_hash": original_hash,
                "encrypted": True,
                "timestamp": self._get_timestamp()
            }
        except Exception as e:
            logger.error(f"Error encrypting file: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def decrypt_file(self, encrypted_file_path: str, output_path: str = None) -> Dict[str, Any]:
        """
        Decrypt file
        
        Args:
            encrypted_file_path: Path to encrypted file
            output_path: Output path for decrypted file
        
        Returns:
            Decryption result
        """
        try:
            # Read encrypted file
            with open(encrypted_file_path, 'rb') as f:
                encrypted_data = f.read()
            
            # Decrypt
            decrypted_data = self.cipher.decrypt(encrypted_data)
            
            if output_path is None:
                output_path = encrypted_file_path.replace('.enc', '')
            
            # Write decrypted file
            with open(output_path, 'wb') as f:
                f.write(decrypted_data)
            
            return {
                "status": "success",
                "output_path": output_path,
                "decrypted": True,
                "timestamp": self._get_timestamp()
            }
        except Exception as e:
            logger.error(f"Error decrypting file: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate secure random token"""
        return base64.urlsafe_b64encode(os.urandom(length)).decode()
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp"""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
    
    @staticmethod
    def verify_hash(file_path: str, expected_hash: str, algorithm: str = "sha256") -> bool:
        """
        Verify file hash integrity
        
        Args:
            file_path: Path to file
            expected_hash: Expected hash value
            algorithm: Hash algorithm
        
        Returns:
            True if hash matches, False otherwise
        """
        try:
            hash_obj = hashlib.new(algorithm)
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    hash_obj.update(chunk)
            
            return hash_obj.hexdigest() == expected_hash
        except Exception as e:
            logger.error(f"Error verifying hash: {e}")
            return False
