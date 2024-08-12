from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.database import get_db
from app.models import User
from pydantic import BaseModel
import logging

# Constants for JWT
SECRET_KEY = "your_secret_key"  # Replace with a secure key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize the router
router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic model for user creation
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

# Helper functions for password verification and hashing
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Function to create a JWT token
def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Endpoint for user registration
@router.post("/register/")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        logger.info(f"Received registration request for username: {user.username}, email: {user.email}")

        # Check if the username already exists
        db_user = db.query(User).filter(User.username == user.username).first()
        if db_user:
            logger.warning(f"Username {user.username} already registered.")
            raise HTTPException(status_code=400, detail="Username already registered")
        
        # Check if the email already exists
        db_user = db.query(User).filter(User.email == user.email).first()
        if db_user:
            logger.warning(f"Email {user.email} already registered.")
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash the user's password
        hashed_password = get_password_hash(user.password)
        logger.info(f"Password hashed successfully for username: {user.username}")

        # Create a new user
        new_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"User {new_user.username} registered successfully.")

        return {"username": new_user.username, "email": new_user.email}
    
    except Exception as e:
        logger.error(f"Error during registration for username: {user.username}, email: {user.email}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Endpoint for user login
@router.post("/login/")
def login(user: UserCreate, db: Session = Depends(get_db)):
    try:
        logger.info(f"Login attempt for username: {user.username}")

        db_user = db.query(User).filter(User.username == user.username).first()
        if db_user is None or not verify_password(user.password, db_user.hashed_password):
            logger.warning(f"Invalid login attempt for username: {user.username}")
            raise HTTPException(status_code=401, detail="Invalid username or password")

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": db_user.username}, expires_delta=access_token_expires
        )
        logger.info(f"User {user.username} logged in successfully. Token generated.")

        return {"access_token": access_token, "token_type": "bearer"}
    
    except Exception as e:
        logger.error(f"Error during login for username: {user.username}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
