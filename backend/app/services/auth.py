import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from app.core.config import settings
import os

# Initialize Firebase Admin
def init_firebase():
    if not firebase_admin._apps:
        try:
            # Option 1: JSON string in env var (preferred for production/Railway)
            json_str = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
            if json_str:
                import json
                cred = credentials.Certificate(json.loads(json_str))
                firebase_admin.initialize_app(cred)
                return
            
            # Option 2: Path to file (local development)
            key_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY", "serviceAccountKey.json")
            if os.path.exists(key_path):
                cred = credentials.Certificate(key_path)
                firebase_admin.initialize_app(cred)
            else:
                print(f"Warning: Firebase Admin Service Account Key not found at {key_path}")
        except Exception as e:
            print(f"Failed to initialize firebase admin: {e}")

init_firebase()

def verify_firebase_token(id_token: str) -> Optional[dict]:
    if not firebase_admin._apps:
        print("Error: Firebase Admin is not initialized. Cannot verify token.")
        return None
        
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        print(f"Firebase token verification failed (Detailed Error): {e}")
        return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

