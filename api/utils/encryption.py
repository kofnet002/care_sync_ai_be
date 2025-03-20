from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class NoteEncryption:
    @staticmethod
    def generate_key_pair():
        """Generate a new RSA key pair"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()
        
        # Serialize keys for storage
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_pem, public_pem

    @staticmethod
    def encrypt_note(content: str, public_key_pem: bytes) -> dict:
        """Encrypt note content using hybrid encryption"""
        # Generate a random symmetric key
        symmetric_key = Fernet.generate_key()
        fernet = Fernet(symmetric_key)
        
        # Encrypt the content with symmetric key
        encrypted_content = fernet.encrypt(content.encode())
        
        # Load the public key
        public_key = serialization.load_pem_public_key(public_key_pem)
        
        # Encrypt the symmetric key with the public key
        encrypted_key = public_key.encrypt(
            symmetric_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return {
            'encrypted_content': base64.b64encode(encrypted_content).decode('utf-8'),
            'encrypted_key': base64.b64encode(encrypted_key).decode('utf-8')
        }

    @staticmethod
    def decrypt_note(encrypted_data: dict, private_key_pem: bytes) -> str:
        """Decrypt note content using private key"""
        try:
            # Load the private key
            private_key = serialization.load_pem_private_key(
                private_key_pem,
                password=None
            )
            
            # Decode the encrypted data
            encrypted_content = base64.b64decode(encrypted_data['encrypted_content'])
            encrypted_key = base64.b64decode(encrypted_data['encrypted_key'])
            
            # Decrypt the symmetric key
            symmetric_key = private_key.decrypt(
                encrypted_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            # Decrypt the content
            fernet = Fernet(symmetric_key)
            decrypted_content = fernet.decrypt(encrypted_content)
            
            return decrypted_content.decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")